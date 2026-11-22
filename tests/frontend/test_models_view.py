# checks the console's Models view against real clones: the page the frame loads, and the naive
# drift chip comparing a commit's generated model with the one before it

import re
import subprocess

import pytest
from fastapi.testclient import TestClient

from GitHub_Connector.api import app
from GitHub_Connector.settings import get_settings
from models.common import write_model

# one in-scope file, enough for the structural generator to have something to say
CODE = {"src/app.py": "def charge(amount):\n    return amount\n"}
SCOPE = {"exclude": ["tests/**"], "include": ["**/*.py"]}
RULES = {"rules": [{"owners": ["zoe@x.com"], "pattern": "src/app.py"}], "schema_version": 1}


def chips(text):
    # maps each panel's title to the drift chip beside it, so one model's answer is read alone
    return dict(re.findall(r'<h2>(\w+)<span class="chip \w+">([^<]+)</span></h2>', text))


def _git(cwd, *args, author="ana@x.com"):
    # runs one git command with a scripted author
    env = ["-c", "user.email=" + author, "-c", "user.name=" + author.split("@")[0]]
    subprocess.run(["git", "-C", str(cwd), *env, *args], check=True, capture_output=True)


def _repo(tmp_path, *commits):
    # builds a bare repository with one commit per dict, and returns owner/name, the head SHA and
    # the folder the connector's clone URL is pointed at
    work = tmp_path / "work"
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    for commit in commits:
        author = commit.pop("__author__", "ana@x.com")
        for path, text in commit.items():
            target = work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        _git(work, "add", "-A", author=author)
        _git(work, "commit", "-qm", "change", author=author)
    bare = tmp_path / "remotes" / "owner" / "repo.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(bare)], check=True)
    # lets a partial clone filter and ask for objects by id, as GitHub does
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()
    return "owner/repo", head, tmp_path / "remotes"


@pytest.fixture
def view(tmp_path, monkeypatch):
    # asks the route for one commit's models, against a bare repository on disk
    def ask(*commits):
        repo, head, remotes = _repo(tmp_path, *commits)
        monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", remotes.as_uri() + "/")
        get_settings.cache_clear()
        try:
            response = TestClient(app).get(
                "/models/view", params={"repository": repo, "commit_id": head}
            )
        finally:
            get_settings.cache_clear()
        return response

    return ask


def test_the_frame_is_served_one_html_page(view):
    response = view({**CODE, "models/scope.json": write_model(SCOPE)})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.text.startswith("<!doctype html>")


def test_a_commit_that_changes_the_code_reads_as_changed(view):
    # the second commit adds a function, so the regenerated model is not the one before it
    response = view(
        {**CODE, "models/scope.json": write_model(SCOPE)},
        {"src/app.py": CODE["src/app.py"] + "\n\ndef refund(amount):\n    return -amount\n"},
    )
    # the added function is structural; the behavioral model is untouched, and says so separately
    assert chips(response.text)["Structural"] == "drifted from previous commit"
    assert chips(response.text)["Behavioral"] == "same as previous commit"


def test_a_commit_that_leaves_the_code_alone_reads_as_unchanged(view):
    # the second commit touches a file out of scope, so both commits generate the same model
    response = view(
        {**CODE, "models/scope.json": write_model(SCOPE)},
        {"README.md": "# notes\n"},
    )
    assert chips(response.text)["Structural"] == "same as previous commit"
    assert "drifted from previous commit" not in response.text


def test_a_first_commit_has_nothing_to_compare_with(view):
    response = view({**CODE, "models/scope.json": write_model(SCOPE)})
    assert "Not checked for drift" in response.text
    assert "has no earlier commit to compare with" in response.text
    # with nothing to compare against, no model claims to be in step
    assert set(chips(response.text).values()) == {"not checked"}


