import unittest
from asset_preflight import choose_review, validate_plan
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
