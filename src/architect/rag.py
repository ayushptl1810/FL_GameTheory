# src/architect/rag.py
from __future__ import annotations
import json
import os
import urllib.request
from dataclasses import dataclass
import numpy as np
from architect.types import ProblemSpec

# Remote (hosted) embedding models, tried in order. Nothing runs locally unless
# every remote path is unavailable.
#   ARCHITECT_EMBED_PROVIDER  nvidia | huggingface | local | hashing  (force one)
#   ARCHITECT_EMBED_MODEL     override the model id for the chosen provider
_NVIDIA_EMBED_DEFAULT = "nvidia/nv-embedqa-e5-v5"
_HF_EMBED_DEFAULT = "BAAI/bge-small-en-v1.5"


def _embed_nvidia(texts):
    from openai import OpenAI  # same SDK/endpoint as llm.py
    key = os.environ.get("ARCHITECT_LLM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if not key:
        raise RuntimeError("no NVIDIA_API_KEY for embeddings")
    model = os.environ.get("ARCHITECT_EMBED_MODEL", _NVIDIA_EMBED_DEFAULT)
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
    try:
        resp = client.embeddings.create(
            model=model, input=list(texts),
            extra_body={"input_type": "passage", "truncate": "END"})
    except Exception:  # some NIM embed models reject extra_body / large batches
        resp = client.embeddings.create(model=model, input=list(texts))
    return np.asarray([d.embedding for d in resp.data], dtype=float)


def _embed_huggingface(texts):
    token = (os.environ.get("HF_TOKEN")
             or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
             or os.environ.get("HUGGING_FACE_HUB_TOKEN"))
    if not token:
        raise RuntimeError("no HF_TOKEN for embeddings")
    model = os.environ.get("ARCHITECT_EMBED_MODEL", _HF_EMBED_DEFAULT)
    url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
    body = json.dumps({"inputs": list(texts),
                       "options": {"wait_for_model": True}}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        vecs = json.loads(r.read())
    return np.asarray(vecs, dtype=float)


def _embed_local(texts):
    from sentence_transformers import SentenceTransformer
    model = os.environ.get("ARCHITECT_EMBED_MODEL", "all-MiniLM-L6-v2")
    _m = _embed_local.__dict__.setdefault("m", SentenceTransformer(model))
    return np.asarray(_m.encode(list(texts)))


def _embed_hashing(texts):
    # last-resort deterministic bag-of-chars; correctness holds, quality does not
    out = []
    for t in texts:
        v = np.zeros(384)
        for i, ch in enumerate(t.lower()):
            v[(ord(ch) * 131 + i) % 384] += 1.0
        out.append(v)
    return np.asarray(out)


_EMBED_CHAIN = [
    ("nvidia", _embed_nvidia),
    ("huggingface", _embed_huggingface),
    ("local", _embed_local),
    ("hashing", _embed_hashing),
]


def _default_embed(texts):
    forced = os.environ.get("ARCHITECT_EMBED_PROVIDER")
    chain = ([(n, f) for n, f in _EMBED_CHAIN if n == forced] if forced
             else _EMBED_CHAIN)
    last = None
    for _name, fn in chain:
        try:
            return fn(texts)
        except Exception as exc:  # noqa: BLE001
            last = exc
    raise RuntimeError(f"all embedding backends failed; last error: {last}")

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
