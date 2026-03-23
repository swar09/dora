"""Type stub generator for dora-rs Python nodes.

This module provides utilities to automatically generate Python type stubs
(.pyi files) from Python modules. It utilizes the `inspect` module for
reflection and the `ast` module to construct the stub syntax tree.
"""

import argparse
import ast
import importlib
import inspect
import logging
import re
import subprocess
from collections.abc import Mapping
from functools import reduce
from typing import Any, Dict, List, Optional, Set, Tuple, Union


def path_to_type(*elements: str) -> ast.AST:
    """
    Builds an AST node representing a dotted type path from the given name components.
    
    Parameters:
        *elements (str): Name components in order (e.g., "typing", "List", "T") that form a dotted path.
    
    Returns:
        ast.AST: An AST node for the dotted path (an `ast.Name` for a single component or nested `ast.Attribute` nodes for multiple components).
    """
    base: ast.AST = ast.Name(id=elements[0], ctx=ast.Load())
    for e in elements[1:]:
        base = ast.Attribute(value=base, attr=e, ctx=ast.Load())
    return base


OBJECT_MEMBERS = dict(inspect.getmembers(object))
BUILTINS: Dict[str, Union[None, Tuple[List[ast.AST], ast.AST]]] = {
    "__annotations__": None,
    "__bool__": ([], path_to_type("bool")),
    "__bytes__": ([], path_to_type("bytes")),
    "__class__": None,
    "__contains__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__del__": None,
    "__delattr__": ([path_to_type("str")], path_to_type("None")),
    "__delitem__": ([path_to_type("typing", "Any")], path_to_type("typing", "Any")),
    "__dict__": None,
    "__dir__": None,
    "__doc__": None,
    "__eq__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__format__": ([path_to_type("str")], path_to_type("str")),
    "__ge__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__getattribute__": ([path_to_type("str")], path_to_type("typing", "Any")),
    "__getitem__": ([path_to_type("typing", "Any")], path_to_type("typing", "Any")),
    "__gt__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__hash__": ([], path_to_type("int")),
    "__init__": ([], path_to_type("None")),
    "__init_subclass__": None,
    "__iter__": ([], path_to_type("typing", "Any")),
    "__le__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__len__": ([], path_to_type("int")),
    "__lt__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__module__": None,
    "__ne__": ([path_to_type("typing", "Any")], path_to_type("bool")),
    "__new__": None,
    "__next__": ([], path_to_type("typing", "Any")),
    "__int__": ([], path_to_type("None")),
    "__reduce__": None,
    "__reduce_ex__": None,
    "__repr__": ([], path_to_type("str")),
    "__setattr__": (
        [path_to_type("str"), path_to_type("typing", "Any")],
        path_to_type("None"),
    ),
    "__setitem__": (
        [path_to_type("typing", "Any"), path_to_type("typing", "Any")],
        path_to_type("typing", "Any"),
    ),
    "__sizeof__": None,
    "__str__": ([], path_to_type("str")),
    "__subclasshook__": None,
}


def module_stubs(module: Any) -> ast.Module:
    """
    Generate an AST Module containing type stub definitions for the given importable module.
    
    Parameters:
        module (Any): The importable Python module to reflect and generate stubs from.
    
    Returns:
        ast.Module: An AST whose body begins with required import statements followed by generated class and function stub nodes.
    """
    types_to_import = {"typing"}
    classes = []
    functions = []
    for member_name, member_value in inspect.getmembers(module):
        element_path = [module.__name__, member_name]
        if member_name.startswith("__") or member_name.startswith("DoraStatus"):
            pass
        elif inspect.isclass(member_value):
            classes.append(
                class_stubs(member_name, member_value, element_path, types_to_import),
            )
        elif inspect.isbuiltin(member_value):
            functions.append(
                function_stub(
                    member_name,
                    member_value,
                    element_path,
                    types_to_import,
                    in_class=False,
                ),
            )
        else:
            logging.warning(f"Unsupported root construction {member_name}")
    return ast.Module(
        body=[ast.Import(names=[ast.alias(name=t)]) for t in sorted(types_to_import)]
        + classes
        + functions,
        type_ignores=[],
    )


