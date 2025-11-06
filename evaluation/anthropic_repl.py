"""
REPL Environment with Anthropic Sub-RLM for actual RLM integration.
"""
import os
from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.anthropic_client import AnthropicClient


class Sub_RLM_Anthropic(RLM):
    """Sub-RLM using Anthropic for REPL environment."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", context_slices: dict = None):
        self.api_key = api_key
        self.model = model
        self.context_slices = context_slices or {}
        self.client = AnthropicClient(api_key=api_key, model=model)

    def completion(self, prompt, ctx_slice_id: str = None) -> str:
        """
        Sub-LLM query with optional context slice.

        This is the KEY function that RLM uses for sub-calls!
        """
        try:
            # Build messages
            if isinstance(prompt, str):
                content = prompt
            else:
                # If it's already messages, extract content
                content = prompt

            # Add context slice if specified
            if ctx_slice_id and ctx_slice_id in self.context_slices:
                slice_obj = self.context_slices[ctx_slice_id]
                slice_content = slice_obj.content if hasattr(slice_obj, 'content') else str(slice_obj)
                content = f"Context slice '{ctx_slice_id}':\n{slice_content}\n\n{content}"

            # Call Anthropic
            response = self.client.completion(content)
            return response

        except Exception as e:
            return f"Error in sub-LLM call: {str(e)}"

    def cost_summary(self):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()


def create_anthropic_repl_env(api_key: str, context_slices: dict, model: str = "claude-3-opus-20240229"):
    """
    Create REPLEnv with Anthropic Sub-RLM.

    This allows RLM to make sub-calls using Anthropic models.
    """
    # Set dummy OPENAI_API_KEY so REPLEnv constructor doesn't fail
    # (we'll immediately replace the sub_rlm with Anthropic version)
    os.environ['OPENAI_API_KEY'] = 'dummy-key-not-used'

    # Create REPLEnv (it will create OpenAI sub_rlm, but we'll replace it)
    repl_env = REPLEnv(
        recursive_model=model,
        context_json=None,
        context_str=None,
        context_slices=context_slices
    )

    # Replace the sub_rlm with Anthropic version
    repl_env.sub_rlm = Sub_RLM_Anthropic(
        api_key=api_key,
        model=model,
        context_slices=context_slices
    )

    # Update the llm_query function to use our Anthropic sub_rlm
    def llm_query(prompt: str, slice_id: str = None) -> str:
        """Query LLM with optional context slice."""
        return repl_env.sub_rlm.completion(prompt, ctx_slice_id=slice_id)

    repl_env.globals['llm_query'] = llm_query

    return repl_env
