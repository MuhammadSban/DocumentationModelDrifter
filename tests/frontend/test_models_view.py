# checks the console's Models view against real clones: the page the frame loads, and the naive
# drift chip comparing a commit's generated model with the one before it

import re
import subprocess

import pytest
from fastapi.testclient import TestClient

from GitHub_Connector.api import app
from GitHub_Connector.settings import get_settings
from models.common import write_model
from models.structural_model import generate_structural

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
    # asks the route for one commit's models, against a bare repository on disk. verbosity previews
    # the models at one level of the ladder, as the parameters panel's form asks for them.
    def ask(*commits, verbosity=None, panel=None):
        repo, head, remotes = _repo(tmp_path, *commits)
        monkeypatch.setenv("DRIFTER_REMOTE_BASE_URL", remotes.as_uri() + "/")
        get_settings.cache_clear()
        params = {"repository": repo, "commit_id": head}
        if verbosity is not None:
            params["verbosity"] = verbosity
        if panel is not None:
            params["panel"] = panel
        try:
            response = TestClient(app).get("/models/view", params=params)
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


# ------------------------------------------------- the parameters panel and its verbosity level

# a class with a method, so a level below MEMBERS has something to drop from the page
LADDER = {
    "src/shop/models.py": "class Base:\n    def save(self):\n        pass\n",
    "src/shop/orders.py": "from shop.models import Base\n\n\nclass Order(Base):\n    pass\n",
}


def test_the_panel_is_on_the_page_with_one_stop_per_level(view):
    response = view({**LADDER, "models/scope.json": write_model(SCOPE)})

    assert "Parameters" in response.text
    assert response.text.count('name="verbosity"') == 4
    # a GET form, so changing the level needs no script
    assert 'method="get"' in response.text
    assert 'action="/models/view"' in response.text


@pytest.mark.parametrize("level, drawn", [(1, False), (2, True), (3, True), (4, True)])
def test_a_preview_draws_the_classes_only_from_the_level_that_holds_them(view, level, drawn):
    # one repository per call: the fixture builds its work tree once, so a test asks once
    response = view({**LADDER, "models/scope.json": write_model(SCOPE)}, verbosity=level)

    assert ("Order" in response.text) is drawn


def test_no_level_draws_the_level_the_repository_commits(view):
    # the committed level is the page's default, not level 4, so a repository that has chosen one
    # is shown as it has chosen
    response = view({**LADDER, "models/scope.json": write_model({**SCOPE, "verbosity": 1})})

    assert "Order" not in response.text
    assert "which is the level this repository commits" in response.text


def test_a_preview_says_it_is_a_preview_and_names_both_levels(view):
    response = view({**LADDER, "models/scope.json": write_model(SCOPE)}, verbosity=2)

    assert "as a preview" in response.text
    assert "This repository commits level 4" in response.text
    assert "drifter check" in response.text


def test_no_preview_note_where_the_two_levels_agree(view):
    response = view({**LADDER, "models/scope.json": write_model(SCOPE)}, verbosity=4)

    assert "as a preview" not in response.text
    assert "which is the level this repository commits" in response.text


@pytest.mark.parametrize("bad", [0, 5, 99, "high"])
def test_a_level_outside_the_ladder_is_refused_before_any_clone(view, bad):
    # 400, not 422: this app answers every one of FastAPI's own validation failures in the error
    # shape of the route's family (GitHub_Connector/api.py:88), as the malformed-name case does
    response = TestClient(app).get(
        "/models/view",
        params={"repository": "owner/repo", "commit_id": "a" * 40, "verbosity": bad},
    )

    assert response.status_code == 400


def test_a_preview_compares_the_drawn_level_with_itself(view):
    # both snapshots take the same level, so a change the previewed level does not describe is not
    # reported as drift. Without that the head would be drawn at level 1 and the base at level 4,
    # and every class and method would read as having disappeared.
    base = {**LADDER, "models/scope.json": write_model(SCOPE)}
    head = {"src/shop/models.py": "class Base:\n    def save(self, force=False):\n        pass\n"}

    response = view(base, head, verbosity=1)

    assert chips(response.text)["Structural"] == "same as previous commit"


