import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from models3d import ModelLibrary
from sketchfab_models import SketchfabLibrary, unpack_model, license_info
from site_store import SiteStore

def archive_bytes(uri="mesh.bin", extra=None):
    scene={"asset":{"version":"2.0"},"meshes":[{}],"buffers":[{"uri":uri,"byteLength":4}]}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as archive:
        archive.writestr("scene.gltf",json.dumps(scene))
        archive.writestr("mesh.bin",b"mesh")
        if extra:
            archive.writestr(extra,b"bad")
    return buf.getvalue()

class SketchfabImportTests(unittest.TestCase):
    def test_unsafe_paths(self):
        for raw in [archive_bytes("../mesh.bin"),archive_bytes("https://other.test/mesh.bin"),archive_bytes(extra="../bad.bin")]:
            with self.assertRaises(ValueError):
                unpack_model(raw,"public/test/",10000)
        with self.assertRaises(ValueError):
            unpack_model(archive_bytes(),"public/test/",4)
    def test_license(self):
        self.assertIsNone(license_info({"license":{"slug":"by-nc","url":"https://creativecommons.org/licenses/by-nc/4.0/"}}))
        self.assertEqual(license_info({"license":{"url":"http://creativecommons.org/licenses/by/4.0/"}})[0],"CC BY 4.0")
    @patch("sketchfab_models.request_bytes",return_value=archive_bytes())
    @patch("sketchfab_models.api")
    def test_export(self,api,download):
        uid="a"*32
        detail={"name":"Chair","faceCount":30,"isDownloadable":True,"user":{"username":"Artist"},
                "license":{"url":"https://creativecommons.org/licenses/by/4.0/"}}
        api.side_effect=[{"results":[{"uid":uid,"faceCount":30}]},detail,detail,
                         {"gltf":{"url":"https://sketchfab-prod-media.s3.amazonaws.com/archives/a"}}]
        models=ModelLibrary()
        library=SketchfabLibrary("fake-test-token",models)
        self.assertEqual(library.search("chair")[0]["id"],uid)
        item=library.save(uid)
        self.assertEqual(models.downloads,1)
        self.assertNotIn("headers",download.call_args.kwargs)
        store=SiteStore(models=models)
        store.write("src/App.vue","<template><main>Test</main></template>")
        store.write("src/style.css","main { color: red; }")
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"site.zip"
            store.export(target,"test")
            with zipfile.ZipFile(target) as z:
                self.assertIn("public/"+item["path"],z.namelist())
                html=z.read("index.html").decode()
                self.assertIn("Artist",html)
                self.assertIn("Sketchfab",html)
                self.assertIn("CC BY 4.0",html)
                self.assertNotIn("fake-test-token",z.read("MODEL_CREDITS.json").decode())
