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

if __name__=="__main__":
    unittest.main()