def test_panel_off_drops_the_stops_and_keeps_the_note(view):
    # the console's Models tab carries its own verbosity slider, so the framed page is asked for
    # the note alone: two controls for one value, one of them scrolled out of sight, is worse
    response = view({**LADDER, "models/scope.json": write_model(SCOPE)}, panel="off", verbosity=2)

    assert response.status_code == 200
    assert 'name="verbosity"' not in response.text
    assert "<form" not in response.text
    assert "Showing level 2 of 4, Types, as a preview" in response.text
    # and no stop to remember, so the page keeps none
    assert "localStorage" not in response.text


def test_the_page_reports_its_level_to_whoever_framed_it(view):
    # the console's slider starts where the repository is, and names a preview as one, only because
    # the page tells it both numbers
    response = view({**LADDER, "models/scope.json": write_model({**SCOPE, "verbosity": 1})},
                    panel="off", verbosity=3)

    assert 'drifter: "level", drawn: 3, committed: 1' in response.text
    assert "parent !== window" in response.text


def test_the_console_slider_and_the_page_name_the_same_levels():
    # two files name the ladder, index.html for the slider and model_viewer.py for the note. They
    # must agree, or the slider says Members while the page draws something else.
    from pathlib import Path

    from Frontend import ui
    from Frontend.model_viewer import LEVEL_NAMES

    console = (Path(ui.__file__).parent / "index.html").read_text(encoding="utf-8")
    for level, (name, _) in LEVEL_NAMES.items():
        assert f'{level}: ["{name}"' in console, f"the console does not call level {level} {name}"


def test_the_console_server_forwards_every_path_the_console_asks_the_api_for():
    # the console and the server that fronts it are two files, and the models page went missing
    # because they disagreed: index.html framed /models/view while ui.py forwarded only /system/*,
    # so the frame got a 404 and the page, panel and all, never appeared. This pins the agreement.
    from pathlib import Path

    from Frontend import ui

    console = (Path(ui.__file__).parent / "index.html").read_text(encoding="utf-8")
    asked = set(re.findall(r'api\("(/[\w/.-]+)', console))

    assert "/models/view" in asked, "the console no longer frames the models page by that path"
    for path in asked:
        assert path.startswith(ui.PROXIED) or path == "/system", f"ui.py would serve {path} as a file"
    # and it still serves its own files rather than proxying everything
    assert not "/index.html".startswith(ui.PROXIED)
    assert not "/app.css".startswith(ui.PROXIED)


@pytest.mark.parametrize(
    "declared, named",
    [(1, "level 1 of 4, Overview"), (3, "level 3 of 4, Members"), (None, "level 4 of 4, Full")],
)
def test_the_standalone_render_names_the_level_the_folder_declares(tmp_path, declared, named):
    # the panel must never claim Full over a model that holds less. Rendered to a file there is no
    # route to ask for another level, so the only level it can name is the committed one.
    from Frontend.model_loader import load_models
    from Frontend.model_viewer import main

    scope = dict(SCOPE) if declared is None else {**SCOPE, "verbosity": declared}
    (tmp_path / "scope.json").write_text(write_model(scope))
    (tmp_path / "ownership.json").write_text(write_model(RULES))
    (tmp_path / "structural.json").write_text(write_model(generate_structural(CODE)))
    out = tmp_path / "page.html"

    assert main([str(tmp_path), "-o", str(out)]) == 0

    assert f"Showing {named}," in out.read_text()
    assert load_models(tmp_path).scope.verbosity == (declared or 4)


def test_a_level_the_ladder_does_not_hold_labels_the_page_rather_than_failing(tmp_path):
    # the check refuses such a value; the viewer must still draw something and name a real level,
    # since a page that 500s teaches the reader nothing
    from Frontend.model_loader import load_models

    (tmp_path / "scope.json").write_text(write_model({**SCOPE, "verbosity": 7}))
    (tmp_path / "ownership.json").write_text(write_model(RULES))

    assert load_models(tmp_path).scope.verbosity == 4


def test_the_standalone_render_shows_the_panel_read_only():
    # rendered to a file there is no server to ask for another level, so the stops are disabled and
    # the page says how to change it, rather than offering a control that would do nothing
    from Frontend.model_loader import models_from_dicts
    from Frontend.model_viewer import render

    models = models_from_dicts({"scope.json": SCOPE}, "a folder")
    page = render(models, drawn_level=3, committed_level=3)

    assert "Parameters" in page
    assert "<form" not in page
    # every one of the four stops is shown and none is offered
    assert page.count('name="verbosity"') == 4
    assert page.count(" disabled>") == 4
    assert "drifter update" in page
    assert "localStorage" not in page
