from google.genai import types

from agent.core.tool_registry import Tool, ToolContext
from agent.features.tools._workspace import safe_workspace_path


def read_file(ctx: ToolContext, path: str):

    file_path = safe_workspace_path(path)

    if not file_path.is_file():

        raise FileNotFoundError(f"File not found: {path}")

    content = file_path.read_text(encoding="utf-8")

    return content[:20000]


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="read_file",
        description="Read a text file inside the workspace folder.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={"path": types.Schema(type=types.Type.STRING)},
            required=["path"],
        ),
    ),
    handler=read_file,
)
