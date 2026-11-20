from ddgs import DDGS
from google.genai import types

from agent.core.tool_registry import Tool, ToolContext


def web_search(ctx: ToolContext, query: str):

    results = DDGS().text(query, max_results=5)

    output = []

    for item in results:

        output.append(
            {
                "title": item.get("title"),
                "url": item.get("href"),
                "snippet": item.get("body"),
            }
        )

    return output


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="web_search",
        description="Search the internet and return relevant results.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={"query": types.Schema(type=types.Type.STRING)},
            required=["query"],
        ),
    ),
    handler=web_search,
)
