# freezes the behavioral format as generate_behavioral writes it (spec #30, "Behavioral format"):
# each snippet's exact write_model text; any change here is a format change and bumps schema_version

import json
from pathlib import Path

import jsonschema
import pytest

from models.behavioral_model import generate_behavioral
from models.common import write_model

EMPTY = '{\n  "schema_version": 1,\n  "states": [],\n  "transitions": []\n}\n'


SCHEMA = json.loads((Path(__file__).resolve().parents[2] / "Source" / "models" / "behavioral.schema.json").read_text("utf-8"))


def text(files):
    # renders the behavioral model of files exactly as drifter init writes it, after checking it
    # against behavioral.schema.json, so every golden is a valid model
    model = generate_behavioral(files)
    jsonschema.validate(model, SCHEMA)
    return write_model(model)


def test_self_attribute_checks_across_methods_share_one_class_machine():
    files = {"order.py": (
        "class Order:\n"
        "    def pay(self):\n"
        "        if self.status == 'open':\n"
        "            self.status = 'paid'\n"
        "\n"
        "    def ship(self):\n"
        "        if self.status == 'paid':\n"
        "            self.status = 'shipped'\n"
    )}

    assert text(files) == r'''{
  "schema_version": 1,
  "states": [
    {
      "file": "order.py",
      "id": "state:[\"order.py\",\"order:Order\",\"self.status\",\"open\"]",
      "kind": "state",
      "machine": "order:Order",
      "value": "open",
      "variable": "self.status"
    },
    {
      "file": "order.py",
      "id": "state:[\"order.py\",\"order:Order\",\"self.status\",\"paid\"]",
      "kind": "state",
      "machine": "order:Order",
      "value": "paid",
      "variable": "self.status"
    },
    {
      "file": "order.py",
      "id": "state:[\"order.py\",\"order:Order\",\"self.status\",\"shipped\"]",
      "kind": "state",
      "machine": "order:Order",
      "value": "shipped",
      "variable": "self.status"
    }
  ],
  "transitions": [
    {
      "file": "order.py",
      "guard": "self.status == 'open'",
      "id": "transition:[\"order.py\",\"order:Order.pay\",\"state:[\\\"order.py\\\",\\\"order:Order\\\",\\\"self.status\\\",\\\"open\\\"]\",\"state:[\\\"order.py\\\",\\\"order:Order\\\",\\\"self.status\\\",\\\"paid\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"order.py\",\"order:Order\",\"self.status\",\"open\"]",
      "target": "state:[\"order.py\",\"order:Order\",\"self.status\",\"paid\"]",
      "trigger": "order:Order.pay"
    },
    {
      "file": "order.py",
      "guard": "self.status == 'paid'",
      "id": "transition:[\"order.py\",\"order:Order.ship\",\"state:[\\\"order.py\\\",\\\"order:Order\\\",\\\"self.status\\\",\\\"paid\\\"]\",\"state:[\\\"order.py\\\",\\\"order:Order\\\",\\\"self.status\\\",\\\"shipped\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"order.py\",\"order:Order\",\"self.status\",\"paid\"]",
      "target": "state:[\"order.py\",\"order:Order\",\"self.status\",\"shipped\"]",
      "trigger": "order:Order.ship"
    }
  ]
}
'''


