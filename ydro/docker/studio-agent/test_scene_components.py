from pathlib import Path
import unittest
from quality import quality_issues

ROOT=Path(__file__).parent
STORY=(ROOT/"SceneStory.vue").read_text(encoding="utf-8")

class SceneComponentTests(unittest.TestCase):
    def test_scene_story_has_mobile_visual_slot(self):
        self.assertIn('name="mobile-visual"',STORY)
        self.assertIn(".tn-story .tn-story-stage { display: none; }",STORY)
        self.assertIn(".tn-story .tn-story-mobile-visual",STORY)

    def test_active_story_caption_has_readable_state(self):
        self.assertIn("opacity: .36",STORY)
        self.assertIn("opacity: 1",STORY)

    def test_custom_story_visual_requires_mobile_visual_slot(self):
        app='''<SceneStory :chapters="chapters">
<template #visual="{ item }"><div>{{ item.title }}</div></template>
</SceneStory>'''
        issues=quality_issues({"src/App.vue":app},"cinema")
        self.assertTrue(any("#mobile-visual" in issue for issue in issues))
        app=app.replace("</SceneStory>",'<template #mobile-visual="{ item }"><div>{{ item.title }}</div></template>\n</SceneStory>')
        issues=quality_issues({"src/App.vue":app},"cinema")
        self.assertFalse(any("#mobile-visual" in issue for issue in issues))

if __name__=="__main__":
    unittest.main()
