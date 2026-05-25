import json
import os
import re
import time
import random
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI

load_dotenv()

DEFAULT_BASE_URL = "https://servicesessentials.ibm.com/apis/v3"
DEFAULT_MODEL = "global/anthropic.claude-sonnet-4-5-20250929-v1:0"

# Retry configuration
MAX_RETRIES = 4          # total attempts (1 original + 3 retries)
RETRY_BASE_DELAY = 2.0   # seconds — doubles each attempt
RETRY_MAX_DELAY = 30.0   # cap on wait time


def clear_proxy_env() -> None:
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        os.environ.pop(key, None)


def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return api_key


def get_base_url() -> str:
    return os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL)


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def create_client() -> OpenAI:
    clear_proxy_env()
    return OpenAI(
        api_key=get_api_key(),
        base_url=get_base_url(),
    )


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient errors worth retrying (network, 5xx).
    Return False for permanent failures like auth errors (4xx)."""
    if isinstance(exc, APIConnectionError):
        return True  # DNS failures, dropped connections, timeouts
    if isinstance(exc, APIStatusError):
        return exc.status_code >= 500  # only retry server-side errors
    return False


def generate_text(
    prompt: str,
    *,
    model: str | None = None,
    max_output_tokens: int = 500,
) -> str:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = create_client()
            response = client.responses.create(
                model=model or get_model(),
                input=prompt,
                max_output_tokens=max_output_tokens,
            )
            return response.output_text or ""
        except Exception as exc:
            last_exc = exc
            if not _is_retryable(exc) or attempt == MAX_RETRIES:
                raise
            delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
            # add a small random jitter so parallel calls don't all retry together
            jitter = random.uniform(0, delay * 0.2)
            wait = round(delay + jitter, 1)
            print(
                f"[llm_gateway] Connection error on attempt {attempt}/{MAX_RETRIES} "
                f"({type(exc).__name__}). Retrying in {wait}s ...",
                flush=True,
            )
            time.sleep(wait)

    # should never reach here, but satisfies type checker
    raise last_exc  # type: ignore[misc]


def generate_json(
    prompt: str,
    *,
    model: str | None = None,
    max_output_tokens: int = 2000,
) -> dict[str, Any]:
    response_text = generate_text(
        prompt,
        model=model,
        max_output_tokens=max_output_tokens,
    )
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text)

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))

