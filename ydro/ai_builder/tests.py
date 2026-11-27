from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from .generator import generate_demo
import json
import tempfile
from pathlib import Path

@override_settings(STUDIO_DEMO_ENABLED=True, STUDIO_AI_PROVIDER='demo')
class StudioTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.a = User.objects.create_user(username="studio-a", password="test-password")
        self.b = User.objects.create_user(username="studio-b", password="test-password")
        self.client.force_authenticate(self.a)
    def test_lifecycle_and_isolation(self):
        url = "/api/studio/projects/"
        result = self.client.post(url, {"name": "Demo", "prompt": "Test site", "engine": "quick"}, format="json")
        self.assertEqual(result.status_code, 201)
        data = result.data
        root = url + data["id"] + "/"
        first = data["revisions"][0]["id"]
        result = self.client.post(root+"edit/", {"instruction":"темный"}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data["revisions"]), 2)
        self.assertEqual(self.client.post(root+f"publish/{first}/").data["published_revision"], first)
        self.assertEqual(self.client.get(root+f"export/{first}/").status_code, 200)
        self.client.force_authenticate(self.b)
        self.assertEqual(self.client.get(root).status_code, 404)
        self.assertEqual(self.client.post(root+"edit/", {"instruction":"test"}).status_code, 404)
        self.assertEqual(self.client.post(root+f"publish/{first}/").status_code, 404)
        self.assertEqual(self.client.get(root+f"export/{first}/").status_code, 404)
    def test_escape(self):
        self.assertNotIn("<script>", generate_demo("<script>", "<script>", "<script>"))
    @override_settings(STUDIO_DEMO_ENABLED=False)
    def test_disabled(self):
        self.assertEqual(self.client.get("/api/studio/projects/").status_code, 404)

    def test_vue_export_and_edit_base(self):
        import io
        import json
        import zipfile
        url="/api/studio/projects/"
        p=self.client.post(url,{"name":"Поэт","prompt":"Стихи","style":"premium","engine":"quick"},format="json").data
        root=url+p["id"]+"/"
        original=p["revisions"][0]["id"]
        edit=self.client.post(root+"edit/",{"instruction":"тёмный фон","revision":original},format="json")
        self.assertEqual(edit.status_code,200)
        dark=edit.data["revisions"][0]["id"]
        response=self.client.get(root+f"export/{dark}/")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            self.assertIn("src/App.vue",z.namelist())
            spec=json.loads(z.read("src/design.json"))
            self.assertEqual(spec["theme"],"dark")
        second=self.client.post(root+"edit/",{"instruction":"оставь как есть","revision":original},format="json")
        self.assertEqual(second.status_code,200)
        from .models import Revision
        self.assertEqual(Revision.objects.get(pk=second.data["revisions"][0]["id"]).design["theme"],"editorial")

    def test_cinematic_job_queue_status_and_preview(self):
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(
            STUDIO_CINEMATIC_ENABLED=True,STUDIO_JOB_ROOT=jobs,STUDIO_OUTPUT_ROOT=outputs
        ):
            payload={"name":"Architecture Film","prompt":"Cinematic architecture bureau","style":"cinema","engine":"cinematic","hero_mode":"environment"}
            with self.captureOnCommitCallbacks(execute=True):
                response=self.client.post("/api/studio/projects/",payload,format="json")
            self.assertEqual(response.status_code,202)
            project_id=response.data["id"]
            queued=Path(jobs)/"pending"/f"{project_id}.json"
            self.assertTrue(queued.is_file())
            envelope=json.loads(queued.read_text(encoding="utf-8"))
            self.assertEqual(envelope["profile"],"cinema")
            self.assertEqual(envelope["hero_mode"],"environment")

            duplicate=self.client.post("/api/studio/projects/",payload,format="json")
            self.assertEqual(duplicate.status_code,409)

            run="verified-architecture"
            dist=Path(outputs)/run/"dist"
            dist.mkdir(parents=True)
            (dist/"index.html").write_text("<h1>Verified architecture</h1>",encoding="utf-8")
            state=Path(jobs)/"status"/f"{project_id}.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"status":"complete","stage":"verified","error":"","run_directory":run}),encoding="utf-8")
            detail=self.client.get(f"/api/studio/projects/{project_id}/")
            self.assertEqual(detail.data["generation_status"],"complete")
            self.assertTrue(detail.data["preview_path"])
            preview=self.client.get(detail.data["preview_path"])
            self.assertEqual(preview.status_code,200)
            self.assertIn(b"Verified architecture",b"".join(preview.streaming_content))

    @override_settings(STUDIO_CINEMATIC_ENABLED=False)
    def test_cinematic_queue_requires_local_worker(self):
        response=self.client.post("/api/studio/projects/",{"name":"No worker","prompt":"test","engine":"cinematic"},format="json")
        self.assertEqual(response.status_code,503)

    def test_cinematic_draft_preview_keeps_visual_score(self):
        from .models import Project
        with tempfile.TemporaryDirectory() as outputs, override_settings(STUDIO_OUTPUT_ROOT=outputs):
            run=Path(outputs)/"draft"
            dist=run/"dist"
            dist.mkdir(parents=True)
            (dist/"index.html").write_text("<h1>Local draft</h1>",encoding="utf-8")
            marker=run/"studio-result.json"
            project=Project.objects.create(owner=self.a,name="Draft",prompt="test",engine="cinematic",
                generation_status="complete",generation_stage="technical-preview",run_directory="draft")
            url=f"/api/studio/projects/{project.id}/"
            for status,score in (("needs_revision",62),("unavailable",None),("skipped",None),("passed",91)):
                marker.write_text(json.dumps({"technical_passed":True,"status":status,"score":score}),encoding="utf-8")
                data=self.client.get(url).data
                self.assertEqual(data["generation_status"],"complete")
                self.assertEqual(data["visual_review"],{"status":status,"score":score,"threshold":85})
                self.assertTrue(data["preview_path"])
                self.assertFalse(data["source_archive_available"])
                self.assertEqual(self.client.get(data["preview_path"]).status_code,200)
            marker.write_text(json.dumps({"technical_passed":True,"status":"passed","score":62}),encoding="utf-8")
            self.assertEqual(self.client.get(url).data["visual_review"]["status"],"unverified")
            project.generation_stage="verified-import"
            project.save(update_fields=["generation_stage"])
            marker.write_text(json.dumps({"technical_passed":True,"status":"passed","score":91}),encoding="utf-8")
            self.assertEqual(self.client.get(url).data["visual_review"]["status"],"unverified")
            project.generation_status="failed"
            project.save(update_fields=["generation_status"])
            self.assertEqual(self.client.get(url).data["preview_path"],"")

    def test_default_generation_uses_cinematic_not_demo(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(
            STUDIO_CINEMATIC_ENABLED=True, STUDIO_JOB_ROOT=jobs, STUDIO_OUTPUT_ROOT=outputs
        ), patch("ai_builder.views.generate") as quick:
            with self.captureOnCommitCallbacks(execute=True):
                response=self.client.post("/api/studio/projects/", {"name":"Cars","prompt":"Автосайт"},format="json")
            self.assertEqual(response.status_code,202)
            self.assertEqual(response.data["engine"],"cinematic")
            self.assertEqual(response.data["revisions"],[])
            envelope=json.loads((Path(jobs)/"pending"/f'{response.data["id"]}.json').read_text(encoding="utf-8"))
            self.assertEqual(envelope["profile"],"cinema")
            self.assertEqual(envelope["asset_style"],"realistic")
            quick.assert_not_called()

    @override_settings(STUDIO_CINEMATIC_ENABLED=False)
    def test_default_generation_never_silently_falls_back_to_quick(self):
        from unittest.mock import patch
        from .models import Project
        with patch("ai_builder.views.generate") as quick:
            response=self.client.post("/api/studio/projects/",{"name":"Cars","prompt":"Автосайт"},format="json")
        self.assertEqual(response.status_code,503)
        quick.assert_not_called()
        self.assertFalse(Project.objects.filter(owner=self.a).exists())

    def test_progress_event_tracks_worker_not_polling(self):
        from .models import Project
        from django.utils import timezone
        with tempfile.TemporaryDirectory() as jobs, override_settings(STUDIO_JOB_ROOT=jobs):
            project=Project.objects.create(owner=self.a,name="Progress",prompt="test",engine="cinematic",
                generation_status="queued",generation_stage="queued")
            path=Path(jobs)/"status"/f"{project.id}.json"
            path.parent.mkdir()
            stamp=timezone.now().isoformat()
            url=f"/api/studio/projects/{project.id}/"
            for stage in ("preparing","assets","generating","building","auditing","visual-review","finalizing"):
                path.write_text(json.dumps({"status":"running","stage":stage,"updated_at":stamp,"run_directory":""}),encoding="utf-8")
                first=self.client.get(url).data
                second=self.client.get(url).data
                self.assertEqual(first["generation_stage"],stage)
                self.assertEqual(first["generation_event_at"],stamp)
                self.assertEqual(first["generation_event_at"],second["generation_event_at"])
                self.assertEqual(first["updated_at"],second["updated_at"])
            path.write_text("[]",encoding="utf-8")
            self.assertIsNone(self.client.get(url).data["generation_event_at"])

    def test_cinematic_contacts_are_saved_and_queued(self):
        contacts={"phone":"+7 (900) 123-45-67","email":"sales@example.com","telegram":"https://t.me/example","address":"Москва"}
        with tempfile.TemporaryDirectory() as jobs, override_settings(STUDIO_CINEMATIC_ENABLED=True,STUDIO_JOB_ROOT=jobs):
            with self.captureOnCommitCallbacks(execute=True):
                response=self.client.post("/api/studio/projects/",{"name":"Contact site","prompt":"Test","contacts":contacts},format="json")
            self.assertEqual(response.status_code,202)
            self.assertEqual(response.data["contacts"],contacts)
            payload=json.loads((Path(jobs)/"pending"/f'{response.data["id"]}.json').read_text(encoding="utf-8"))
            self.assertEqual(payload["contacts"],contacts)
            self.assertEqual(payload["prompt"],"Test")
            self.client.force_authenticate(self.b)
            self.assertEqual(self.client.get("/api/studio/projects/"+response.data["id"]+"/").status_code,404)

    def test_reject_unsafe_contact_links(self):
        for url in ("javascript:alert(1)","ftp://example.com/path","https://user:password@example.com/"):
            response=self.client.post("/api/studio/projects/",{"name":"Test","prompt":"test","contacts":{"website":url}},format="json")
            self.assertEqual(response.status_code,400)

    @override_settings(STUDIO_CINEMATIC_ENABLED=True)
    def test_block_edit_candidate_accept_and_rollback(self):
        from .models import Project
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(STUDIO_JOB_ROOT=jobs,STUDIO_OUTPUT_ROOT=outputs):
            root=Path(outputs)
            for run in ("original","block-edit-test"):
                dist=root/run/"dist"
                dist.mkdir(parents=True)
                (dist/"index.html").write_text(run)
                (root/run/"tracknode-agent-site.zip").write_bytes(b"fixture")
                (root/run/"studio-result.json").write_text(json.dumps({"technical_passed":True,"status":"skipped"}))
            p=Project.objects.create(owner=self.a,name="Cars",prompt="Cars",engine="cinematic",run_directory="original",generation_stage="technical-preview")
            url=f"/api/studio/projects/{p.id}/"
            with self.captureOnCommitCallbacks(execute=True):
                result=self.client.post(url+"blocks/home/regenerate/",{"instruction":"Fix title","upgrade_motion":True},format="json")
            self.assertEqual(result.status_code,202)
            edit=result.data["block_edit"]
            self.assertEqual(result.data["preview_version"],"original")
            envelope=json.loads((Path(jobs)/"pending"/f'{edit["id"]}.json').read_text())
            self.assertEqual(envelope["base_run"],"original")
            self.assertEqual(envelope["kind"],"block_edit")
            self.assertEqual(self.client.post(url+"blocks/about/regenerate/",{"instruction":"test"},format="json").status_code,409)
            status=Path(jobs)/"status"/f'{edit["id"]}.json'
            status.parent.mkdir()
            status.write_text(json.dumps({"project_id":edit["id"],"status":"complete","stage":"technical-preview","run_directory":"block-edit-test"}))
            self.assertEqual(self.client.get(url).data["block_edit"]["status"],"complete")
            decision=url+"block-edits/"+edit["id"]+"/"
            self.client.force_authenticate(self.b)
            self.assertEqual(self.client.post(decision+"accept/").status_code,404)
            self.client.force_authenticate(self.a)
            self.assertEqual(self.client.post(decision+"accept/").data["preview_version"],"block-edit-test")
            self.assertEqual(self.client.post(decision+"rollback/").data["preview_version"],"original")

    @override_settings(STUDIO_CINEMATIC_ENABLED=True)
    def test_local_hero_film_queues_without_replacing_current_version(self):
        from .models import Project
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(STUDIO_JOB_ROOT=jobs,STUDIO_OUTPUT_ROOT=outputs):
            root=Path(outputs)/"original"
            (root/"dist").mkdir(parents=True)
            (root/"dist"/"index.html").write_text("original")
            (root/"tracknode-agent-site.zip").write_bytes(b"fixture")
            p=Project.objects.create(owner=self.a,name="Cars",prompt="Cars",engine="cinematic",run_directory="original")
            url=f"/api/studio/projects/{p.id}/blocks/"
            payload={"instruction":"film","local_hero_film":True}
            self.assertEqual(self.client.post(url+"about/regenerate/",payload,format="json").status_code,400)
            with self.captureOnCommitCallbacks(execute=True):
                result=self.client.post(url+"home/regenerate/",payload,format="json")
            self.assertEqual(result.status_code,202)
            edit=result.data["block_edit"]
            envelope=json.loads((Path(jobs)/"pending"/f'{edit["id"]}.json').read_text())
            self.assertIs(envelope["local_hero_film"],True)
            self.assertEqual(result.data["preview_version"],"original")
            self.assertEqual(envelope["base_run"],"original")


    @override_settings(STUDIO_CINEMATIC_ENABLED=True)
    def test_project_versions_restore_history_and_export(self):
        from .models import Project, BlockEdit
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(STUDIO_JOB_ROOT=jobs, STUDIO_OUTPUT_ROOT=outputs):
            root=Path(outputs)
            for run in ("original", "block-edit-one", "block-edit-two"):
                dist=root/run/"dist"
                dist.mkdir(parents=True)
                (dist/"index.html").write_text(run)
                (root/run/"tracknode-agent-site.zip").write_bytes(run.encode())
                (root/run/"studio-result.json").write_text(json.dumps({"technical_passed":True,"status":"skipped"}))
            p=Project.objects.create(owner=self.a,name="Versions",prompt="Test",engine="cinematic",run_directory="original",generation_stage="technical-preview")
            url=f"/api/studio/projects/{p.id}/"
            initial=self.client.get(url).data["versions"][0]
            self.assertEqual(initial["number"],1)
            self.assertTrue(initial["current"])
            self.assertEqual(len(self.client.get(url+"versions/").data),1)
            status_dir=Path(jobs)/"status"
            status_dir.mkdir()
            for base,run in (("original","block-edit-one"),("block-edit-one","block-edit-two")):
                e=BlockEdit.objects.create(project=p,block="home",instruction=run,base_run=base,base_stage="technical-preview")
                (status_dir/f"{e.id}.json").write_text(json.dumps({"project_id":str(e.id),"status":"complete","stage":"technical-preview","run_directory":run}))
                accepted=self.client.post(url+f"block-edits/{e.id}/accept/")
                self.assertEqual(accepted.status_code,200)
            versions=accepted.data["versions"]
            self.assertEqual([x["number"] for x in versions],[3,2,1])
            self.assertTrue(versions[0]["current"])
            latest=versions[0]
            self.assertEqual(self.client.get(initial["preview_path"]).status_code,200)
            self.assertEqual(self.client.get(url+f'versions/{initial["id"]}/export/').status_code,200)
            restore_url=url+f'versions/{initial["id"]}/restore/'
            self.client.force_authenticate(self.b)
            self.assertEqual(self.client.get(url+"versions/").status_code,404)
            self.assertEqual(self.client.post(restore_url,{"expected_version":latest["id"]},format="json").status_code,404)
            self.assertEqual(self.client.get(url+f'versions/{initial["id"]}/export/').status_code,404)
            self.client.force_authenticate(self.a)
            pending=BlockEdit.objects.create(project=p,block="home",instruction="Pending",base_run="block-edit-two",base_stage="technical-preview")
            self.assertEqual(self.client.post(restore_url,{"expected_version":latest["id"]},format="json").status_code,409)
            pending.decision="discarded"
            pending.save(update_fields=["decision"])
            restored=self.client.post(restore_url,{"expected_version":latest["id"]},format="json")
            self.assertEqual(restored.status_code,200)
            self.assertEqual(restored.data["preview_version"],"original")
            self.assertEqual(restored.data["versions"][0]["kind"],"restored")
            self.assertEqual(restored.data["versions"][0]["restored_from"],initial["id"])
            self.assertEqual(len(restored.data["versions"]),4)
            self.assertEqual(self.client.post(restore_url,{"expected_version":latest["id"]},format="json").status_code,409)
            self.assertTrue((root/"block-edit-two"/"dist"/"index.html").exists())
            (root/"block-edit-one"/"tracknode-agent-site.zip").unlink()
            missing=url+f'versions/{versions[1]["id"]}/restore/'
            self.assertEqual(self.client.post(missing,{"expected_version":restored.data["versions"][0]["id"]},format="json").status_code,409)

    def test_project_versions_adopt_existing_accepted_history(self):
        from .models import Project, BlockEdit
        with tempfile.TemporaryDirectory() as jobs, tempfile.TemporaryDirectory() as outputs, override_settings(STUDIO_JOB_ROOT=jobs, STUDIO_OUTPUT_ROOT=outputs):
            root=Path(outputs)
            for run in ("original","block-edit-old"):
                (root/run/"dist").mkdir(parents=True)
                (root/run/"dist"/"index.html").write_text(run)
                (root/run/"studio-result.json").write_text(json.dumps({"technical_passed":True,"status":"skipped"}))
            p=Project.objects.create(owner=self.a,name="Legacy",prompt="Test",engine="cinematic",run_directory="block-edit-old",generation_stage="technical-preview")
            e=BlockEdit.objects.create(project=p,block="home",instruction="Old",base_run="original",base_stage="technical-preview",decision="accepted")
            status=Path(jobs)/"status"/f"{e.id}.json"
            status.parent.mkdir()
            status.write_text(json.dumps({"project_id":str(e.id),"status":"complete","stage":"technical-preview","run_directory":"block-edit-old"}))
            url=f"/api/studio/projects/{p.id}/versions/"
            first=self.client.get(url).data
            self.assertEqual(len(first),2)
            self.assertTrue(first[0]["current"])
            self.assertTrue(all(v["legacy"] for v in first))
            self.assertEqual([v["id"] for v in self.client.get(url).data],[v["id"] for v in first])
