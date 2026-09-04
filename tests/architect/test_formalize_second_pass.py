from architect import formalize


def test_prior_reason_threads_into_user_message():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return "{}"  # invalid AST -> formalize_entry returns None, fine for this assertion
    formalize.formalize_entry(
        {"category": "Stackelberg", "mechanism": {}},
        "paper text",
        complete=fake_complete,
        prior_reason="follower FOC is transcendental with no closed-form root",
    )
    assert "reformulation" in seen["user"]
    assert "transcendental with no closed-form root" in seen["user"]
    assert "provably-slack term" in seen["user"]


def test_prior_reason_ignored_when_concerns_present():
    seen = {}
    def fake_complete(system, user, *, json_mode=False):
        seen["user"] = user
        return "{}"
    formalize.formalize_entry(
        {"category": "Stackelberg", "mechanism": {}}, "t",
        complete=fake_complete,
        concerns=[{"field": "utility", "issue": "real concern"}],
        prior_reason="should not appear",
    )
    assert "real concern" in seen["user"]
    assert "should not appear" not in seen["user"]


def test_run_batch_second_pass_passes_notes_as_prior_reason(tmp_path, monkeypatch):
    import json
    corpus = [{"paper_id": "T1", "category": "Stackelberg",
               "notes": "Batch C: follower IR left null (fail-closed)",
               "mechanism": {}}]
    p = tmp_path / "c.json"
    p.write_text(json.dumps(corpus))
    captured = {}
    def fake_retry(entry, pdf_text, *, complete=None, prior_reason=None):
        captured["prior_reason"] = prior_reason
        return formalize.FormalizeResult("VERIFIED_TEMPLATE", None, [], 0, False, "")
    monkeypatch.setattr(formalize, "formalize_with_retry", fake_retry)
    monkeypatch.setattr(formalize, "pdf_text", lambda *_a, **_k: None)
    formalize.run_batch(str(p), ids="T1", second_pass=True, dry_run=False)
    assert "follower IR left null" in (captured["prior_reason"] or "")
