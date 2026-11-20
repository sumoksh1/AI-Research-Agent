from google.genai import types

from agent.core.errors import AgentExecutionError
from agent.core.llm import call_gemini
from agent.core.tool_registry import ToolContext
from agent.features.memory import build_user_message, remember_user_message
from agent.features.tools import registry


# ==========================================
# CREATE THE REACT AGENT
# ==========================================


def run_agent(user_msg, session, memory_store, remember=True):

    # --------------------------------------
    # RETRIEVE LONG-TERM MEMORIES
    # --------------------------------------

    enhanced_message = build_user_message(user_msg, memory_store)

    # --------------------------------------
    # ADD MESSAGE TO SHORT-TERM MEMORY
    # --------------------------------------

    session.add_user_message(enhanced_message)

    messages = session.messages

    tool_context = ToolContext(memory_store=memory_store)

    # --------------------------------------
    # REACT AGENT LOOP
    # --------------------------------------

    for step in range(10):

        print(f"\n========== AGENT ITERATION {step + 1} ==========")

        # CALL GEMINI

        try:

            response = call_gemini(messages, registry.gemini_tools())

        except Exception as e:

            raise AgentExecutionError(f"Gemini API error: {e}") from e

        if not response.candidates:

            raise AgentExecutionError("Gemini returned no candidates.")

        candidate = response.candidates[0]

        # CHECK TOKEN LIMIT

        if candidate.finish_reason == types.FinishReason.MAX_TOKENS:

            raise AgentExecutionError("Response was truncated.")

        # PRESERVE COMPLETE MODEL RESPONSE

        messages.append(candidate.content)

        # DISPLAY MODEL TEXT

        for part in candidate.content.parts:

            if part.text:

                print("\nTHOUGHT / RESPONSE:")

                print(part.text)

        # EXTRACT FUNCTION CALLS

        function_calls = response.function_calls

        # NO FUNCTION CALLS = FINAL ANSWER

        if not function_calls:

            print("\nAGENT FINISHED.")

            final_answer = response.text or ""

            # SAVE LONG-TERM MEMORIES
            # Only for original user requests.

            if remember:

                remember_user_message(user_msg, memory_store)

            return final_answer

        # EXECUTE REQUESTED TOOLS

        function_response_parts = []

        for function_call in function_calls:

            function_name = function_call.name

            function_args = function_call.args

            print("\nACTION:")

            print("Tool:", function_name)

            print("Arguments:", function_args)

            try:

                result = registry.execute(function_name, function_args, tool_context)

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

        # SEND OBSERVATIONS BACK TO GEMINI

        messages.append(types.Content(role="user", parts=function_response_parts))

    raise AgentExecutionError("Maximum agent iterations reached.")
