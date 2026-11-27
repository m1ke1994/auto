"""Bounded storyboard contract for new cinematic projects."""
import json
from art_direction import HERO_DIRECTIONS

SECTIONS=("home","about","services","benefits","contacts")
LAYOUTS=frozenset(("full_bleed","editorial_split","museum_focus","floating_edges",
    "sticky_story","immersive_stage","chapter_carousel","horizontal_gallery",
    "feature_stack","showcase","editorial_gallery","quote_scene","detail_scene",
    "transformation","finale"))
CAROUSELS=frozenset(("chapter_carousel","horizontal_gallery","feature_stack","showcase","editorial_gallery"))
STORIES=frozenset(("sticky_story",))
FIELDS=("visual","caption","start","end","transition","mobile")

def validate_hero_options(raw):
    choices={"direction":("auto",*HERO_DIRECTIONS),"motion":("directed","still"),
             "speed":("focused","balanced","calm"),"lighting":("auto","softbox","dramatic")}
    if not isinstance(raw,dict) or set(raw)-choices.keys()-{"captions"}:
        raise ValueError("Unsupported Hero direction options.")
    result={}
    for key,allowed in choices.items():
        if key in raw:
            if raw[key] not in allowed:
                raise ValueError("Unsupported Hero "+key+".")
            result[key]=raw[key]
    if "captions" in raw:
        captions=raw["captions"]
        if not isinstance(captions,list) or not 1<=len(captions)<=5 or any(
            not isinstance(text,str) or not 2<=len(text.strip())<=145 or "{" in text for text in captions
        ):
            raise ValueError("Hero requires one to five distinct short captions.")
        captions=[text.strip() for text in captions]
        if len(set(captions))!=len(captions):
            raise ValueError("Hero captions must be distinct.")
        result["captions"]=captions
    return result

def validate_storyboard(raw):
    if isinstance(raw,str):
        if len(raw)>16000:
            raise ValueError("Storyboard too large (16000 characters maximum).")
        try:
            raw=json.loads(raw)
        except (ValueError,TypeError):
            raise ValueError("Storyboard must be valid JSON.") from None
    if not isinstance(raw,dict):
        raise ValueError("Storyboard must be an object.")
    def phrase(value,label,limit=500):
        if not isinstance(value,str) or not 3<=len(value.strip())<=limit:
            raise ValueError("Storyboard needs a concise "+label+".")
        return value.strip()
    concept=phrase(raw.get("concept"),"concept",1000)
    rhythm=phrase(raw.get("rhythm"),"text and color rhythm",1000)
    chapters=raw.get("chapters")
    if not isinstance(chapters,list) or len(chapters)!=5:
        raise ValueError("Storyboard needs five ordered business chapters.")
    clean=[]
    for expected,chapter in zip(SECTIONS,chapters):
        if not isinstance(chapter,dict) or chapter.get("section")!=expected:
            raise ValueError("Storyboard sections must be home, about, services, benefits, contacts in order.")
        layout=chapter.get("layout")
        if not isinstance(layout,str) or layout not in LAYOUTS:
            raise ValueError("Choose a supported scene layout for "+expected+".")
        clean.append({"section":expected,"layout":layout,**{k:phrase(chapter.get(k),expected+" "+k) for k in FIELDS}})
    layouts={c["layout"] for c in clean}
    if len(layouts)<3 or not layouts&CAROUSELS or not layouts&STORIES or clean[-1]["layout"]!="finale":
        raise ValueError("Use at least three distinct layouts, one sticky_story, one carousel layout and a finale in contacts.")
    if clean[0]["layout"] in CAROUSELS|STORIES or any(c["section"] not in ("about","services","benefits") for c in clean if c["layout"] in CAROUSELS|STORIES):
        raise ValueError("Place the narrative and carousel in middle chapters, not the hero or contacts.")
    result={"concept":concept,"rhythm":rhythm,"chapters":clean}
    if "hero" in raw:
        result["hero"]=validate_hero_options(raw["hero"])
    return result
