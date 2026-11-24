from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from .generator import generate_demo

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
