"""Immutability of raw inputs: raw/manifest.sha256 lists every raw file and its hash.

`python -m resolve raw-manifest` records the current raw files (run once when adding a new raw
version). Every build verifies the manifest and stops if a raw file changed or appeared unrecorded.
"""
import hashlib

from .paths import private_root

MANIFEST = "manifest.sha256"


def _files(raw):
    return sorted(p for p in raw.rglob("*") if p.is_file() and p.name != MANIFEST)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest():
    raw = private_root() / "raw"
    lines = [f"{_sha256(p)}  {p.relative_to(raw).as_posix()}" for p in _files(raw)]
    (raw / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def verify():
    raw = private_root() / "raw"
    path = raw / MANIFEST
    if not path.exists():
        raise RuntimeError("raw/manifest.sha256 missing: run  python -m resolve raw-manifest")
    recorded = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        recorded[rel] = digest
    problems = []
    present = {p.relative_to(raw).as_posix(): p for p in _files(raw)}
    for rel, p in present.items():
        if rel not in recorded:
            problems.append(f"unrecorded raw file: {rel}")
        elif _sha256(p) != recorded[rel]:
            problems.append(f"raw file changed: {rel}")
    problems += [f"raw file missing: {rel}" for rel in recorded if rel not in present]
    if problems:
        raise RuntimeError("raw store integrity check failed:\n  " + "\n  ".join(problems))
    return len(recorded)
