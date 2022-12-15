import numpy as np
import pytest

from spg_overlay.utils.utils import normalize_angle, sign


def test_normalize_angle():
    assert normalize_angle(0) == 0
    assert normalize_angle(3) == 3
    assert normalize_angle(-3) == -3
    assert normalize_angle(-4) > 0
    assert normalize_angle(4) < 0
    assert normalize_angle(-400) > -3.1416
    assert normalize_angle(-400) < 3.1416
    assert normalize_angle(400) > -3.1416
    assert normalize_angle(400) < 3.1416

    assert np.isnan(normalize_angle(np.nan))
    assert np.isnan(normalize_angle(np.Inf))
    assert np.isnan(normalize_angle(np.NINF))


def test_sign():
    assert sign(0) == 1
    assert sign(1) == 1
    assert sign(-1) == -1
    assert sign(10000) == 1
    assert sign(-10000) == -1

    assert sign(np.NAN) == 1
    assert sign(np.Inf) == 1
    assert sign(np.NINF) == -1
