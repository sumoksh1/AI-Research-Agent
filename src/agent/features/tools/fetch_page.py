import requests
from bs4 import BeautifulSoup
from google.genai import types

from agent.core.tool_registry import Tool, ToolContext


def fetch_page(ctx: ToolContext, url: str):

    if not url.startswith(("http://", "https://")):

        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unnecessary HTML elements.

    for element in soup(["script", "style", "nav", "footer", "header"]):

        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return text[:5000]


TOOL = Tool(
    declaration=types.FunctionDeclaration(
        name="fetch_page",
        description="Fetch a webpage and extract readable text.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={"url": types.Schema(type=types.Type.STRING)},
            required=["url"],
        ),
    ),
    handler=fetch_page,
)