def class_stubs(
    cls_name: str, cls_def: Any, element_path: List[str], types_to_import: Set[str],
) -> ast.ClassDef:
    """
    Generate an AST ClassDef representing type stubs for the given class.
    
    Parameters:
        cls_name (str): Name of the class.
        cls_def (Any): The runtime class object to inspect.
        element_path (List[str]): Dotted path segments locating the class inside the module.
        types_to_import (Set[str]): Mutable set to which required module import paths will be added.
    
    Returns:
        ast.ClassDef: An AST node for the class containing generated attributes, methods, magic methods, constants, and a cleaned docstring if present.
    """
    attributes: List[ast.AST] = []
    methods: List[ast.AST] = []
    magic_methods: List[ast.AST] = []
    constants: List[ast.AST] = []
    for member_name, member_value in inspect.getmembers(cls_def):
        current_element_path = [*element_path, member_name]
        if member_name == "__init__":
            try:
                inspect.signature(cls_def)  # we check it actually exists
                methods = [
                    function_stub(
                        member_name,
                        cls_def,
                        current_element_path,
                        types_to_import,
                        in_class=True,
                    ),
                    *methods,
                ]
            except ValueError as e:
                if "no signature found" not in str(e):
                    raise ValueError(
                        f"Error while parsing signature of {cls_name}.__init_",
                    ) from e
        elif (
            member_value == OBJECT_MEMBERS.get(member_name)
            or BUILTINS.get(member_name, ()) is None
        ):
            pass
        elif inspect.isdatadescriptor(member_value):
            attributes.extend(
                data_descriptor_stub(
                    member_name, member_value, current_element_path, types_to_import,
                ),
            )
        elif inspect.isroutine(member_value):
            (magic_methods if member_name.startswith("__") else methods).append(
                function_stub(
                    member_name,
                    member_value,
                    current_element_path,
                    types_to_import,
                    in_class=True,
                ),
            )
        elif member_name == "__match_args__":
            constants.append(
                ast.AnnAssign(
                    target=ast.Name(id=member_name, ctx=ast.Store()),
                    annotation=ast.Subscript(
                        value=path_to_type("tuple"),
                        slice=ast.Tuple(
                            elts=[path_to_type("str"), ast.Ellipsis()], ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    ),
                    value=ast.Constant(member_value),
                    simple=1,
                ),
            )
        elif member_value is not None:
            constants.append(
                ast.AnnAssign(
                    target=ast.Name(id=member_name, ctx=ast.Store()),
                    annotation=concatenated_path_to_type(
                        member_value.__class__.__name__, element_path, types_to_import,
                    ),
                    value=ast.Ellipsis(),
                    simple=1,
                ),
            )
        else:
            logging.warning(
                f"Unsupported member {member_name} of class {'.'.join(element_path)}",
            )

    doc = inspect.getdoc(cls_def)
    doc_comment = build_doc_comment(doc) if doc else None
    return ast.ClassDef(
        cls_name,
        bases=[],
        keywords=[],
        body=(
            ([doc_comment] if doc_comment else [])
            + attributes
            + methods
            + magic_methods
            + constants
        )
        or [ast.Ellipsis()],
        decorator_list=[path_to_type("typing", "final")],
    )


def data_descriptor_stub(
    data_desc_name: str,
    data_desc_def: Any,
    element_path: List[str],
    types_to_import: Set[str],
) -> Union[Tuple[ast.AnnAssign, ast.Expr], Tuple[ast.AnnAssign]]:
    """
    Create an AST stub for a data descriptor (an attribute), optionally extracting a return-type annotation and a cleaned docstring expression.
    
    Parameters:
        data_desc_name (str): The attribute name to use in the generated annotated assignment.
        data_desc_def (Any): The descriptor object whose docstring may contain return-type and `:return:` information.
        element_path (List[str]): Dotted path components leading to this descriptor (used for error messages and type resolution).
        types_to_import (Set[str]): Set that will be updated with module paths required by produced type AST nodes.
    
    Returns:
        tuple:
            - ast.AnnAssign: Annotated assignment for the attribute; annotation is derived from the descriptor docstring or `typing.Any` when absent.
            - ast.Expr (optional): A cleaned docstring expression produced from a single `:return:` doc line when present.
    
    Raises:
        ValueError: If multiple `:return:` entries are found in the descriptor's docstring.
    """
    annotation = None
    doc_comment = None

    doc = inspect.getdoc(data_desc_def)
    if doc is not None:
        annotation = returns_stub(data_desc_name, doc, element_path, types_to_import)
        m = re.findall(r"^ *:return: *(.*) *$", doc, re.MULTILINE)
        if len(m) == 1:
            doc_comment = m[0]
        elif len(m) > 1:
            raise ValueError(
                f"Multiple return annotations found with :return: in {'.'.join(element_path)} documentation",
            )

    assign = ast.AnnAssign(
        target=ast.Name(id=data_desc_name, ctx=ast.Store()),
        annotation=annotation or path_to_type("typing", "Any"),
        simple=1,
    )
    doc_comment = build_doc_comment(doc_comment) if doc_comment else None
    return (assign, doc_comment) if doc_comment else (assign,)


def function_stub(
    fn_name: str,
    fn_def: Any,
    element_path: List[str],
    types_to_import: Set[str],
    *,
    in_class: bool,
) -> ast.FunctionDef:
    """
    Create an AST FunctionDef representing a stub for a top-level function or a class method.
    
    Parameters:
        fn_name (str): Function or method name.
        fn_def (Any): The runtime callable object being reflected.
        element_path (List[str]): Dotted path segments used to resolve referenced types.
        types_to_import (Set[str]): Mutable set to record modules whose names must be imported for resolved types.
        in_class (bool): True when the stub is for a method defined on a class (affects decorators like `staticmethod`).
    
    Returns:
        ast.FunctionDef: An AST node describing the generated function or method stub.
    """
    body: List[ast.AST] = []
    doc = inspect.getdoc(fn_def)
    if doc is not None:
        doc_comment = build_doc_comment(doc)
        if doc_comment is not None:
            body.append(doc_comment)

    decorator_list = []
    if in_class and hasattr(fn_def, "__self__"):
        decorator_list.append(ast.Name("staticmethod"))

    return ast.FunctionDef(
        fn_name,
        arguments_stub(fn_name, fn_def, doc or "", element_path, types_to_import),
        body or [ast.Ellipsis()],
        decorator_list=decorator_list,
        returns=(
            returns_stub(fn_name, doc, element_path, types_to_import) if doc else None
        ),
        lineno=0,
    )


def arguments_stub(
    callable_name: str,
    callable_def: Any,
    doc: str,
    element_path: List[str],
    types_to_import: Set[str],
) -> ast.arguments:
    """
    Builds an ast.arguments node representing a callable's parameters by combining its runtime signature with types declared in the docstring.
    
    Parameters:
        callable_name (str): Name of the callable (used for builtin overrides like magic methods).
        callable_def (Any): The callable object whose signature is inspected.
        doc (str): Docstring text containing `:type <name>: <type>` annotations and `, optional` modifiers.
        element_path (List[str]): Path to the callable used in error messages and to resolve relative type names.
        types_to_import (Set[str]): Set that will be updated with module paths required by parsed type ASTs.
    
    Returns:
        ast.arguments: An AST arguments node with parameters annotated, defaults and kw defaults set, and var/kw varargs populated.
    
    Raises:
        ValueError: If a doc-declared parameter does not exist in the signature; if a signature parameter (other than `self`) lacks a type in the docstring; or if there is a mismatch between optional markers and default values.
    """
    real_parameters: Mapping[str, inspect.Parameter] = inspect.signature(
        callable_def,
    ).parameters
    if callable_name == "__init__":
        real_parameters = {
            "self": inspect.Parameter("self", inspect.Parameter.POSITIONAL_ONLY),
            **real_parameters,
        }

    parsed_param_types = {}
    optional_params = set()

    # Types for magic functions types
    builtin = BUILTINS.get(callable_name)
    if isinstance(builtin, tuple):
        param_names = list(real_parameters.keys())
        if param_names and param_names[0] == "self":
            del param_names[0]
        parsed_param_types = {name: t for name, t in zip(param_names, builtin[0])}

    # Types from comment
    for match in re.findall(
        r"^ *:type *([a-zA-Z0-9_]+): ([^\n]*) *$", doc, re.MULTILINE,
    ):
        if match[0] not in real_parameters:
            raise ValueError(
                f"The parameter {match[0]} of {'.'.join(element_path)} "
                "is defined in the documentation but not in the function signature",
            )
        type = match[1]
        if type.endswith(", optional"):
            optional_params.add(match[0])
            type = type[:-10]
        parsed_param_types[match[0]] = convert_type_from_doc(
            type, element_path, types_to_import,
        )

    # we parse the parameters
    posonlyargs = []
    args = []
    vararg = None
    kwonlyargs = []
    kw_defaults = []
    kwarg = None
    defaults = []
    for param in real_parameters.values():
        if param.name != "self" and param.name not in parsed_param_types:
            raise ValueError(
                f"The parameter {param.name} of {'.'.join(element_path)} "
                "has no type definition in the function documentation",
            )
        param_ast = ast.arg(
            arg=param.name, annotation=parsed_param_types.get(param.name),
        )

        default_ast = None
        if param.default != param.empty:
            default_ast = ast.Constant(param.default)
            if param.name not in optional_params:
                raise ValueError(
                    f"Parameter {param.name} of {'.'.join(element_path)} "
                    "is optional according to the type but not flagged as such in the doc",
                )
        elif param.name in optional_params:
            raise ValueError(
                f"Parameter {param.name} of {'.'.join(element_path)} "
                "is optional according to the documentation but has no default value",
            )

        if param.kind == param.POSITIONAL_ONLY:
            args.append(param_ast)
            # posonlyargs.append(param_ast)
            # defaults.append(default_ast)
        elif param.kind == param.POSITIONAL_OR_KEYWORD:
            args.append(param_ast)
            defaults.append(default_ast)
        elif param.kind == param.VAR_POSITIONAL:
            vararg = param_ast
        elif param.kind == param.KEYWORD_ONLY:
            kwonlyargs.append(param_ast)
            kw_defaults.append(default_ast)
        elif param.kind == param.VAR_KEYWORD:
            kwarg = param_ast

    return ast.arguments(
        posonlyargs=posonlyargs,
        args=args,
        vararg=vararg,
        kwonlyargs=kwonlyargs,
        kw_defaults=kw_defaults,
        defaults=defaults,
        kwarg=kwarg,
    )


def returns_stub(
    callable_name: str, doc: str, element_path: List[str], types_to_import: Set[str],
) -> Optional[ast.AST]:
    """
    Produce an AST node representing the callable's return type as declared in its docstring.
    
    Parameters:
        callable_name (str): The callable's short name used to consult built-in overrides.
        doc (str): The callable's docstring which may contain a single `:rtype:` directive.
        element_path (List[str]): Dotted path to the callable used in error messages and import resolution.
        types_to_import (Set[str]): Mutable set to record any module paths required by the produced AST.
    
    Returns:
        ast.AST: AST node representing the resolved return type.
    
    Raises:
        ValueError: If no `:rtype:` is found and there is no BUILTINS fallback, or if multiple `:rtype:` directives are present.
    """
    m = re.findall(r"^ *:rtype: *([^\n]*) *$", doc, re.MULTILINE)
    if len(m) == 0:
        builtin = BUILTINS.get(callable_name)
        if isinstance(builtin, tuple) and builtin[1] is not None:
            return builtin[1]
        raise ValueError(
            f"The return type of {'.'.join(element_path)} "
            "has no type definition using :rtype: in the function documentation",
        )
    if len(m) > 1:
        raise ValueError(
            f"Multiple return type annotations found with :rtype: for {'.'.join(element_path)}",
        )
    return convert_type_from_doc(m[0], element_path, types_to_import)


def convert_type_from_doc(
    type_str: str, element_path: List[str], types_to_import: Set[str],
) -> ast.AST:
    """
    Parse a type expression from a docstring into an AST type node and record any required imports.
    
    Parameters:
        type_str (str): Type expression extracted from a docstring (whitespace will be trimmed).
        element_path (List[str]): Module/class path used to resolve relative type names.
        types_to_import (Set[str]): Mutable set updated with module paths that must be imported for the resulting AST.
    
    Returns:
        ast.AST: An AST node representing the parsed type expression.
    
    Raises:
        ValueError: If the type expression is syntactically invalid or contains unsupported constructs.
    """
    type_str = type_str.strip()
    return parse_type_to_ast(type_str, element_path, types_to_import)


def parse_type_to_ast(
    type_str: str, element_path: List[str], types_to_import: Set[str],
) -> ast.AST:
    """
    Parse a textual type expression into an equivalent Python AST node.
    
    Supports dotted names, bracketed generic-like nesting (e.g. "Mapping[str, List[Foo]]"),
    and unions expressed with the token "or" (e.g. "A or B or C"). Adds any
    referenced module paths to `types_to_import` via `concatenated_path_to_type`.
    
    Parameters:
        type_str (str): The type expression to parse.
        element_path (List[str]): Path components identifying the element that uses
            this type (used only for error messages and import resolution).
        types_to_import (Set[str]): A mutable set that will be populated with
            module paths that must be imported to reference parsed types.
    
    Returns:
        ast.AST: An AST node representing the parsed type expression.
    
    Raises:
        ValueError: If the type expression is malformed or contains unknown/empty
            components that cannot be converted to an AST.
    """
    tokens = []
    current_token = ""
    for c in type_str:
        if "a" <= c <= "z" or "A" <= c <= "Z" or c == ".":
            current_token += c
        else:
            if current_token:
                tokens.append(current_token)
            current_token = ""
            if c != " ":
                tokens.append(c)
    if current_token:
        tokens.append(current_token)

    # let's first parse nested parenthesis
    stack: List[List[Any]] = [[]]
    for token in tokens:
        if token == "[":
            children: List[str] = []
            stack[-1].append(children)
            stack.append(children)
        elif token == "]":
            stack.pop()
        else:
            stack[-1].append(token)

    # then it's easy
    def parse_sequence(sequence: List[Any]) -> ast.AST:
        # we split based on "or"
        """
        Parse a token sequence into an AST representing a type expression.
        
        Parameters:
        	sequence (List[Any]): A flat list of tokens and nested lists where string tokens name types (e.g., "dora.Node"),
        		the special token "or" separates union members, and nested lists represent generic type arguments.
        
        Returns:
        	ast.AST: An AST node representing the parsed type expression. Unions are combined with `ast.BinOp(..., ast.BitOr(), ...)`
        		and parameterized/generic types are represented with `ast.Subscript`.
        
        Raises:
        	ValueError: If the sequence contains an empty union group or an otherwise unrecognizable structure.
        """
        or_groups: List[List[str]] = [[]]
        print(sequence)
        # TODO: Fix sequence
        if ("Ros" in sequence and "2" in sequence) or ("dora.Ros" in sequence and "2" in sequence):
            sequence = ["".join(sequence)]

        for e in sequence:
            if e == "or":
                or_groups.append([])
            else:
                or_groups[-1].append(e)
        if any(not g for g in or_groups):
            raise ValueError(
                f"Not able to parse type '{type_str}' used by {'.'.join(element_path)}",
            )

        new_elements: List[ast.AST] = []
        for group in or_groups:
            if len(group) == 1 and isinstance(group[0], str):
                new_elements.append(
                    concatenated_path_to_type(group[0], element_path, types_to_import),
                )
            elif (
                len(group) == 2
                and isinstance(group[0], str)
                and isinstance(group[1], list)
            ):
                new_elements.append(
                    ast.Subscript(
                        value=concatenated_path_to_type(
                            group[0], element_path, types_to_import,
                        ),
                        slice=parse_sequence(group[1]),
                        ctx=ast.Load(),
                    ),
                )
            else:
                raise ValueError(
                    f"Not able to parse type '{type_str}' used by {'.'.join(element_path)}",
                )
        return reduce(
            lambda left, right: ast.BinOp(left=left, op=ast.BitOr(), right=right),
            new_elements,
        )

    return parse_sequence(stack[0])


def concatenated_path_to_type(
    path: str, element_path: List[str], types_to_import: Set[str],
) -> ast.AST:
    """Convert a dotted path string into an AST type node and track imports.

    Args:
        path (str): The dotted path string (e.g., "dora.Node").
        element_path (List[str]): The path to the element being typed.
        types_to_import (Set[str]): Set of modules that need to be imported.

    Returns:
        ast.AST: The AST representing the type path.

    """
    parts = path.split(".")
    if any(not p for p in parts):
        raise ValueError(
            f"Not able to parse type '{path}' used by {'.'.join(element_path)}",
        )
    if len(parts) > 1:
        types_to_import.add(".".join(parts[:-1]))
    return path_to_type(*parts)


def build_doc_comment(doc: str) -> Optional[ast.Expr]:
    """
    Clean a docstring and return it as an AST expression suitable for a stub.
    
    Strips Sphinx-style directive lines starting with `:type` or `:rtype` and preserves the remaining lines.
    
    Parameters:
        doc (str): Raw docstring text.
    
    Returns:
        ast.Expr: An AST expression containing the cleaned docstring, or `None` if the cleaned text is empty.
    """
    lines = [line.strip() for line in doc.split("\n")]
    clean_lines = []
    for line in lines:
        if line.startswith((":type", ":rtype")):
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines).strip()
    return ast.Expr(value=ast.Constant(text)) if text else None


def format_with_ruff(file: str) -> None:
    """
    Format a Python source file using the Ruff formatter.
    
    Parameters:
        file (str): Path to the file to format.
    """
    subprocess.check_call(["python", "-m", "ruff", "format", file])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Python type stub from a python module.",
    )
    parser.add_argument(
        "module_name", help="Name of the Python module for which generate stubs",
    )
    parser.add_argument(
        "out",
        help="Name of the Python stub file to write to",
        type=argparse.FileType("wt"),
    )
    parser.add_argument(
        "--ruff", help="Formats the generated stubs using Ruff", action="store_true",
    )
    args = parser.parse_args()
    stub_content = ast.unparse(module_stubs(importlib.import_module(args.module_name)))
    args.out.write(stub_content)
    if args.ruff:
        format_with_ruff(args.out.name)
