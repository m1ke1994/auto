"""Read-only, streamed fingerprints for immutable build artifacts."""
import hashlib
import zipfile
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(run):
    run = Path(run)
    dist = run / "dist"
    archive = run / "tracknode-agent-site.zip"
    if (dist.is_symlink() or archive.is_symlink() or not archive.is_file()
            or not (dist / "index.html").is_file()):
        raise OSError("Version artifacts missing or unsafe")
    digest = hashlib.sha256()
    count = size = 0
    for path in sorted(dist.rglob("*"), key=lambda p: p.relative_to(dist).as_posix()):
        if path.is_symlink():
            raise OSError("Symlink in version build")
        if path.is_dir():
            continue
        if not path.is_file():
            raise OSError("Unsupported build artifact")
        relative = path.relative_to(dist).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(sha256_file(path).encode("ascii") + b"\n")
        count += 1
        size += path.stat().st_size
    runtime = {}
    try:
        with zipfile.ZipFile(archive) as source:
            for name in ("src/components/CinemaModel.vue", "src/cinematic-motion.js",
                         "STORYBOARD.json"):
                try:
                    info = source.getinfo(name)
                except KeyError:
                    continue
                if info.file_size <= 2 * 1024 * 1024:
                    runtime[name] = hashlib.sha256(source.read(info)).hexdigest()
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        # Legacy fixtures / archives without a known runtime are not assigned a fake version.
        runtime = {}
    return {"schema": 1, "archive_sha256": sha256_file(archive),
            "dist_sha256": digest.hexdigest(), "dist_files": count,
            "dist_bytes": size, "archive_bytes": archive.stat().st_size,
            "runtime": runtime}


def matches_manifest(run, expected):
    if not expected or expected.get("schema") != 1:
        return False
    try:
        return build_manifest(run) == expected
    except (OSError, ValueError):
        return False
