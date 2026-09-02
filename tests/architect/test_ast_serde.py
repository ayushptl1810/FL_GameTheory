import pytest
from architect.ast import (
    Const, Sym, Sum, Prod, Pow, Func, IndexedFamily,
    AllocHighest, AllocTopK, AllocWeightedWelfare, Mechanism,
    to_dict, from_dict, ASTSchemaError,
)


def _sample_mechanism():
    return Mechanism(
        category="Contract",
        utility=Sum([Prod([Sym("theta"), Sym("R")]), Func("ln", Sym("P"))]),
        payment=Sym("P"),
        ic=Sum([Sym("a"), Const(-1.0)]),
        ir=Sym("a"),
        params={"num_types": 3},
        type_space=[0.2, 0.5, 0.9],
        allocation=None,
        meta={"num_types": 3},
    )


def test_roundtrip_full_mechanism():
    m = _sample_mechanism()
    assert from_dict(to_dict(m)) == m


def test_roundtrip_every_node_type():
    m = Mechanism(
        category="VCG",
        utility=Pow(Sym("x"), 2),
        payment=IndexedFamily("p", "i", ["a", "b"]),
        ic=Const(0.0),
        ir=Const(0.0),
        allocation=AllocWeightedWelfare(["1", "2"]),
    )
    assert from_dict(to_dict(m)) == m
    m2 = Mechanism(category="VCG", utility=Const(0.0), payment=Const(0.0),
                   ic=Const(0.0), ir=Const(0.0), allocation=AllocTopK(3))
    assert from_dict(to_dict(m2)) == m2
    m3 = Mechanism(category="VCG", utility=Const(0.0), payment=Const(0.0),
                   ic=Const(0.0), ir=Const(0.0), allocation=AllocHighest())
    assert from_dict(to_dict(m3)) == m3


def test_to_dict_is_json_safe():
    import json
    d = to_dict(_sample_mechanism())
    assert json.loads(json.dumps(d)) == d


def test_from_dict_unknown_tag_raises():
    with pytest.raises(ASTSchemaError):
        from_dict({"t": "Bogus", "value": 1})


def test_from_dict_validates_mechanism_subtrees():
    bad = {
        "t": "Mechanism", "category": "Contract",
        "utility": {"t": "Sum", "terms": []},  # empty Sum -> validate_ast raises
        "payment": {"t": "Const", "value": 0.0},
        "ic": {"t": "Const", "value": 0.0},
        "ir": {"t": "Const", "value": 0.0},
        "params": {}, "type_space": [], "allocation": None, "meta": {},
    }
    with pytest.raises(ASTSchemaError):
        from_dict(bad)
