# shares what every model generator needs: parsing the in-scope files and writing a model file

from __future__ import annotations

import ast
import json
import warnings


class ParseFailed(Exception):
    # reports an in-scope file that is not valid Python, the spec's PARSE_FAILED (3.2, 5.2)
    code = "PARSE_FAILED"

    def __init__(self, path: str, line: int | None, reason: str):
        self.path = path
        self.line = line
        self.reason = reason
        where = f"{path}, line {line}" if line else path
        super().__init__(f"{where}: {reason}")


def parse_files(files: dict[str, str]) -> dict[str, ast.Module]:
    # parses every file (repo-relative path -> text) before any model is built, so one bad file
    # fails the whole check; returns the trees by path, in path order
    trees = {}
    for path in sorted(files):
        try:
            # silences SyntaxWarning, a warning is not a parse failure
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trees[path] = ast.parse(files[path], filename=path)
        except SyntaxError as exc:
            raise ParseFailed(path, exc.lineno, exc.msg) from None
        except ValueError as exc:
            # catches source ast cannot read at all, such as a null byte
            raise ParseFailed(path, None, str(exc)) from None
    return trees


def write_model(model: dict) -> str:
    # renders a model in the spec's layout (3.2): sorted keys, 2-space indent, non-ASCII as is,
    # LF line endings and one trailing newline
    return json.dumps(model, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
