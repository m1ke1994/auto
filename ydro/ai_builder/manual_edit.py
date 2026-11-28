"""Conservative source-level visual text editing. Stdlib only, runs offline."""
import hashlib
import json
import re
import stat
import sys
import zipfile
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path

MAX_ARCHIVE = 40 * 1024 * 1024
MAX_FIELDS = 300
MAX_CHANGES = 12
MAX_TEXT = 500
TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "a", "button",
        "li", "strong", "em", "small", "label", "blockquote", "figcaption", "div"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
TRUSTED = {"CinemaModel.vue", "SceneStory.vue", "SceneCarousel.vue",
           "HeroObjectStage.vue", "AboutMetrics.vue"}


class ManualEditError(ValueError):
    pass


def read_source(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > MAX_ARCHIVE:
        raise ManualEditError("Unsupported source archive")
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if len(entries) > 512 or sum(e.file_size for e in entries) > MAX_ARCHIVE:
            raise ManualEditError("Source archive exceeds limits")
        files, seen, tree = {}, set(), {}
        for e in entries:
            name = e.orig_filename.replace("\\", "/")
            directory = name.endswith("/")
            name = name.rstrip("/") if directory else name
            parts = name.split("/")
            if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and not p.startswith(".") for p in parts):
                raise ManualEditError("Unsafe source path")
            mode = stat.S_IFMT(e.external_attr >> 16) if e.create_system == 3 else 0
            if (mode not in (0, stat.S_IFDIR, stat.S_IFREG) or
                    (mode == stat.S_IFDIR and not directory) or
                    (mode == stat.S_IFREG and directory) or e.flag_bits & 1):
                raise ManualEditError("Unsafe source entry")
            if name.lower() in seen:
                raise ManualEditError("Duplicate source entry")
            seen.add(name.lower())
            for i in range(1, len(parts)+1):
                prefix = "/".join(parts[:i])
                kind = "directory" if directory or i < len(parts) else "file"
                previous = tree.setdefault(prefix.lower(), (prefix, kind))
                if previous != (prefix, kind):
                    raise ManualEditError("Source path collision")
            if directory:
                if e.file_size:
                    raise ManualEditError("Invalid source directory")
                continue
            if len(files) >= 180:
                raise ManualEditError("Source file limit exceeded")
            files[name] = z.read(e)
    meta = json.loads(files.get("tracknode-agent.json", b"{}"))
    if not isinstance(meta, dict) or meta.get("engine") != "openhands-sdk" or meta.get("checkpoint"):
        raise ManualEditError("Unsupported source format")
    return files


def fingerprint(files):
    digest = hashlib.sha256()
    for name, value in sorted(files.items()):
        digest.update(name.encode("utf-8") + b"\0" + hashlib.sha256(value).digest())
    return digest.hexdigest()


def normalize(text):
    return " ".join(text.split())


class TextFields(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0] + [m.end() for m in re.finditer("\n", source)]
        self.stack = []
        self.fields = []
        self.feed(source)
        self.close()

    def offset(self):
        row, column = self.getpos()
        return self.lines[row-1] + column

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        attrs = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        section = (attrs.get("data-tn-section") or
                   ("header" if tag == "header" else "footer" if tag == "footer" else "") or
                   (parent["section"] if parent else ""))
        template = tag == "template" or bool(parent and parent["template"])
        blocked = bool(parent and parent["blocked"]) or (
            tag in ("script", "style", "svg", "math", "textarea", "pre", "code", "option") or
            any(k in attrs for k in ("v-for", "v-pre", "v-html", "v-text", "v-model", "data-tn-film-caption")) or
            any(k.startswith("data-tn-contact") for k in attrs) or
            str(attrs.get("href") or "").startswith(("tel:", "mailto:")) or
            (tag not in TAGS and tag not in ("template", "main", "section", "header", "footer",
                                              "article", "aside", "nav", "ul", "ol", "figure", "form")))
        self.stack.append({"tag": tag, "start": self.offset()+len(self.get_starttag_text()),
                           "template": template, "blocked": blocked, "section": section})

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            node = self.stack[i]
            if node["tag"] != tag:
                continue
            exact = i == len(self.stack)-1
            del self.stack[i:]
            if not exact or not node["template"] or node["blocked"] or tag not in TAGS:
                return
            start, end = node["start"], self.offset()
            raw = self.source[start:end]
            # Only a plain leaf, never markup, directives, expressions or mixed content.
            if "<" in raw or "{" in raw or "}" in raw:
                return
            trimmed = raw.strip()
            value = normalize(unescape(trimmed))
            if not 2 <= len(value) <= MAX_TEXT:
                return
            start += len(raw)-len(raw.lstrip())
            end -= len(raw)-len(raw.rstrip())
            self.fields.append((start, end, tag, node["section"] or "content", value))
            return


