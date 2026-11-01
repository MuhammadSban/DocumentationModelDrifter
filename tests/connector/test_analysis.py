# checks that an analysis needs no LLM, the spec allows none at runtime

from contextlib import contextmanager

from GitHub_Connector import analysis, runs
from GitHub_Connector.fetch import Comparison, FileChange
from GitHub_Connector.schemas import AnalysisRequest, ChangeType


@contextmanager
def fake_fetch(repo, head, base, deadline):
    # replaces the clone with one changed file, so no git or network is needed; the empty tree
    # holds no /models, so the model check reaches MODELS_NOT_FOUND without running git
    yield Comparison(
        repo=repo,
        head="a" * 40,
        base="b" * 40,
        changes=[FileChange("src/app.py", ChangeType.MODIFIED)],
        _tree={},
    )


def test_analyze_runs_without_an_llm(monkeypatch):
    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)

    result = analysis.analyze(AnalysisRequest(repository="owner/repo", commit_id="a" * 40))

    assert result.issues == []
    assert [c.path for c in result.changes] == ["src/app.py"]


def test_over_2000_changes_is_a_saved_change_limit_error(monkeypatch):
    @contextmanager
    def big_fetch(repo, head, base, deadline):
        # changes one more file than mapping-v1.1.yaml's max_changed_files allows
        yield Comparison(
            repo=repo,
            head="a" * 40,
            base="b" * 40,
            changes=[FileChange(f"src/m{i}.py", ChangeType.ADDED) for i in range(2001)],
            _tree={},
        )

    saved = []
    monkeypatch.setattr(analysis, "fetch", big_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: saved.append(args))

    result = analysis.analyze(AnalysisRequest(repository="owner/repo", commit_id="a" * 40))

    assert result.status == "ERROR"
    assert result.error.code == "CHANGE_LIMIT_EXCEEDED"
    assert (result.changes, result.skipped, result.unmapped, result.issues) == ([], [], [], [])
    # the model check does not depend on status, so it still reached a no-verdict code (spec 5.2)
    assert result.drift_error.code == "MODELS_NOT_FOUND"
    assert saved
