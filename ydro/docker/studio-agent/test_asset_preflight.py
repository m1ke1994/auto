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
