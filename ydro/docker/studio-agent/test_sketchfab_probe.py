import io
import json
import unittest
import zipfile
from unittest.mock import patch
from sketchfab_probe import probe, license_ok, allowed_cdn, validate_archive

class SketchfabTests(unittest.TestCase):
    def test_license_and_hosts(self):
        self.assertTrue(license_ok({"license":{"slug":"by"}}))
        self.assertFalse(license_ok({"license":{"slug":"by-nc"}}))
        self.assertFalse(license_ok({}))
        self.assertFalse(allowed_cdn("https://sketchfab-prod-media.s3.amazonaws.com.evil.test/archives/a"))
        self.assertTrue(allowed_cdn("https://sketchfab-prod-media.s3.amazonaws.com/archives/a"))
    @patch("sketchfab_probe.request_bytes")
    @patch("sketchfab_probe.api")
    def test_probe(self, api, request):
        uid="a"*32
        api.side_effect=[{"uid":"test"},{"results":[{"uid":uid,"faceCount":30,"isDownloadable":True}]},
                         {"isDownloadable":True,"license":{"slug":"cc0"}},
                         {"gltf":{"url":"https://sketchfab-prod-media.s3.amazonaws.com/archives/a"}}]
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as archive:
            archive.writestr("scene.gltf",json.dumps({"asset":{"version":"2.0"},"meshes":[{}]}))
        request.return_value=buf.getvalue()
        probe("fake-test-token")
        self.assertNotIn("headers",request.call_args.kwargs)
        self.assertEqual(api.call_args.args[0],"/models/"+uid+"/download")
    def test_invalid_archive(self):
        with self.assertRaises(ValueError):
            validate_archive(b"not a zip")
