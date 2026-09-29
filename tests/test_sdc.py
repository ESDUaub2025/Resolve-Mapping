"""Disclosure-control rules on synthetic respondents (no real data)."""
import pytest

from resolve import sdc
from resolve.dictionary import load


def record(i, adm3, adm2, **answers):
    d = load()
    values, status = {}, {}
    for f in d.fields:
        if f.privacy == "identity":
            continue
        if f.code in answers:
            values[f.code], status[f.code] = answers[f.code], "reported"
        else:
            values[f.code], status[f.code] = None, "not_provided"
    return {"response_id": f"T-{i}:test", "respondent_id": f"T-{i}", "instrument": "test",
            "location": {"adm3_pcode": adm3, "adm2_pcode": adm2, "locality_id": adm3},
            "values": values, "status": status}


@pytest.fixture
def records():
    big = [record(i, "V1", "D1", water_availability="always", gender="male",
                  income_sources=["crops"]) for i in range(6)]
    small = [record(10 + i, "V2", "D1", water_availability="never", gender="female",
                    income_sources=["business"]) for i in range(2)]
    other_small = [record(20 + i, "V3", "D1", water_availability="rarely", gender="male",
                          income_sources=["crops"]) for i in range(3)]
    tiny_district = [record(30, "V9", "D2", water_availability="always")]
    return big + small + other_small + tiny_district


def test_village_published_only_at_or_above_k(records):
    villages, _, _ = sdc.summarize(records, k=5)
    assert [v["adm3_pcode"] for v in villages] == ["V1"]
    assert villages[0]["n_respondents"] == 6


def test_small_villages_pooled_into_district_remainder(records):
    _, districts, _ = sdc.summarize(records, k=5)
    d1 = next(x for x in districts if x["adm2_pcode"] == "D1")
    assert d1["n_remainder"] == 5          # V2 (2) + V3 (3); V1 is published separately
    counts = d1["remainder_indicators"]["water_availability"]["counts"]
    assert counts["never"] == 2 and counts["rarely"] == 3 and counts["always"] == 0


def test_district_below_k_is_not_published(records):
    _, districts, log = sdc.summarize(records, k=5)
    assert "D2" not in {x["adm2_pcode"] for x in districts}
    assert {"adm2_pcode": "D2", "n": 1} in log["suppressed_districts"]


def test_sensitive_fields_only_at_district_level(records):
    villages, districts, _ = sdc.summarize(records, k=5)
    assert "gender" not in villages[0]["indicators"]
    assert "income_sources" not in villages[0]["indicators"]
    assert "gender" in districts[0]["indicators"]


def test_small_cells_suppressed_with_complement_for_single_choice(records):
    _, districts, _ = sdc.summarize(records, k=5)
    gender = next(x for x in districts if x["adm2_pcode"] == "D1")["indicators"]["gender"]
    # female = 2 would be derivable from the total, so both cells are hidden
    assert gender["counts"]["female"] is None
    assert gender["counts"]["male"] is None
    assert gender["suppressed"] == "small_cells"


def test_indicator_with_fewer_than_k_answers_is_suppressed(records):
    villages, _, _ = sdc.summarize(records, k=5)
    s = villages[0]["indicators"]["soil_types"]  # nobody answered
    assert s["counts"] is None and s["suppressed"] == "fewer_than_k_answers"
    assert s["status_counts"] == {"not_provided": 6}
