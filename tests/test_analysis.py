"""Statistical helpers of resolve.analysis on synthetic data."""
import numpy as np

from resolve.analysis import bh_qvalues, mantel_haenszel


def test_single_stratum_equals_crude_odds_ratio():
    # a=20 b=10 c=10 d=20 -> OR = (20*20)/(10*10) = 4
    x = np.array([1] * 30 + [0] * 30)
    y = np.array([1] * 20 + [0] * 10 + [1] * 10 + [0] * 20)
    odds, lo, hi, p = mantel_haenszel(x, y, np.array(["s"] * 60))
    assert abs(odds - 4.0) < 1e-9
    assert lo < 4 < hi and lo > 1
    assert p < 0.05


def test_stratification_removes_confounding_by_region():
    # Within each region exposure and outcome are unrelated (OR = 1), but region drives both.
    def block(n_x1_y1, n_x1_y0, n_x0_y1, n_x0_y0, region):
        x = [1] * (n_x1_y1 + n_x1_y0) + [0] * (n_x0_y1 + n_x0_y0)
        y = [1] * n_x1_y1 + [0] * n_x1_y0 + [1] * n_x0_y1 + [0] * n_x0_y0
        return x, y, [region] * len(x)
    x1, y1, s1 = block(40, 10, 8, 2, "a")   # OR 1 inside region a
    x2, y2, s2 = block(2, 8, 10, 40, "b")   # OR 1 inside region b
    x, y, s = map(np.array, (x1 + x2, y1 + y2, s1 + s2))
    odds, lo, hi, _ = mantel_haenszel(x, y, s)
    assert abs(odds - 1.0) < 1e-9 and lo < 1 < hi


def test_undefined_ratio_returns_none():
    x = np.array([1, 1, 0, 0])
    y = np.array([1, 1, 1, 1])
    assert mantel_haenszel(x, y, np.array(["s"] * 4)) is None


def test_benjamini_hochberg():
    q = bh_qvalues([0.01, 0.04, 0.03, 0.5])
    assert list(np.round(q, 4)) == [0.04, 0.0533, 0.0533, 0.5]
    assert all(qi >= pi for qi, pi in zip(q, [0.01, 0.04, 0.03, 0.5]))
