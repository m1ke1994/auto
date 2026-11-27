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
    # The trusted model renderer already eases motion; a second page-scroll
    # controller competes with it. Reject obvious Lenis imports on model pages.
    if re.search(r"<CinemaModel\b",source):
        scripts="\n".join(v for p,v in files.items() if p.endswith((".vue",".js",".ts")))
        if re.search(r"""(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)['"]lenis(?:/[^'"]*)?['"]""",scripts,re.I):
            issues.append("Remove Lenis from pages with CinemaModel; use native scroll and the trusted model renderer.")
    if profile=="cinema":
        # A primary 3D Hero is a film contract, not a decorative model embed.
        home_match=re.search(r"<section\b(?=[^>]*\bid\s*=\s*['\"]home['\"])[^>]*>(.*?)</section>",app,re.S)
        home=home_match.group(1) if home_match else ""
        if re.search(r"<CinemaModel\b",home):
            if len(re.findall(r"<CinemaModel\b",home))!=1:
                issues.append("The film Hero must contain exactly one persistent primary CinemaModel.")
            if not re.search(r'class\s*=\s*["\'][^"\']*\bhero-stage\b',home):
                issues.append("The film Hero needs one full-screen .hero-stage containing the primary CinemaModel.")
            if not re.search(r'class\s*=\s*["\'][^"\']*\bhero-content\b',home):
                issues.append("The film Hero needs a semantic .hero-content overlay.")
            if not re.search(r'class\s*=\s*["\'][^"\']*\btn-film-captions\b',home):
                issues.append("Add the five-beat .tn-film-captions overlay to the Hero.")
            caption_tags=re.findall(r'<[^>]*\bdata-tn-film-caption\b[^>]*>',home)
            if len(caption_tags)!=5:
                issues.append("The film Hero must contain exactly five independent scroll captions.")
            else:
                intervals=[]
                for tag in caption_tags:
                    start=re.search(r"data-tn-film-start\s*=\s*['\"](0(?:\.\d+)?|1(?:\.0+)?)['\"]",tag)
                    end=re.search(r"data-tn-film-end\s*=\s*['\"](0(?:\.\d+)?|1(?:\.0+)?)['\"]",tag)
                    if not start or not end:
                        intervals=[]
                        break
                    a,b=float(start.group(1)),float(end.group(1))
                    if not 0<=a<b<=1:
                        intervals=[]
                        break
                    intervals.append((a,b))
                if len(intervals)!=5 or intervals[0][0]!=0 or intervals[-1][1]!=1 or any(intervals[i][1]>intervals[i+1][0] for i in range(4)):
                    issues.append("Hero captions need five ordered, non-overlapping scroll intervals spanning 0–100%.")
        # A custom desktop SceneStory visual is not enough: each chapter needs a
        # matching mobile visual slot or the mobile story silently renders empty.
        if re.search(r"<SceneStory\b",app) and re.search(r"<template\s+#visual\b",app):
            if not re.search(r"<template\s+#mobile-visual\b",app):
                issues.append("SceneStory custom #visual requires a per-chapter #mobile-visual slot; otherwise mobile chapters render empty.")
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
