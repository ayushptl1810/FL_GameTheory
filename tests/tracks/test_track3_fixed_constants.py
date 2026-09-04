"""Track 3 fixed-constants box reduction (`_fix_declared_constants`)."""

from tracks.track3_dreal import _fix_declared_constants


def test_fixed_constants_reduce_bounds():
    bounds = {"theta": (0, 1), "a": (0, 10), "b": (0, 10), "c": (0, 10),
              "d": (0, 10), "e": (0, 10), "f": (0, 10)}   # 7 > _MAX_BOX_DIMS
    mech = {"fixed_constants": {"a": 2.0, "b": 3.0, "c": 1.5}}
    nb, ns = _fix_declared_constants(mech, dict(bounds), {})
    assert set(nb) == {"theta", "d", "e", "f"}
    assert ns == {"a": 2.0, "b": 3.0, "c": 1.5}


def test_fixed_constants_absent_field_unchanged():
    bounds = {"x": (0, 1), "y": (0, 1)}
    nb, ns = _fix_declared_constants({}, dict(bounds), {"z": 9.0})
    assert nb == bounds
    assert ns == {"z": 9.0}


def test_fixed_constants_non_numeric_skipped():
    bounds = {"x": (0, 1), "y": (0, 1), "z": (0, 1)}
    mech = {"fixed_constants": {"x": "lots", "y": None, "z": 4}}
    nb, ns = _fix_declared_constants(mech, dict(bounds), {})
    assert set(nb) == {"x", "y"}          # only z pinned
    assert ns == {"z": 4.0}
