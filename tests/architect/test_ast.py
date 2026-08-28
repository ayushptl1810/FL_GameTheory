import pytest
from architect.ast import Const, Sym, Sum, Prod, Pow, Func, IndexedFamily, validate_ast, ASTSchemaError


def test_valid_ast_passes():
    node = Sum([Prod([Const(2), Pow(Sym("theta"), 2)]), Const(1)])
    validate_ast(node)  # no raise


def test_non_integer_pow_exp_rejected():
    with pytest.raises(ASTSchemaError):
        validate_ast(Pow(Sym("x"), 2.5))


def test_unknown_func_rejected():
    with pytest.raises(ASTSchemaError):
        validate_ast(Func("sqrt", Sym("x")))


def test_empty_sum_rejected():
    with pytest.raises(ASTSchemaError):
        validate_ast(Sum([]))


def test_indexed_family_needs_nonempty_over():
    with pytest.raises(ASTSchemaError):
        validate_ast(IndexedFamily("R", "i", []))
