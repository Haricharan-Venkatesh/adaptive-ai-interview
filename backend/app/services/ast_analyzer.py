"""
AST-based Code Analysis Service.

Uses Python's built-in `ast` module to perform static analysis on candidate code submissions.
This complements the LLM-based analysis by providing deterministic metrics.
"""

import ast
from typing import Any


def analyze_code_ast(code: str) -> dict[str, Any]:
    """
    Perform static analysis on the given Python code.

    Returns a dictionary containing:
    - syntax_valid: bool
    - error_message: str (if syntax_valid is False)
    - functions: list of function names defined
    - classes: list of class names defined
    - imports: list of imported modules
    - num_nodes: total number of AST nodes (rough proxy for size/complexity)
    """
    result = {
        "syntax_valid": False,
        "error_message": None,
        "functions": [],
        "classes": [],
        "imports": [],
        "num_nodes": 0,
    }

    if not code or not code.strip():
        result["error_message"] = "Empty code submission."
        return result

    try:
        tree = ast.parse(code)
        result["syntax_valid"] = True
    except SyntaxError as e:
        result["error_message"] = str(e)
        return result

    # Count nodes
    result["num_nodes"] = sum(1 for _ in ast.walk(tree))

    # Extract definitions and imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result["imports"].append(node.module)

    return result
