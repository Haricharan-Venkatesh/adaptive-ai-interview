"""
Unit tests for the AST Code Analysis Service.
"""

from app.services.ast_analyzer import analyze_code_ast


def test_analyze_valid_code():
    code = """
import math
from typing import List

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
        
def main():
    c = Calculator()
    print(c.add(1, 2))
"""
    result = analyze_code_ast(code)
    
    assert result["syntax_valid"] is True
    assert result["error_message"] is None
    assert "Calculator" in result["classes"]
    assert "add" in result["functions"]
    assert "main" in result["functions"]
    assert "math" in result["imports"]
    assert "typing" in result["imports"]
    assert result["num_nodes"] > 10


def test_analyze_invalid_code():
    code = """
def add(a, b)
    return a + b
"""
    result = analyze_code_ast(code)
    
    assert result["syntax_valid"] is False
    assert "expected ':'" in result["error_message"] or "invalid syntax" in result["error_message"]
    assert result["functions"] == []


def test_analyze_empty_code():
    result = analyze_code_ast("")
    
    assert result["syntax_valid"] is False
    assert result["error_message"] == "Empty code submission."


def test_analyze_whitespace_only():
    result = analyze_code_ast("   \n  \t  ")
    
    assert result["syntax_valid"] is False
    assert result["error_message"] == "Empty code submission."
