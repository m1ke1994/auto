from pathlib import Path
import unittest
from quality import quality_issues

ROOT=Path(__file__).parent
STORY=(ROOT/"SceneStory.vue").read_text(encoding="utf-8")

class SceneComponentTests(unittest.TestCase):
    def test_scene_story_has_mobile_visual_slot(self):
        self.assertIn('name="mobile-visual"',STORY)
        self.assertIn(".tn-story .tn-story-stage { display: none; }",STORY)
        self.assertIn(".tn-story .tn-story-mobile-visual",STORY)

    def test_active_story_caption_has_readable_state(self):
        self.assertIn("opacity: .36",STORY)
        self.assertIn("opacity: 1",STORY)

    def test_custom_story_visual_requires_mobile_visual_slot(self):
        app='''<SceneStory :chapters="chapters">
<template #visual="{ item }"><div>{{ item.title }}</div></template>
</SceneStory>'''
        issues=quality_issues({"src/App.vue":app},"cinema")
        self.assertTrue(any("#mobile-visual" in issue for issue in issues))
        app=app.replace("</SceneStory>",'<template #mobile-visual="{ item }"><div>{{ item.title }}</div></template>\n</SceneStory>')
        issues=quality_issues({"src/App.vue":app},"cinema")
        self.assertFalse(any("#mobile-visual" in issue for issue in issues))

    def test_procedural_direction_preserves_explicit_no_3d_and_other_subjects(self):
        from art_direction import cinematic_direction
        p={"mode":"cinematic","subject":"beauty atelier"}
        self.assertEqual(cinematic_direction(p,None,"Без внешних 3D-моделей")["hero_preset"],"serum")
        self.assertIsNone(cinematic_direction(p,None,"Без 3D")["hero_preset"])
        self.assertIsNone(cinematic_direction({"mode":"cinematic","subject":"architecture"},None,"office")["hero_preset"])
        self.assertIsNone(cinematic_direction(p,{"yaw":45},"beauty")["hero_preset"])

    def test_trusted_object_contract(self):
        from site_store import SiteStore
        s=SiteStore()
        s.hero_preset="serum"
        self.assertTrue(s.scene_issues())
        s.write("src/App.vue", """<script setup>import HeroObjectStage from './components/HeroObjectStage.vue'</script><template><section id="home"><HeroObjectStage preset="serum" /></section></template>""")
        self.assertFalse(s.scene_issues())
        with self.assertRaises(ValueError):
            s.write("src/components/HeroObjectStage.vue","override")
        self.assertIn("import('three')",(ROOT/"HeroObjectStage.vue").read_text(encoding="utf-8"))

    def test_automated_review_is_honestly_labeled(self):
        import tempfile, zipfile, json
        from site_store import SiteStore
        s=SiteStore()
        s.write("src/App.vue","<template><main><h1>Example</h1></main></template>")
        s.write("src/style.css","main{color:red}")
        s.set_review("Automated structural review only; build and visual quality unverified.",origin="automated_structural")
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"site.zip"
            s.export(output,"test")
            with zipfile.ZipFile(output) as z:
                self.assertEqual(json.loads(z.read("tracknode-agent.json"))["review_origin"],"automated_structural")
                self.assertIn("Automated structural source check",z.read("SELF_REVIEW.md").decode())
        s.hero_preset="serum"
        s.profile="cinema"
        with self.assertRaises(ValueError):
            s.set_review("Automated review must not approve missing required structure.",origin="automated_structural")

if __name__=="__main__":
    unittest.main()
