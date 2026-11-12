import os
import time
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from pydantic import BaseModel

# ==========================================
# 1. INITIALIZE ENVIRONMENT AND GEMINI
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

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


# ==========================================
# 2. PLANNING DATA STRUCTURE
# ==========================================


class Plan(BaseModel):

    tasks: List[str]


class AgentSession:

    def __init__(self):

        # Stores the complete conversation history
        self.messages = []

    def add_user_message(self, text):

        self.messages.append(
            types.Content(role="user", parts=[types.Part.from_text(text=text)])
        )

    def clear(self):

        # Start a fresh conversation
        self.messages.clear()


class AgentExecutionError(Exception):
    """Raised when an agent execution cannot complete."""

    pass


# ==========================================
# 3. DEFINE PYTHON TOOLS
# ==========================================


# TOOL 1: CALCULATOR


def calculator(expression: str):

    # Learning-only implementation.
    # eval() is not safe for untrusted input in production.

    return eval(expression, {"__builtins__": {}}, {})


# TOOL 2: WEB SEARCH


def web_search(query: str):

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


# HELPER: SAFE WORKSPACE PATH


def safe_workspace_path(path: str):

    file_path = (WORKSPACE / path).resolve()

    if not file_path.is_relative_to(WORKSPACE):
        raise ValueError("Access outside workspace is not allowed.")

    return file_path


# TOOL 3: READ FILE


def read_file(path: str):

    file_path = safe_workspace_path(path)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    content = file_path.read_text(encoding="utf-8")

    return content[:20000]


# TOOL 4: WRITE FILE


def write_file(path: str, content: str):

    file_path = safe_workspace_path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate again after creating parent directories.
    file_path = safe_workspace_path(path)

    file_path.write_text(content, encoding="utf-8")

    return f"Successfully saved file: {path}"


# TOOL 5: FETCH WEBPAGE


def fetch_page(url: str):

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


# ==========================================
# 4. MAP TOOL NAMES TO PYTHON FUNCTIONS
# ==========================================

TOOL_FUNCS = {
    "calculator": calculator,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "fetch_page": fetch_page,
}


# ==========================================
# 5. DECLARE TOOLS TO GEMINI
# ==========================================

tools = [
    types.Tool(
        function_declarations=[
            # CALCULATOR
            types.FunctionDeclaration(
                name="calculator",
                description="Evaluate mathematical expressions.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"expression": types.Schema(type=types.Type.STRING)},
                    required=["expression"],
                ),
            ),
            # WEB SEARCH
            types.FunctionDeclaration(
                name="web_search",
                description="Search the internet and return relevant results.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"query": types.Schema(type=types.Type.STRING)},
                    required=["query"],
                ),
            ),
            # READ FILE
            types.FunctionDeclaration(
                name="read_file",
                description="Read a text file inside the workspace folder.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"path": types.Schema(type=types.Type.STRING)},
                    required=["path"],
                ),
            ),
            # WRITE FILE
            types.FunctionDeclaration(
                name="write_file",
                description="Create or overwrite a text file inside the workspace folder.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "path": types.Schema(type=types.Type.STRING),
                        "content": types.Schema(type=types.Type.STRING),
                    },
                    required=["path", "content"],
                ),
            ),
            # FETCH WEBPAGE
            types.FunctionDeclaration(
                name="fetch_page",
                description="Fetch a webpage and extract its readable text.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"url": types.Schema(type=types.Type.STRING)},
                    required=["url"],
                ),
            ),
        ]
    )
]


# ==========================================
# 6. GEMINI API CALL WITH RETRIES
# ==========================================


def call_gemini(messages):

    max_retries = 3

    for attempt in range(max_retries):

        try:

            print(f"Calling Gemini (attempt {attempt + 1})...")

            response = client.models.generate_content(
                model=MODEL,
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=tools,
                    max_output_tokens=2000,
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )

            return response

        except errors.APIError as e:

            if e.code not in (429, 500, 502, 503, 504):
                raise

            print("Temporary API error:", e)

            if attempt == max_retries - 1:
                raise

            wait_time = 2**attempt

            print(f"Retrying in {wait_time} seconds...")

            time.sleep(wait_time)

    raise RuntimeError("Gemini API failed after retries")


# ==========================================
# 7. CREATE THE REACT AGENT
# ==========================================


