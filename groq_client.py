
import os
from functools import lru_cache

from dotenv import load_dotenv
from groq import Groq
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

# Load environment variables from the project-root .env file.
load_dotenv()

DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_TIMEOUT = 60


class GroqClientError(Exception):
    """Raised when a Groq request cannot be completed."""


@lru_cache(maxsize=1)
def get_client() -> Groq:
    """Create and cache the Groq client."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise GroqClientError(
            "GROQ_API_KEY is missing. Add it to your project-root .env file."
        )

    return Groq(
        api_key=api_key,
        timeout=DEFAULT_TIMEOUT,
        max_retries=2,
    )


def generate_with_groq(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """
    Send a prompt to Groq and return the generated text.

    Args:
        prompt: The prompt sent to the model.
        model: Groq model identifier. Defaults to DEFAULT_MODEL.
        temperature: Sampling temperature.
        max_tokens: Maximum generated tokens.

    Returns:
        Generated response text.

    Raises:
        GroqClientError: If configuration or the API request fails.
        ValueError: If the input parameters are invalid.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non-empty string.")

    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        raise ValueError("temperature must be a number.")

    if not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2.")

    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool):
        raise ValueError("max_tokens must be an integer.")

    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1.")

    selected_model = model or os.getenv("GROQ_MODEL") or DEFAULT_MODEL

    try:
        client = get_client()

        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise GroqClientError(
                "Groq returned an empty response."
            )

        return content.strip()

    except GroqClientError:
        raise

    except RateLimitError as exc:
        raise GroqClientError(
            "Groq rate limit reached. Wait before retrying."
        ) from exc

    except APITimeoutError as exc:
        raise GroqClientError(
            "Groq request timed out. Try again."
        ) from exc

    except APIConnectionError as exc:
        raise GroqClientError(
            "Could not connect to Groq. Check your internet connection."
        ) from exc

    except APIStatusError as exc:
        raise GroqClientError(
            f"Groq API returned HTTP {exc.status_code}. "
            "Check your API key, model access, and request limits."
        ) from exc

    except Exception as exc:
        raise GroqClientError(
            f"Unexpected Groq error: {type(exc).__name__}: {exc}"
        ) from exc
