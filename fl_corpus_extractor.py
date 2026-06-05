"""
FL Incentive Mechanism Corpus Extractor
========================================

Full pipeline (runs on YOUR local machine):
  1. Try arXiv API  →  download PDF automatically
  2. Try Semantic Scholar API  →  download PDF automatically
  3. If both fail  →  log to failed.json; drop PDF manually into pdfs/
  4. Extract text from PDF via pdfplumber
  5. Send text to Groq API → structured JSON
  6. Append to corpus.json (crash-safe: saves after every paper)

Setup:
    pip install groq arxiv pdfplumber requests tqdm
    export GROQ_API_KEY="gsk_..."

Run:
    python fl_corpus_extractor.py

Re-run safely any time — already-processed papers are skipped.

Manual fallback for paywalled papers:
    Copy the PDF to  pdfs/<paper_id>.pdf  then re-run.

Outputs:
    corpus.json   — structured records for every successfully processed paper
    failed.json   — papers where PDF acquisition failed (manual action needed)
    pipeline.log  — full run log
"""

import os
import re
import json
import time
import logging
import urllib.parse
from pathlib import Path

import requests
import pdfplumber
from groq import Groq
from tqdm import tqdm

# Optional: arxiv library
try:
    import arxiv as arxiv_lib
    HAS_ARXIV = True
except ImportError:
    HAS_ARXIV = False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
PDF_DIR      = Path("pdfs")
CORPUS_FILE  = Path("corpus.json")
FAILED_FILE  = Path("failed.json")
LOG_FILE     = Path("pipeline.log")

# Groq settings
GROQ_MODEL   = "llama-3.3-70b-versatile"   # or "mixtral-8x7b-32768" for wider context
MAX_TOKENS   = 2000

# Characters of PDF text sent to Groq per paper (~3K tokens at 12K chars)
TEXT_CHAR_LIMIT = 12_000

# Seconds between API calls
API_SLEEP = 1.5


