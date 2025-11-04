"""
Anthropic Client wrapper compatible with RLM interface.
"""

import os
from typing import Optional


class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")

        self.model = model

        # Import anthropic SDK
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def completion(
        self,
        messages: list[dict[str, str]] | str,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ) -> str:
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            # Convert messages to Anthropic format
            # Anthropic requires system messages to be separate
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    conversation_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Make API call
            if system_message:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_message,
                    messages=conversation_messages,
                    **kwargs
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=conversation_messages,
                    **kwargs
                )

            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Error generating completion: {str(e)}")
