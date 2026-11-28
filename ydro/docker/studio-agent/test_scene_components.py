from pathlib import Path
import unittest
from quality import quality_issues

ROOT=Path(__file__).parent
STORY=(ROOT/"SceneStory.vue").read_text(encoding="utf-8")
METRICS=(ROOT/"AboutMetrics.vue").read_text(encoding="utf-8")

class SceneComponentTests(unittest.TestCase):
    def test_carousel_is_trusted_and_exported_for_every_profile(self):
        import json, tempfile, zipfile
        from site_store import SiteStore, RESERVED
        carousel=(ROOT/"SceneCarousel.vue").read_text(encoding="utf-8")
        for token in ('data-tn-carousel-runtime="2"', 'scrollbar-width:none', '::-webkit-scrollbar', 'passive:false', 'event.cancelable', 'el.scrollLeft>=max-2'):
            self.assertIn(token,carousel)
        self.assertIn("src/components/SceneCarousel.vue",RESERVED)
        s=SiteStore()
        s.write("src/App.vue","<template><main><h1>Example</h1></main></template>")
        s.write("src/style.css","main{color:red}")
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"site.zip"
            s.export(output,"test")
            with zipfile.ZipFile(output) as z:
                self.assertEqual(z.read("src/components/SceneCarousel.vue").decode(),carousel)
                self.assertEqual(json.loads(z.read("public/tn-carousel-contract.json"))["version"],2)

    def test_about_metrics_is_trusted_accessible_and_motion_safe(self):
        for token in ("data-tn-about-metrics", "data-tn-metric-state", "ScrollTrigger.create", "once: props.once", "prefers-reduced-motion:reduce", "metric.current = metric.target", "tn-metric-digit-track"):
            self.assertIn(token,METRICS)
        self.assertIn("src/components/AboutMetrics.vue",__import__('site_store').RESERVED)

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
        self.assertIsNone(cinematic_direction(p,None,"Без внешних 3D-моделей")["hero_preset"])
        self.assertIsNone(cinematic_direction(p,None,"Без 3D")["hero_preset"])
        self.assertIsNone(cinematic_direction({"mode":"cinematic","subject":"architecture"},None,"office")["hero_preset"])
        self.assertIsNone(cinematic_direction(p,{"yaw":45},"beauty")["hero_preset"])

    def test_subject_specific_hero_object_library(self):
        from art_direction import cinematic_direction, procedural_preset
        self.assertEqual(procedural_preset({"subject":"premium coffee shop"},""),"cup")
        self.assertIsNone(procedural_preset({"subject":"interior design with a coffee table"},""))
        self.assertEqual(procedural_preset({"subject":"ювелирный салон"},""),"ring")
        self.assertEqual(procedural_preset({"subject":"watchmaker"},""),"watch")
        self.assertEqual(procedural_preset({"subject":"студия флористики"},""),"vase")
        self.assertEqual(procedural_preset({"subject":"podcast studio"},""),"microphone")
        self.assertIsNone(procedural_preset({"subject":"architecture studio"},""))
        self.assertIsNone(procedural_preset({"subject":"engineering studio"},""))
        self.assertIsNone(procedural_preset({"subject":"watching videos"},""))
        self.assertIsNone(procedural_preset({"subject":"coffee shop"},"Без 3D"))
        self.assertIsNone(cinematic_direction({"mode":"cinematic","subject":"coffee shop"},None,"")["hero_preset"])

    def test_hero_stage_uses_physical_materials_and_trusted_studio_environment(self):
        source=(ROOT/"HeroObjectStage.vue").read_text(encoding="utf-8")
        for token in ("RoomEnvironment","PMREMGenerator","MeshPhysicalMaterial","transmission:.96","sheen:1","T.ExtrudeGeometry","T.TorusGeometry","data-tn-object-preset"):
            self.assertIn(token,source)
        for preset in ("serum","jar","tube","perfume","cup","vase","watch","ring","microphone"):
            self.assertIn("'"+preset+"'",source)
        self.assertIn("prefers-reduced-motion: reduce",source)
        self.assertIn("lathe([[0,0],[.43,0],[.52,.06],[.54,.16],[.54,1.16],[.49,1.3],[.28,1.47],[.27,1.58],[0,1.58]],glass,-.82)",source)
        self.assertNotIn("]],-.82,glass)",source)
        self.assertIn("IntersectionObserver",source)
        self.assertNotIn("requestAnimationFrame(animate)",source)

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

    def test_primary_cinema_hero_requires_five_timed_film_captions(self):
        from quality import quality_issues
        app='''<template>
<section id="home" data-tn-section="home">
<div class="hero-stage"><CinemaModel model-path="tn-models/car/model.gltf" /></div>
<div class="hero-content"><h1>Drive the future</h1><div class="tn-film-captions">
<p data-tn-film-caption data-tn-film-start="0" data-tn-film-end="0.18">First</p>
<p data-tn-film-caption data-tn-film-start="0.20" data-tn-film-end="0.38">Second</p>
<p data-tn-film-caption data-tn-film-start="0.40" data-tn-film-end="0.58">Third</p>
<p data-tn-film-caption data-tn-film-start="0.60" data-tn-film-end="0.78">Fourth</p>
<p data-tn-film-caption data-tn-film-start="0.80" data-tn-film-end="1">Fifth</p>
</div></div></section></template>'''
        files={"src/App.vue":app}
        issues=quality_issues(files,"cinema")
        self.assertFalse(any("film Hero" in x or "film captions" in x or "scroll intervals" in x for x in issues))
        broken=app.replace('data-tn-film-end="0.38"','data-tn-film-end="0.58"')
        issues=quality_issues({"src/App.vue":broken},"cinema")
        self.assertTrue(any("scroll intervals" in x for x in issues))

    def test_primary_cinema_model_cannot_be_only_in_a_later_section(self):
        from quality import quality_issues
        app='''<template>
<section id="home" data-tn-section="home"><h1>Hero</h1></section>
<section id="about" data-tn-section="about"><CinemaModel model-path="tn-models/car/model.gltf" /></section>
</template>'''
        issues=quality_issues({"src/App.vue":app},"cinema")
        self.assertTrue(any("inside the home Hero" in x for x in issues))

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
