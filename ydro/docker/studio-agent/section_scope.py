"""Shared bounded semantic section discovery for Django and the offline agent.

Only literal, unique, non-nested semantic sections in Vue templates are eligible.
An unmarked or ambiguous section is never guessed from CSS or page appearance.
"""
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import PurePosixPath

SECTION_ID = re.compile(r"[a-z][a-z0-9-]{0,47}")
RESERVED = {"manual", "header", "footer"}
TRUSTED = {"CinemaModel.vue", "SceneStory.vue", "SceneCarousel.vue",
           "HeroObjectStage.vue", "AboutMetrics.vue"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


def valid_scope(value):
    return isinstance(value, str) and value != "manual" and bool(SECTION_ID.fullmatch(value))


def marker(tag, attrs):
    if tag in ("header", "footer") and "data-tn-" + tag in attrs:
        return tag
    value = attrs.get("data-tn-section")
    if (tag == "section" and valid_scope(value) and value not in RESERVED
            and attrs.get("id") == value):
        return value
    return None


class Sections(HTMLParser):
    def __init__(self, source, require_template=True):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0] + [m.end() for m in re.finditer("\n", source)]
        self.stack = []
        self.found = []
        self.require_template = require_template
        self.feed(source)
        self.close()

    def source_offset(self):
        row, col = self.getpos()
        return self.offsets[row-1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        attrs = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        in_template = tag == "template" or bool(parent and parent["template"])
        blocked = bool(parent and parent["blocked"]) or (
            tag in ("script", "style", "svg", "math", "pre", "code")
            or any(k in attrs for k in ("v-for", "v-if", "v-else-if", "v-else", "v-html", "v-pre", "v-slot"))
            or any(k.startswith(("v-slot:", "#")) for k in attrs))
        has_marker = ("data-tn-section" in attrs or "data-tn-header" in attrs or "data-tn-footer" in attrs)
        key = marker(tag, attrs)
        parents = [n for n in self.stack if n["has_marker"]]
        for n in parents:
            n["nested"] = True
        self.stack.append({"tag": tag, "start": self.source_offset(), "template": in_template,
                           "blocked": blocked, "key": key, "has_marker": has_marker,
                           "nested": bool(parents)})

    def handle_startendtag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-tn-section" in attrs or "data-tn-header" in attrs or "data-tn-footer" in attrs:
            for n in self.stack:
                if n["has_marker"]:
                    n["nested"] = True

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            node = self.stack[i]
            if node["tag"] != tag:
                continue
            exact = i == len(self.stack)-1
            del self.stack[i:]
            if not node["has_marker"]:
                return
            end = self.source.index(">", self.source_offset()) + 1
            self.found.append((node["key"], node["start"], end,
                               exact and (node["template"] or not self.require_template)
                               and not node["blocked"] and not node["nested"]))
            return


def discover(sources):
    found = []
    for name, source in sorted(sources.items()):
        if (not name.startswith("src/") or not name.endswith(".vue")
                or PurePosixPath(name).name in TRUSTED or len(source.encode("utf-8")) > 64000):
            continue
        for key, start, end, eligible in Sections(source).found:
            if key:
                found.append((key, name, start, end, eligible))
    counts = Counter(item[0] for item in found)
    return {key: (name, start, end) for key, name, start, end, eligible in found
            if eligible and counts[key] == 1}
