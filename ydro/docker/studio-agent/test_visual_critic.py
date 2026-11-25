import json
import unittest
from visual_critic import parse_review, WEIGHTS

class CriticTests(unittest.TestCase):
    def fixture(self):
        return {"scores":dict(WEIGHTS),"observations":[{"image":"desktop-0.png","description":"Visible subject."}],"issues":[],"summary":"Review."}
    def test_pass(self):
        self.assertTrue(parse_review(json.dumps(self.fixture()),["desktop-0.png"])["passed"])
    def test_critical_overrides_score(self):
        data=self.fixture()
        data["issues"]=[{"severity":"critical","image":"desktop-0.png","problem":"Tiny car on huge platform.","fix":"Replace asset with isolated car."}]
        result=parse_review(json.dumps(data),["desktop-0.png"])
        self.assertEqual(result["score"],100)
        self.assertFalse(result["passed"])
    def test_low_asset_score(self):
        data=self.fixture()
        data["scores"]["asset_quality"]=17
        self.assertFalse(parse_review(json.dumps(data),["desktop-0.png"])["passed"])
    def test_missing_images_and_bad_scores(self):
        with self.assertRaises(ValueError):
            parse_review(json.dumps(self.fixture()),["desktop-0.png","desktop-25.png"])
        data=self.fixture()
        data["scores"]["composition"]=21
        with self.assertRaises(ValueError):
            parse_review(json.dumps(data),["desktop-0.png"])
