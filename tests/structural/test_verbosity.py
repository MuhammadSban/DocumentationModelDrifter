# freezes the verbosity ladder of scope.json's verbosity key: what each level of the structural
# model holds, that each level is a subset of the one above it, and that the default is byte for
# byte what the generator wrote before the key existed (E02)

import pytest

from models.common import write_model
from models.structural_model import (
    FULL,
    KEPT_KINDS,
    MEMBERS,
    OVERVIEW,
    TYPES,
    generate_structural,
)

# one small repository holding every kind and both edge kinds: two modules, one importing the
# other, and a class that extends a class of this repository
CODE = {
    "src/shop/models.py": "class Base:\n    def save(self, force=False):\n        pass\n",
    "src/shop/orders.py": (
        "import asyncio\n"
        "from shop.models import Base\n"
        "\n"
        "class Order(Base):\n"
        "    @property\n"
        "    def total(self):\n"
        "        return 0\n"
        "\n"
        "    async def cancel(self, reason, *, force=False):\n"
        "        pass\n"
        "\n"
        "def charge(amount, /, currency='GBP'):\n"
        "    return amount\n"
    ),
}

LEVELS = (OVERVIEW, TYPES, MEMBERS, FULL)


def kinds(model):
    # the node kinds one model holds, as a set, so a level is judged by what it describes
    return {node["kind"] for node in model["nodes"]}


def ids(model):
    # every element id of one model, nodes and edges together, for the subset comparison
    return {element["id"] for value in model.values() if isinstance(value, list) for element in value}


def test_the_default_is_what_the_generator_wrote_before_verbosity_existed():
    # the one promise the whole feature rests on: a repository that commits no key sees no change,
    # so no committed model and no golden moves
    assert write_model(generate_structural(CODE)) == write_model(generate_structural(CODE, FULL))


def test_each_level_is_a_subset_of_the_level_above_it():
    # the ladder is a ladder: a level adds to the level below and never swaps one thing for another
    for lower, higher in zip(LEVELS, LEVELS[1:]):
        assert ids(generate_structural(CODE, lower)) <= ids(generate_structural(CODE, higher))


def test_overview_holds_the_modules_and_the_imports_between_them():
    model = generate_structural(CODE, OVERVIEW)
    assert kinds(model) == {"module"}
    assert [edge["id"] for edge in model["edges"]] == ["imports:shop.orders->shop.models"]


def test_types_adds_the_classes_and_the_inheritance():
    model = generate_structural(CODE, TYPES)
    assert kinds(model) == {"module", "class"}
    assert "inherits:shop.orders:Order->shop.models:Base" in ids(model)


def test_members_adds_the_functions_and_methods_without_their_signatures():
    model = generate_structural(CODE, MEMBERS)
    assert kinds(model) == {"module", "class", "function", "method"}
    charge = next(node for node in model["nodes"] if node["id"] == "shop.orders:charge")
    assert set(charge) == {"file", "id", "kind"}


def test_full_adds_the_signatures():
    charge = next(
        node
        for node in generate_structural(CODE, FULL)["nodes"]
        if node["id"] == "shop.orders:charge"
    )
    assert charge["params"] == ["amount", "/", "currency"]
    assert charge["async"] is False
    cancel = next(
        node
        for node in generate_structural(CODE, FULL)["nodes"]
        if node["id"] == "shop.orders:Order.cancel"
    )
    assert cancel["async"] is True
    assert cancel["params"] == ["self", "reason", "*", "force"]


def test_every_level_sorts_its_lists_and_pins_the_schema_version():
    # the seam's rules hold at every level, not only at the default (model-seam.md)
    for level in LEVELS:
        model = generate_structural(CODE, level)
        assert model["schema_version"] == 1
        for value in model.values():
            if isinstance(value, list):
                assert value == sorted(value, key=lambda element: element["id"])


def test_a_level_outside_the_ladder_is_refused():
    # the core validates the committed value, and the generator refuses one that got past it
    for bad in (0, 5, "high", None):
        with pytest.raises(ValueError):
            generate_structural(CODE, bad)


def test_the_ladder_covers_every_level_it_names():
    # KEPT_KINDS and the four names stay in step, so a fifth level cannot be half-added
    assert sorted(KEPT_KINDS) == sorted(LEVELS)
