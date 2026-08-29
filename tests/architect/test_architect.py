import json
import pytest
from architect.types import ProblemSpec, Feedback
from architect.architect import propose, ast_from_json, ASTDecodeError, SYNTHESIS_PROMPT
from architect.ast import Sum, Unknown

_MENU_JSON = {
  "category": "Contract",
  "utility": {"t":"Sum","terms":[{"t":"Sym","name":"R_i"},
     {"t":"Prod","factors":[{"t":"Const","value":-1},{"t":"Sym","name":"theta_i"},
      {"t":"Sym","name":"e_i"}]}]},
  "payment": {"t":"Sym","name":"R_i"},
  "ic": {"t":"Sum","terms":[{"t":"Sym","name":"theta_i"}]},
  "ir": {"t":"Sym","name":"R_i"},
  "params": {}, "type_space": ["lo","hi"]
}

def test_ast_from_json_roundtrips_node_types():
    node = ast_from_json({"t":"Sum","terms":[{"t":"Unknown","name":"a"}]})
    assert isinstance(node, Sum) and isinstance(node.terms[0], Unknown)

def test_ast_from_json_rejects_unknown_type():
    with pytest.raises(ASTDecodeError):
        ast_from_json({"t":"Bogus"})

def test_propose_builds_mechanism():
    m = propose(ProblemSpec(raw_text="2-type screening"), "Retrieval",
                rag_hits=[{"paper_id":"X","mechanism":{}}], feedback=None,
                complete=lambda s, u, **k: json.dumps(_MENU_JSON))
    assert m.category == "Contract"

def test_synthesis_prompt_demands_unknowns():
    assert "Unknown" in SYNTHESIS_PROMPT


def test_extract_json_strips_fence_and_prose():
    from architect.architect import _extract_json
    assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _extract_json('here you go:\n{"a": 1}\nhope that helps') == '{"a": 1}'
    assert _extract_json('{"a": 1}') == '{"a": 1}'


def test_stackelberg_meta_defaults_filled():
    import json
    from architect.architect import propose
    from architect.types import ProblemSpec
    j = {"category": "Stackelberg",
         "utility": {"t": "Sym", "name": "u"}, "payment": {"t": "Sym", "name": "p_i"},
         "ic": {"t": "Sym", "name": "x"}, "ir": {"t": "Sym", "name": "u"},
         "params": {}, "type_space": ["lo", "hi"]}  # no meta
    m = propose(ProblemSpec(raw_text="x"), "Synthesis", [], None,
                complete=lambda s, u, **k: json.dumps(j))
    assert m.meta["equilibrium_existence"] is True
    assert m.meta["num_types"] == 2
    assert m.meta["follower_decision"] == r"\( e_i \)"


def test_guess_type_variable_from_two_term_ic():
    from architect.ast import Const, Sym, Sum, Prod
    from architect.architect import _guess_type_variable
    own = Sum([Sym("R_i"), Prod([Const(-1), Sym("theta_i"), Sym("e_i")])])
    other = Sum([Sym("R_j"), Prod([Const(-1), Sym("theta_i"), Sym("e_j")])])
    ic = Sum([own, Prod([Const(-1), other])])
    assert _guess_type_variable(ic) == "theta_i"


def test_contract_type_variable_default_from_ic():
    import json
    from architect.architect import propose
    from architect.types import ProblemSpec
    j = {"category": "Contract",
         "utility": {"t": "Sym", "name": "R_i"}, "payment": {"t": "Sym", "name": "R_i"},
         "ic": {"t": "Sum", "terms": [
             {"t": "Sum", "terms": [{"t": "Sym", "name": "R_i"},
              {"t": "Prod", "factors": [{"t": "Const", "value": -1},
               {"t": "Sym", "name": "theta_i"}, {"t": "Sym", "name": "e_i"}]}]},
             {"t": "Prod", "factors": [{"t": "Const", "value": -1},
              {"t": "Sum", "terms": [{"t": "Sym", "name": "R_j"},
               {"t": "Prod", "factors": [{"t": "Const", "value": -1},
                {"t": "Sym", "name": "theta_i"}, {"t": "Sym", "name": "e_j"}]}]}]}]},
         "ir": {"t": "Sym", "name": "R_i"}, "params": {}, "type_space": ["lo", "hi"]}
    m = propose(ProblemSpec(raw_text="x"), "Synthesis", [], None,
                complete=lambda s, u, **k: json.dumps(j))
    assert m.meta["type_variable"] == "theta_i"
