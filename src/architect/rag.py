# src/architect/rag.py
from __future__ import annotations
import json
from dataclasses import dataclass
import numpy as np
from architect.types import ProblemSpec

def _default_embed(texts):
    try:
        from sentence_transformers import SentenceTransformer
        _m = _default_embed.__dict__.setdefault(
            "m", SentenceTransformer("all-MiniLM-L6-v2"))
        return np.asarray(_m.encode(list(texts)))
    except Exception:  # noqa: BLE001
        # ponytail: hashing fallback; swap for a real embedder before eval
        out = []
        for t in texts:
            v = np.zeros(384)
            for i, ch in enumerate(t.lower()):
                v[(ord(ch) * 131 + i) % 384] += 1.0
            out.append(v)
        return np.asarray(out)

def _norm(a):
    n = np.linalg.norm(a, axis=1, keepdims=True)
    return a / np.clip(n, 1e-12, None)

@dataclass
class Index:
    entries: list
    vectors: np.ndarray
    embed: object

def build_index(corpus_path: str = "corpus.json", *, embed=None) -> Index:
    embed = embed or _default_embed
    entries = json.load(open(corpus_path))
    texts = [f"{e.get('fl_setup','')} {e.get('title','')}" for e in entries]
    return Index(entries, _norm(embed(texts)), embed)

def _rank(spec, index):
    q = _norm(index.embed([spec.raw_text]))[0]
    sims = index.vectors @ q
    order = sorted(range(len(sims)),
                   key=lambda i: (-round(float(sims[i]), 3),
                                  index.entries[i].get("z3_validated") is not True))
    return order, sims

def retrieve(spec: ProblemSpec, k: int = 5, *, index: Index) -> list:
    order, _ = _rank(spec, index)
    return [index.entries[i] for i in order[:k]]

def nearest_distance(spec: ProblemSpec, index: Index) -> float:
    order, sims = _rank(spec, index)
    return 1.0 - float(sims[order[0]])
