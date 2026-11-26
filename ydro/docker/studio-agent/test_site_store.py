import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from site_store import SiteStore

class StoreTests(unittest.TestCase):
    def test_paths(self):
        store=SiteStore()
        for path in ("../secret","/proc/self/environ","src/../x.js","src/.env","package.json","src/main.js","src/landing-progress.js","src\\x.vue","src/a.sh"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                store.write(path,"x")
        store.write("src/components/Hero.vue","<template><h1>Hero</h1></template>")
        self.assertIn("Hero",store.read("src/components/Hero.vue"))
        with self.assertRaises(ValueError):
            store.read("/proc/self/environ")
    def test_export(self):
        store=SiteStore()
        with self.assertRaises(ValueError):
            store.validate()
        store.write("src/App.vue",'<template><main><section><h1>Beauty Atelier</h1><p class="hero-lede">A quiet premium beauty studio.</p></section></main></template>')
        store.write("src/style.css","main { color: red; }")
        store.write("src/components/Hero.vue","<template><h1>Hero</h1></template>")
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"site.zip"
            store.export(output,"deepseek-v4-pro")
            with zipfile.ZipFile(output) as z:
                self.assertIn("src/App.vue",z.namelist())
                html=z.read("index.html").decode()
                self.assertIn("<title>Beauty Atelier</title>",html)
                self.assertIn('name="description"',html)
                self.assertIn("src/landing-progress.js",z.namelist())
                self.assertIn("src/components/CinemaModel.vue",z.namelist())
                self.assertIn("src/cinematic-motion.js",z.namelist())
                self.assertIn("src/components/SceneCarousel.vue",z.namelist())
                self.assertIn("src/components/SceneStory.vue",z.namelist())
                self.assertIn("installLandingProgress();",z.read("src/main.js").decode())
                progress=z.read("src/landing-progress.js").decode()
                self.assertIn("transform-origin:left center",progress)
                self.assertIn("root.scrollHeight - root.clientHeight",progress)
                self.assertIn("root.scrollTop / max",progress)
                self.assertFalse(json.loads(z.read("tracknode-agent.json"))["build_verified"])
                self.assertEqual(json.loads(z.read("package.json"))["scripts"]["build"],"vite build")
            with self.assertRaises(FileExistsError):
                store.export(output,"deepseek-v4-pro")
    def test_trusted_cinema_component(self):
        with self.assertRaises(ValueError):
            SiteStore().write("src/components/CinemaModel.vue","override")

    def test_cinematic_direction(self):
        from art_direction import cinematic_direction
        plan={"mode":"immersive","subject":"sports car"}
        item={"quality_tier":"conditional","yaw":225}
        normal=cinematic_direction(plan,item,"car detailing")
        self.assertEqual(normal["opening_yaw"],225)
        self.assertEqual(normal["model_role"],"primary")
        self.assertNotIn(normal["motion"],("idle_float","detail_focus"))
        accent=cinematic_direction(plan,item,"маленькая модель по краям")
        self.assertEqual(accent["layout"],"floating_edges")
        self.assertEqual(accent["model_role"],"accent")
        self.assertNotEqual(accent["motion"],"idle_float")
        self.assertEqual(cinematic_direction(plan,None,"site")["layout"],"editorial_photo")
        self.assertEqual(normal,cinematic_direction(plan,item,"car detailing"))
        with self.assertRaises(ValueError):
            SiteStore().write("src/cinematic-motion.js","override")

    def test_storyboard_contract(self):
        from storyboard import validate_storyboard
        layouts=("full_bleed","sticky_story","horizontal_gallery","quote_scene","finale")
        sections=("home","about","services","benefits","contacts")
        raw={"concept":"A deliberate film about design","rhythm":"Quiet light and changing typography","chapters":[
            dict(section=s,layout=l,visual="a specific product",caption="an honest title",start="opening frame",end="closing frame",transition="slow dissolve",mobile="readable stacked fallback") for s,l in zip(sections,layouts)]}
        store=SiteStore()
        store.scene_required=True
        self.assertTrue(store.scene_issues())
        store.set_storyboard(json.dumps(raw))
        self.assertEqual(store.storyboard,validate_storyboard(raw))
        self.assertEqual(len(store.scene_issues()),2)
        for name in ("SceneStory","SceneCarousel"):
            with self.assertRaises(ValueError):
                store.write("src/components/"+name+".vue","override")
        with tempfile.TemporaryDirectory() as d:
            store.set_plan("Original art direction and storyboard for a product film. "*2)
            store.write("src/style.css","main{color:red}")
            p=Path(d)/"checkpoint.zip"
            store.checkpoint(p,"test","cinema")
            with zipfile.ZipFile(p) as z:
                self.assertEqual(json.loads(z.read("STORYBOARD.json")),store.storyboard)
                self.assertEqual(json.loads(z.read("public/tn-scene-contract.json"))["version"],1)
        raw["chapters"][1]["layout"]="full_bleed"
        with self.assertRaises(ValueError):
            validate_storyboard(raw)

    def test_limits(self):
        with self.assertRaises(ValueError):
            SiteStore().write("src/App.vue","x"*64001)

    def test_premium_art_direction_and_review(self):
        store=SiteStore()
        store.write("src/App.vue", """<script setup>
import SiteFooter from './components/SiteFooter.vue'
import SiteHeader from './components/SiteHeader.vue'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
const options = { scrub: true }
</script><template><SiteHeader /><main>
<section id="home" data-tn-section="home" data-tn-scene="opening"><h1>Hero</h1><div data-tn-motion>One</div></section>
<section id="about" data-tn-section="about" data-tn-scene="middle"><div data-tn-motion>Two</div></section>
<section id="services" data-tn-section="services" data-tn-scene="finale"><article data-tn-service>Three</article></section>
<section id="benefits" data-tn-section="benefits">Benefits</section>
<section id="contacts" data-tn-section="contacts">Contacts</section>
</main><SiteFooter /></template>""")
        store.write("src/components/SiteHeader.vue","<template><header data-tn-header><nav><a href='#home'>Home</a><a href='#about'>About</a><a href='#services'>Services</a><a href='#contacts'>Contacts</a></nav></header></template>")
        store.write("src/components/SiteFooter.vue","<template><footer data-tn-footer><a href='#home'>Top</a></footer></template>")
        store.write("src/style.css","main { color: red; }")
        store.write("src/components/Hero.vue","<template><h1>Hero</h1></template>")
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"site.zip"
            with self.assertRaises(ValueError):
                store.export(output,"deepseek-v4-pro","cinema")
            store.set_plan("Art direction, audience, scenes, motion and accessibility. " * 3)
            store.set_review("Source review only; build and browser checks still pending.")
            store.write("src/style.css","main { color: blue; }")
            with self.assertRaises(ValueError):
                store.export(output,"deepseek-v4-pro","cinema")
            store.set_review("Source review only; build and browser checks still pending.")
            store.export(output,"deepseek-v4-pro","cinema")
            with zipfile.ZipFile(output) as z:
                self.assertIn("ART_DIRECTION.md",z.namelist())
                self.assertIn("SELF_REVIEW.md",z.namelist())
                self.assertFalse(json.loads(z.read("tracknode-agent.json"))["visual_verified"])
                deps=json.loads(z.read("package.json"))["dependencies"]
                self.assertEqual(set(deps),{"vue","three","gsap","lenis"})

    def test_quality_gate(self):
        from quality import quality_issues
        store=SiteStore()
        store.profile="cinema"
        store.write("src/App.vue","<template><main>Site</main></template>")
        store.write("src/style.css","main { color: red; }")
        issues=quality_issues(store.files,"cinema")
        self.assertTrue(any("SiteFooter" in issue for issue in issues))
        self.assertTrue(any("scrubbed" in issue for issue in issues))
        self.assertTrue(any("SiteHeader" in issue for issue in issues))
        self.assertTrue(any("id=contacts" in issue for issue in issues))
        self.assertTrue(any("data-tn-service" in issue for issue in issues))
        with self.assertRaisesRegex(ValueError,"Fix before review"):
            store.set_review("Source review should reject incomplete cinematic pages.")

    def test_required_section_attributes(self):
        from quality import literal_attribute
        self.assertTrue(literal_attribute('<section id="home">',"id","home"))
        self.assertFalse(literal_attribute('<section :id="home">',"id","home"))
        self.assertFalse(literal_attribute('<section data-id="home">',"id","home"))

    def test_profiles(self):
        from art_direction import PROFILES, build_prompt
        for profile in PROFILES:
            self.assertIn("USER BRIEF EXAMPLE",build_prompt("USER BRIEF EXAMPLE",profile))
            self.assertIn("filling strictly left to right",build_prompt("Test",profile))
        with self.assertRaises(ValueError):
            SiteStore().write("src/landing-progress.js","override")
        self.assertIn("scroll-driven scenes",build_prompt("Test","cinema"))

if __name__=="__main__":
    unittest.main()

    def test_public_contacts_are_trusted_and_exported_without_ai(self):
        store=SiteStore()
        contacts={"phone":"+7 (900) 123-45-67","email":"sales@example.com","address":"Москва <Example>","telegram":"https://t.me/example"}
        store.set_contacts(contacts)
        store.write("src/App.vue","<template><main>Test</main></template>")
        store.write("src/style.css","main{color:red}")
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/"contacts.zip"
            store.export(output,"test")
            with zipfile.ZipFile(output) as z:
                self.assertEqual(json.loads(z.read("CONTACTS.json")),contacts)
                entries=json.loads(z.read("public/tn-contact-contract.json"))
                self.assertEqual(entries[0]["href"],"tel:+79001234567")
                self.assertEqual(entries[1]["href"],"mailto:sales@example.com")
                self.assertIn("node.textContent",z.read("src/tn-contacts.js").decode())
                self.assertIn("installContacts();",z.read("src/main.js").decode())
        for data in ({"website":"javascript:alert(1)"},{"website":"https://user:pass@example.com/"},{"phone":"abc"},{"email":"x@example.com?subject=bad"}):
            with self.assertRaises(ValueError):
                store.set_contacts(data)
        with self.assertRaises(ValueError):
            store.write("src/tn-contacts.js","override")
