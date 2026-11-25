"""Source heuristics: enforce structural requirements, not artistic quality."""
import re

REQUIRED_SECTIONS = ("home", "about", "services", "benefits", "contacts")

def literal_attribute(tag, name, value):
    return bool(re.search(r"(?<![\w:-])" + re.escape(name) + r"\s*=\s*(['\"])" + re.escape(value) + r"\1", tag))

def quality_issues(files, profile):
    issues=[]
    app=files.get("src/App.vue","")
    footer=files.get("src/components/SiteFooter.vue","")
    header=files.get("src/components/SiteHeader.vue","")
    source="\n".join(v for p,v in files.items() if p.endswith(".vue"))
    if not re.search(r"<header\b[^>]*\bdata-tn-header\b",header) or not re.search(r"<nav\b",header):
        issues.append("Create SiteHeader.vue with <header data-tn-header> and semantic navigation.")
    if not re.search(r"\bimport\s+SiteHeader\s+from\s+['\"]\./components/SiteHeader\.vue['\"]",app) or not re.search(r"<SiteHeader\b",app):
        issues.append("Import and render SiteHeader in App.vue before main.")
    if not re.search(r"<main\b",app):
        issues.append("App.vue must contain a main element wrapping the landing sections.")
    tags=re.findall(r"<section\b[^>]*>",source)
    for key in REQUIRED_SECTIONS:
        if not any(literal_attribute(tag,"id",key) and literal_attribute(tag,"data-tn-section",key) for tag in tags):
            issues.append("Add a distinct section with id="+key+" and data-tn-section="+key+".")
    if not re.search(r"<h1\b",source):
        issues.append("Hero needs an actual h1 heading.")
    for key in ("home","about","services","contacts"):
        if not literal_attribute(header,"href","#"+key):
            issues.append("Header must link to #"+key+" with a literal anchor.")
    if not re.search(r"\bdata-tn-service\b",source):
        issues.append("Mark real service/product cards with data-tn-service (at least three rendered cards).")
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
