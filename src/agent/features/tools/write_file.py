from google.genai import types

from agent.core.tool_registry import Tool, ToolContext
from agent.features.tools._workspace import safe_workspace_path


def write_file(ctx: ToolContext, path: str, content: str):

    file_path = safe_workspace_path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate again after creating directories.
    file_path = safe_workspace_path(path)

    file_path.write_text(content, encoding="utf-8")

    return f"Successfully saved file: {path}"


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="write_file",
        description="Create or overwrite a text file inside workspace.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "path": types.Schema(type=types.Type.STRING),
                "content": types.Schema(type=types.Type.STRING),
            },
            required=["path", "content"],
        ),
    ),
    handler=write_file,
)