def catalog(files):
    fields = []
    for name, value in sorted(files.items()):
        if not (name.startswith("src/") and name.endswith(".vue")) or Path(name).name in TRUSTED:
            continue
        if len(value) > 64000:
            continue
        source = value.decode("utf-8")
        for start, end, tag, section, text in TextFields(source).fields:
            key = hashlib.sha256(f"{name}:{start}:{end}:{text}".encode()).hexdigest()[:32]
            fields.append({"id": key, "file": name, "start": start, "end": end,
                           "tag": tag, "section": section, "text": text})
            if len(fields) >= MAX_FIELDS:
                return fields
    return fields


def public_fields(files):
    return [{k: f[k] for k in ("id", "tag", "section", "text")} for f in catalog(files)]


def apply_changes(files, expected, changes):
    if expected != fingerprint(files):
        raise ManualEditError("Source version changed")
    if not isinstance(changes, list) or not 1 <= len(changes) <= MAX_CHANGES:
        raise ManualEditError("Invalid change count")
    fields = {f["id"]: f for f in catalog(files)}
    edits, seen = {}, set()
    for change in changes:
        if not isinstance(change, dict) or set(change) != {"id", "text"}:
            raise ManualEditError("Invalid change")
        key, value = change["id"], change["text"]
        if not isinstance(key, str) or key not in fields or key in seen:
            raise ManualEditError("Unknown or duplicate field")
        seen.add(key)
        if (not isinstance(value, str) or not 2 <= len(value.strip()) <= MAX_TEXT or
                any(c in value for c in "{}") or any(ord(c) < 32 or ord(c) == 127 for c in value)):
            raise ManualEditError("Invalid text; use plain text without template expressions")
        f = fields[key]
        value = normalize(value)
        if value == f["text"]:
            continue
        # Escape HTML syntax; never generate Vue expressions, attributes or JS.
        edits.setdefault(f["file"], []).append((f["start"], f["end"], escape(value, quote=False)))
    if not edits:
        raise ManualEditError("No text changes")
    result = dict(files)
    for name, replacements in edits.items():
        source = files[name].decode("utf-8")
        for start, end, value in sorted(replacements, reverse=True):
            source = source[:start] + value + source[end:]
        if len(source.encode("utf-8")) > 64000:
            raise ManualEditError("Edited component too large")
        result[name] = source.encode("utf-8")
    meta = json.loads(result["tracknode-agent.json"])
    meta.update(build_verified=False, visual_verified=False, manual_edit=True)
    result["tracknode-agent.json"] = json.dumps(meta, ensure_ascii=False).encode("utf-8")
    return result


def main():
    job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    files = read_source(sys.argv[2])
    result = apply_changes(files, job["source_fingerprint"], job["changes"])
    with zipfile.ZipFile(sys.argv[3], "x", compression=zipfile.ZIP_DEFLATED) as z:
        for name, value in result.items():
            z.writestr(name, value)
    print("STUDIO_MANUAL_SOURCE_READY", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("STUDIO_MANUAL_EDIT_FAILED: " + type(exc).__name__, file=sys.stderr, flush=True)
        raise SystemExit(1) from None
