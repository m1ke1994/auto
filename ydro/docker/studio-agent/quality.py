"""Source heuristics: enforce structural requirements, not artistic quality."""
import re

def quality_issues(files, profile):
    issues=[]
    app=files.get("src/App.vue","")
    footer=files.get("src/components/SiteFooter.vue","")
    if not re.search(r"<footer\b[^>]*\bdata-tn-footer\b",footer):
        issues.append("Create src/components/SiteFooter.vue with <footer data-tn-footer>.")
    if not re.search(r"<SiteFooter\b|<site-footer\b",app):
        issues.append("Render SiteFooter in App.vue after the main content.")
    if not re.search(r"\bimport\s+SiteFooter\s+from\s+['\"]\./components/SiteFooter\.vue['\"]",app):
        issues.append("Import SiteFooter from ./components/SiteFooter.vue in App.vue.")
    if not re.search(r"<a\b|<nav\b",footer):
        issues.append("Footer needs useful navigation or contact links, not only copyright.")
    if profile=="cinema":
        source="\n".join(v for p,v in files.items() if p.endswith((".vue",".js",".ts")))
        scenes=set(re.findall(r'\bdata-tn-scene\s*=\s*["\']([a-zA-Z0-9_-]+)["\']',source))
        if len(scenes)<3:
            issues.append("Mark at least 3 distinct cinematic chapters with literal data-tn-scene names.")
        if not re.search(r"from\s*['\"]gsap/ScrollTrigger['\"]",source):
            issues.append("Import GSAP ScrollTrigger for real scroll-driven scenes.")
        if not re.search(r"\bscrub\s*:\s*(?:true|[0-9]+(?:\.[0-9]+)?)\b",source):
            issues.append("Implement a scrubbed scroll timeline, not only on-enter fade-ins.")
        if len(re.findall(r"\bdata-tn-motion\b",source))<2:
            issues.append("Mark at least two actually animated visual layers with data-tn-motion.")
    return issues
