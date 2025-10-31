"""
Test Anthropic API and find available models.
"""

from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Try different model names
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-5-haiku-20241022",
    "claude-3-haiku-20240307",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
]

print("Testing Anthropic API with different model names...\n")

for model in models_to_try:
    try:
        print(f"Trying {model}...", end=" ")
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Say OK"}]
        )
        print(f"✓ SUCCESS - {response.content[0].text}")
        print(f"  Model {model} is accessible!\n")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f"✗ Model not found")
        else:
            print(f"✗ FAILED - {error_msg[:80]}")

print("\nRecommendation: Use the first successful model above.")
