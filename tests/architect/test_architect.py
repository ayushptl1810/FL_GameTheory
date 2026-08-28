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
