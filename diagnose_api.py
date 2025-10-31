"""
Diagnose API key issues.
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

print("API Key Diagnostics")
print("=" * 80)
print(f"Key starts with: {api_key[:20] if api_key else 'NOT FOUND'}...")
print(f"Key length: {len(api_key) if api_key else 0} characters")
print(f"Key format: {'sk-proj-' if api_key and api_key.startswith('sk-proj-') else 'Other'}")
print()

client = OpenAI(api_key=api_key)

# Try a minimal request with detailed error handling
print("Attempting minimal API call...")
print("-" * 80)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✓ SUCCESS! API key is working.")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ FAILED with error:")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error message: {str(e)}")
    print()

    if "Access denied" in str(e):
        print("DIAGNOSIS: Access Denied Error")
        print("-" * 80)
        print("This typically means:")
        print("  1. No billing/payment method set up on the OpenAI account")
        print("  2. Free trial credits have been exhausted")
        print("  3. Account is not in good standing")
        print()
        print("To fix:")
        print("  - Go to https://platform.openai.com/settings/organization/billing")
        print("  - Add a payment method")
        print("  - Ensure there are available credits or billing is active")
    elif "Invalid" in str(e) or "Incorrect" in str(e):
        print("DIAGNOSIS: Invalid API Key")
        print("-" * 80)
        print("The API key format is incorrect or the key has been revoked.")
        print("  - Generate a new key at https://platform.openai.com/api-keys")
    elif "quota" in str(e).lower():
        print("DIAGNOSIS: Quota Exceeded")
        print("-" * 80)
        print("You've hit your usage limits.")
        print("  - Check your usage at https://platform.openai.com/usage")
    else:
        print("DIAGNOSIS: Unknown Error")
        print("-" * 80)
        print("Check the OpenAI status page: https://status.openai.com/")
