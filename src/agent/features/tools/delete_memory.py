from google.genai import types

from agent.core.tool_registry import Tool, ToolContext


def delete_memory(ctx: ToolContext, memory_id: int):

    ctx.memory_store.delete(memory_id)

    return f"Memory {memory_id} deleted successfully."


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="delete_memory",
        description="Delete a saved long-term memory using its database ID.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "memory_id": {
                    "type": "INTEGER",
                    "description": "The ID of the memory to delete.",
                }
            },
            "required": ["memory_id"],
        },
    ),
    handler=delete_memory,
)
