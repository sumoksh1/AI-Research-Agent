from google.genai import types

from agent.core.tool_registry import Tool, ToolContext


def find_memory(ctx: ToolContext, keyword: str):

    return ctx.memory_store.find(keyword)


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="find_memory",
        description="Search long-term memories using a keyword.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "keyword": {
                    "type": "STRING",
                    "description": "The keyword to search for in saved memories.",
                }
            },
            "required": ["keyword"],
        },
    ),
    handler=find_memory,
)
