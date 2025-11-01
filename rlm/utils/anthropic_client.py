"""
Anthropic Claude Client wrapper.
"""

import os
from typing import Optional
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class AnthropicClient:
    """Client wrapper for Anthropic Claude API."""

    # Model mapping for convenience
    MODEL_MAPPING = {
        "gpt-5": "claude-sonnet-4-5-20250929",
        "gpt-5-nano": "claude-3-5-haiku-20241022",
        "gpt-5-mini": "claude-3-5-sonnet-20241022",
        "claude-sonnet": "claude-sonnet-4-5-20250929",
        "claude-haiku": "claude-3-5-haiku-20241022",
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Map model name if needed
        self.model = self.MODEL_MAPPING.get(model, model)
        self.client = Anthropic(api_key=self.api_key)

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def completion(
        self,
        messages: list[dict[str, str]] | str | dict[str, str],
        max_tokens: Optional[int] = 8192,
        **kwargs
    ) -> str:
        """
        Generate completion using Anthropic Claude API.

        Args:
            messages: Either a string, a single message dict, or a list of message dicts
            max_tokens: Maximum tokens to generate (default 8192)
            **kwargs: Additional arguments to pass to the API

        Returns:
            str: The completion text
        """
        try:
            # Convert input to list of messages format
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]
            elif isinstance(messages, dict):
                messages = [messages]

            # Separate system messages from conversation
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.get("role") == "system":
                    # Anthropic requires system message as separate parameter
                    system_message = msg.get("content", "")
                else:
                    conversation_messages.append(msg)

            # Make API call
            api_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": conversation_messages,
            }

            if system_message:
                api_params["system"] = system_message

            # Add any additional kwargs
            api_params.update(kwargs)

            response = self.client.messages.create(**api_params)

            # Track token usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Error generating completion: {str(e)}")

    def get_cost_summary(self) -> dict[str, float]:
        """
        Get token usage and cost summary.

        Returns:
            dict with input_tokens, output_tokens, and estimated_cost
        """
        # Approximate costs (as of 2025) - adjust based on actual pricing
        # Claude Sonnet 4.5: $3/M input, $15/M output
        # Claude 3.5 Sonnet: $3/M input, $15/M output
        # Claude 3.5 Haiku: $0.80/M input, $4/M output

        if "haiku" in self.model.lower():
            cost_per_input_token = 0.80 / 1_000_000
            cost_per_output_token = 4.00 / 1_000_000
        else:
            cost_per_input_token = 3.00 / 1_000_000
            cost_per_output_token = 15.00 / 1_000_000

        input_cost = self.total_input_tokens * cost_per_input_token
        output_cost = self.total_output_tokens * cost_per_output_token
        total_cost = input_cost + output_cost

        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

    def reset_usage(self):
        """Reset token usage counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
