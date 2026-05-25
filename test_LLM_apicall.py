"""
test_LLM_apicall.py
--------------------
Quick smoke-test to verify that the IBM enterprise LLM API gateway
is reachable and returning a valid response.

Run from the USECASE-1 root directory:
    python test_LLM_apicall.py
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

# ── 1. Load credentials from .env ─────────────────────────────────────────────
load_dotenv()

API_KEY  = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://servicesessentials.ibm.com/apis/v3")
MODEL    = os.getenv("OPENAI_MODEL",    "global/anthropic.claude-sonnet-4-5-20250929-v1:0")

# ── 2. Clear any proxy settings that could interfere ──────────────────────────
for _key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
             "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(_key, None)

# ── 3. Basic pre-flight checks ─────────────────────────────────────────────────
print("=" * 60)
print("  LLM API Smoke Test")
print("=" * 60)
print(f"  Base URL : {BASE_URL}")
print(f"  Model    : {MODEL}")
print(f"  API Key  : {'SET [OK]' if API_KEY else 'NOT SET [!!]'}")
print("=" * 60)

if not API_KEY:
    print("\n[ERROR] OPENAI_API_KEY is not set in .env. Aborting.")
    sys.exit(1)

# ── 4. Make the API call ───────────────────────────────────────────────────────
TEST_PROMPT = "Say hello and confirm you are working. Keep it to one sentence."

print(f"\n[INFO] Sending test prompt: \"{TEST_PROMPT}\"\n")

try:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    response = client.responses.create(
        model=MODEL,
        input=TEST_PROMPT,
        max_output_tokens=100,
    )

    answer = response.output_text or ""

    print("[SUCCESS] LLM responded successfully!")
    print("-" * 60)
    print(f"  Response: {answer.strip()}")
    print("-" * 60)

except Exception as exc:
    print(f"[FAILED]  API call raised an exception:\n  {type(exc).__name__}: {exc}")
    sys.exit(1)

print("\n[DONE] Smoke test passed. The LLM API is working correctly.\n")
