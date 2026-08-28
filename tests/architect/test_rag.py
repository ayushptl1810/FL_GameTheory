# tests/architect/test_rag.py
import numpy as np
from architect.types import ProblemSpec
from architect.rag import build_index, retrieve, nearest_distance

def _toy_embed(texts):
    out = []
    for t in texts:
        v = np.zeros(8)
        for ch in t.lower():
            v[ord(ch) % 8] += 1
        out.append(v)
    return np.array(out)

def test_retrieve_finds_paraphrase(tmp_path):
    corpus = tmp_path / "c.json"
    corpus.write_text('[{"paper_id":"A","title":"auction for clients",'
                      '"fl_setup":"budget limited client selection auction",'
                      '"category":"VCG","z3_validated":true,"mechanism":{}},'
                      '{"paper_id":"B","title":"contract menu",'
                      '"fl_setup":"private type screening contract",'
                      '"category":"Contract","z3_validated":null,"mechanism":{}}]')
    idx = build_index(str(corpus), embed=_toy_embed)
    hits = retrieve(ProblemSpec(raw_text="budget limited client selection auction"),
                    k=1, index=idx)
    assert hits[0]["paper_id"] == "A"

def test_nearest_distance_in_unit_range(tmp_path):
    corpus = tmp_path / "c.json"
    corpus.write_text('[{"paper_id":"A","title":"x","fl_setup":"y",'
                      '"category":"VCG","z3_validated":true,"mechanism":{}}]')
    idx = build_index(str(corpus), embed=_toy_embed)
    d = nearest_distance(ProblemSpec(raw_text="y"), idx)
    assert 0.0 <= d <= 2.0
