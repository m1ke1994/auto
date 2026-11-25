import unittest
from asset_preflight import choose_review, validate_plan, thumbnail_url, rank_previews
class PreflightTests(unittest.TestCase):
    def test_critical_overrides_score(self):
        self.assertIsNone(choose_review({"reviews":[{"candidate":"candidate-1","score":100,"critical":True,"reason":"Huge podium","yaw":45}]},["candidate-1"]))
    def test_select_best(self):
        result=choose_review({"reviews":[{"candidate":"candidate-1","score":86,"critical":False,"reason":"Good","yaw":45},{"candidate":"candidate-2","score":92,"critical":False,"reason":"Better","yaw":135}]},["candidate-1","candidate-2"])
        self.assertEqual(result["candidate"],"candidate-2")
    def test_missing_candidate(self):
        with self.assertRaises(ValueError):
            choose_review({"reviews":[]},["candidate-1"])
    def test_invalid_plan(self):
        with self.assertRaises(ValueError):
            validate_plan({"mode":"immersive","subject":"car","queries":[],"required":True,"use_model":False,"direction":"A sufficiently long direction"})
    def test_normalize_harmless_format_variations(self):
        data={"mode":" Immersive ","subject":"car","queries":["realistic sports car (PBR)","car/coupe","extra query"],"required":"true","use_model":True,"direction":"A distinctive editorial composition. "*30,"extra":"ignored"}
        plan=validate_plan(data)
        self.assertEqual(plan["mode"],"immersive")
        self.assertEqual(plan["queries"],["realistic sports car PBR","car coupe"])
        self.assertEqual(len(plan["direction"]),600)
        self.assertIs(plan["required"],True)
    def test_explicit_mode_and_required_override(self):
        data={"mode":"other","subject":"car","queries":"sports coupe","required":False,"use_model":False,"direction":"A distinct full-screen composition."}
        plan=validate_plan(data,hero="immersive",force_model=True)
        self.assertTrue(plan["required"] and plan["use_model"])
        self.assertEqual(plan["mode"],"immersive")
    def test_required_without_query_fails(self):
        with self.assertRaises(ValueError):
            validate_plan({"mode":"immersive","subject":"car","queries":[],"required":True,"use_model":True,"direction":"A distinct full-screen composition."})

    def test_thumbnail_host_and_model_binding(self):
        uid="a"*32
        def entry(url):
            return {"images":[{"width":720,"height":405,"url":url}]}
        good="https://media.sketchfab.com/models/"+uid+"/thumbnails/abc/def.jpeg"
        self.assertEqual(thumbnail_url(uid,entry(good)),good)
        self.assertIsNone(thumbnail_url(uid,entry(good.replace("media.sketchfab.com","evil.test"))))
        self.assertIsNone(thumbnail_url(uid,entry(good.replace(uid,"b"*32))))
        self.assertIsNone(thumbnail_url(uid,entry(good+"?token=secret")))
    def test_thumbnail_critical_blocks_even_high_score(self):
        result=rank_previews({"reviews":[{"id":"a","score":95,"critical":True},{"id":"b","score":82,"critical":False},{"id":"c","score":70,"critical":False}]},["a","b","c"])
        self.assertEqual(result,["b"])
    def test_thumbnail_missing_or_invalid_score(self):
        with self.assertRaises(ValueError):
            rank_previews({"reviews":[]},["a"])
        with self.assertRaises(ValueError):
            rank_previews({"reviews":[{"id":"a","score":101,"critical":False}]},["a"])
