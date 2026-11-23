# parses JavaScript into the syntax subset the existing model generators read, never executable code

from __future__ import annotations

import ast
import posixpath
from functools import lru_cache

from models.common import JAVASCRIPT_EXTENSIONS as EXTENSIONS, ParseFailed

FUNCTIONS = {"function_declaration", "generator_function_declaration", "function_expression", "generator_function", "arrow_function"}
CLASSES = {"class_declaration", "class"}


@lru_cache(maxsize=1)
def _language():
    # shares the immutable grammar, keeping each parser local to its call
    from tree_sitter import Language
    import tree_sitter_javascript

    return Language(tree_sitter_javascript.language())


def parse_javascript(path: str, source: str):
    # rejects error recovery trees, so malformed JavaScript never becomes a partial model
    try:
        from tree_sitter import Parser

        tree = Parser(_language()).parse(source.encode("utf-8"))
    except ImportError:
        raise ParseFailed(path, None, "JavaScript requires tree-sitter==0.25.2 and tree-sitter-javascript==0.25.0") from None
    if tree.root_node.has_error:
        pending = [tree.root_node]
        while pending:
            node = pending.pop()
            if node.is_error or node.is_missing:
                raise ParseFailed(path, node.start_point.row + 1, "invalid JavaScript syntax")
            pending.extend(reversed(node.children))
        raise ParseFailed(path, 1, "invalid JavaScript syntax")
    return tree


def lower_javascript(trees: dict) -> dict[str, ast.Module]:
    # indexes direct exports before imports, leaving Python trees untouched
    javascript = {path: tree for path, tree in trees.items() if path.endswith(EXTENSIONS)}
    exports = {path: _exports(tree.root_node) for path, tree in javascript.items()}
    return {
        path: ast.Module(body=_Lower(path, javascript, exports).statements(tree.root_node.named_children), type_ignores=[])
        for path, tree in javascript.items()
    }


def _text(node) -> str:
    return node.text.decode("utf-8") if node is not None else ""


def _string(node) -> str | None:
    # decodes literal JavaScript strings without evaluating any expression
    if node is None or node.type != "string":
        return None
    text = _text(node)[1:-1]
    out, index = [], 0
    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
    while index < len(text):
        char = text[index]
        index += 1
        if char != "\\":
            out.append(char)
            continue
        if index == len(text):
            return None
        char = text[index]
        index += 1
        if char in "\r\n":
            if char == "\r" and text[index:index + 1] == "\n":
                index += 1
            continue
        if char in ("u", "x"):
            end = index + (4 if char == "u" else 2)
            if char == "u" and text[index:index + 1] == "{":
                end = text.find("}", index + 1)
                if end == -1:
                    return None
                digits = text[index + 1:end]
                end += 1
            else:
                digits = text[index:end]
            try:
                out.append(chr(int(digits, 16)))
            except (ValueError, OverflowError):
                return None
            index = end
        else:
            out.append(escapes.get(char, char))
    value = "".join(out)
    try:
        return value.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    except UnicodeDecodeError:
        return None


def _compact(node) -> str:
    # normalizes pattern spacing while preserving literal contents
    if node.type == "comment":
        return ""
    if node.type == "string":
        return repr(_string(node))
    if not node.children:
        return _text(node)
    return "".join(_compact(child) for child in node.children)


