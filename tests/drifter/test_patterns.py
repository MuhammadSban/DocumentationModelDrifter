# checks the one glob matcher mapping-v1.1.yaml, scope.json and ownership rules share (spec 3.2)

from models.common import glob


def matches(path, pattern):
    # says whether the whole path matches, as every caller asks
    return glob(pattern).match(path) is not None


def test_double_star_slash_matches_a_root_file_and_a_nested_one():
    assert matches("app.py", "**/*.py")
    assert matches("src/pkg/app.py", "**/*.py")


def test_star_does_not_cross_a_slash():
    assert matches("src/app.py", "src/*.py")
    assert not matches("src/pkg/app.py", "src/*.py")


def test_folder_double_star_covers_everything_under_it():
    assert matches("tests/test_a.py", "tests/**")
    assert matches("tests/unit/test_a.py", "tests/**")
    assert not matches("src/tests_helper.py", "tests/**")


def test_exact_path_matches_only_itself():
    assert matches("src/app.py", "src/app.py")
    assert not matches("src/app.pyc", "src/app.py")
    assert not matches("lib/src/app.py", "src/app.py")
