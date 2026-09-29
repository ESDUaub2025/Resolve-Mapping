"""Loads and checks the field dictionary and controlled vocabularies (dictionary/*.yaml)."""
import re
from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from .paths import DICTIONARY
from .textnorm import for_matching, normalize_arabic_letters

PRIVACY_CLASSES = ("identity", "research", "public_district", "public_village")
PUBLIC_CLASSES = ("public_district", "public_village")
FIELD_TYPES = ("text", "date", "categorical", "ordinal", "multi")
CODED_TYPES = ("categorical", "ordinal", "multi")

# Value-state vocabulary (plan A5). "suppressed" only appears in public aggregates.
STATUSES = {
    "reported": {"en": "Reported", "ar": "مُبلَّغ عنه"},
    "not_provided": {"en": "Not provided", "ar": "لم تتم الإجابة"},
    "not_asked": {"en": "Not asked in this survey", "ar": "لم يُطرح في هذا الاستبيان"},
    "not_applicable": {"en": "Not applicable", "ar": "لا ينطبق"},
    "invalid": {"en": "Unreadable / ambiguous answer", "ar": "إجابة غير واضحة"},
    "suppressed": {"en": "Hidden to protect privacy", "ar": "مخفي لحماية الخصوصية"},
}


class DictionaryError(ValueError):
    pass


@dataclass
class Code:
    code: str
    label: dict
    patterns: list
    expands_to: list = field(default_factory=list)
    exclusive: bool = False


@dataclass
class Vocabulary:
    name: str
    kind: str
    codes: list
    note: str = ""
    generated: bool = False  # codes filled in at build time (e.g. farmer_type)

    @property
    def code_names(self):
        return [c.code for c in self.codes]

    def label(self, code, lang="en"):
        for c in self.codes:
            if c.code == code:
                return c.label.get(lang) or c.label["en"]
        raise KeyError(code)

    def codes_in(self, text):
        """All codes whose patterns occur in `text`, in vocabulary order."""
        norm = for_matching(text)
        if norm is None:
            return []
        return [c.code for c in self.codes if any(p.search(norm) for p in c.patterns)]

    def expand(self, codes):
        out = []
        for name in codes:
            spec = next(c for c in self.codes if c.code == name)
            for target in spec.expands_to or [name]:
                if target not in out:
                    out.append(target)
        order = self.code_names
        return sorted(out, key=order.index)


@dataclass
class Field:
    code: str
    label: dict
    type: str
    privacy: str
    group: str
    sources: dict
    vocab: str = None
    applies_if: dict = None
    note: str = ""
    derived: bool = False  # computed by resolve.analysis, not read from a survey column
    short_label: dict = None

    @property
    def is_public(self):
        return self.privacy in PUBLIC_CLASSES


@dataclass
class Dictionary:
    fields: list
    vocabularies: dict
    groups: dict
    instruments: dict
    datasets: dict

    def field(self, code):
        for f in self.fields:
            if f.code == code:
                return f
        raise KeyError(code)

    def vocab_for(self, fld):
        return self.vocabularies[fld.vocab] if fld.vocab else None

    def fields_for(self, instrument):
        return [f for f in self.fields if instrument in f.sources]


def _compile(pattern):
    # Patterns are written against normalized text; normalize Arabic letters in the pattern too.
    return re.compile(normalize_arabic_letters(pattern), re.IGNORECASE)


def _load_yaml(name):
    with open(DICTIONARY / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(maxsize=1)
def load() -> Dictionary:
    vocab_doc = _load_yaml("vocabularies.yaml")
    vocabularies = {}
    for name, spec in vocab_doc.items():
        codes = [
            Code(
                code=str(c["code"]),
                label=c["label"],
                patterns=[_compile(p) for p in c.get("match", [])],
                expands_to=c.get("expands_to", []),
                exclusive=c.get("exclusive", False),
            )
            for c in spec["codes"]
        ]
        vocabularies[name] = Vocabulary(name, spec["kind"], codes, spec.get("note", ""), spec.get("generated", False))

    field_doc = _load_yaml("fields.yaml")
    fields = [Field(**{k: v for k, v in f.items()}) for f in field_doc["fields"]]
    d = Dictionary(
        fields=fields,
        vocabularies=vocabularies,
        groups=field_doc["groups"],
        instruments=_load_yaml("instruments.yaml"),
        datasets=_load_yaml("datasets.yaml"),
    )
    check(d)
    return d


def check(d: Dictionary):
    """Structural invariants of the dictionary itself. Raises DictionaryError."""
    errors = []
    seen = set()
    for f in d.fields:
        if f.code in seen:
            errors.append(f"duplicate field code {f.code}")
        seen.add(f.code)
        if f.type not in FIELD_TYPES:
            errors.append(f"{f.code}: unknown type {f.type}")
        if f.privacy not in PRIVACY_CLASSES:
            errors.append(f"{f.code}: unknown privacy class {f.privacy}")
        if f.group not in d.groups:
            errors.append(f"{f.code}: unknown group {f.group}")
        if f.type in CODED_TYPES:
            if f.vocab not in d.vocabularies:
                errors.append(f"{f.code}: vocabulary {f.vocab!r} not defined")
            elif (d.vocabularies[f.vocab].kind == "multi") != (f.type == "multi"):
                errors.append(f"{f.code}: type {f.type} does not match vocabulary kind")
        elif f.vocab:
            errors.append(f"{f.code}: {f.type} field must not have a vocabulary")
        if f.privacy in PUBLIC_CLASSES and f.type not in CODED_TYPES:
            errors.append(f"{f.code}: only coded fields can be public (free text is never published)")
        if f.privacy == "identity" and f.type != "text":
            errors.append(f"{f.code}: identity fields must be text")
        for instrument in f.sources:
            if instrument not in d.instruments:
                errors.append(f"{f.code}: unknown instrument {instrument}")
        if f.applies_if:
            parent = f.applies_if.get("field")
            if parent not in seen:
                errors.append(f"{f.code}: applies_if parent {parent!r} must be defined earlier")
    for v in d.vocabularies.values():
        names = v.code_names
        if len(names) != len(set(names)):
            errors.append(f"vocabulary {v.name}: duplicate codes")
        for c in v.codes:
            if not c.patterns and not v.generated:
                errors.append(f"vocabulary {v.name}: code {c.code} has no match patterns")
            for target in c.expands_to:
                if target not in names:
                    errors.append(f"vocabulary {v.name}: {c.code} expands to unknown {target}")
            if "en" not in c.label or "ar" not in c.label:
                errors.append(f"vocabulary {v.name}: code {c.code} needs en and ar labels")
    if errors:
        raise DictionaryError("; ".join(errors))
