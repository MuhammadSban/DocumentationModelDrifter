# shares what every model generator needs: parsing the in-scope files and writing a model file

from __future__ import annotations

import ast
import json
import re
import warnings
from functools import lru_cache

JAVASCRIPT_EXTENSIONS = (".js", ".mjs", ".cjs", ".jsx")


class ParseFailed(Exception):
    # reports invalid in-scope source, the spec's PARSE_FAILED (3.2, 5.2)
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
    javascript = False
    for path in sorted(files):
        try:
            if path.endswith(JAVASCRIPT_EXTENSIONS):
                from models.javascript_model import parse_javascript

                trees[path] = parse_javascript(path, files[path])
                javascript = True
                continue
            # silences SyntaxWarning, a warning is not a parse failure
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trees[path] = ast.parse(files[path], filename=path)
        except SyntaxError as exc:
            raise ParseFailed(path, exc.lineno, exc.msg) from None
        except ValueError as exc:
            # catches source ast cannot read at all, such as a null byte
            raise ParseFailed(path, None, str(exc)) from None
    if javascript:
        from models.javascript_model import lower_javascript

        trees.update(lower_javascript(trees))
    return trees


def write_model(model: dict) -> str:
    # renders a model in the spec's layout (3.2): sorted keys, 2-space indent, non-ASCII as is,
    # LF line endings and one trailing newline
    return json.dumps(model, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def literal(path: str) -> str:
    # escapes a path for glob, so a pattern made from it matches that path only
    return "".join("\\" + c if c in "\\*?" else c for c in path)


@lru_cache(maxsize=256)
def glob(pattern: str) -> re.Pattern:
    # turns a POSIX glob into a regex: "**/" is zero or more folders, "**" anything, "*" one
    # segment's text, "?" one character, a backslash makes the next character literal. The one matcher
    # scope.json, ownership rules and mapping-v1.1.yaml share, so a pattern means the same thing
    # in all three (phase4.md Q3)
    out, i = [], 0
    while i < len(pattern):
        if pattern[i] == "\\" and i + 1 < len(pattern):
            out.append(re.escape(pattern[i + 1]))
            i += 2
        elif pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    # compiles with DOTALL, so ".*" crosses a newline, which git allows in a file name
    return re.compile("".join(out) + r"\Z", re.DOTALL)