def _exports(root) -> dict[str, str]:
    # resolves direct named/default export aliases, without following re-export chains
    found = {}
    for node in root.named_children:
        if node.type == "export_statement" and node.child_by_field_name("source") is None:
            declaration = node.child_by_field_name("declaration") or node.child_by_field_name("value")
            default = any(child.type == "default" for child in node.children)
            if declaration is not None:
                name = _text(declaration.child_by_field_name("name"))
                if default:
                    found["default"] = name or ("default" if declaration.type in FUNCTIONS | CLASSES else _text(declaration))
                elif declaration.type in FUNCTIONS | CLASSES and name:
                    found[name] = name
                elif declaration.type in ("lexical_declaration", "variable_declaration"):
                    for item in declaration.named_children:
                        name = _text(item.child_by_field_name("name"))
                        found[name] = name
            for clause in node.named_children:
                if clause.type == "export_clause":
                    for item in clause.named_children:
                        name = _text(item.child_by_field_name("name"))
                        alias = _text(item.child_by_field_name("alias")) or name
                        found[alias] = name
        elif node.type == "expression_statement" and node.named_children:
            assignment = node.named_children[0]
            if assignment.type != "assignment_expression":
                continue
            left = _text(assignment.child_by_field_name("left"))
            right = assignment.child_by_field_name("right")
            if right is not None and right.type == "identifier":
                if left == "module.exports":
                    found["default"] = _text(right)
                elif left.startswith(("exports.", "module.exports.")):
                    found[left.rsplit(".", 1)[1]] = _text(right)
    return found


