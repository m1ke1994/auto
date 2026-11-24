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
