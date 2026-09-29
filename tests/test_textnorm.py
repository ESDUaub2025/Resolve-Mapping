from resolve.textnorm import clean, for_matching, key


def test_clean_collapses_whitespace_and_nbsp():
    assert clean("  تربة رملية\xa0 ") == "تربة رملية"


def test_clean_treats_empty_and_nan_as_missing():
    assert clean("") is None
    assert clean("   ") is None
    assert clean(float("nan")) is None
    assert clean(None) is None
    assert clean("nan") is None


def test_clean_keeps_real_zero_and_no():
    assert clean("0") == "0"
    assert clean("No") == "No"


def test_for_matching_normalizes_arabic_orthography():
    # taa marbuta / haa, alef maqsura / yaa, hamza forms, diacritics
    assert for_matching("كحلونية") == for_matching("كحلونيه")
    assert for_matching("مرستى") == for_matching("مرستي")
    assert for_matching("أكثر") == for_matching("اكثر")
    assert for_matching("يدوياً") == for_matching("يدويا")


def test_for_matching_converts_eastern_arabic_digits():
    assert for_matching("٣٠٠ ليتر") == "300 ليتر"


def test_key_ignores_spacing_and_punctuation():
    assert key("مزرعه الشوف") == key("مزرعهالشوف")
    assert key("Al-Barouk") == key("al barouk")