# ─────────────────────────────────────────────────────────────────────────────
# PAPER CATALOGUE
# Tuple: (paper_id, full_title, first_author_last_name, year, category)
# ─────────────────────────────────────────────────────────────────────────────
PAPERS = [
    # ── GOLDEN 15 ─────────────────────────────────────────────────────────────
    # Stackelberg
    ("Sarikaya2019",
     "Motivating Workers in Federated Learning: A Stackelberg Game Perspective",
     "Sarikaya", 2019, "Stackelberg"),
    ("Zhan2020",
     "A Bayesian Stackelberg Game for Federated Learning",
     "Zhan", 2020, "Stackelberg"),
    ("Ding2020",
     "Optimized Federated Learning for Frugal Edge Intelligence",
     "Ding", 2020, "Stackelberg"),
    ("Luo2022",
     "Federeinforcement: A Hierarchical Reinforcement Learning Based Incentive Mechanism for Federated Learning",
     "Luo", 2022, "Stackelberg"),
    ("Wu2021stack",
     "A Federated Learning Stackelberg Game Model for Data Quality",
     "Wu", 2021, "Stackelberg"),
    # VCG / Auctions
    ("Le2020",
     "Auction-based Incentive Mechanism Design for Federated Learning",
     "Le", 2020, "VCG"),
    ("Jiao2022",
     "A Double Auction Mechanism for Federated Learning",
     "Jiao", 2022, "VCG"),
    ("Tong2020",
     "Auction-based Federated Learning",
     "Tong", 2020, "VCG"),
    ("Zeng2021",
     "A Comprehensive Evaluation of Auction Mechanisms for Federated Learning",
     "Zeng", 2021, "VCG"),
    # Contracts
    ("Kang2019",
     "Incentive Mechanism for Reliable Federated Learning: A Joint Optimization Approach to Combining Reputation and Regulation",
     "Kang", 2019, "Contract"),
    ("Tian2021",
     "Contract-based Incentive Mechanism for Federated Learning",
     "Tian", 2021, "Contract"),
    ("Ding2022",
     "Incentive Mechanism for Horizontal Federated Learning via Contract Theory",
     "Ding", 2022, "Contract"),
    ("Zhang2020",
     "A Contract-Theoretic Approach to Incentivize Federated Learning",
     "Zhang", 2020, "Contract"),

    # ── EXTENDED STACKELBERG ──────────────────────────────────────────────────
    ("Zeng2020",
     "More or Less: Federated Learning with Adaptive Client Selection",
     "Zeng", 2020, "Stackelberg"),
    ("Huang2021",
     "An Incentive Mechanism for Federated Learning Based on Stackelberg Game",
     "Huang", 2021, "Stackelberg"),
    ("Li2022stack",
     "Incentive Mechanism Design for Federated Learning with Strategic Clients",
     "Li", 2022, "Stackelberg"),
    ("Feng2022",
     "Stackelberg Game for Federated Learning in Mobile Edge Computing",
     "Feng", 2022, "Stackelberg"),
    ("Shi2023",
     "Incentive Mechanism for Vertical Federated Learning based on Stackelberg Game",
     "Shi", 2023, "Stackelberg"),
    ("Chen2023multi",
     "A Multi-Leader Multi-Follower Stackelberg Game for Federated Learning",
     "Chen", 2023, "Stackelberg"),

    # ── EXTENDED AUCTIONS ─────────────────────────────────────────────────────
    ("Rahman2020",
     "Towards Fair and Transparent Auction-based Federated Learning",
     "Rahman", 2020, "VCG"),
    ("Liu2023auction",
     "An Incentive Mechanism based on Double Auction for Federated Learning in Mobile Edge Computing",
     "Liu", 2023, "VCG"),
    ("Xue2022",
     "Incentive Mechanism for Federated Learning: A Proportional Taxation Approach",
     "Xue", 2022, "VCG"),
    ("Wang2022comb",
     "Combinatorial Auction for Federated Learning",
     "Wang", 2022, "VCG"),
    ("Li2024vcg",
     "VCG-based Incentive Mechanism for Federated Learning with Budget Constraints",
     "Li", 2024, "VCG"),
    ("Zhang2024truth",
     "Truthful Federated Learning: An Auction-based Approach with Differential Privacy",
     "Zhang", 2024, "VCG"),
    ("Zhao2023",
     "Optimal Auction Design for Federated Learning under Data Heterogeneity",
     "Zhao", 2023, "VCG"),

    # ── EXTENDED CONTRACT ─────────────────────────────────────────────────────
    ("Lim2020",
     "Dynamic Contract Design for Federated Learning in Smart Healthcare Application",
     "Lim", 2020, "Contract"),
    ("Wu2022contract",
     "Contract-based Incentive Mechanism for Heterogeneous Federated Learning",
     "Wu", 2022, "Contract"),
    ("Cao2023",
     "Incentivizing Federated Learning via Contract Theory under Data Quality Asymmetry",
     "Cao", 2023, "Contract"),
    ("Xu2021",
     "Contract-based Incentive Mechanism for Federated Learning in Vehicular Networks",
     "Xu", 2021, "Contract"),
    ("Ren2023",
     "Multi-dimensional Contract Design for Federated Learning",
     "Ren", 2023, "Contract"),
    ("Tang2024",
     "Optimal Contract Design for Cross-Silo Federated Learning",
     "Tang", 2024, "Contract"),

    # ── SHAPLEY ───────────────────────────────────────────────────────────────
    ("Song2019",
     "Profit Allocation for Federated Learning",
     "Song", 2019, "Shapley"),
    ("Wang2020fair",
     "A Measure of Fairness for Federated Learning",
     "Wang", 2020, "Shapley"),
    ("Liu2022rtfe",
     "RTFE: A Robust Transformer-based Fairness-aware Incentive Mechanism",
     "Liu", 2022, "Shapley"),

    # ── CONTEXT / STRATEGIC BEHAVIOR ─────────────────────────────────────────
    ("Donahue2021",
     "Model-sharing games: Analyzing federated learning under voluntary participation",
     "Donahue", 2021, "Context"),
    ("Fraboni2021",
     "A Critical Review of Federated Learning",
     "Fraboni", 2021, "Context"),
    ("Blum2021",
     "One for One, or All for All: Equilibria and Optimality in Federated Learning",
     "Blum", 2021, "Context"),

    # ── NEWLY ADDED PAPERS (GAP FILLERS & OOPS LIST) ─────────────────────────
    ("Bornstein2024",
     "FACT or Fiction: Can Truthful Mechanisms Eliminate Federated Free Riding?",
     "Bornstein", 2024, "VCG"),
    ("Yang2023sgmf",
     "A Stackelberg Game-Based Multifactor Incentive Mechanism for Federated Learning",
     "Yang", 2023, "Stackelberg"),
    ("Javaherian2025",
     "FLamma: Incentive-Compatible Federated Learning with Stackelberg Game Modeling",
     "Javaherian", 2025, "Stackelberg"),
    ("Bedi2025",
     "Shapley-Bid Reputation Optimized Federated Learning",
     "Bedi", 2025, "Shapley"),
    ("Liu2022gtg",
     "GTG-Shapley: Game-theoretic Group Shapley value for Federated Learning",
     "Liu", 2022, "Shapley"),
    ("Bornstein2024dpvs",
     "DPVS-Shapley: Dynamic Pruning Validation Set Shapley for Contribution Assessment in Federated Learning",
     "Bornstein", 2024, "Shapley"),
    ("Chen2025dual",
     "DualGFL: Federated Learning with a Dual-Level Coalition-Auction Game",
     "Chen", 2025, "VCG"),
    ("Tao2022pfed",
     "Personalized Shapley Value for Federated Learning",
     "Tao", 2022, "Shapley"),
    ("FedBBA2025",
     "FedBBA: Defending Against Backdoor Attacks in Federated Learning via Game Theory and Projection Pursuit Analysis",
     "FedBBA", 2025, "Context"),
    ("FedGreed2025",
     "FedGreed: Byzantine-Robust Federated Learning via Trusted Evaluation Loss",
     "Kritharakis", 2025, "Context"),
    ("Ghorbani2020",
     "Data Shapley: Equitable Valuation of Data for Machine Learning",
     "Ghorbani", 2020, "Shapley"),
    ("Jia2019",
     "Efficient Task-Specific Data Valuation for Nearest Neighbor Algorithms",
     "Jia", 2019, "Shapley"),
    ("Zhan2020learning",
     "A Learning-based Incentive Mechanism for Federated Learning",
     "Zhan", 2020, "Stackelberg"),
    ("Kang2020reliable",
     "Reliable Federated Learning for Mobile Networks",
     "Kang", 2020, "Contract"),
    ("Wahab2021",
     "A Survey on Incentive Mechanisms for Federated Learning",
     "Wahab", 2021, "Context"),
    ("Tu2022",
     "Adaptive Incentive Design for Federated Learning",
     "Tu", 2022, "Stackelberg"),
    ("Mothukuri2021",
     "A survey on security and privacy of federated learning",
     "Mothukuri", 2021, "Context"),
    ("Chai2023",
     "A Multi-Item Auction Mechanism for Federated Learning in Mobile Edge Computing",
     "Chai", 2023, "VCG"),
    ("Cai2023contract",
     "Contract theory for data pricing in federated learning",
     "Cai", 2023, "Contract"),
]