class _Lower:
    def __init__(self, path, trees, exports):
        self.path = path
        self.paths = trees
        self.exports = exports

    def resolve(self, source):
        # accepts relative in-scope files only, never package installation or ambiguous guesses
        if not source or not source.startswith(("./", "../")) or "?" in source or "#" in source:
            return None
        target = posixpath.normpath(posixpath.join(posixpath.dirname(self.path), source))
        if target.startswith("../") or target.startswith("/"):
            return None
        if target in self.paths:
            return target
        candidates = {target + ext for ext in EXTENSIONS} | {target + "/index" + ext for ext in EXTENSIONS}
        matches = sorted(candidates & self.paths.keys())
        return matches[0] if len(matches) == 1 else None

    def imports(self, target, binding=None, clause=None):
        # represents imports using the existing import resolver's module and definition bindings
        module = "./" + target
        exports = self.exports[target]
        aliases = []
        if binding is not None:
            if binding.type == "identifier":
                name = exports.get("default")
                if name:
                    aliases.append(ast.alias(name=name, asname=_text(binding)))
                else:
                    return [ast.Import(names=[ast.alias(name=module, asname=_text(binding))])]
            elif binding.type == "object_pattern":
                for item in binding.named_children:
                    name = item.child_by_field_name("key") if item.type == "pair_pattern" else item
                    local = item.child_by_field_name("value") if item.type == "pair_pattern" else item
                    if name is not None and local is not None and local.type in ("identifier", "shorthand_property_identifier_pattern"):
                        exported = _string(name) if name.type == "string" else _text(name)
                        aliases.append(ast.alias(name=exports.get(exported, exported), asname=_text(local)))
        if clause is not None:
            for item in clause.named_children:
                if item.type == "identifier":
                    aliases.append(ast.alias(name=exports.get("default", "default"), asname=_text(item)))
                elif item.type == "namespace_import":
                    return [ast.Import(names=[ast.alias(name=module, asname=_text(item.named_children[0]))])]
                elif item.type == "named_imports":
                    for spec in item.named_children:
                        if spec.type != "import_specifier":
                            continue
                        name = spec.child_by_field_name("name")
                        exported = _string(name) if name.type == "string" else _text(name)
                        local = _text(spec.child_by_field_name("alias")) or exported
                        aliases.append(ast.alias(name=exports.get(exported, exported), asname=local))
        if aliases:
            return [ast.ImportFrom(module=module, names=aliases, level=0)]
        return [ast.Import(names=[ast.alias(name=module, asname=None)])]

    def require(self, node):
        # recognizes literal CommonJS require calls only
        if node is None or node.type != "call_expression" or _text(node.child_by_field_name("function")) != "require":
            return None
        args = node.child_by_field_name("arguments")
        if args is None or len(args.named_children) != 1:
            return None
        return self.resolve(_string(args.named_children[0]))

    def statements(self, nodes):
        result = []
        for node in nodes:
            result.extend(self.statement(node))
        return result

    def body(self, node):
        if node is None:
            return []
        if node.type in ("statement_block", "class_body", "else_clause", "finally_clause"):
            return self.statements(node.named_children)
        return self.statement(node)

    def function(self, node, name):
        params = node.child_by_field_name("parameters")
        params = list(params.named_children) if params is not None else [node.child_by_field_name("parameter")]
        args = []
        for parameter in params:
            if parameter is None or parameter.type == "comment":
                continue
            if parameter.type == "assignment_pattern":
                parameter = parameter.child_by_field_name("left")
            args.append(ast.arg(arg=_compact(parameter)))
        body = node.child_by_field_name("body")
        statements = self.body(body) if body is not None and body.type == "statement_block" else [ast.Return(value=self.expression(body))]
        kind = ast.AsyncFunctionDef if any(child.type == "async" for child in node.children) else ast.FunctionDef
        return kind(name=name, args=ast.arguments(posonlyargs=[], args=args, vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
                    body=statements, decorator_list=[], returns=None, type_comment=None, type_params=[])

    def class_(self, node, name):
        heritage = next((child for child in node.named_children if child.type == "class_heritage"), None)
        bases = [self.expression(heritage.named_children[0])] if heritage is not None else []
        body = node.child_by_field_name("body")
        members = []
        if body is not None:
            for item in body.named_children:
                label = item.child_by_field_name("name") or item.child_by_field_name("property")
                if label is None or label.type not in ("property_identifier", "private_property_identifier", "identifier"):
                    continue
                if item.type == "method_definition":
                    members.append(self.function(item, _text(label)))
                elif item.type == "field_definition":
                    value = item.child_by_field_name("value")
                    if value is not None and value.type in FUNCTIONS:
                        members.append(self.function(value, _text(label)))
        return ast.ClassDef(name=name, bases=bases, keywords=[], body=members, decorator_list=[], type_params=[])

    def statement(self, node):
        kind = node.type
        if kind in ("comment", "empty_statement"):
            return [ast.Pass()]
        if kind == "export_statement":
            declaration = node.child_by_field_name("declaration") or node.child_by_field_name("value")
            if declaration is not None:
                if declaration.type in FUNCTIONS:
                    return [self.function(declaration, _text(declaration.child_by_field_name("name")) or "default")]
                if declaration.type in CLASSES:
                    return [self.class_(declaration, _text(declaration.child_by_field_name("name")) or "default")]
                return self.statement(declaration)
            target = self.resolve(_string(node.child_by_field_name("source")))
            return self.imports(target) if target else []
        if kind == "import_statement":
            target = self.resolve(_string(node.child_by_field_name("source")))
            clause = next((child for child in node.named_children if child.type == "import_clause"), None)
            return self.imports(target, clause=clause) if target else []
        if kind in FUNCTIONS:
            name = _text(node.child_by_field_name("name"))
            return [self.function(node, name)] if name else [self.unknown()]
        if kind in CLASSES:
            name = _text(node.child_by_field_name("name"))
            return [self.class_(node, name)] if name else [self.unknown()]
        if kind in ("lexical_declaration", "variable_declaration"):
            return self.statements(node.named_children)
        if kind == "variable_declarator":
            name, value = node.child_by_field_name("name"), node.child_by_field_name("value")
            if name is not None and name.type == "identifier" and value is not None:
                if value.type in FUNCTIONS:
                    return [self.function(value, _text(name))]
                if value.type in CLASSES:
                    return [self.class_(value, _text(name))]
            target = self.require(value)
            if target:
                return self.imports(target, binding=name)
            return [ast.Assign(targets=[self.expression(name)], value=self.expression(value))]
        if kind == "expression_statement":
            value = node.named_children[0]
            target = self.require(value)
            if target:
                return self.imports(target)
            if value.type == "assignment_expression":
                return [ast.Assign(targets=[self.expression(value.child_by_field_name("left"))], value=self.expression(value.child_by_field_name("right")))]
            return [ast.Expr(value=self.expression(value))]
        if kind == "if_statement":
            return [ast.If(test=self.expression(node.child_by_field_name("condition")),
                           body=self.body(node.child_by_field_name("consequence")), orelse=self.body(node.child_by_field_name("alternative")))]
        if kind == "return_statement":
            return [ast.Return(value=self.expression(node.named_children[0]) if node.named_children else None)]
        if kind == "throw_statement":
            return [ast.Raise(exc=self.expression(node.named_children[0]), cause=None)]
        if kind == "break_statement":
            return [ast.Break()]
        if kind == "continue_statement":
            return [ast.Continue()]
        if kind in ("for_statement", "for_in_statement", "while_statement", "do_statement"):
            return [ast.While(test=ast.Name(id="__javascript_loop__", ctx=ast.Load()), body=self.body(node.child_by_field_name("body")), orelse=[])]
        if kind == "try_statement":
            handler = node.child_by_field_name("handler")
            handlers = [ast.ExceptHandler(type=None, name=None, body=self.body(handler.child_by_field_name("body")))] if handler else []
            return [ast.Try(body=self.body(node.child_by_field_name("body")), handlers=handlers, orelse=[], finalbody=self.body(node.child_by_field_name("finalizer")))]
        if kind == "statement_block":
            return [ast.If(test=ast.Name(id="__javascript_block__", ctx=ast.Load()), body=self.body(node), orelse=[])]
        return [self.unknown()]

    def expression(self, node):
        if node is None:
            return self.unknown().value
        kind = node.type
        if kind == "parenthesized_expression" and node.named_children:
            return self.expression(node.named_children[0])
        if kind in ("identifier", "property_identifier", "shorthand_property_identifier_pattern"):
            return ast.Name(id=_text(node), ctx=ast.Load())
        if kind == "this":
            return ast.Name(id="self", ctx=ast.Load())
        if kind == "string":
            return ast.Constant(value=_string(node))
        if kind in ("true", "false", "null", "undefined"):
            return ast.Constant(value={"true": True, "false": False}.get(kind))
        if kind == "number":
            try:
                return ast.Constant(value=float(_text(node).replace("_", "")))
            except ValueError:
                return self.unknown().value
        if kind == "member_expression" and not any(c.type == "optional_chain" for c in node.children):
            return ast.Attribute(value=self.expression(node.child_by_field_name("object")), attr=_text(node.child_by_field_name("property")), ctx=ast.Load())
        if kind == "subscript_expression":
            return ast.Subscript(value=self.expression(node.child_by_field_name("object")), slice=self.expression(node.child_by_field_name("index")), ctx=ast.Load())
        if kind == "binary_expression":
            operator = _text(node.child_by_field_name("operator"))
            if operator in ("===", "==", "!==", "!="):
                return ast.Compare(left=self.expression(node.child_by_field_name("left")), ops=[ast.Eq() if operator in ("===", "==") else ast.NotEq()],
                                   comparators=[self.expression(node.child_by_field_name("right"))])
        if kind == "unary_expression" and _text(node.child_by_field_name("operator")) == "!":
            return ast.UnaryOp(op=ast.Not(), operand=self.expression(node.child_by_field_name("argument")))
        if kind == "call_expression":
            function = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            target = ast.Name(id="log", ctx=ast.Load()) if _text(function) == "console.log" else self.expression(function)
            return ast.Call(func=target, args=[self.expression(arg) for arg in args.named_children if arg.type != "comment"] if args else [], keywords=[])
        return self.unknown().value

    @staticmethod
    def unknown():
        # preserves unsupported effects as a barrier for the behavioral miner
        return ast.Expr(value=ast.Call(func=ast.Name(id="__javascript_unknown__", ctx=ast.Load()), args=[], keywords=[]))

