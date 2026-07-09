"""Search arXiv and Semantic Scholar for FL incentive mechanism papers."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV_API = "http://export.arxiv.org/api/query"
S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"

_ATOM = "http://www.w3.org/2005/Atom"
_ARXIV = "http://arxiv.org/schemas/atom"
NS = {"atom": _ATOM, "arxiv": _ARXIV}


def _get(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FL-corpus-preloader/1.0 (research)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (attempt + 1)
                print(f"    [rate-limit] waiting {wait}s...")
                time.sleep(wait)
            elif attempt == retries - 1:
                raise
            else:
                time.sleep(3 * (attempt + 1))
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(3 * (attempt + 1))
    return ""


def _arxiv_id_clean(url_or_id: str) -> str:
    """Strip version suffix: '2309.11722v2' -> '2309.11722'."""
    raw = url_or_id.split("/abs/")[-1].split("/pdf/")[-1]
    return raw.split("v")[0] if "v" in raw and raw.split("v")[-1].isdigit() else raw


def search_arxiv(query: str, max_results: int = 100) -> list[dict]:
    params = urllib.parse.urlencode({
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    xml_text = _get(f"{ARXIV_API}?{params}")
    if not xml_text:
        return []
    if "<!DOCTYPE" in xml_text or "<!ENTITY" in xml_text:
        return []

    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", NS):
        id_el = entry.find("atom:id", NS)
        if id_el is None:
            continue

        arxiv_id = _arxiv_id_clean(id_el.text.strip())
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        pub_el = entry.find("atom:published", NS)

        title = (title_el.text or "").strip().replace("\n", " ")
        abstract = (summary_el.text or "").strip().replace("\n", " ")
        published = (pub_el.text or "")[:10]

        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", pdf_url)
                break

        categories = list({
            c.get("term") for c in entry.findall("atom:category", NS)
            if c.get("term")
        })

        papers.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "published": published,
            "pdf_url": pdf_url,
            "categories": categories,
            "source": "arxiv",
        })

    return papers


def search_semantic_scholar(query: str, max_results: int = 25, min_year: int = 2019) -> list[dict]:
    params = urllib.parse.urlencode({
        "query": query,
        "limit": min(max_results, 100),
        "fields": "title,abstract,year,externalIds,openAccessPdf",
        "year": f"{min_year}-",
    })
    try:
        text = _get(f"{S2_API}?{params}")
        data = json.loads(text)
    except Exception:
        return []

    papers = []
    for p in data.get("data", []):
        ext = (p.get("externalIds") or {})
        arxiv_id = ext.get("ArXiv")
        if not arxiv_id:
            continue

        arxiv_id = _arxiv_id_clean(arxiv_id)
        pdf_info = p.get("openAccessPdf") or {}
        pdf_url = pdf_info.get("url") or f"https://arxiv.org/pdf/{arxiv_id}"

        papers.append({
            "arxiv_id": arxiv_id,
            "title": (p.get("title") or "").strip(),
            "abstract": (p.get("abstract") or "").strip(),
            "published": str(p.get("year") or ""),
            "pdf_url": pdf_url,
            "categories": [],
            "source": "semantic_scholar",
        })

    return papers


def is_relevant(paper: dict, keywords: list[str]) -> bool:
    text = f"{paper['title']} {paper.get('abstract', '')}".lower()
    return any(kw.lower() in text for kw in keywords)


def search_all(config: dict, category: str | None = None) -> list[dict]:
    """Run all configured queries; deduplicate by arXiv ID; filter by relevance.

    Pass category (e.g. 'Shapley') to use targeted queries from category_queries
    in config instead of the default broad query set.
    """
    if category:
        cat_cfg = config.get('category_queries', {}).get(category)
        if not cat_cfg:
            valid = list(config.get('category_queries', {}).keys())
            raise ValueError(f'Unknown category {category!r}. Valid: {valid}')
        config = dict(config)
        config['arxiv'] = dict(config['arxiv'])
        config['arxiv']['queries'] = cat_cfg.get('arxiv', config['arxiv']['queries'])
        config['semantic_scholar'] = dict(config['semantic_scholar'])
        config['semantic_scholar']['queries'] = cat_cfg.get('semantic_scholar', config['semantic_scholar']['queries'])
        config['relevance_keywords'] = cat_cfg.get('relevance_keywords', config['relevance_keywords'])
        print(f'  [category={category}] using targeted queries')
    seen: dict[str, dict] = {}
    relevance_kws: list[str] = config.get("relevance_keywords", [])

    arxiv_cfg = config.get("arxiv", {})
    max_per_query = arxiv_cfg.get("max_results_per_query", 100)

    for query in arxiv_cfg.get("queries", []):
        print(f"  [arXiv] {query[:72]}...")
        try:
            for p in search_arxiv(query, max_results=max_per_query):
                if p["arxiv_id"] not in seen:
                    seen[p["arxiv_id"]] = p
        except Exception as e:
            print(f"         error: {e}")
        time.sleep(3)  # arXiv asks for >=3s between bulk requests

    s2_cfg = config.get("semantic_scholar", {})
    if s2_cfg.get("enabled", True):
        for query in s2_cfg.get("queries", []):
            print(f"  [S2]    {query[:72]}...")
            try:
                for p in search_semantic_scholar(
                    query,
                    max_results=s2_cfg.get("max_results_per_query", 25),
                    min_year=s2_cfg.get("min_year", 2019),
                ):
                    if p["arxiv_id"] not in seen:
                        seen[p["arxiv_id"]] = p
            except Exception as e:
                print(f"         error: {e}")
            time.sleep(1)

    all_papers = list(seen.values())
    relevant = [p for p in all_papers if is_relevant(p, relevance_kws)]
    print(f"\n  {len(all_papers)} unique papers found -> {len(relevant)} pass relevance filter")
    return relevant