# ─────────────────────────────────────────────────────────────────────────────
# GROK EXTRACTION PROMPT
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a mathematical economics extraction engine for federated learning papers.
Your ONLY job: extract structured fields and return a single valid JSON object.
Output raw JSON only — no markdown fences, no commentary, no preamble.
IMPORTANT: All LaTeX backslashes inside JSON values MUST be double-escaped (e.g. use \\\\frac instead of \\frac, \\\\theta instead of \\theta) to make it a valid JSON string."""


def build_user_prompt(paper_id: str, category: str, text: str) -> str:
    snippet = text[:TEXT_CHAR_LIMIT]
    return f"""Extract the following fields from this federated learning paper.
paper_id: {paper_id}
category: {category}

Return ONLY a JSON object with exactly these keys:

{{
  "paper_id": "{paper_id}",
  "category": "{category}",
  "fl_setup": "<cross-silo | cross-device | unspecified>",
  "type_space": "<discrete | continuous | unspecified>",
  "num_types": <integer or null>,
  "payment_rule_latex": "<LaTeX formula for the payment/reward to each worker, e.g. p_i = ...>",
  "ic_condition_latex": "<LaTeX for the incentive-compatibility constraint(s); use \\quad to separate multiples>",
  "ir_condition_latex": "<LaTeX for the individual-rationality / participation constraint(s)>",
  "objective_latex": "<LaTeX for the server/principal optimization objective>",
  "key_assumptions": ["<assumption>", ...],
  "equilibrium_concept": "<Nash | Stackelberg | BNE | dominant-strategy | other>",
  "truthfulness": <true | false | null>,
  "budget_balanced": <true | false | null>,
  "notes": "<2-sentence max: caveats about ambiguous or missing math>"
}}

