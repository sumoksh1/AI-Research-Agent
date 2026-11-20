from agent.core.tool_registry import ToolRegistry
from agent.features.tools import (
    calculator,
    delete_memory,
    fetch_page,
    find_memory,
    read_file,
    web_search,
    write_file,
)

# Order matches the declaration order sent to Gemini.
registry = ToolRegistry(
    [
        calculator.TOOL,
        web_search.TOOL,
        read_file.TOOL,
        write_file.TOOL,
        fetch_page.TOOL,
        find_memory.TOOL,
        delete_memory.TOOL,
    ]
)
