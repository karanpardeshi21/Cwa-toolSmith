import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Always load .env from the directory containing this file.
ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=False)

def generate_with_groq(prompt: str) -> str:
    """Send a prompt to Groq and return the model's response."""

    api_key = os.getenv("GROQ_API_KEY")


    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Check your project-root .env file."
        )

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        # Keep the model configurable so we can change it later.
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate focused Python tool candidates. "
                    "Follow the requested output format exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=2500,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty response.")

    return content
