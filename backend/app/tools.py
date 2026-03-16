import ast
import operator as op

notes_memory = []

# allowed operators for safe arithmetic
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):  # numbers
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Invalid constant")

    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError("Operator not allowed")

        return _ALLOWED_OPERATORS[operator_type](left, right)

    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        operator_type = type(node.op)

        if operator_type not in _ALLOWED_OPERATORS:
            raise ValueError("Unary operator not allowed")

        return _ALLOWED_OPERATORS[operator_type](operand)

    raise ValueError("Invalid expression")


def calculator(expression: str):
    """
    Safe arithmetic calculator.
    Supports +, -, *, /, //, %, **, parentheses, unary + and -.
    """
    try:
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval(parsed.body)
        return result
    except Exception:
        return "invalid expression"


def notes_store(text: str):
    notes_memory.append(text)
    return "note stored"


TOOLS = {
    "calculator": calculator,
    "notes_store": notes_store,
}