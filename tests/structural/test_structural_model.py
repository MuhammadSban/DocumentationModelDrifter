# tests the structural generator against the rules agreed for structural.json

import pytest

from models.common import ParseFailed, write_model
from models.structural_model import generate_structural, module_id

SHOP = {
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
}


def ids(model, kind=None):
    # lists the ids of the model's nodes and edges, optionally of one kind
    return [e["id"] for e in model["nodes"] + model["edges"] if kind in (None, e["kind"])]


def node(model, node_id):
    # finds one node by id
    return next(n for n in model["nodes"] if n["id"] == node_id)


def test_shop_example():
    def method(path, node_id, kind, params):
        return {"async": False, "decorators": [], "file": path, "id": node_id, "kind": kind,
                "params": params}

    assert generate_structural(SHOP) == {
        "edges": [
            {"file": "src/shop/orders.py", "id": "imports:shop.orders->shop.models",
             "kind": "imports", "source": "shop.orders", "target": "shop.models"},
            {"file": "src/shop/orders.py", "id": "imports:shop.orders->shop.payments",
             "kind": "imports", "source": "shop.orders", "target": "shop.payments"},
            {"file": "src/shop/orders.py", "id": "inherits:shop.orders:Order->shop.models:Base",
             "kind": "inherits", "source": "shop.orders:Order", "target": "shop.models:Base"},
        ],
        "nodes": [
            {"file": "src/shop/__init__.py", "id": "shop", "kind": "module"},
            {"file": "src/shop/models.py", "id": "shop.models", "kind": "module"},
            {"file": "src/shop/models.py", "id": "shop.models:Base", "kind": "class"},
            method("src/shop/models.py", "shop.models:Base.save", "method", ["self"]),
            {"file": "src/shop/orders.py", "id": "shop.orders", "kind": "module"},
            {"file": "src/shop/orders.py", "id": "shop.orders:Order", "kind": "class"},
            method("src/shop/orders.py", "shop.orders:Order.cancel", "method", ["self", "reason"]),
            {"file": "src/shop/payments.py", "id": "shop.payments", "kind": "module"},
            method("src/shop/payments.py", "shop.payments:charge", "function",
                   ["amount", "*", "currency"]),
        ],
        "schema_version": 1,
    }


@pytest.mark.parametrize("path, expected", [
    ("src/shop/orders.py", "shop.orders"),
    ("shop/orders.py", "shop.orders"),
    ("src/shop/__init__.py", "shop"),
    ("tool.py", "tool"),
    ("__init__.py", "__init__"),
    ("src/__init__.py", "src"),
])
def test_module_ids(path, expected):
    assert module_id(path) == expected


def test_src_init_and_root_init_get_distinct_ids():
    # checks neither node is lost, both ids were once __init__
    model = generate_structural({"__init__.py": "X=1\n", "src/__init__.py": "Y=1\n"})
    assert ids(model) == ["__init__", "src"]


def test_nested_classes_and_their_methods():
    model = generate_structural({"m.py": (
        "class Outer:\n"
        "    class Inner:\n"
        "        def go(self): ...\n"
    )})
    assert ids(model) == ["m", "m:Outer", "m:Outer.Inner", "m:Outer.Inner.go"]
    assert node(model, "m:Outer.Inner.go")["kind"] == "method"


def test_definitions_in_blocks_and_functions_are_left_out():
    model = generate_structural({"m.py": (
        "def outer():\n"
        "    def inner(): ...\n"
        "if True:\n"
        "    def hidden(): ...\n"
        "try:\n"
        "    class Hidden: ...\n"
        "except ImportError:\n"
        "    pass\n"
        "if __name__ == '__main__':\n"
        "    def main(): ...\n"
    )})
    assert ids(model) == ["m", "m:outer"]


def test_name_defined_twice_keeps_last_definition():
    model = generate_structural({"m.py": (
        "class A:\n"
        "    def old(self): ...\n"
        "class A:\n"
        "    def new(self): ...\n"
        "def f(a): ...\n"
        "def f(a, b): ...\n"
    )})
    assert ids(model) == ["m", "m:A", "m:A.new", "m:f"]
    assert node(model, "m:f")["params"] == ["a", "b"]


