import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from site_store import SiteStore

class StoreTests(unittest.TestCase):
    def test_paths(self):
        store=SiteStore()
        for path in ("../secret","/proc/self/environ","src/../x.js","src/.env","package.json","src/main.js","src\\x.vue","src/a.sh"):
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
        store.write("src/App.vue","<template><main>Site</main></template>")
        store.write("src/style.css","main { color: red; }")
        store.write("src/components/Hero.vue","<template><h1>Hero</h1></template>")
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"site.zip"
            store.export(output,"deepseek-v4-pro")
            with zipfile.ZipFile(output) as z:
                self.assertIn("src/App.vue",z.namelist())
                self.assertFalse(json.loads(z.read("tracknode-agent.json"))["build_verified"])
                self.assertEqual(json.loads(z.read("package.json"))["scripts"]["build"],"vite build")
            with self.assertRaises(FileExistsError):
                store.export(output,"deepseek-v4-pro")
    def test_limits(self):
        with self.assertRaises(ValueError):
            SiteStore().write("src/App.vue","x"*64001)

    def test_premium_art_direction_and_review(self):
        store=SiteStore()
        store.write("src/App.vue","<template><main>Site</main></template>")
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

    def test_profiles(self):
        from art_direction import PROFILES, build_prompt
        for profile in PROFILES:
            self.assertIn("USER BRIEF EXAMPLE",build_prompt("USER BRIEF EXAMPLE",profile))
        self.assertIn("scroll-driven scenes",build_prompt("Test","cinema"))

if __name__=="__main__":
    unittest.main()