def test_a_change_to_a_state_machine_drifts_the_behavioral_model_alone(view):
    # the second commit changes only a lifecycle, so behavioral drifts and structural does not
    machine = ("class Order:\n    def pay(self):\n"
               '        if self.status == "open":\n            self.status = "paid"\n')
    response = view(
        {**CODE, "src/orders.py": machine, "models/scope.json": write_model(SCOPE)},
        {"src/orders.py": machine.replace('"paid"', '"settled"')},
    )
    assert chips(response.text)["Behavioral"] == "drifted from previous commit"
    assert chips(response.text)["Structural"] == "same as previous commit"


def test_the_behavioral_model_is_generated_from_the_code_too(view):
    # the panel is not waiting on a committed behavioral.json that almost no repository has
    response = view({
        **CODE,
        "src/orders.py": ("class Order:\n    def pay(self):\n"
                          '        if self.status == "open":\n            self.status = "paid"\n'),
        "models/scope.json": write_model(SCOPE),
    })
    assert "No <code>behavioral.json</code>" not in response.text
    assert "stateDiagram-v2" in response.text
    assert "<b>1</b> machine" in response.text


def test_the_structural_model_is_drawn_from_the_code_at_that_commit(view):
    # the head carries two modules and the commit before it one, so a page showing two read the head
    response = view(
        {**CODE, "models/scope.json": write_model(SCOPE)},
        {"src/refund.py": "import app\n\n\ndef refund(amount):\n    return -app.charge(amount)\n"},
    )
    assert "<b>2</b> modules" in response.text
    # the import the head commit added, which the model records as an edge and the diagram draws
    assert "<b>1</b> edge" in response.text
    assert "refund" in response.text


def test_a_committed_ownership_model_wins_over_a_mined_one(view):
    # zoe owns src/app.py by the committed file and has never committed; ana wrote every commit.
    # Only a page reading the committed file shows zoe and not ana.
    response = view({
        **CODE,
        "models/scope.json": write_model(SCOPE),
        "models/ownership.json": write_model(RULES),
    })
    assert "zoe@x.com" in response.text
    assert "ana@x.com" not in response.text
    assert "it has committed no" not in response.text
    # ownership is never regenerated, so the naive check has no answer for it
    assert "not checked" in response.text


def test_a_repository_without_an_ownership_model_has_one_mined_from_its_history(view):
    response = view({**CODE, "models/scope.json": write_model(SCOPE)})
    assert "No <code>ownership.json</code>" not in response.text
    # ana wrote every commit, so history names her the owner of the file she wrote
    assert "ana@x.com" in response.text


def test_a_mined_ownership_model_is_marked_as_a_proposal(view):
    # the one way this panel could mislead: a mining read as the repository's own declaration
    response = view({**CODE, "models/scope.json": write_model(SCOPE)})
    assert "it has committed no" in response.text
    assert "not ownership this repository has declared" in response.text


def test_automation_is_not_mined_as_an_owner(view):
    # a repository whose only other author is automation names the person, not the tool
    response = view({**CODE, "models/scope.json": write_model(SCOPE)},
                    {"__author__": "noreply@anthropic.com",
                     "src/app.py": CODE["src/app.py"] + "\n# touched\n"})
    assert "noreply@anthropic.com" not in response.text
    assert "ana@x.com" in response.text


def test_a_repository_with_no_models_folder_at_all_still_shows_both_models(view):
    # the common case: nothing has ever run drifter init here
    response = view({**CODE, "README.md": "# notes\n"})
    assert response.status_code == 200
    assert "Structural" in response.text
    assert "ana@x.com" in response.text
    # with no scope.json the page falls back to the default, so the README is not an owned path
    assert "README.md" not in response.text


def test_a_commit_with_no_python_is_not_checked(view):
    response = view({"README.md": "# notes\n", "models/scope.json": write_model(SCOPE)})
    assert response.status_code == 200
    assert "has no files in scope" in response.text


def test_a_malformed_repository_name_is_rejected(view, tmp_path, monkeypatch):
    client = TestClient(app)
    assert client.get("/models/view", params={"repository": "nope", "commit_id": "a" * 40}).status_code == 400
    assert client.get("/models/view", params={"repository": "owner/name", "commit_id": "zz"}).status_code == 400
