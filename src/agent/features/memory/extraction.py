from typing import List

from pydantic import BaseModel

from agent.core.llm import generate_structured


class MemoryExtraction(BaseModel):

    facts: List[str]


# ==========================================
# LONG-TERM MEMORY EXTRACTION
# ==========================================


def extract_memories(user_message):

    print("\n========== EXTRACTING MEMORIES ==========")

    prompt = f"""

    You are a long-term memory extraction system.

    Extract useful, stable facts explicitly stated
    by the user in the message below.

    Examples of useful information:

    - Name or preferred form of address
    - Learning goals
    - Ongoing projects
    - Technical preferences
    - Long-term interests

    Do not save:

    - Temporary requests
    - One-time calculations
    - Guesses or assumptions
    - Passwords
    - API keys
    - Other secrets
    - Sensitive personal information

    Do not invent facts.

    If there are no useful facts,
    return an empty list.

    USER MESSAGE:

    {user_message}

    """

    parsed = generate_structured(prompt, MemoryExtraction)

    if parsed is None:

        return []

    return parsed.facts


# ==========================================
# SAVE USER MEMORIES
# ==========================================


def remember_user_message(user_message, memory_store):

    try:

        facts = extract_memories(user_message)

        if not facts:

            print("No useful long-term memories found.")

            return

        for fact in facts:

            memory_store.save(fact)

            print("Saved memory:", fact)

    except Exception as e:

        # Memory failure should not crash
        # the main agent.

        print("Memory extraction failed:", e)
