# checks the batched blob reader on a fresh blobless clone of a local bare repo (D11, issue #18):
# the same sources as a local checkout, a failed batch that fails at once, one download per read,
# and git calls held to the deadline with the clone deleted afterwards

import subprocess
from types import SimpleNamespace

import pytest

from drifter.check import LocalReader, read_sources
from GitHub_Connector import fetch as fetch_module
from GitHub_Connector.fetch import fetch
from GitHub_Connector.schemas import AnalysisError, ErrorCode
from GitHub_Connector.settings import get_settings
from models.common import write_model
from models.structural_model import generate_structural

CODE = {"src/app.py": "def charge(amount):\n    return amount\n", "src/util.py": "X = 1\n"}
OWNED = {"rules": [{"owners": ["ana@x.com"], "pattern": "src/**"}], "schema_version": 1}
SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}


def _git(cwd, *args, author="ana@x.com"):
    # runs one git command as a scripted author and returns its text
    return subprocess.run(["git", "-C", str(cwd), "-c", f"user.email={author}", "-c", "user.name=x", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def _commit(work, files, author="ana@x.com"):
    # writes files, commits them as author and returns the new head SHA
    for path, text in files.items():
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_bytes(text.encode())
    _git(work, "add", "-A", author=author)
    _git(work, "commit", "-qm", "change", author=author)
    return _git(work, "rev-parse", "HEAD")


@pytest.fixture
def served(tmp_path, monkeypatch):
    # commits aligned code then a second author's change, serves both as owner/repo, and returns
    # the work checkout, the head SHA and the folder clones are made in
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    models = {
        "models/behavioral.json": write_model({"schema_version": 1}),
        "models/ownership.json": write_model(OWNED),
        "models/scope.json": write_model(SCOPE),
        "models/structural.json": write_model(generate_structural(CODE)),
    }
    _commit(work, {**CODE, **models})
    head = _commit(work, {"src/util.py": "X = 2\n", "tests/test_app.py": "def test_x():\n    pass\n"},
                   author="bob@x.com")
    bare = tmp_path / "remotes" / "owner" / "repo.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    _git(work, "push", "-q", str(bare), "main")
    clones = tmp_path / "clones"
    monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", (tmp_path / "remotes").as_uri() + "/")
    monkeypatch.setenv("DRIFTER_CLONE_DIR", str(clones))
    get_settings.cache_clear()
    yield work, head, clones
    get_settings.cache_clear()


def test_the_remote_reader_reads_what_the_local_reader_reads(served):
    work, head, _ = served

    with fetch("owner/repo", head) as cmp:
        remote = read_sources(cmp)

    assert remote == read_sources(LocalReader(work, head))
    # pins what both read, so two empty answers cannot pass
    assert sorted(remote.files) == ["src/app.py", "src/util.py"]
    assert [c.author_email for c in remote.commits] == ["bob@x.com"]


def test_a_skipped_batch_fails_at_once_instead_of_fetching_lazily(served, monkeypatch):
    _, head, _ = served
    run = fetch_module._Git.run

    def no_batch(self, *args, **kwargs):
        # answers the batch fetch as if it succeeded without downloading anything
        if args[0] == "fetch" and "--stdin" in args:
            return subprocess.CompletedProcess(args, 0, b"", b"")
        return run(self, *args, **kwargs)

    monkeypatch.setattr(fetch_module._Git, "run", no_batch)

    with fetch("owner/repo", head) as cmp, pytest.raises(AnalysisError) as err:
        cmp.read(["src/app.py"])

    assert err.value.code == ErrorCode.ANALYSIS_FAILED
    assert "so the batch failed" in err.value.message


def test_one_read_leaves_exactly_two_promisor_packs(served):
    _, head, clones = served

    with fetch("owner/repo", head) as cmp:
        blobs = cmp.read(["models/scope.json", "src/app.py", "src/util.py"])
        packs = list(clones.glob("*/clone/.git/objects/pack/*.promisor"))

    assert blobs["src/util.py"] == b"X = 2\n"
    assert len(packs) == 2
    assert list(clones.iterdir()) == []


def test_a_git_call_over_its_timeout_fails_the_read(served):
    _, head, clones = served

    with fetch("owner/repo", head) as cmp, pytest.raises(AnalysisError) as err:
        # caps each git call far below what any call takes, once the clone exists
        cmp._git.timeout = 1e-6
        cmp.read(["src/app.py"])

    assert err.value.code == ErrorCode.ANALYSIS_FAILED
    assert "A git call took longer than" in err.value.message
    assert list(clones.iterdir()) == []


def test_a_read_past_the_deadline_fails_and_the_clone_is_deleted(served, monkeypatch):
    _, head, clones = served

    with pytest.raises(AnalysisError) as err:
        with fetch("owner/repo", head, deadline=1e12) as cmp:
            # moves the clock past the deadline once the clone exists
            monkeypatch.setattr(fetch_module, "time", SimpleNamespace(monotonic=lambda: 2e12))
            cmp.read(["src/app.py"])

    assert err.value.code == ErrorCode.ANALYSIS_FAILED
    assert f"longer than {get_settings().analysis_deadline:g} s" in err.value.message
    assert list(clones.iterdir()) == []
