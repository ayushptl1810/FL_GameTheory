# tests/architect/test_formalize_smoke.py
import os
import pytest
from architect.formalize import run_batch

SMOKE_IDS = ["Cong2020vcg", "2102_03401", "1811_12082",
             "Kang2019contract_mobile", "Deng2020fmore_auction"]


@pytest.mark.llm
@pytest.mark.skipif(
    os.environ.get("ARCHITECT_LLM_SMOKE") != "1"
    or not (os.environ.get("ARCHITECT_LLM_API_KEY")
            or os.environ.get("NVIDIA_API_KEY")
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENAI_API_KEY")),
    reason="set ARCHITECT_LLM_SMOKE=1 and an API key to run the LLM smoke test",
)
def test_formalize_smoke_dry_run(tmp_path):
    import shutil
    cp = str(tmp_path / "corpus.json")
    shutil.copy("corpus.json", cp)
    out = run_batch(cp, ids=SMOKE_IDS, dry_run=True)
    assert out["summary"]["selected"] == len(SMOKE_IDS)
    assert os.path.isfile(out["report_path"])
    print("SMOKE SUMMARY:", out["summary"])
