"""Tests for shared verdict/LaTeX-cleaning helpers in tracks/__init__.py."""

from tracks import finalize_verdict, strip_redundant_outer_parens


class TestFinalizeVerdict:
    def test_all_ok_entry_specific_is_verified(self):
        assert finalize_verdict(all_ok=True, has_cex=False, entry_specific=True) == "VERIFIED"

    def test_all_ok_not_entry_specific_is_downgraded_to_template(self):
        assert finalize_verdict(all_ok=True, has_cex=False, entry_specific=False) == "VERIFIED_TEMPLATE"

    def test_counterexample_beats_entry_specific(self):
        assert finalize_verdict(all_ok=False, has_cex=True, entry_specific=True) == "COUNTEREXAMPLE"
        assert finalize_verdict(all_ok=False, has_cex=True, entry_specific=False) == "COUNTEREXAMPLE"

    def test_neither_ok_nor_cex_is_unknown(self):
        assert finalize_verdict(all_ok=False, has_cex=False, entry_specific=True) == "UNKNOWN"
        assert finalize_verdict(all_ok=False, has_cex=False, entry_specific=False) == "UNKNOWN"


class TestStripRedundantOuterParens:
    def test_strips_matched_outer_wrap(self):
        assert strip_redundant_outer_parens("(U_i - U_j)") == "U_i - U_j"

    def test_leaves_unwrapped_string_untouched(self):
        assert strip_redundant_outer_parens("U_i - U_j") == "U_i - U_j"

    def test_does_not_corrupt_trailing_function_call(self):
        # Regression test: a naive `s.strip("()")` truncates the closing
        # paren of `\ln(...)`, turning valid LaTeX into an unbalanced,
        # silently-wrong expression.
        s = r"r_i \ln(1/\theta_i)"
        assert strip_redundant_outer_parens(s) == s

    def test_does_not_strip_when_close_precedes_end(self):
        # "(a)(b)" -- the first ')' closes before the string ends, so this
        # is not a single redundant wrapping pair.
        s = "(a)(b)"
        assert strip_redundant_outer_parens(s) == s

    def test_handles_nested_parens(self):
        assert strip_redundant_outer_parens("(a(b)c)") == "a(b)c"
