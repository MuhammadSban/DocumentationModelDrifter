# tests the Step-trailer hook as Claude Code runs it: PreToolUse JSON on stdin, exit code and stderr out

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "step-trailer.py"


def repo_on(tmp_path, branch):
    # creates an empty git repository whose current branch is `branch`
    subprocess.run(["git", "init", "-q", "-b", branch, str(tmp_path)], check=True)
    return tmp_path


def run_hook(cwd, command, tool="Bash"):
    # runs the hook the way Claude Code does before a shell tool call
    event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}, "cwd": str(cwd)}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True, cwd=cwd)


def test_epic_branch_commit_without_trailer_is_blocked_and_told_the_line(tmp_path):
    repo = repo_on(tmp_path, "E99-test")
    result = run_hook(repo, 'git commit -m "Add the parser"')
    assert result.returncode == 2
    assert "Step: i/N" in result.stderr
    assert "docs/epics/E99-test/EPIC.md" in result.stderr


@pytest.mark.parametrize("trailer", ["Step: 1/3", "Step: plan", "Step: close"])
def test_epic_branch_commit_with_a_trailer_runs(tmp_path, trailer):
    repo = repo_on(tmp_path, "E99-test")
    result = run_hook(repo, f'git commit -m "Add the parser" -m "{trailer}"')
    assert result.returncode == 0


def test_commit_on_another_branch_is_untouched(tmp_path):
    repo = repo_on(tmp_path, "docs/some-fix")
    result = run_hook(repo, 'git commit -m "Fix a typo"')
    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize("command", ["git status", "git log --grep commit", "git commit-tree abc", "git --no-pager log -1 commit"])
def test_epic_branch_command_that_is_not_a_commit_runs(tmp_path, command):
    repo = repo_on(tmp_path, "E99-test")
    assert run_hook(repo, command).returncode == 0


@pytest.mark.parametrize("command", ['git -C . commit -m "x"', 'git -c user.name=a commit -m "x"', 'git.exe commit -m "x"'])
def test_epic_branch_commit_behind_git_options_is_blocked(tmp_path, command):
    repo = repo_on(tmp_path, "E99-test")
    assert run_hook(repo, command).returncode == 2


def test_powershell_commit_is_checked_like_bash(tmp_path):
    repo = repo_on(tmp_path, "E99-test")
    assert run_hook(repo, "git commit -m 'Add the parser'", tool="PowerShell").returncode == 2
    assert run_hook(repo, "git commit -m 'Add the parser' -m 'Step: 2/3'", tool="PowerShell").returncode == 0


def test_heredoc_message_with_the_trailer_on_its_own_line_runs(tmp_path):
    repo = repo_on(tmp_path, "E99-test")
    command = "git commit -m \"$(cat <<'EOF'\nAdd the parser\n\nStep: 1/3\nCo-Authored-By: A <a@b.c>\nEOF\n)\""
    assert run_hook(repo, command).returncode == 0
