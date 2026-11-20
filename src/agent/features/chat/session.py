from google.genai import types


# ==========================================
# SHORT-TERM MEMORY
# ==========================================


class AgentSession:

    def __init__(self):

        # Stores the current conversation history.
        self.messages = []

    def add_user_message(self, text):

        self.messages.append(
            types.Content(role="user", parts=[types.Part.from_text(text=text)])
        )

    def clear(self):

        self.messages.clear()
