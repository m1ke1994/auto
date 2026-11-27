import unittest
from block_edit import patch, find_block

class BlockEditTests(unittest.TestCase):
    def setUp(self):
        self.home='<section id="home" data-tn-section="home"><h1>Old</h1><section><p>Nested</p></section></section>'
        self.about='<section id="about" data-tn-section="about"><h2>About</h2></section>'
        self.files={"src/App.vue":("<template>"+self.home+self.about+"</template>").encode(),"src/style.css":b"body{color:red}","tracknode-agent.json":b'{"engine":"openhands-sdk"}',"public/photo.webp":b"asset"}

    def test_only_selected_root_and_scoped_css(self):
        result=patch(self.files,"home",{"markup":self.home.replace("Old","New"),"rules":[{"selector":"h1","declarations":"font-size:clamp(2rem,4vw,4rem)","mobile":False}]})
        self.assertIn(self.about.encode(),result["src/App.vue"])
        self.assertIn(b"#home h1{",result["src/style.css"])
        self.assertEqual(result["public/photo.webp"],self.files["public/photo.webp"])
        self.assertIn(b"Old",self.files["src/App.vue"])

    def test_reject_other_section_and_global_style(self):
        for markup,rules in [(self.home+self.about,[]),(self.home,[{"selector":"h1","declarations":"color:red}body{display:none","mobile":False}])]:
            with self.assertRaises(ValueError):
                patch(self.files,"home",{"markup":markup,"rules":rules})

    def test_existing_model_path_is_locked(self):
        old=self.home.replace("<h1>Old</h1>",'<CinemaModel model-path="tn-models/car/model.gltf" />')
        self.files["src/App.vue"]=("<template>"+old+self.about+"</template>").encode()
        with self.assertRaises(ValueError):
            patch(self.files,"home",{"markup":old.replace("tn-models/car/","tn-models/other/"),"rules":[]})

    def test_multiline_unicode_source_offsets(self):
        source='<template>\n  <header data-tn-header>Привет</header>\n  '+self.home.replace('Old','Инженерия эмоций')+'\n'+self.about+'\n</template>'
        name,start,end=find_block({'src/App.vue':source},'home')
        self.assertEqual(source[start:end],self.home.replace('Old','Инженерия эмоций'))
        name,start,end=find_block({'src/App.vue':source},'header')
        self.assertEqual(source[start:end],'<header data-tn-header>Привет</header>')

    def test_equivalent_root_format_and_scoped_selectors(self):
        changed=self.home.replace('<section id="home" data-tn-section="home">',"<section data-tn-section='home' id='home'>").replace("Old","New")
        result=patch(self.files,"home",{"markup":"  "+changed+"\n","rules":[{"selector":":scope, :scope h1, .hero-copy p","declarations":"color:red","mobile":False}]})
        self.assertIn(b'<section id="home" data-tn-section="home">',result["src/App.vue"])
        self.assertIn(b"#home,#home h1,#home .hero-copy p{color:red}",result["src/style.css"])
        self.assertIn(self.about.encode(),result["src/App.vue"])

    def test_reject_changed_root_and_escaping_selector(self):
        for markup,selector in [(self.home.replace('id="home"','id="home" class="changed"'),"h1"),(self.home,"h1, :scope + body")]:
            with self.assertRaises(ValueError):
                patch(self.files,"home",{"markup":markup,"rules":[{"selector":selector,"declarations":"color:red","mobile":False}]})

    def test_safe_failure_reason(self):
        from block_edit import BlockEditError, failure_detail
        self.assertEqual(failure_detail(BlockEditError("Outer tag attributes changed")),"Outer tag attributes changed")
        self.assertEqual(failure_detail(ValueError("secret response content")),"ValueError")

    def test_root_class_selector_targets_root_not_descendant(self):
        home=self.home.replace('data-tn-section="home">','data-tn-section="home" class="hero opening">')
        self.files["src/App.vue"]=("<template>"+home+self.about+"</template>").encode()
        rules=[
            {"selector":".hero","declarations":"display:grid","mobile":False},
            {"selector":".hero .hero-stage","declarations":"min-width:0","mobile":False},
            {"selector":".hero","declarations":"display:flex","mobile":True},
            {"selector":":scope .hero","declarations":"color:red","mobile":False},
        ]
        result=patch(self.files,"home",{"markup":home,"rules":rules})
        css=result["src/style.css"]
        self.assertIn(b"#home.hero{display:grid}",css)
        self.assertIn(b"#home.hero .hero-stage{min-width:0}",css)
        self.assertIn(b"@media(max-width:760px){#home.hero{display:flex}}",css)
        self.assertIn(b"#home .hero{color:red}",css)
        self.assertIn(self.about.encode(),result["src/App.vue"])

    def test_local_film_preserves_other_blocks_and_assets(self):
        from block_edit import apply_hero_film
        home='<section id="home" data-tn-section="home" class="hero"><div class="hero-stage"><CinemaModel model-path="tn-models/car/model.gltf" /></div><div class="hero-content"><h1>Engineering</h1></div></section>'
        self.files["src/App.vue"]=("<template>"+home+self.about+"</template>").encode()
        out=apply_hero_film(self.files)
        self.assertIn(b'data-tn-hero-film',out["src/App.vue"])
        self.assertIn(b'data-tn-film-version="2"',out["src/App.vue"])
        self.assertIn(b'data-tn-film-turn="180"',out["src/App.vue"])
        self.assertIn(b'data-tn-film-pace="compact"',out["src/App.vue"])
        # Attribute order is not part of the HTML contract; check the actual home root.
        from block_edit import FilmMarkup
        source=out["src/App.vue"].decode()
        _,start,end=find_block({"src/App.vue":source},"home")
        root=FilmMarkup(source[start:end]).nodes[0]
        self.assertIn("data-tn-film-background",root["attrs"])
        self.assertEqual(root["attrs"].get("data-tn-film-turn"),"180")
        self.assertEqual(root["attrs"].get("data-tn-film-pace"),"compact")
        self.assertEqual(root["attrs"].get("data-tn-film-engine"),"smooth")
        self.assertEqual(root["attrs"].get("data-tn-film-camera"),"stable")
        import json
        meta=json.loads(out["tracknode-agent.json"])
        self.assertEqual(meta["hero_film_turn"],180)
        self.assertEqual(meta["hero_film_pace"],"compact")
        self.assertEqual(meta["hero_film_engine"],"smooth")
        self.assertEqual(meta["hero_film_camera"],"stable")
        self.assertIn(b'position:sticky !important; top:0',out["src/style.css"])
        self.assertIn(b'transform:translate3d(0,var(--tn-film-offset),0)',out["src/style.css"])
        self.assertIn(b'height:calc(var(--tn-film-vh)*2.2)',out["src/style.css"])
        self.assertIn(b'height:calc(var(--tn-film-vh)*1.8)',out["src/style.css"])
        self.assertIn(b'data-tn-film-background-layer><CinemaModel',out["src/App.vue"])
        self.assertIn(b'class="tn-film-screen"',out["src/App.vue"])
        self.assertIn(self.about.encode(),out["src/App.vue"])
        self.assertEqual(out["public/photo.webp"],self.files["public/photo.webp"])
        self.assertEqual(apply_hero_film(out)["src/App.vue"],out["src/App.vue"])
        self.assertEqual(apply_hero_film(out)["src/style.css"],out["src/style.css"])
    def test_local_film_refuses_unknown_layout(self):
        from block_edit import apply_hero_film
        with self.assertRaises(ValueError):
            apply_hero_film(self.files)

    def test_windows_archive_with_directory_records(self):
        import tempfile, zipfile
        from pathlib import Path
        from block_edit import read_archive
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"windows.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("src/","")
                z.writestr("src\\components\\","")
                z.writestr("src\\components\\Hero.vue","<template/>")
                z.writestr("tracknode-agent.json",'{"engine":"openhands-sdk"}')
            self.assertEqual(read_archive(path)["src/components/Hero.vue"],b"<template/>")
            self.assertNotIn("src/",read_archive(path))

    def test_archive_rejects_traversal_and_aliases_after_normalizing(self):
        import tempfile, zipfile
        from pathlib import Path
        from block_edit import read_archive
        for names in (["..\\escape.py"],["C:\\evil"],["\\absolute"],["src//file"],["src/App.vue","src\\App.vue"],["src/App.vue","SRC/other.vue"],["src","src/App.vue"],["src/child","src"],[".env"],["src/.git/config"]):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as d:
                path=Path(d)/"bad.zip"
                with zipfile.ZipFile(path,"w") as z:
                    z.writestr("tracknode-agent.json",'{"engine":"openhands-sdk"}')
                    for name in names:
                        z.writestr(name,b"content")
                with self.assertRaises(ValueError):
                    read_archive(path)

    def test_archive_rejects_symlink_even_with_directory_suffix(self):
        import tempfile, zipfile, stat
        from pathlib import Path
        from block_edit import read_archive
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bad.zip"
            with zipfile.ZipFile(path,"w") as z:
                z.writestr("tracknode-agent.json",'{"engine":"openhands-sdk"}')
                entry=zipfile.ZipInfo("src/link/")
                entry.create_system=3
                entry.external_attr=(stat.S_IFLNK|0o777)<<16
                z.writestr(entry,b"")
            with self.assertRaises(ValueError):
                read_archive(path)

    def test_background_removes_old_split_wrapper_and_preserves_model_slot(self):
        from block_edit import apply_hero_film
        model='<CinemaModel model-path="tn-models/car/model.gltf"><template #fallback><img src="/car.webp"/></template></CinemaModel>'
        home='<section id="home" data-tn-section="home" class="hero"><div class="hero-stage"><div class="right-column" style="width:30%">'+model+'</div></div><div class="hero-content"><h1>Engineering</h1><p class="hero-sub">Description</p></div></section>'
        self.files["src/App.vue"]=("<template>"+home+self.about+"</template>").encode()
        out=apply_hero_film(self.files)
        self.assertIn(model.encode(),out["src/App.vue"])
        self.assertNotIn(b"right-column",out["src/App.vue"])
        self.assertIn(b'<div class="hero-content"><h1>Engineering</h1>',out["src/App.vue"])
        old=dict(out)
        old["src/App.vue"]=old["src/App.vue"].replace(b'data-tn-film-turn="180" data-tn-film-pace="compact" data-tn-film-engine="smooth" data-tn-film-camera="stable"',b'data-tn-film-turn="360"')
        old["src/style.css"]=old["src/style.css"].replace(b'height:calc(var(--tn-film-vh)*2.2)',b'height:calc(var(--tn-film-vh)*6)').replace(b'height:calc(var(--tn-film-vh)*1.8)',b'height:calc(var(--tn-film-vh)*6)')
        self.assertEqual(apply_hero_film(old)["src/App.vue"],out["src/App.vue"])
        self.assertEqual(apply_hero_film(old)["src/style.css"],out["src/style.css"])
        self.assertEqual(apply_hero_film(out)["src/style.css"],out["src/style.css"])

    def test_nested_split_layout_is_hoisted_to_fullscreen_background(self):
        from block_edit import apply_hero_film, FilmMarkup
        model='<CinemaModel model-path="tn-models/car/model.gltf" />'
        copy='<div class="hero-content"><h1>Engineering</h1><p class="hero-sub">Description</p><div class="hero-actions"><a href="#contacts">Contact</a></div></div>'
        cue='<div class="hero-scrollcue">Scroll</div>'
        home='<section id="home" data-tn-section="home"><div class="split-layout"><div class="left-column">'+copy+'</div><div class="right-column"><div class="hero-stage">'+model+'</div></div></div>'+cue+'</section>'
        self.files["src/App.vue"]=("<template>"+home+self.about+"</template>").encode()
        out=apply_hero_film(self.files)
        source=out["src/App.vue"].decode()
        parsed=FilmMarkup(source)
        screen=parsed.by_class("tn-film-screen")[0]
        stage=parsed.by_class("hero-stage")[0]
        self.assertIs(stage["parent"],screen)
        self.assertIs(parsed.by_class("hero-content")[0]["parent"],screen)
        self.assertNotIn("split-layout",source)
        self.assertNotIn("right-column",source)
        self.assertIn(model,source)
        self.assertIn(copy,source)
        self.assertIn(cue,source)
        self.assertIn(self.about,source)
        self.assertEqual(apply_hero_film(out)["src/App.vue"],out["src/App.vue"])

    def test_conditional_layout_scope_is_not_silently_removed(self):
        from block_edit import apply_hero_film, primary_hero_film, BlockEditError
        home='<section id="home" data-tn-section="home"><div v-for="car in cars"><div class="hero-stage"><CinemaModel :model-path="car.path" /></div><div class="hero-content"><h1>{{ car.name }}</h1></div></div></section>'
        source="<template>"+home+"</template>"
        self.files["src/App.vue"]=source.encode()
        self.assertTrue(primary_hero_film({"src/App.vue":source}))
        with self.assertRaises(BlockEditError):
            apply_hero_film(self.files)