def test_local_machine_with_elif_chain_reversed_guard_and_annotated_assignment():
    # one function's local variable: an elif chain, a "x" == var guard read as var == 'x', and an
    # annotated assignment as the destination
    files = {"lights.py": (
        "def step(light):\n"
        "    if light == 'red':\n"
        "        light = 'green'\n"
        "    elif 'green' == light:\n"
        "        light: str = 'amber'\n"
    )}

    assert text(files) == r'''{
  "schema_version": 1,
  "states": [
    {
      "file": "lights.py",
      "id": "state:[\"lights.py\",\"lights:step\",\"light\",\"amber\"]",
      "kind": "state",
      "machine": "lights:step",
      "value": "amber",
      "variable": "light"
    },
    {
      "file": "lights.py",
      "id": "state:[\"lights.py\",\"lights:step\",\"light\",\"green\"]",
      "kind": "state",
      "machine": "lights:step",
      "value": "green",
      "variable": "light"
    },
    {
      "file": "lights.py",
      "id": "state:[\"lights.py\",\"lights:step\",\"light\",\"red\"]",
      "kind": "state",
      "machine": "lights:step",
      "value": "red",
      "variable": "light"
    }
  ],
  "transitions": [
    {
      "file": "lights.py",
      "guard": "light == 'green'",
      "id": "transition:[\"lights.py\",\"lights:step\",\"state:[\\\"lights.py\\\",\\\"lights:step\\\",\\\"light\\\",\\\"green\\\"]\",\"state:[\\\"lights.py\\\",\\\"lights:step\\\",\\\"light\\\",\\\"amber\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"lights.py\",\"lights:step\",\"light\",\"green\"]",
      "target": "state:[\"lights.py\",\"lights:step\",\"light\",\"amber\"]",
      "trigger": "lights:step"
    },
    {
      "file": "lights.py",
      "guard": "light == 'red'",
      "id": "transition:[\"lights.py\",\"lights:step\",\"state:[\\\"lights.py\\\",\\\"lights:step\\\",\\\"light\\\",\\\"red\\\"]\",\"state:[\\\"lights.py\\\",\\\"lights:step\\\",\\\"light\\\",\\\"green\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"lights.py\",\"lights:step\",\"light\",\"red\"]",
      "target": "state:[\"lights.py\",\"lights:step\",\"light\",\"green\"]",
      "trigger": "lights:step"
    }
  ]
}
'''


def test_punctuation_and_non_ascii_values_are_kept_inside_the_id():
    files = {"tags.py": (
        "def tag(mode):\n"
        "    if mode == 'ready, \"set\"':\n"
        "        mode = 'café'\n"
    )}

    assert text(files) == r'''{
  "schema_version": 1,
  "states": [
    {
      "file": "tags.py",
      "id": "state:[\"tags.py\",\"tags:tag\",\"mode\",\"café\"]",
      "kind": "state",
      "machine": "tags:tag",
      "value": "café",
      "variable": "mode"
    },
    {
      "file": "tags.py",
      "id": "state:[\"tags.py\",\"tags:tag\",\"mode\",\"ready, \\\"set\\\"\"]",
      "kind": "state",
      "machine": "tags:tag",
      "value": "ready, \"set\"",
      "variable": "mode"
    }
  ],
  "transitions": [
    {
      "file": "tags.py",
      "guard": "mode == 'ready, \"set\"'",
      "id": "transition:[\"tags.py\",\"tags:tag\",\"state:[\\\"tags.py\\\",\\\"tags:tag\\\",\\\"mode\\\",\\\"ready, \\\\\\\"set\\\\\\\"\\\"]\",\"state:[\\\"tags.py\\\",\\\"tags:tag\\\",\\\"mode\\\",\\\"café\\\"]\"]",
      "kind": "transition",
      "source": "state:[\"tags.py\",\"tags:tag\",\"mode\",\"ready, \\\"set\\\"\"]",
      "target": "state:[\"tags.py\",\"tags:tag\",\"mode\",\"café\"]",
      "trigger": "tags:tag"
    }
  ]
}
'''


@pytest.mark.parametrize("source", [
    "def f(s):\n    if s == 'a':\n        pass\n    else:\n        s = 'b'\n",
    "def f(s):\n    if s != 'z':\n        if s == 'a':\n            s = 'b'\n",
    "def f(s, x):\n    if s == 'a' and x:\n        s = 'b'\n",
    "def f(s):\n    if s == 'a':\n        s = make()\n",
    "def f(s):\n    if s == State.A:\n        s = State.B\n",
    "def f():\n    global s\n    if s == 'a':\n        s = 'b'\n",
    "def f(s):\n    def g():\n        nonlocal s\n    if s == 'a':\n        s = 'b'\n",
], ids=["else", "nested", "compound", "non-literal", "enum", "global", "nonlocal"])
def test_a_left_out_construct_gives_no_element(source):
    assert text({"m.py": source}) == EMPTY
