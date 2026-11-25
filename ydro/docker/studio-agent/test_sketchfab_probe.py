import io
import json
import unittest
import zipfile
from unittest.mock import patch
from sketchfab_probe import api, probe, license_ok, allowed_cdn, validate_archive, NetworkFailure

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
    @patch("sketchfab_probe.cdn_diagnostics")
    @patch("sketchfab_probe.time.sleep")
    @patch("sketchfab_probe.request_bytes",side_effect=NetworkFailure("network request failed: ReadTimeout"))
    @patch("sketchfab_probe.api")
    def test_network_retry(self, api, request, sleep, diagnostics):
        uid="a"*32
        link={"gltf":{"url":"https://sketchfab-prod-media.s3.amazonaws.com/archives/a"}}
        api.side_effect=[{"uid":"test"},{"results":[{"uid":uid,"faceCount":30}]},
                         {"isDownloadable":True,"license":{"slug":"cc0"}},link,link]
        with self.assertRaisesRegex(ValueError,"SKETCHFAB_CDN_DOWNLOAD_FAILED"):
            probe("fake-test-token")
        self.assertEqual(request.call_count,2)
        self.assertEqual(api.call_count,5)
        diagnostics.assert_called_once_with("sketchfab-prod-media.s3.amazonaws.com")
    @patch("sketchfab_probe.time.sleep")
    @patch("sketchfab_probe.request_bytes",side_effect=[NetworkFailure("ReadTimeout"),b'{"results":[]}'])
    def test_api_retry(self,request,sleep):
        self.assertEqual(api("/search","fake-token"),{"results":[]})
        self.assertEqual(request.call_count,2)
        self.assertEqual(request.call_args.kwargs["timeout"],(12,45))
        sleep.assert_called_once_with(2)
    @patch("sketchfab_probe.request_bytes",side_effect=ValueError("HTTP 401"))
    def test_api_does_not_retry_auth_failure(self,request):
        with self.assertRaisesRegex(ValueError,"HTTP 401"):
            api("/me","fake-token")
        request.assert_called_once()
    def test_invalid_archive(self):
        with self.assertRaises(ValueError):
            validate_archive(b"not a zip")
