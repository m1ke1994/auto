import tempfile
import json
import unittest
import zipfile
from pathlib import Path
from site_store import SiteStore
from media import MediaLibrary
from models3d import ModelLibrary
from repair_input import restore, technical_notes, critic_notes, photo_repair_allowed

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

    def test_checkpoint_atomic_and_not_publishable(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source-checkpoint.zip"
            old=SiteStore(MediaLibrary(""),ModelLibrary())
            old.set_plan("Keep this original layout and recover only the missing files. "*2)
            self.assertFalse(old.checkpoint(p,"test","cinema"))
            old.write("src/style.css","main { color: red; }")
            self.assertTrue(old.checkpoint(p,"test","cinema"))
            old.write("src/style.css","main { color: blue; }")
            old.checkpoint(p,"test","cinema")
            self.assertFalse(p.with_name(p.name+".tmp").exists())
            with self.assertRaises(ValueError):
                restore(SiteStore(MediaLibrary(""),ModelLibrary()),p)
            new=SiteStore(MediaLibrary(""),ModelLibrary())
            info=restore(new,p,allow_checkpoint=True)
            self.assertTrue(info["checkpoint"])
            self.assertEqual(old.files,new.files)
            with self.assertRaises(ValueError):
                new.export(Path(d)/"final.zip","test","cinema")

    def test_photo_asset_repair_policy_is_model_aware(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"visual-review.json"
            report={
                "model":"deepseek-flash","status":"needs_revision","passed":False,
                "devices":{
                    "desktop":{"score":52,"summary":"Photo assets are weak.","scores":{
                        "asset_quality":12,"composition":12,"originality":8,"typography":6,
                        "sections":5,"lighting_palette":5,"usability":4},"issues":[]},
                    "mobile":{"score":54,"summary":"Some images lack impact.","scores":{
                        "asset_quality":15,"composition":12,"originality":8,"typography":6,
                        "sections":5,"lighting_palette":5,"usability":3},"issues":[]}
                }
            }
            p.write_text(json.dumps(report),encoding="utf-8")
            notes=critic_notes(p)
            self.assertTrue(photo_repair_allowed({},notes))
            self.assertFalse(photo_repair_allowed({"approved-car-model":{}},notes))
            report["devices"]["desktop"]["scores"]["asset_quality"]=18
            report["devices"]["mobile"]["scores"]["asset_quality"]=20
            p.write_text(json.dumps(report),encoding="utf-8")
            notes=critic_notes(p)
            self.assertFalse(photo_repair_allowed({},notes))

    def test_technical_diagnostics_reject_infrastructure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"failure.json"
            data={"kind":"tracknode-technical-failure","stage":"audit",
                  "audit":{"passed":False,"checks":[
                    {"name":"desktop","checks":{"noHorizontalOverflow":False}},
                    {"name":"mobile","checks":{"noHorizontalOverflow":True}}]}}
            def save():
                p.write_text(json.dumps(data),encoding="utf-8")
            save()
            self.assertIn("noHorizontalOverflow",technical_notes(p))
            data["audit"]["error"]="browser crashed"
            save()
            with self.assertRaises(ValueError):
                technical_notes(p)
            del data["audit"]["error"]
            data["audit"]["checks"][0]["checks"]={"importedModelsReady":False}
            save()
            with self.assertRaises(ValueError):
                technical_notes(p)
            data={"kind":"tracknode-technical-failure","stage":"build","diagnostic":"Vue parse error"}
            save()
            self.assertIn("Vue parse error",technical_notes(p))
