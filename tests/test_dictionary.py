"""The field dictionary and vocabularies are internally consistent and map real answers correctly."""
import pytest

from resolve.dictionary import CODED_TYPES, PUBLIC_CLASSES, check, load


@pytest.fixture(scope="module")
def d():
    return load()


def test_dictionary_passes_structural_checks(d):
    check(d)  # raises DictionaryError on any problem


def test_identity_fields_are_never_public(d):
    identity = [f for f in d.fields if f.privacy == "identity"]
    assert {f.code for f in identity} == {"name_latin", "name_arabic", "phone"}
    assert all(not f.is_public for f in identity)


def test_free_text_is_never_public(d):
    assert all(f.type in CODED_TYPES for f in d.fields if f.privacy in PUBLIC_CLASSES)


def test_every_field_has_bilingual_labels(d):
    for f in d.fields:
        assert f.label.get("en") and f.label.get("ar"), f.code


def test_every_instrument_has_a_village_source(d):
    for instrument in d.instruments:
        assert instrument in d.field("village_reported").sources


# Real answer strings from the two instruments (no personal data) -> expected codes.
CASES = [
    ("reliance", "Partial credit", ["partial"]),           # machine-translation error in source
    ("reliance", "Full accreditation", ["total"]),         # machine-translation error in source
    ("reliance", "It is not used", ["not_used"]),
    ("reliance", "اعتماد كلي", ["total"]),
    ("income_source", "Non-agricultural work", ["non_ag_labour"]),
    ("income_source", "Crop cultivation, agricultural work", ["crops", "ag_labour"]),
    ("water_availability", "rarely sufficient", ["rarely"]),
    ("water_availability", "Totally insufficient", ["never"]),
    ("yes_no", "Yes (Small)", ["yes"]),
    ("yes_no", " نعم", ["yes"]),
    ("cost_share", "From 20% to 50%", ["20_50"]),
    ("cost_share", "> 50%", ["gt_50"]),
    ("age_group", "> 55", ["age_over_55"]),
    ("land_size_band", "< 5 dunums (< 5,000 m²)", ["lt_5_dunum"]),
    ("land_size_band", "More than 2 hectares (> 20,000 m²)", ["gt_2_ha"]),
    ("production_level", "Medium production (for local consumption and some sales)", ["medium"]),
    ("homes_share", "Almost all homes", ["almost_all"]),
    ("irrigation_need_change", "not sure", ["unsure"]),
    ("climate_change", "Rise in temperature, Decrease in rainfall, Increase in heatwaves",
     ["temperature_rise", "rainfall_decrease", "heatwaves"]),
]


@pytest.mark.parametrize("vocab,text,expected", CASES)
def test_vocabulary_matching(d, vocab, text, expected):
    assert d.vocabularies[vocab].codes_in(text) == expected


def test_all_of_the_above_expands(d):
    v = d.vocabularies["seed_criteria"]
    assert v.expand(v.codes_in("All of the above")) == ["price", "productivity", "pest_resistance"]
