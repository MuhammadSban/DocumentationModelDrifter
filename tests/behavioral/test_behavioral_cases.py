import textwrap

import pytest

from models.behavioral_model import generate_behavioral


def mine(body, method=False, asynchronous=False):
    # reads snippets without executing their state changes, calls or context managers
    signature = ("async " if asynchronous else "") + "def step("
    signature += ("self, " if method else "") + "state, session, guard, logger):\n"
    source = signature + textwrap.indent(body, "    ")
    if method:
        source = "class Order:\n" + textwrap.indent(source, "    ")
    return generate_behavioral({"flow.py": source})


@pytest.mark.parametrize("variable,method", [
    ("session['state']", False),
    ('session["state"]', False),
    ("session['meta']['state']", False),
    ("self.data['state']", True),
    ("self['state']", True),
])
def test_literal_dictionary_states_keep_their_machine(variable, method):
    model = mine(f"if {variable} == 'open':\n    {variable} = 'paid'\n", method=method)
    assert len(model["transitions"]) == 1
    normalized = variable.replace('"', "'")
    assert {state["variable"] for state in model["states"]} == {normalized}
    assert {state["machine"] for state in model["states"]} == {"flow:Order" if method else "flow:step"}
    assert {state["value"] for state in model["states"]} == {"open", "paid"}


@pytest.mark.parametrize("body", [
    "if state != 'open':\n    return\nstate = 'paid'\n",
    "if 'open' != state:\n    return\nstate = 'paid'\n",
    "if not (state == 'open'):\n    return\nstate = 'paid'\n",
    "if state != 'open':\n    raise ValueError()\nstate = 'paid'\n",
    "if state != 'open':\n    with guard:\n        return\nstate = 'paid'\n",
    "if state != 'open':\n    if guard:\n        return\n    else:\n        raise ValueError()\nstate = 'paid'\n",
])
def test_exit_guards_supply_the_fallthrough_state(body):
    model = mine(body)
    assert len(model["transitions"]) == 1
    assert model["transitions"][0]["guard"] == "state == 'open'"
    assert {state["value"] for state in model["states"]} == {"open", "paid"}


@pytest.mark.parametrize("statement", [
    "print(state)",
    "log('moving')",
    "logger.info('moving', extra={'state': state})",
    "logging.warning('moving')",
    "print(f'moving {state}')",
    "note = 1",
])
def test_observational_statements_allow_a_transition(statement):
    model = mine(f"if state == 'open':\n    {statement}\n    state = 'paid'\n")
    assert len(model["transitions"]) == 1


@pytest.mark.parametrize("body,asynchronous", [
    ("with guard:\n    if state == 'open':\n        state = 'paid'\n", False),
    ("if state == 'open':\n    with guard:\n        state = 'paid'\n", False),
    ("async with guard:\n    if state == 'open':\n        state = 'paid'\n", True),
])
def test_context_blocks_expose_supported_state_changes(body, asynchronous):
    assert len(mine(body, asynchronous=asynchronous)["transitions"]) == 1


@pytest.mark.parametrize("statement", [
    "mutate()",
    "print(mutate())",
    "logger.info('moving', extra=mutate())",
    "print((state := 'cancelled'))",
    "print(await mutate())",
    "state = lookup()",
    "state = 10",
    "if guard:\n    mutate()",
    "return",
])
def test_effects_and_unknown_destinations_stop_the_transition(statement):
    body = "if state == 'open':\n" + textwrap.indent(statement, "    ") + "\n    state = 'paid'\n"
    assert mine(body, asynchronous=True)["transitions"] == []


@pytest.mark.parametrize("prefix", [
    "return\n",
    "raise ValueError()\n",
    "if guard:\n    return\nelse:\n    return\n",
])
def test_obviously_unreachable_state_changes_are_ignored(prefix):
    assert mine(prefix + "if state == 'open':\n    state = 'paid'\n")["transitions"] == []


def test_context_manager_may_suppress_an_exception():
    body = "if state != 'open':\n    with guard:\n        raise ValueError()\nstate = 'paid'\n"
    assert mine(body)["transitions"] == []


def test_rebinding_the_dictionary_invalidates_its_guard():
    body = "if session['state'] == 'open':\n    session = None\n    session['state'] = 'paid'\n"
    assert mine(body)["transitions"] == []


def test_rebinding_self_invalidates_its_guard():
    body = "if self.status == 'open':\n    self = None\n    self.status = 'paid'\n"
    assert mine(body, method=True)["transitions"] == []
