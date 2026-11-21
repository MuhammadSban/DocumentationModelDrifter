# blocks an agent's git commit on an Epic branch that carries no Step: trailer (CLAUDE.md R7)

import json
import re
import subprocess
import sys

# matches git commit as text, with git's own options (-C dir, -c k=v) allowed before the subcommand
COMMIT = re.compile(r"\bgit(?:\.exe)?\s+(?:-[Cc]\s+\S+\s+|-\S+\s+)*commit(?![\w-])")
# matches an Epic's branch name, E<nn>-slug (docs/epics/README.md)
EPIC_BRANCH = re.compile(r"E\d\d-")
# matches the trailer where a line or a quoted -m value starts, since the hook sees the command, not the message
TRAILER = re.compile(r"""(?m)(?:^|["'])[ \t]*Step: (?:\d+/\d+|plan|close)(?=["'\s]|$)""")


def main():
    event = json.load(sys.stdin)
    command = event.get("tool_input", {}).get("command", "")
    if not COMMIT.search(command) or TRAILER.search(command):
        return
    branch = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True, cwd=event.get("cwd") or None
    ).stdout.strip()
    if not EPIC_BRANCH.match(branch):
        return
    print(
        f"Blocked: {branch} is an Epic branch, so the commit message needs a Step: line (CLAUDE.md R7). "
        f"Add `Step: i/N` for step i of the N in docs/epics/{branch}/EPIC.md, "
        "`Step: plan` for a commit that drafts or revises the Epic, or `Step: close` for the closing commit.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