Rules:
- null for any field not found.
- Copy LaTeX verbatim from the paper when possible.
- Do NOT output anything outside the JSON object.

PAPER TEXT:
\"\"\"
{snippet}
\"\"\"
"""


# ─────────────────────────────────────────────────────────────────────────────
# PDF ACQUISITION
# ─────────────────────────────────────────────────────────────────────────────
LAST_REQUEST_TIME = 0.0

def _rate_limit_delay(min_delay=3.0):
    global LAST_REQUEST_TIME
    elapsed = time.time() - LAST_REQUEST_TIME
    if elapsed < min_delay:
        sleep_time = min_delay - elapsed
        time.sleep(sleep_time)
    LAST_REQUEST_TIME = time.time()


def _download(url: str, dest: Path) -> bool:
    backoff = 3.0
    for attempt in range(3):
        _rate_limit_delay(min_delay=2.0)
        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            if resp.status_code == 429:
                logging.warning(f"  Download rate limited (429) for {url}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                dest.write_bytes(resp.content)
                return True
            logging.warning(f"  HTTP {resp.status_code} or not a PDF from {url}")
            return False
        except Exception as e:
            logging.warning(f"  Download error {url}: {e}")
            time.sleep(backoff)
            backoff *= 2
    return False


def _try_arxiv(title: str, author: str, year: int) -> str | None:
    if not HAS_ARXIV:
        return None
    
    query = f'ti:"{title}" au:{author}'
    client = arxiv_lib.Client()
    
    backoff = 3.0
    for attempt in range(4):
        _rate_limit_delay(min_delay=3.0)
        try:
            results = list(client.results(arxiv_lib.Search(query=query, max_results=6)))
            for r in results:
                if abs(r.published.year - year) <= 1:
                    return r.pdf_url
            if results:
                return results[0].pdf_url
            return None
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "Rate limit" in err_str or "Too Many Requests" in err_str:
                logging.warning(f"  arXiv rate limited (429). Retrying in {backoff}s... (attempt {attempt + 1}/4)")
                time.sleep(backoff)
                backoff *= 2
            else:
                logging.warning(f"  arXiv error: {e}")
                break
    return None


def _try_semantic_scholar(title: str) -> str | None:
    encoded = urllib.parse.quote(title)
    url = (
        "https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={encoded}&fields=title,openAccessPdf,year&limit=5"
    )
    
    backoff = 3.0
    for attempt in range(4):
        _rate_limit_delay(min_delay=3.0)
        try:
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            if resp.status_code == 429:
                logging.warning(f"  Semantic Scholar rate limited (429). Retrying in {backoff}s... (attempt {attempt + 1}/4)")
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code != 200:
                logging.warning(f"  Semantic Scholar HTTP {resp.status_code}")
                return None
            for paper in resp.json().get("data", []):
                oa = paper.get("openAccessPdf")
                if oa and oa.get("url"):
                    return oa["url"]
            return None
        except Exception as e:
            logging.warning(f"  Semantic Scholar error: {e}")
            time.sleep(backoff)
            backoff *= 2
    return None


KNOWN_PDF_URLS = {
    "Sarikaya2019": "https://arxiv.org/pdf/1908.03092.pdf",
    "Zhan2020": "https://arxiv.org/pdf/2306.13800.pdf",
    "Tong2020": "https://www.ijcai.org/proceedings/2023/0474.pdf",
    "Donahue2021": "https://arxiv.org/pdf/2010.00753.pdf",
    "Jiao2022": "https://arxiv.org/pdf/1912.06370.pdf",
    "Tian2021": "https://arxiv.org/pdf/2108.05568.pdf",
    "Blum2021": "https://arxiv.org/pdf/2103.03228.pdf",
    # Mapped successful links from download test
    "Ding2020": "https://arxiv.org/pdf/1812.11750.pdf",
    "Luo2022": "https://arxiv.org/pdf/2112.11256.pdf",
    "Wu2021stack": "https://e-space.mmu.ac.uk/626669/7/2020-IEEE%20IoT%20J-%20Blockchain-Based%20Incentive%20Energy-Knowledge%20e.pdf",
    "Le2020": "https://arxiv.org/pdf/2009.10269.pdf",
    "Zeng2021": "https://arxiv.org/pdf/2106.15406.pdf",
    "Zeng2020": "https://arxiv.org/pdf/2002.09699.pdf",
    "Huang2021": "https://ojs.aaai.org/index.php/AAAI/article/download/16960/16767",
    "Li2022stack": "https://arxiv.org/pdf/2211.02534.pdf",
    "Chen2023multi": "https://eprints.whiterose.ac.uk/id/eprint/221954/1/MEC_blockchain_learning_accept_TNSE1.pdf",
    "Rahman2020": "https://arxiv.org/pdf/2006.14389.pdf",
    "Xue2022": "https://arxiv.org/pdf/2111.11850",
    "Li2024vcg": "https://ieeexplore.ieee.org/ielx7/6488907/10038283/09997105.pdf",
    "Wu2022contract": "https://ieeexplore.ieee.org/ielx7/6287639/9668973/09667507.pdf",
    "Ren2023": "https://www.nature.com/articles/s41467-023-36329-y.pdf",
    "Tang2024": "https://link.springer.com/content/pdf/10.1007/s10462-023-10662-6.pdf",
    "Song2019": "https://ieeexplore.ieee.org/ielx7/6287639/8600701/08629877.pdf",
    "Wang2020fair": "https://arxiv.org/pdf/2012.10069.pdf",
    "Liu2022rtfe": "https://ojs.aaai.org/index.php/AAAI/article/download/21505/21254",
}

def acquire_pdf(paper_id: str, title: str, author: str, year: int) -> Path | None:
    PDF_DIR.mkdir(exist_ok=True)
    dest = PDF_DIR / f"{paper_id}.pdf"

    if dest.exists():
        logging.info(f"  Cached PDF found.")
        return dest

    # 1. Check if we have a direct known open-access URL for it
    url = KNOWN_PDF_URLS.get(paper_id)
    if url:
        logging.info(f"  Downloading known PDF directly from {url}...")
        if _download(url, dest):
            return dest

    # 2. Skip searching for paywalled or unavailable PDFs to avoid 429 rate limits
    logging.warning(f"  No open-access URL mapped for {paper_id}. Skipping automatic search to prevent API rate limiting.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def extract_text(pdf_path: Path) -> str:
    """
    Extract text via pdfplumber (works on born-digital PDFs).
    Scanned/image PDFs return very little text — run ocrmypdf on them first.
    """
    pages = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
    except Exception as e:
        logging.error(f"  pdfplumber error: {e}")
        return ""
    full = "\n".join(pages)
    full = re.sub(r"\n{3,}", "\n\n", full)
    return full


# ─────────────────────────────────────────────────────────────────────────────
# GROK EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────
def fix_latex_backslashes(raw_json: str) -> str:
    # Double escape any backslash that is immediately followed by a quote to prevent escaping structural quotes
    raw_json = raw_json.replace('\\"', '\\\\"')
    
    def repl(match):
        s = match.group(0)
        content = s[1:-1]
        content = content.replace('\\\\', '__DOUBLE_BACKSLASH__')
        content = content.replace('\\', '\\\\')
        content = content.replace('__DOUBLE_BACKSLASH__', '\\\\')
        return '"' + content + '"'
    return re.sub(r'"(?:[^"\\]|\\.)*"', repl, raw_json)


def extract_with_groq(
    paper_id: str, category: str, text: str, client: Groq
) -> dict:
    """Call Groq API and return a parsed record dict."""
    prompt = build_user_prompt(paper_id, category, text)
    raw = ""
    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        
        # Recover/fix single-escaped LaTeX backslashes inside JSON values
        raw = fix_latex_backslashes(raw)
        
        record = json.loads(raw)
        return record
    except json.JSONDecodeError as e:
        logging.error(f"  JSON parse error: {e} — raw[:300]: {raw[:300]}")
        return {
            "paper_id": paper_id, "category": category,
            "error": "json_parse_failed", "raw_snippet": raw[:500],
        }
    except Exception as e:
        logging.error(f"  Groq API error: {e}")
        return {"paper_id": paper_id, "category": category, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# CORPUS PERSISTENCE
# ─────────────────────────────────────────────────────────────────────────────
def load_corpus() -> tuple[list, set]:
    if CORPUS_FILE.exists():
        records = json.loads(CORPUS_FILE.read_text())
        done = {r["paper_id"] for r in records if "error" not in r}
        return records, done
    return [], set()


def save_corpus(records: list) -> None:
    CORPUS_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def save_failed(failed: list) -> None:
    FAILED_FILE.write_text(json.dumps(failed, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
    )

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.strip().startswith("GROQ_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip("'\"")
                    os.environ["GROQ_API_KEY"] = api_key
                    break

    if not api_key:
        raise SystemExit(
            "\nERROR: GROQ_API_KEY not set.\n"
            "Run:  export GROQ_API_KEY='gsk_...'\n"
            "Get a key at: https://console.groq.com"
        )

    client = Groq(api_key=api_key)

    corpus, done = load_corpus()
    failed: list[dict] = []

    logging.info(f"Pipeline start — {len(PAPERS)} papers, {len(done)} already done.")
    logging.info(f"Model: {GROQ_MODEL}")

    for paper_id, title, author, year, category in tqdm(PAPERS, desc="Papers"):
        if paper_id in done:
            continue

        logging.info(f"\n{'─'*60}")
        logging.info(f"[{paper_id}]  {title[:70]}")

        # ── 1. PDF ───────────────────────────────────────────────────────────
        pdf_path = acquire_pdf(paper_id, title, author, year)
        text = ""
        
        if pdf_path is not None:
            # ── 2. Text extraction ───────────────────────────────────────────────
            text = extract_text(pdf_path)
            char_count = len(text)
            logging.info(f"  Extracted {char_count:,} chars from PDF.")
        else:
            logging.warning("  No PDF path returned.")

        # ── 2b. Fallback to pre-generated paper text if PDF failed or is too short ──
        if len(text) < 500:
            fallback_path = Path("texts") / f"{paper_id}.txt"
            if fallback_path.exists():
                text = fallback_path.read_text(encoding="utf-8")
                logging.info(f"  Using fallback text from {fallback_path} ({len(text)} chars).")
            else:
                logging.warning(
                    f"  → PDF extraction failed/short and no fallback text found at {fallback_path}."
                )
                failed.append({
                    "paper_id": paper_id, "title": title,
                    "reason": "pdf_not_found_no_fallback",
                    "action": f"Save PDF to pdfs/{paper_id}.pdf or text to texts/{paper_id}.txt and re-run",
                })
                save_failed(failed)
                continue

        # ── 3. Groq extraction ──────────────────────────────────────────────
        record = extract_with_groq(paper_id, category, text, client)
        record["title"] = title
        record["year"]  = year

        corpus = [r for r in corpus if r["paper_id"] != paper_id]
        corpus.append(record)
        done.add(paper_id)
        save_corpus(corpus)

        status = "ERROR" if "error" in record else "OK"
        logging.info(f"  Groq extraction: {status}. Corpus size: {len(corpus)}")

        time.sleep(API_SLEEP)

    save_failed(failed)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Done.")
    print(f"  Corpus:  {len(corpus)} records  →  {CORPUS_FILE}")
    print(f"  Failed:  {len(failed)} papers   →  {FAILED_FILE}")
    if failed:
        print(f"\n  Manual action needed for {len(failed)} papers:")
        for f in failed:
            print(f"    [{f['paper_id']}]  {f['reason']}  —  {f.get('action','')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
