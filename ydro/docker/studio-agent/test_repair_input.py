import tempfile
import unittest
import zipfile
from pathlib import Path
from site_store import SiteStore
from media import MediaLibrary
from models3d import ModelLibrary
from repair_input import restore

class RepairTests(unittest.TestCase):
    def test_restore_source_and_remove_model(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"site.zip"
            old=SiteStore(MediaLibrary(""),ModelLibrary())
            old.write("src/App.vue","<template><main>Site</main></template>")
            old.write("src/style.css","main { color: red; }")
            old.set_plan("Preserve the original art direction and improve the page. "*2)
            old.export(path,"test")
            new=SiteStore(MediaLibrary(""),ModelLibrary())
            restore(new,path)
            self.assertEqual(old.files,new.files)
            self.assertFalse(new.self_review)
            new.models.credits["chair"]={"path":"tn-models/chair/model.gltf"}
            new.models.assets["public/tn-models/chair/model.gltf"]=b"model"
            new.remove_model("chair")
            self.assertFalse(new.models.assets)
            self.assertIn("chair",new.models.rejected)
            with self.assertRaises(ValueError):
                new.models.save("chair")
    def test_reject_unsafe_archive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"site.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("../secret","x")
            with self.assertRaises(ValueError):
                restore(SiteStore(MediaLibrary(""),ModelLibrary()),p)
