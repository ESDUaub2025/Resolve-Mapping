"""Filesystem locations. Restricted data lives only in the private store, never in this repo."""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DICTIONARY = REPO / "dictionary"
REF = REPO / "ref"
PUBLIC = REPO / "public"
PUBLIC_DATA = PUBLIC / "data"


class PrivateStoreMissing(RuntimeError):
    pass


def private_root() -> Path:
    """The private data store (raw, registry, staging, canonical, research build).

    Set RESOLVE_PRIVATE_DATA to override; defaults to a sibling folder of the repository.
    """
    root = Path(os.environ.get("RESOLVE_PRIVATE_DATA", REPO.parent / "RESOLVE-data-private"))
    if not (root / "raw").is_dir():
        raise PrivateStoreMissing(
            f"Private data store not found at {root}. Set RESOLVE_PRIVATE_DATA to its location."
        )
    root = root.resolve()
    if REPO in root.parents or root == REPO:
        raise PrivateStoreMissing("The private data store must not be inside the public repository.")
    return root


def codab_dir() -> Path:
    return private_root() / "raw" / "admin_boundaries" / "codab-2026-01-26"
