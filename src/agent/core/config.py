import os

from pathlib import Path

from dotenv import load_dotenv

# ==========================================
# ENVIRONMENT AND SETTINGS
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

MODEL = "gemini-3.5-flash-lite"

SYSTEM_INSTRUCTION = """
You are a helpful research and coding assistant.

Follow the ReAct pattern:

1. Briefly explain the next action when useful.
2. Select an appropriate available tool.
3. Examine the result returned by the tool.
4. Adapt your next action based on the observation.
5. Continue until the task is complete.

Do not invent tool results.

If a tool fails, examine the error and decide
how to proceed.

Do not call tools unnecessarily.

When finished, provide a clear final answer.
"""

WORKSPACE = Path("workspace").resolve()

WORKSPACE.mkdir(parents=True, exist_ok=True)
