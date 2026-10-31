# tests the parsing and writing every model generator shares

import ast

import pytest

from models.common import ParseFailed, parse_files, write_model


def test_parse_files_returns_a_tree_per_path_in_path_order():
    trees = parse_files({"b.py": "x = 1\n", "a.py": "", "c/d.py": "def f(): ...\n"})
    assert list(trees) == ["a.py", "b.py", "c/d.py"]
    assert all(isinstance(t, ast.Module) for t in trees.values())


def test_syntax_error_names_file_and_line():
    with pytest.raises(ParseFailed) as err:
        parse_files({"ok.py": "x = 1\n", "bad.py": "x = 1\ndef f(:\n"})
    assert err.value.code == "PARSE_FAILED"
    assert (err.value.path, err.value.line) == ("bad.py", 2)
    assert str(err.value).startswith("bad.py, line 2: ")


def test_first_bad_file_in_path_order_is_reported():
    with pytest.raises(ParseFailed) as err:
        parse_files({"z.py": "def (\n", "a.py": "class\n"})
    assert err.value.path == "a.py"


def test_null_byte_is_a_parse_failure():
    with pytest.raises(ParseFailed) as err:
        parse_files({"nul.py": "x = 1\0\n"})
    assert err.value.path == "nul.py"


def test_syntax_warning_is_not_a_failure():
    # "\d" is an invalid escape, a SyntaxWarning only
    assert "w.py" in parse_files({"w.py": 'p = "\\d"\n'})


def test_write_model_layout():
    text = write_model({"b": [1], "a": "é"})
    assert text == '{\n  "a": "é",\n  "b": [\n    1\n  ]\n}\n'
