# checks that an analysis needs no LLM, the spec allows none at runtime

from contextlib import contextmanager

from GitHub_Connector import analysis, runs
from GitHub_Connector.fetch import Comparison, FileChange
from GitHub_Connector.schemas import AnalysisRequest, ChangeType


def test_analyze_runs_without_an_llm(monkeypatch):
    # replaces the clone with one changed file, so no git or network is needed
    @contextmanager
    def fake_fetch(repo, head, base, deadline):
        yield Comparison(
            repo=repo,
            head="a" * 40,
            base="b" * 40,
            changes=[FileChange("src/app.py", ChangeType.MODIFIED)],
        )

    monkeypatch.setattr(analysis, "fetch", fake_fetch)
    monkeypatch.setattr(runs, "save", lambda *args: None)

    result = analysis.analyze(AnalysisRequest(repository="owner/repo", commit_id="a" * 40))

    assert result.issues == []
    assert [c.path for c in result.changes] == ["src/app.py"]