@pytest.mark.parametrize("signature, params", [
    ("def f(): ...", []),
    ("def f(a, /, b, *args, c, **kw): ...", ["a", "/", "b", "*args", "c", "**kw"]),
    ("def f(a, *, b=1): ...", ["a", "*", "b"]),
    ("def f(a: int = 1, b: str = 'x'): ...", ["a", "b"]),
])
def test_params(signature, params):
    assert node(generate_structural({"m.py": signature + "\n"}), "m:f")["params"] == params


def test_decorators_and_async():
    model = generate_structural({"m.py": (
        "@app.get('/x')\n"
        "@cache\n"
        "async def f(): ...\n"
    )})
    assert node(model, "m:f")["decorators"] == ["app.get", "cache"]
    assert node(model, "m:f")["async"] is True


def test_relative_imports():
    model = generate_structural({
        "pkg/__init__.py": "from . import a\n",
        "pkg/a.py": "from .b import X\n",
        "pkg/b.py": "class X: ...\n",
        "pkg/sub/__init__.py": "",
        "pkg/sub/c.py": "from .. import b\nfrom ..a import thing\n",
    })
    assert ids(model, "imports") == [
        "imports:pkg->pkg.a",
        "imports:pkg.a->pkg.b",
        "imports:pkg.sub.c->pkg.a",
        "imports:pkg.sub.c->pkg.b",
    ]


def test_external_imports_are_dropped():
    model = generate_structural({"m.py": "import os\nfrom typing import Any\nimport json as j\n"})
    assert ids(model, "imports") == []


def test_same_import_twice_is_one_edge():
    model = generate_structural({
        "a.py": "import b\n\ndef f():\n    import b\n",
        "b.py": "",
    })
    assert ids(model, "imports") == ["imports:a->b"]


@pytest.mark.parametrize("code", [
    "from shop.models import Base\nclass Order(Base): ...\n",
    "from shop.models import Base as B\nclass Order(B): ...\n",
    "from shop import models\nclass Order(models.Base): ...\n",
    "import shop.models as m\nclass Order(m.Base): ...\n",
    "import shop.models\nclass Order(shop.models.Base): ...\n",
])
def test_inherits_through_imports_and_aliases(code):
    model = generate_structural({**SHOP, "src/shop/orders.py": code})
    assert "inherits:shop.orders:Order->shop.models:Base" in ids(model, "inherits")


def test_inherits_within_one_module_and_nested():
    model = generate_structural({"m.py": (
        "class A: ...\n"
        "class B(A): ...\n"
        "class Outer:\n"
        "    class Inner: ...\n"
        "class C(Outer.Inner): ...\n"
    )})
    assert ids(model, "inherits") == ["inherits:m:B->m:A", "inherits:m:C->m:Outer.Inner"]


def test_external_bases_are_dropped():
    model = generate_structural({"m.py": (
        "import enum\n"
        "class E(ValueError): ...\n"
        "class S(enum.Enum): ...\n"
        "class G(list[int]): ...\n"
    )})
    assert ids(model, "inherits") == []


def test_calls_are_not_modelled():
    assert ids(generate_structural(SHOP), "calls") == []


def test_comments_and_whitespace_change_nothing():
    noisy = {**SHOP, "src/shop/orders.py": (
        "# orders\n"
        "from shop.models import Base\n\n\n"
        "from shop import payments  # pay\n"
        "\n\n"
        "class Order( Base ):\n"
        "    '''An order.'''\n\n"
        "    def cancel(self,   reason=None):\n"
        "        # cancel it\n"
        "        payments.charge( 0 )\n"
    )}
    assert write_model(generate_structural(noisy)) == write_model(generate_structural(SHOP))


def test_file_order_changes_nothing():
    reversed_shop = dict(reversed(list(SHOP.items())))
    assert write_model(generate_structural(reversed_shop)) == write_model(generate_structural(SHOP))


def test_bad_file_fails_the_whole_model():
    with pytest.raises(ParseFailed) as err:
        generate_structural({**SHOP, "src/shop/broken.py": "def (\n"})
    assert err.value.path == "src/shop/broken.py"
