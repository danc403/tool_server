# calculator.py
import json
import asyncio
import math
import ast

async def calculate_expression(expression: str) -> dict:
    """
    Evaluates a mathematical expression safely and returns the result.

    This tool is designed for performing precise arithmetic and mathematical operations
    using a secure expression evaluator, ensuring accuracy and handling common math functions.
    It supports standard arithmetic operators (+, -, *, /, %, **), parentheses,
    and common mathematical functions from Python's 'math' module (e.g., sin(), cos(), sqrt(), log()).

    Args:
        expression (str): The mathematical expression to evaluate.
                          Example: "(5 + 3) * (10 / 2) - sqrt(25)"
                          Note: You can use math functions directly (e.g., 'sqrt(25)' instead of 'math.sqrt(25)').

    Returns:
        dict: A dictionary representing the JSON response.

        On **success**:
        ```json
        {
          "status": "success",
          "data": {
            "expression": "(5 + 3) * (10 / 2) - sqrt(25)",
            "result": 35.0
          }
        }
        ```

        On **failure**:
        ```json
        {
          "status": "error",
          "message": "A descriptive error message."
        }
        ```
    """
    try:
        # A tiny async pause for compatibility with the server's await call
        await asyncio.sleep(0.01)

        if not isinstance(expression, str) or not expression.strip():
            return {"status": "error", "message": "Mathematical expression cannot be empty."}

        # 1. Create a whitelist of allowed functions and constants from the math module
        allowed_names = {
            "__builtins__": {} # Remove all default Python built-ins (no import, no open, etc.)
        }
        
        for name in dir(math):
            if not name.startswith('_'):
                obj = getattr(math, name)
                allowed_names[name] = obj

        # 2. Add standard arithmetic power if needed (math.pow is already there, but ** is handled by eval)
        
        # 3. Security Check: Validate that the expression is a pure expression and not a statement
        # This prevents things like 'x = 5' or multi-line code.
        try:
            node = ast.parse(expression, mode='eval')
        except SyntaxError:
            return {"status": "error", "message": "Invalid syntax in mathematical expression."}

        # 4. Evaluate in a restricted environment
        # We use the whitelist as both globals and locals
        result = eval(expression, allowed_names, allowed_names)

        # Ensure the result is a number. 
        if not isinstance(result, (int, float, complex)):
             return {"status": "error", "message": "Expression evaluation resulted in a non-numeric type."}

        # Convert complex numbers to string or handle them, otherwise JSON serializing will fail
        if isinstance(result, complex):
            result = str(result)

        return {
            "status": "success",
            "data": {
                "expression": expression,
                "result": result
            }
        }
        
    except ZeroDivisionError:
        return {"status": "error", "message": "Division by zero is not allowed."}
    except Exception as e:
        # Catch any other unexpected errors (Overflow, ValueErrors for log(-1), etc.)
        return {"status": "error", "message": f"Error evaluating expression: {str(e)}"}

async def calculator(expression: str) -> str:
    """
    Performs mathematical calculations. Supports arithmetic and math functions like sqrt, sin, and log.

    Args:
        expression (str): The math expression to solve. (e.g. '2 + 2' or 'sqrt(16)')

    Returns:
        str: A JSON string containing the result or error message.
    """
    result = await calculate_expression(expression)
    return json.dumps(result, indent=2)
