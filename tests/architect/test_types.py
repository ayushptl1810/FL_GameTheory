from architect.types import ProblemSpec, Feedback, ArchitectResult

def test_problemspec_defaults():
    s = ProblemSpec(raw_text="x")
    assert s.failure_modes == [] and s.missing_fields == []

def test_feedback_shape():
    fb = Feedback(kind="counterexample", counterexample={"type": "a=1"}, conditions=[], hint="")
    assert fb.kind == "counterexample"

def test_result_shape():
    r = ArchitectResult(status="FAILED", mechanism_latex="", mechanism_dict={},
                        certificate=[], mode="Synthesis", iterations=3,
                        solver_calls=2, wall_clock=1.0, transcript=[])
    assert r.status == "FAILED"
