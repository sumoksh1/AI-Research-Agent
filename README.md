# AI Research Agent

An interactive command-line research and coding assistant powered by Google's
Gemini API. The agent can answer requests directly or make a plan and work
through its tasks sequentially, using tools for web research, calculations, and
workspace file operations.

## Features

- **Direct execution:** Send a request to the Gemini agent and let it decide
  whether to use its tools.
- **Planned execution:** Ask Gemini to break a request into actionable tasks
  and execute them one at a time.
- **Research and workspace tools:** Search the web, fetch and extract webpage
  text, perform calculations, and read or write files under `workspace/`.
- **Conversation context:** Keep short-term conversation history while the
  program is running, with an option to clear it.
- **Long-term memory:** Extract relevant, stable facts from user requests and
  save them to a local SQLite database. Memories can be viewed, searched, and
  deleted by the agent.

## Requirements

- Python 3.14 or newer
- A Google Gemini API key
- [uv](https://docs.astral.sh/uv/) for dependency management (recommended)

## Setup

1. Clone the repository and open a terminal in its root directory.
2. Install the project dependencies:

   ```powershell
   uv sync
   ```

3. Create a local environment file from the example:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Open `.env` and set your API key:

   ```dotenv
   GEMINI_API_KEY=your_gemini_api_key
   ```

   Keep `.env` private; it is excluded from version control.

## Run

Start the interactive CLI from the repository root:

```powershell
uv run agent
```

Choose an option from the menu:

1. **Direct agent execution** — enter a request for the agent.
2. **Planned agent execution** — have the agent generate and execute a task
   plan.
3. **View saved long-term memories** — list facts stored in the local database.
4. **Clear short-term conversation** — clear the current session history;
   saved memories remain.
5. **Exit**.

The agent prints its tool actions, observations, and final responses in the
terminal.

## Available tools

| Tool | Purpose |
| --- | --- |
| `calculator` | Evaluate a mathematical expression. |
| `web_search` | Search the web and return result titles, URLs, and snippets. |
| `fetch_page` | Fetch an HTTP(S) webpage and extract readable text. |
| `read_file` | Read a text file from `workspace/`. |
| `write_file` | Create or overwrite a text file under `workspace/`. |
| `find_memory` | Search saved memories by keyword. |
| `delete_memory` | Delete a saved memory by its database ID. |

File read and write tools are restricted to the `workspace/` directory. The
agent uses the Gemini `gemini-3.5-flash-lite` model; web search and webpage
fetching require an internet connection.

## Project layout

```text
src/agent/
  app.py              # interactive menu (entry point: `uv run agent`)
  core/
    config.py         # env, model, system instruction, workspace path
    llm.py            # Gemini client, retrying tool call, structured output
    errors.py         # AgentExecutionError
    tool_registry.py  # Tool, ToolContext, ToolRegistry
  features/
    chat/             # short-term session + ReAct loop
    planning/         # plan generation and sequential execution
    memory/           # SQLite store, extraction, retrieval, viewing
    tools/            # one file per tool, each exporting TOOL
```

To add a tool, create `features/tools/<name>.py` exporting
`TOOL = Tool(declaration=..., handler=...)`, where the handler is called as
`handler(ctx, **args)` with `ctx.memory_store` available, then add it to the
registry list in `features/tools/__init__.py`.

## Local data

- `memory.db` stores long-term memories in SQLite and is created in the current
  working directory when the program starts.
- Files the agent reads or writes are located in `workspace/`.
- Conversation history is held in memory for the current process and is not
  persisted between runs.

## Safety note

This is a learning project, not a hardened production agent. The calculator
currently evaluates expressions with Python `eval()` and is explicitly not
safe for untrusted input. Review tool behavior and data handling before using
the project with sensitive information or exposing it to other users.