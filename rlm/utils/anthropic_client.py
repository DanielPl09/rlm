"""
Minimal Anthropic Client for column delegation example.
"""

import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class AnthropicClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def completion(self, messages: list[dict[str, str]] | str, max_tokens: int = 4096, **kwargs) -> str:
        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            # Separate system messages
            system_content = None
            conversation_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    if system_content is None:
                        system_content = msg["content"]
                    else:
                        system_content += "\n\n" + msg["content"]
                else:
                    conversation_messages.append(msg)

            api_kwargs = {
                "model": self.model,
                "messages": conversation_messages,
                "max_tokens": max_tokens,
            }

            if system_content:
                api_kwargs["system"] = system_content

            api_kwargs.update(kwargs)

            response = self.client.messages.create(**api_kwargs)
            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Error generating Anthropic completion: {str(e)}")
