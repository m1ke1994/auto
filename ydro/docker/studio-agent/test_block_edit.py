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
