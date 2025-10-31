"""
Simple test to check API access and find available models.
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test with different models
models_to_try = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo"
]

print("Testing API key access with different models...\n")

for model in models_to_try:
    try:
        print(f"Trying {model}...", end=" ")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        print(f"✓ SUCCESS - {response.choices[0].message.content}")
        print(f"  Model {model} is accessible!\n")
        break
    except Exception as e:
        print(f"✗ FAILED - {str(e)[:80]}\n")

print("\nTo see all available models, the API key needs list permissions.")
print("Using first successful model for testing...")
