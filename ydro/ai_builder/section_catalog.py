"""Load the canonical stdlib-only scope parser shipped with the Studio agent."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from .manual_edit import read_source

_PATH = Path(__file__).resolve().parents[1] / "docker" / "studio-agent" / "section_scope.py"
_SPEC = spec_from_file_location("tracknode_section_scope", _PATH)
_SCOPE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_SCOPE)


def available_sections(archive):
    files = read_source(archive)
    sources = {k: v.decode("utf-8") for k, v in files.items() if k.startswith("src/") and k.endswith(".vue")}
    return _SCOPE.discover(sources)


def valid_scope(value):
    return _SCOPE.valid_scope(value)
