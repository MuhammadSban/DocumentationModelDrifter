# checks the behavioral panel: one state diagram per machine, what it draws and what it leaves out

import re

from Frontend.model_loader import BEHAVIORAL_FILE, behavioral_from_dict
from Frontend.model_viewer import _behavioral
from models.behavioral_model import generate_behavioral


def panel(code):
    # renders the behavioral panel for one file of code
    model = generate_behavioral({"src/shop/orders.py": code})
    return _behavioral(behavioral_from_dict(model, BEHAVIORAL_FILE))


def diagrams(html):
    # returns each Mermaid block's source, as the browser would read it
    import html as unescape

    return [unescape.unescape(b) for b in re.findall(r'<pre class="mermaid">(.*?)</pre>', html, re.S)]


ORDER = '''class Order:
    def pay(self):
        if self.status == "open":
            self.status = "paid"
        elif self.status == "paid":
            self.status = "shipped"

    def cancel(self):
        if self.status == "open":
            self.status = "void"
'''


def test_a_lifecycle_is_drawn_as_a_state_diagram():
    # a lifecycle is a state diagram, not a flowchart (docs/agents/modeling.md)
    source = diagrams(panel(ORDER))[0]
    assert source.startswith("stateDiagram-v2")


def test_every_diagram_carries_its_accessible_title_and_description():
    source = diagrams(panel(ORDER))[0]
    assert "accTitle:" in source
    assert "accDescr:" in source


def test_each_value_is_a_node_and_each_change_an_arrow():
    source = diagrams(panel(ORDER))[0]
    for value in ("open", "paid", "shipped", "void"):
        assert f'"{value}"' in source
    # pay moves open to paid and paid to shipped; cancel moves open to void
    assert source.count(" --> ") == 3


def test_an_arrow_is_labelled_with_the_function_that_moves_it():
    source = diagrams(panel(ORDER))[0]
    assert ": pay" in source
    assert ": cancel" in source


def test_the_guard_is_not_drawn_because_the_source_state_already_says_it():
    # the guard is always "<variable> == <source value>", so drawing it adds text and no fact
    source = diagrams(panel(ORDER))[0]
    assert "==" not in source


def test_no_start_marker_is_invented_for_a_state_nothing_arrives_at():
    # the miner skips else branches and enums, so an unreached state is not therefore the entry
    source = diagrams(panel(ORDER))[0]
    assert "[*]" not in source


def test_two_variables_of_one_class_are_two_machines():
    # the machine of a self attribute is the class, so grouping by machine alone would draw these
    # two unrelated lifecycles as one picture
    html = panel(ORDER + '''
    def flag(self):
        if self.phase == "new":
            self.phase = "review"
''')
    assert "<b>2</b> machines" in html
    assert len(diagrams(html)) == 2
    sources = "".join(diagrams(html))
    assert "self.status" in sources and "self.phase" in sources
    # neither picture holds the other's values
    status, phase = sorted(diagrams(html), key=len, reverse=True)
    assert "review" not in status
    assert "shipped" not in phase


def test_each_diagram_is_captioned_with_its_machine_and_variable():
    html = panel(ORDER)
    assert "shop.orders:Order" in html
    assert "self.status" in html


def test_what_the_miner_cannot_see_is_said_on_the_page():
    # a reader whose state machine looks short needs to know why
    html = panel(ORDER)
    assert "else branches, enums and compound conditions" in html


def test_a_quote_in_a_value_cannot_close_the_mermaid_string():
    html = panel('''def step(state):
    if state == 'say "hi"':
        state = "done"
    return state
''')
    source = diagrams(html)[0]
    assert 'say \'hi\'' in source
    # every state line is still one well-formed declaration
    for line in source.splitlines():
        if line.strip().startswith("state "):
            assert re.match(r'^state "[^"]*" as \w+$', line.strip())


def test_a_model_with_no_transitions_draws_nothing_and_says_so():
    html = panel("def nothing():\n    return 1\n")
    assert diagrams(html) == []
    assert "no lifecycle to draw" in html


def test_an_absent_model_is_not_the_same_as_an_empty_one():
    assert "No <code>behavioral.json</code>" in _behavioral(None)
