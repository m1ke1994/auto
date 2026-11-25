import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile
from models3d import ModelLibrary, safe_relative, file_bytes
from site_store import SiteStore

class ModelTests(unittest.TestCase):
    def test_paths(self):
        for path in ("../x.bin","/x.bin","http://example.org/a.png","textures/../x.bin","x.exe","textures/a%2f.png","x\\a.bin"):
            self.assertFalse(safe_relative(path),path)
        self.assertTrue(safe_relative("textures/a.jpg"))
    @patch("models3d.fetch",return_value=b"bad")
    def test_checksum(self,fetch):
        with self.assertRaisesRegex(ValueError,"integrity"):
            file_bytes({"url":"https://dl.polyhaven.org/x","size":3,"md5":"0"*32},10)
    @patch("models3d.file_bytes")
    @patch("models3d.api")
    def test_model_export(self,api,download):
        raw=json.dumps({"asset":{"version":"2.0"},"meshes":[{}],"buffers":[{"uri":"geometry.bin"}],"images":[{"uri":"textures/a.jpg"}]}).encode()
        api.side_effect=[{"test_chair":{"type":2,"polycount":100,"name":"Chair","authors":{"Artist":"All"}}},{"gltf":{"1k":{"gltf":{"include":{"geometry.bin":{},"textures/a.jpg":{}}}}}}]
        download.side_effect=[raw,b"geometry",b"photo"]
        library=ModelLibrary()
        self.assertEqual(library.search("chair")[0]["license"],"CC0")
        asset=library.save("test_chair")
        self.assertEqual(asset["path"],"tn-models/test_chair/model.gltf")
        store=SiteStore(models=library)
        store.write("src/App.vue","<template><main>Site</main></template>")
        store.write("src/style.css","main { color: red; }")
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"site.zip"
            store.export(output,"deepseek-v4-pro")
            with zipfile.ZipFile(output) as z:
                self.assertIn("public/"+asset["path"],z.namelist())
                self.assertIn("public/tn-models/test_chair/textures/a.jpg",z.namelist())
                self.assertIn("MODEL_CREDITS.json",z.namelist())
                self.assertIn("Poly Haven",z.read("index.html").decode())
