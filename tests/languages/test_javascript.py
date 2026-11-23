# checks JavaScript through the same model entry points as Python

import json
from pathlib import Path

import jsonschema
import pytest

from models.behavioral_model import generate_behavioral
from models.common import ParseFailed, parse_files, write_model
from models.structural_model import generate_structural

SCHEMAS = Path(__file__).resolve().parents[2] / "Source" / "models"


def ids(model, kind):
    return {n["id"] for key in ("nodes", "edges") for n in model[key] if n["kind"] == kind}


def test_javascript_definitions_and_signatures():
    code = {"src/orders.js": "export class Order { async pay(amount, ...rest) {} cancel = (reason) => {}; } export const charge = async (amount=1) => amount;"}
    model = generate_structural(code)
    assert ids(model, "module") == {"./src/orders.js"}
    assert ids(model, "class") == {"./src/orders.js:Order"}
    assert ids(model, "method") == {"./src/orders.js:Order.pay", "./src/orders.js:Order.cancel"}
    pay = next(n for n in model["nodes"] if n["id"].endswith(":Order.pay"))
    assert pay["async"] is True and pay["params"] == ["amount", "...rest"]
    assert ids(model, "function") == {"./src/orders.js:charge"}


@pytest.mark.parametrize("extension", ["js", "mjs", "cjs", "jsx"])
def test_javascript_extensions(extension):
    assert ids(generate_structural({f"app.{extension}": "function run() {}"}), "function") == {f"./app.{extension}:run"}


def test_mixed_language_ids_do_not_collide():
    model = generate_structural({"src/app/js.py": "def python(): pass", "app.js": "function javascript() {}"})
    assert ids(model, "module") == {"app.js", "./app.js"}
    assert ids(model, "function") == {"app.js:python", "./app.js:javascript"}


@pytest.mark.parametrize("import_line", [
    "import {Base as Parent} from './base.js';",
    "import Parent from './base.js';",
    "const Parent = require('./base.js');",
])
def test_import_aliases_resolve_internal_inheritance(import_line):
    model = generate_structural({
        "base.js": "export default class Base {} export {Base}; module.exports = Base;",
        "order.js": import_line + " class Order extends Parent {}",
    })
    assert ids(model, "imports") == {"imports:./order.js->./base.js"}
    assert ids(model, "inherits") == {"inherits:./order.js:Order->./base.js:Base"}


def test_namespace_import_and_commonjs_destructuring():
    for code in ["import * as models from './base.js'; class Order extends models.Base {}", "const {Base: Parent} = require('./base.js'); class Order extends Parent {}"]:
        result = generate_structural({"base.js": "export class Base {}", "order.js": code})
        assert ids(result, "inherits") == {"inherits:./order.js:Order->./base.js:Base"}


def test_external_imports_are_left_out():
    model = generate_structural({"app.js": "import React from 'react'; const fs = require('node:fs'); class A extends React.Component {}"})
    assert model["edges"] == []


def test_unique_extension_and_index_imports():
    model = generate_structural({"src/app.js": "import './helper'; import './package';", "src/helper.mjs": "", "src/package/index.js": ""})
    assert ids(model, "imports") == {"imports:./src/app.js->./src/helper.mjs", "imports:./src/app.js->./src/package/index.js"}


def test_ambiguous_extension_import_is_not_guessed():
    result = generate_structural({"app.js": "import './a';", "a.js": "", "a.mjs": ""})
    assert result["edges"] == []


def test_reexports_produce_module_edges():
    model = generate_structural({"api.js": "export function load(){}", "index.js": "export {load} from './api.js';"})
    assert ids(model, "imports") == {"imports:./index.js->./api.js"}


def test_anonymous_default_export_has_a_stable_name():
    model = generate_structural({"base.js": "export default class { run() {} }", "app.js": "import Base from './base.js'; class A extends Base {}"})
    assert "./base.js:default" in ids(model, "class")
    assert "inherits:./app.js:A->./base.js:default" in ids(model, "inherits")


def test_jsx_is_parsed_without_inventing_component_edges():
    result = generate_structural({"View.jsx": "import React from 'react'; export const View = ({name}) => <div>{name}</div>;"})
    assert ids(result, "function") == {"./View.jsx:View"}
    assert result["edges"] == []


def test_nested_definitions_are_left_out():
    result = generate_structural({"app.js": "function outer(){function inner(){} const nested=()=>{};} if(true){function hidden(){}}"})
    assert ids(result, "function") == {"./app.js:outer"}


def test_javascript_behavior_uses_the_existing_state_machine_shape():
    result = generate_behavioral({"order.js": "class Order { pay(){if(this.status === 'open'){console.log('paying');this.status='paid';}} ship(){if(this.status==='paid'){this.status='shipped';}} }"})
    assert len(result["states"]) == 3 and len(result["transitions"]) == 2
    assert {s["machine"] for s in result["states"]} == {"./order.js:Order"}
    assert {s["variable"] for s in result["states"]} == {"self.status"}


def test_javascript_negative_guard_clause():
    result = generate_behavioral({"order.js": "class Order { pay(){if(this.status!=='open')return;this.status='paid';} }"})
    assert len(result["transitions"]) == 1


def test_unknown_calls_are_behavioral_barriers():
    assert generate_behavioral({"order.js": "class Order { pay(){if(this.status==='open'){mutate();this.status='paid';}} }"})["transitions"] == []


def test_javascript_is_never_executed():
    result = generate_structural({"app.js": "throw new Error('must not run'); while(true){} function run(){}"})
    assert ids(result, "function") == {"./app.js:run"}


@pytest.mark.parametrize("source", ["function ( {", "const x = ;", "class A {"])
def test_invalid_javascript_fails_instead_of_emitting_a_partial_model(source):
    with pytest.raises(ParseFailed) as raised:
        parse_files({"bad.js": source})
    assert raised.value.path == "bad.js" and raised.value.line is not None


def test_mixed_parse_failures_are_reported_in_path_order():
    with pytest.raises(ParseFailed) as raised:
        parse_files({"a.py": "def (", "z.js": "const x = ;"})
    assert raised.value.path == "a.py"


def test_formatting_and_file_order_are_stable():
    first = {"base.js": "export class Base {}", "app.js": "import {Base} from './base.js'; class A extends Base{run(x){}}"}
    second = {"app.js": "// comment\nimport { Base } from \"./base.js\"; class A extends Base { run( x ) { } }", "base.js": "export class Base { }"}
    assert write_model(generate_structural(first)) == write_model(generate_structural(second))


@pytest.mark.parametrize("name,generate", [("structural", generate_structural), ("behavioral", generate_behavioral)])
def test_javascript_output_validates_against_the_unchanged_schema(name, generate):
    result = generate({"a.js": "class A {go(){if(this.state==='a')this.state='b';}}"})
    jsonschema.validate(result, json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8")))

