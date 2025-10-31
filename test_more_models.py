"""
Test more Anthropic model names to find Claude 3.5 Sonnet.
"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Try more model name variations
models_to_try = [
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet",
    "claude-3-5-haiku-latest",
    "claude-3-opus-latest",
]

print("Testing more Anthropic model variations...\n")

for model in models_to_try:
    try:
        print(f"Trying {model}...", end=" ")
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        print(f"✓ SUCCESS - {response.content[0].text}")
        print(f"  Actual model: {response.model}\n")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f"✗ Model not found")
        else:
            print(f"✗ FAILED - {error_msg[:100]}")
