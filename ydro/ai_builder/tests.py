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
        result = self.client.post(url, {"name": "Demo", "prompt": "Test site"}, format="json")
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
        p=self.client.post(url,{"name":"Поэт","prompt":"Стихи","style":"premium"},format="json").data
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
