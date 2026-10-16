"""Exercise the real SEO injection functions without a database or Django runtime."""
import ast
import re
import unittest
from pathlib import Path

source = ast.parse(Path('ydro/apps/sites/views.py').read_text(encoding='utf-8-sig'))
namespace = {'re': re, 'render_public_site_seo_head': lambda seo: '<title>Editable SEO</title>'}
for node in source.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith('_SEO_') for t in node.targets):
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<seo-regex>', 'exec'), namespace)
    if isinstance(node, ast.FunctionDef) and node.name == '_inject_public_site_seo':
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<seo-inject>', 'exec'), namespace)

class SeoHeadTests(unittest.TestCase):
    def test_platform_credit_survives_editable_head_replacement(self):
        html = '''<html><head><title>Old</title><link rel="canonical" href="old">
        <script type="application/ld+json" id="public-site-json-ld">{"name":"old"}</script>
        <script id="tracknode-platform-json-ld" type="application/ld+json">{"name":"TrackNode"}</script>
        </head><body><h1>Leelabird</h1><footer itemscope itemtype="https://schema.org/WebSite"><span itemprop="creator" itemscope itemtype="https://schema.org/Organization"><meta itemprop="name" content="TrackNode"><a href="https://tracknode.ru/">by TrackNode</a></span></footer></body></html>'''
        result = namespace['_inject_public_site_seo'](html, {})
        self.assertEqual(result.count('<title>'), 1)
        self.assertIn('Editable SEO', result)
        self.assertNotIn('public-site-json-ld', result)
        self.assertIn('itemprop="creator"', result)
        self.assertIn('itemtype="https://schema.org/Organization"', result)
        self.assertIn('<h1>Leelabird</h1>', result)
        self.assertIn('by TrackNode', result)

    def test_private_robots_header_keeps_original_request_url(self):
        for file in ['ydro/docker/nginx/templates/default.conf.template', 'ydro/docker/nginx/templates-https/default.conf.template']:
            text = Path(file).read_text()
            self.assertIn('map $request_uri $tracknode_indexing', text)
            self.assertIn('default "noindex, follow"', text)
            self.assertIn('add_header X-Robots-Tag $tracknode_indexing always;', text)
            self.assertIn('try_files $uri $uri/index.html $uri/ /index.html;', text)

if __name__ == '__main__':
    unittest.main()
