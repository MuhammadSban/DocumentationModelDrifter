# checks which paths scope.json feeds to the generators (spec 3.2)

from drifter.check import in_scope

PATHS = ["app.py", "src/a.py", "src/pkg/b.py", "src/c.txt", "tests/test_a.py", "tests/unit/test_b.py"]


def test_defaults_include_python_files_and_exclude_tests():
    assert in_scope(PATHS, {}) == ["app.py", "src/a.py", "src/pkg/b.py"]


def test_a_path_is_kept_when_some_include_matches_and_no_exclude_does():
    scope = {"include": ["src/*.py", "app.py"], "exclude": ["src/a.py"]}
    assert in_scope(PATHS + ["src/d.py"], scope) == ["app.py", "src/d.py"]