def run_agent(user_msg, session):

    # Add the new user message to existing history
    session.add_user_message(user_msg)

    # Use the persistent conversation history
    messages = session.messages

    for step in range(10):

        print(f"\n========== AGENT ITERATION {step + 1} ==========")

        try:

            response = call_gemini(messages)

        except Exception as e:

            raise AgentExecutionError(f"Gemini API error: {e}") from e

        if not response.candidates:

            raise AgentExecutionError("Gemini returned no candidates.")

        candidate = response.candidates[0]

        if candidate.finish_reason == types.FinishReason.MAX_TOKENS:

            raise AgentExecutionError("Response was truncated.")

        # Preserve the complete model response
        messages.append(candidate.content)

        # Display model text
        for part in candidate.content.parts:

            if part.text:

                print("\nTHOUGHT / RESPONSE:")
                print(part.text)

        # Check for tool calls
        function_calls = response.function_calls

        # No tool calls means the model has finished
        if not function_calls:

            print("\nAGENT FINISHED.")

            return response.text or ""

        function_response_parts = []

        # Execute requested tools
        for function_call in function_calls:

            function_name = function_call.name
            function_args = function_call.args

            print("\nACTION:")
            print("Tool:", function_name)
            print("Arguments:", function_args)

            try:

                if function_name not in TOOL_FUNCS:

                    raise ValueError(f"Unknown tool: {function_name}")

                function_to_call = TOOL_FUNCS[function_name]

                result = function_to_call(**function_args)

                is_error = False

            except Exception as e:

                result = f"{type(e).__name__}: {e}"
                is_error = True

            print("\nOBSERVATION:")
            print(result)

            function_response_parts.append(
                types.Part.from_function_response(
                    name=function_name,
                    response={"result": result, "is_error": is_error},
                )
            )

        # Append tool observations to persistent history
        messages.append(types.Content(role="user", parts=function_response_parts))

    raise AgentExecutionError("Maximum agent iterations reached.")


# ==========================================
# 8. CREATE A PLAN
# ==========================================


def create_plan(user_request):

    print("\n========== CREATING PLAN ==========")

    planning_prompt = f"""

    You are a task planner.

    Break the user's request into 3 to 6
    small, clear, actionable tasks.

    Put the tasks in execution order.

    Each task should have a clear outcome.

    Make sure the final task completes the
    user's requested deliverable, if any.

    User request:

    {user_request}

    """

    response = client.models.generate_content(
        model=MODEL,
        contents=planning_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Plan
        ),
    )

    if response.parsed is None:

        raise ValueError("Gemini did not return a valid plan.")

    plan = response.parsed

    if not plan.tasks:

        raise ValueError("Generated plan contains no tasks.")

    print("\nGENERATED PLAN:")

    for index, task in enumerate(plan.tasks, start=1):

        print(f"{index}. {task}")

    return plan


# ==========================================
# 9. EXECUTE THE PLAN
# ==========================================


def execute_plan(user_request):

    plan = create_plan(user_request)

    # Create one short-term memory session
    session = AgentSession()

    task_status = [{"task": task, "status": "pending"} for task in plan.tasks]

    task_results = []

    # Continue with the existing execution loop...

    # ==================================
    # STEP 2: EXECUTE TASKS SEQUENTIALLY
    # ==================================

    for index, task in enumerate(plan.tasks):

        print(f"\n========== EXECUTING TASK {index + 1} ==========")

        task_status[index]["status"] = "in_progress"

        # ==================================
        # GET PREVIOUS TASK RESULTS
        # ==================================

        previous_results = "\n\n".join(
            [
                f"TASK: {item['task']}\n" f"RESULT: {item['result']}"
                for item in task_results
            ]
        )

        if not previous_results:

            previous_results = "No previous tasks completed."

        # ==================================
        # BUILD TASK PROMPT
        # ==================================

        task_prompt = f"""

        ORIGINAL USER REQUEST:

        {user_request}


        COMPLETE PLAN:

        {plan.tasks}


        CURRENT TASK:

        {task}


        RESULTS FROM PREVIOUS TASKS:

        {previous_results}


        YOUR INSTRUCTIONS:

        Focus on completing the CURRENT TASK.

        Use the available tools when necessary.

        Consider results from previous tasks.

        Do not unnecessarily repeat completed work.

        Do not claim to have completed something
        unless you have actually done it.

        Return a concise summary of what you accomplished.

        """

        # ==================================
        # RUN THE EXISTING REACT AGENT
        # ==================================

        try:

            result = run_agent(task_prompt, session)

            task_results.append({"task": task, "result": result})

            task_status[index]["status"] = "completed"

        except Exception as e:

            result = str(e)

            task_results.append({"task": task, "result": result})

            task_status[index]["status"] = "failed"

            print("\nTASK FAILED:")
            print(result)

            # Stop because later tasks may depend on this one.

            for remaining_index in range(index + 1, len(task_status)):

                task_status[remaining_index]["status"] = "skipped"

            break

        print("\nTASK STATUS:")
        print(task_status[index]["status"])

    # ==================================
    # STEP 3: DISPLAY PLAN SUMMARY
    # ==================================

    print("\n========== PLAN SUMMARY ==========")

    for item in task_status:

        print(f"{item['status'].upper()}: {item['task']}")

    return task_results, task_status


# ==========================================
# 10. MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    # Create one persistent session
    session = AgentSession()

    # First interaction
    answer1 = run_agent(
        "My name is Jatin. I am building an AI research agent using Python.", session
    )

    print("\nAGENT:", answer1)

    # Second interaction
    answer2 = run_agent("What programming language am I using?", session)

    print("\nAGENT:", answer2)

    # Third interaction
    answer3 = run_agent("What kind of project am I building?", session)

    print("\nAGENT:", answer3)
