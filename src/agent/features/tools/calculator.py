from google.genai import types

from agent.core.tool_registry import Tool, ToolContext


def calculator(ctx: ToolContext, expression: str):

    # Learning-only implementation.
    # eval() is not safe for untrusted input
    # in production.

    return eval(expression, {"__builtins__": {}}, {})


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="calculator",
        description="Evaluate mathematical expressions.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={"expression": types.Schema(type=types.Type.STRING)},
            required=["expression"],
        ),
    ),
    handler=calculator,
)
