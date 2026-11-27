import unittest
from asset_preflight import choose_review, validate_plan, thumbnail_url, rank_previews, canonical_candidates, expanded_queries, normalize_queries
from art_direction import classify_hero_subject, cinematic_direction
class PreflightTests(unittest.TestCase):
    def test_cinematic_subject_classification_and_direction(self):
        self.assertEqual(classify_hero_subject({"subject":"sports car"}, "premium automobile"), "large_object")
        self.assertEqual(classify_hero_subject({"subject":"luxury residence"}, "architecture and interior"), "architecture")
        self.assertEqual(classify_hero_subject({"subject":"cosmetic tube"}, "small product"), "small_object")
        self.assertEqual(classify_hero_subject({"subject":"forest"}, "landscape environment"), "environment")

        selected={"quality_tier":"premium","yaw":135}
        large=cinematic_direction({"subject":"sports car","mode":"cinematic"},selected,"sports car")
        self.assertEqual(large["subject_type"],"large_object")
        self.assertIn(large["composition"],("center_focus","offset_left","offset_right"))
        self.assertEqual(large["max_rotation_deg"],180)
        self.assertEqual(large["camera_strategy"],"camera_and_light_reveal")

        small=cinematic_direction({"subject":"cosmetic tube","mode":"product"},selected,"cosmetic tube")
        self.assertEqual(small["subject_type"],"small_object")
        self.assertEqual(small["title_strategy"],"intro_titles")
        self.assertEqual(small["camera_strategy"],"gentle_product_drift")
        self.assertEqual(small["max_rotation_deg"],180)

        building=cinematic_direction({"subject":"modern building","mode":"immersive"},selected,"modern building")
        self.assertEqual(building["subject_type"],"architecture")
        self.assertEqual(building["title_strategy"],"overlay_static")
        self.assertEqual(building["max_rotation_deg"],180)

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
        self.assertEqual(plan["queries"],["realistic sports car PBR","car coupe","extra query"])
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
        self.assertEqual(result,["b","c"])
    def test_thumbnail_missing_or_invalid_score(self):
        with self.assertRaises(ValueError):
            rank_previews({"reviews":[]},["a"])
        with self.assertRaises(ValueError):
            rank_previews({"reviews":[{"id":"a","score":101,"critical":False}]},["a"])

    def test_candidate_folders_are_canonical_and_ignore_untrusted_manifest_paths(self):
        items=[{"folder":"../../outside","id":"a"},{"folder":"unexpected","id":"b"}]
        self.assertEqual([x["folder"] for x in canonical_candidates(items)],["candidate-1","candidate-2"])
    def test_candidate_manifest_limit_and_shape(self):
        with self.assertRaises(ValueError):
            canonical_candidates([{}, {}, {}, {}, {}])
        with self.assertRaises(ValueError):
            canonical_candidates(["not-an-object"])

    def test_conditional_threshold_accepts_best_noncritical_candidate(self):
        result=choose_review({"reviews":[{"candidate":"candidate-1","score":72,"critical":False,"reason":"Weak materials","yaw":135},{"candidate":"candidate-2","score":78,"critical":False,"reason":"Good bodywork; materials need cinematic presentation","yaw":225}]},["candidate-1","candidate-2"],min_score=75)
        self.assertEqual(result["candidate"],"candidate-2")
    def test_conditional_threshold_still_rejects_critical_and_low_scores(self):
        result=choose_review({"reviews":[{"candidate":"candidate-1","score":100,"critical":True,"reason":"Wrong geometry","yaw":45},{"candidate":"candidate-2","score":74,"critical":False,"reason":"Too weak","yaw":225}]},["candidate-1","candidate-2"],min_score=75)
        self.assertIsNone(result)
    def test_default_threshold_accepts_75_without_critical_defect(self):
        result=choose_review({"reviews":[{"candidate":"candidate-1","score":84,"critical":False,"reason":"Not premium threshold","yaw":45}]},["candidate-1"])
        self.assertEqual(result["candidate"],"candidate-1")

    def test_optional_render_review_failure_falls_back_without_approving_model(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import asset_preflight as preflight
        with tempfile.TemporaryDirectory() as tmp, patch.object(preflight,"ROOT",Path(tmp)):
            plan={"subject":"car","style":"realistic","mode":"product","required":False,"use_model":True}
            preflight.dump("plan.json",plan)
            preflight.dump("candidates.json",[{"folder":"candidate-1","id":"a"}])
            folder=Path(tmp)/"candidate-1"
            folder.mkdir()
            (folder/"render-ok.json").write_text("{}")
            for yaw in preflight.ANGLES:
                (folder/f"view-{yaw}.png").touch()
            with patch.object(preflight,"image_url",return_value="data:image/jpeg;base64,example"), patch.object(preflight,"flash",side_effect=ValueError("invalid response")):
                self.assertEqual(preflight.select(),0)
                selection=preflight.load("selection.json")
                self.assertEqual(selection["status"],"no_model")
                self.assertEqual(selection["reason"],"visual_review_unavailable")
                self.assertIsNone(selection["selected"])
                plan["required"]=True
                preflight.dump("plan.json",plan)
                with self.assertRaises(ValueError):
                    preflight.select()

    def test_expanded_watch_search_is_bounded_and_semantic(self):
        queries=expanded_queries("luxury mechanical wristwatch with visible movement",["luxury mechanical wristwatch","Luxury mechanical wristwatch"])
        self.assertEqual(len(queries),6)
        self.assertIn("wristwatch",queries)
        self.assertIn("mechanical watch",queries)
        self.assertEqual(len({q.lower() for q in queries}),6)
        self.assertEqual(len(normalize_queries(["query "+str(i) for i in range(12)])),6)
        self.assertNotIn("sports car",expanded_queries("watch",["watch"]))

    def test_four_candidates_and_conditional_floor(self):
        names=[x["folder"] for x in canonical_candidates([{}, {}, {}, {}])]
        self.assertEqual(names,["candidate-1","candidate-2","candidate-3","candidate-4"])
        reviews=[{"candidate":n,"score":s,"critical":c,"reason":"Reviewed","yaw":45}
                 for n,s,c in zip(names,[64,65,100,70],[False,False,True,False])]
        self.assertEqual(choose_review({"reviews":reviews},names)["candidate"],"candidate-4")
        reviews[-1]["score"]=64
        self.assertEqual(choose_review({"reviews":reviews},names)["candidate"],"candidate-2")
        reviews[1]["score"]=64
        self.assertIsNone(choose_review({"reviews":reviews},names))
