# tests the seam every structural and behavioral generator must pass before it plugs in
# (model-seam.md): element rule, unique ids, top-level lists sorted by id, valid against the
# owner's schema when one exists, and a write_model round trip

import json
from pathlib import Path

import pytest

from drifter.check import DriftError, _element_rule
from models.common import write_model
from models.structural_model import generate_structural

# lists the generators under test; an owner adds one line here to run the seam on theirs
SEAM_GENERATORS = {
    "structural": generate_structural,
}

# holds each owner's <name>.schema.json, next to the generators
SCHEMAS = Path(__file__).resolve().parents[2] / "Source" / "models"

# feeds each generator small snippets, path -> text
SNIPPETS = {
    "empty": {},
    "shop": {
        "src/shop/__init__.py": "",
        "src/shop/models.py": "class Base:\n    def save(self): ...\n",
        "src/shop/payments.py": 'def charge(amount, *, currency="USD"): ...\n',
        "src/shop/orders.py": (
            "from shop.models import Base\n"
            "from shop import payments\n"
            "\n"
            "class Order(Base):\n"
            "    def cancel(self, reason=None):\n"
            "        payments.charge(0)\n"
        ),
    },
}


def check_seam(name, model):
    # asserts what the core relies on: the element rule with unique ids (the same check that
    # gives INVALID_MODELS), each top-level list sorted by id, and a stable write_model round trip
    _element_rule(f"models/{name}.json", model)
    for key, value in model.items():
        if isinstance(value, list):
            ids = [e["id"] for e in value]
            assert ids == sorted(ids), f"{key} is not sorted by id"
    text = write_model(model)
    assert write_model(json.loads(text)) == text


@pytest.mark.parametrize("snippet", SNIPPETS)
@pytest.mark.parametrize("name", SEAM_GENERATORS)
def test_generator_meets_the_seam(name, snippet):
    check_seam(name, SEAM_GENERATORS[name](SNIPPETS[snippet]))


@pytest.mark.parametrize("snippet", SNIPPETS)
@pytest.mark.parametrize("name", SEAM_GENERATORS)
def test_generator_output_is_valid_against_its_schema(name, snippet):
    schema_path = SCHEMAS / f"{name}.schema.json"
    if not schema_path.exists():
        pytest.skip(f"{schema_path.name} is not written yet")
    import jsonschema

    jsonschema.validate(SEAM_GENERATORS[name](SNIPPETS[snippet]), json.loads(schema_path.read_text("utf-8")))


def element(element_id, **extra):
    # builds one valid element
    return {"id": element_id, "kind": "module", "file": "a.py", **extra}


@pytest.mark.parametrize(
    "model, error, match",
    [
        ({"nodes": [element("a"), element("a")]}, DriftError, "repeats the id a"),
        ({"nodes": [element("a")], "edges": [element("a")]}, DriftError, "repeats the id a"),
        ({"nodes": [element("b"), element("a")]}, AssertionError, "nodes is not sorted by id"),
        ({"nodes": [{"id": "a", "kind": "module"}]}, DriftError, "without a string id, kind and file"),
    ],
    ids=["duplicate id", "duplicate id across lists", "unsorted list", "missing file"],
)
def test_broken_fake_generator_fails_the_seam(model, error, match):
    with pytest.raises(error, match=match):
        check_seam("fake", model)
