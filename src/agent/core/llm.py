import time

from google import genai
from google.genai import types, errors

from agent.core.config import MODEL, SYSTEM_INSTRUCTION, api_key

client = genai.Client(api_key=api_key)


# ==========================================
# GEMINI API CALL WITH RETRIES
# ==========================================


def call_gemini(messages, tools):

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
# STRUCTURED (JSON SCHEMA) GENERATION
# ==========================================


def generate_structured(prompt, schema):

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=schema
        ),
    )

    return response.parsed
