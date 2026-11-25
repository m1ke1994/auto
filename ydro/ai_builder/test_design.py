import io
import zipfile
from unittest.mock import patch, Mock
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings
from .design import demo_spec, preview, source_files, validate
from .provider import generate, GenerationError

class DesignTests(SimpleTestCase):
    def test_editorial_and_context(self):
        a=demo_spec("Поэт","Сайт для стихов")
        b=demo_spec("Поэт","Сайт для стихов",instruction="тёмный фон",previous=a)
        self.assertEqual(a["pages"],b["pages"])
        self.assertEqual(b["theme"],"dark")
        self.assertIn("Творчество",preview(b))
        self.assertIn("src/SitePage.vue",source_files(b))
    def test_escape_and_schema(self):
        a=demo_spec("<script>alert(1)</script>","Сайт")
        self.assertNotIn("<script>",preview(a))
        with self.assertRaises(ValidationError):
            validate({"theme":"url(javascript:1)","pages":[]})
    @override_settings(STUDIO_AI_PROVIDER="yandex",STUDIO_AI_KEY="test",STUDIO_AI_FOLDER="folder",STUDIO_AI_MODEL="model")
    @patch("ai_builder.provider.requests.post")
    def test_provider(self,post):
        import json
        spec=demo_spec("Поэт","Сайт")
        response=Mock(ok=True,content=b"ok")
        response.json.return_value={"choices":[{"finish_reason":"stop","message":{"content":json.dumps(spec)}}]}
        post.return_value=response
        self.assertEqual(generate("Поэт","Сайт"),spec)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"],"Api-Key test")
        response.json.return_value={"choices":[{"message":{"content":"invalid"}}]}
        with self.assertRaises(GenerationError):
            generate("Поэт","Сайт")

    def test_all_themes_render_css_and_preview(self):
        from .design import THEMES, css
        for theme in THEMES:
            with self.subTest(theme=theme):
                spec=demo_spec("Поэт","Стихи")
                spec["theme"]=theme
                stylesheet=css(spec)
                self.assertEqual(stylesheet.count("{"),stylesheet.count("}"))
                self.assertIn(".num{",stylesheet)
                self.assertIn("<style>"+stylesheet+"</style>",preview(spec))
                self.assertEqual(source_files(spec)["src/style.css"],stylesheet)

    @override_settings(STUDIO_AI_PROVIDER="deepseek", STUDIO_AI_KEY="test", STUDIO_AI_FOLDER="", STUDIO_AI_MODEL="deepseek-v4-pro")
    @patch("ai_builder.provider.requests.post")
    def test_deepseek_json_mode(self, post):
        import json
        spec=demo_spec("Поэт","Сайт")
        response=Mock(ok=True,content=b"ok")
        response.json.return_value={"choices":[{"finish_reason":"stop","message":{"content":json.dumps(spec)}}]}
        post.return_value=response
        self.assertEqual(generate("Поэт","Сайт"),spec)
        args,kwargs=post.call_args
        self.assertEqual(args[0],"https://api.deepseek.com/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"],"Bearer test")
        self.assertEqual(kwargs["json"]["model"],"deepseek-v4-pro")
        self.assertEqual(kwargs["json"]["thinking"],{"type":"disabled"})
        self.assertEqual(kwargs["json"]["response_format"],{"type":"json_object"})
        response.json.return_value={"choices":[{"finish_reason":"length","message":{"content":""}}]}
        with self.assertRaises(GenerationError):
            generate("Поэт","Сайт")
