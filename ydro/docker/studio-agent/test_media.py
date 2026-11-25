import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import zipfile
from PIL import Image
from media import MediaLibrary, allowed_url
from site_store import SiteStore

def response(data):
    r=MagicMock()
    r.__enter__.return_value=r
    r.status_code=200
    r.iter_content.return_value=[data]
    return r

class MediaTests(unittest.TestCase):
    def test_urls(self):
        self.assertTrue(allowed_url("https://images.pexels.com/photos/1/test.jpg",{"images.pexels.com"}))
        for url in ("http://images.pexels.com/x","https://images.pexels.com.evil.test/x","https://images.pexels.com@evil.test/x","https://127.0.0.1/x"):
            self.assertFalse(allowed_url(url,{"images.pexels.com"}))
    @patch("media.requests.get")
    def test_photo_export(self,get):
        photo={"id":123,"url":"https://www.pexels.com/photo/example-123/","photographer":"A & B",
               "alt":"Forest","width":40,"height":20,"src":{"large2x":"https://images.pexels.com/photos/123/x.jpg"}}
        img=io.BytesIO()
        Image.new("RGB",(40,20),"green").save(img,"JPEG")
        get.side_effect=[response(json.dumps({"photos":[photo]}).encode()),response(img.getvalue())]
        library=MediaLibrary("secret-test")
        candidates=library.search("misty forest")
        self.assertEqual(candidates[0]["id"],123)
        self.assertNotIn("download",candidates[0])
        asset=library.save(123)
        self.assertEqual(asset["path"],"src/media/pexels-123.webp")
        self.assertNotIn("headers",get.call_args.kwargs)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])
        store=SiteStore(library)
        store.write("src/App.vue","<template><main>Site</main></template>")
        store.write("src/style.css","main { color: red; }")
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"site.zip"
            store.export(path,"deepseek-v4-pro")
            with zipfile.ZipFile(path) as z:
                self.assertIn(asset["path"],z.namelist())
                self.assertIn("A &amp; B",z.read("index.html").decode())
                self.assertIn("MEDIA_CREDITS.json",z.namelist())
                self.assertNotIn(b"secret-test",b"".join(z.read(n) for n in z.namelist()))
    @patch("media.requests.get")
    def test_replace_keeps_six_photo_limit_and_credits(self,get):
        img=io.BytesIO()
        Image.new("RGB",(40,20),"tan").save(img,"JPEG")
        get.return_value=response(img.getvalue())
        library=MediaLibrary("secret-test")
        for i in range(6):
            path=f"src/media/pexels-{100+i}.webp"
            library.assets[path]=b"old"
            library.credits[path]={"path":path,"id":100+i,"photographer":"Old","url":"https://www.pexels.com/photo/old/"}
        library.downloads=6
        library.candidates[456]={"id":456,"photographer":"New Artist","alt":"Warm salon portrait",
                                 "url":"https://www.pexels.com/photo/example-456/",
                                 "download":"https://images.pexels.com/photos/456/x.jpg",
                                 "width":40,"height":20}
        replaced=library.replace("src/media/pexels-100.webp",456)
        self.assertEqual(replaced["id"],456)
        self.assertEqual(len(library.assets),6)
        self.assertEqual(library.downloads,6)
        self.assertNotIn("src/media/pexels-100.webp",library.assets)
        self.assertIn("src/media/pexels-456.webp",library.assets)
        self.assertEqual(library.credits["src/media/pexels-456.webp"]["photographer"],"New Artist")

    def test_disabled_and_unknown(self):
        lib=MediaLibrary("")
        with self.assertRaises(ValueError):
            lib.search("forest")
        with self.assertRaises(ValueError):
            lib.save(123)
