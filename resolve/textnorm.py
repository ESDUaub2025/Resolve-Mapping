"""Text normalization shared by vocabulary matching, gazetteer lookup and ID keys.

Normalization is used for *matching only*; original values are always kept as-is.
"""
import math
import re
import unicodedata

_EASTERN_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_INVISIBLE = re.compile(r"[ ​-‏‪-‮⁦-⁩﻿]")
_ARABIC_MARKS = re.compile(r"[ً-ْٰـ]")  # harakat, dagger alef, tatweel
_ARABIC_LETTERS = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و"}


def clean(value):
    """Trim and collapse whitespace (incl. NBSP and bidi marks). Empty/NaN -> None."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = _INVISIBLE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if text == "" or text.lower() in {"nan", "<na>", "none", "nat"}:
        return None
    return text


def normalize_arabic_letters(text: str) -> str:
    text = _ARABIC_MARKS.sub("", text)
    for src, dst in _ARABIC_LETTERS.items():
        text = text.replace(src, dst)
    return text


def for_matching(value):
    """Lower-case, Western digits, normalized Arabic letters; None stays None."""
    text = clean(value)
    if text is None:
        return None
    text = normalize_arabic_letters(text.translate(_EASTERN_DIGITS)).lower()
    return re.sub(r"\s+", " ", text)


def key(value):
    """Compact key for identity matching: for_matching without spaces or punctuation."""
    text = for_matching(value)
    if text is None:
        return None
    return re.sub(r"[\s\W_]+", "", text)
