"""
Anthropic Client wrapper for Claude models.
"""

import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

        # Implement cost tracking logic here if needed.

    def completion(
        self,
        messages: list[dict[str, str]] | str,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ) -> str:
        try:
            # Convert string to message format
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            # Anthropic requires separating system messages from regular messages
            system_message = None
            regular_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    # Combine all system messages
                    if system_message is None:
                        system_message = msg["content"]
                    else:
                        system_message += "\n\n" + msg["content"]
                else:
                    regular_messages.append(msg)

            # Make the API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_message if system_message else "",
                messages=regular_messages,
                **kwargs
            )

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Error generating completion: {str(e)}")
