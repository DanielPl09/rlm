"""
Simple Recursive Language Model (RLM) with REPL environment.
"""

from typing import Dict, List, Optional, Any 

from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger


class RLM_REPL(RLM):
    """
    LLM Client that can handle long contexts by recursively calling itself.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "claude-sonnet",
                 recursive_model: str = "claude-sonnet",
                 max_iterations: int = 20,
                 depth: int = 0,
                 enable_logging: bool = False,
                 provider: str = "anthropic",
                 ):
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.provider = provider

        # Initialize the appropriate LLM client
        if provider == "anthropic":
            from rlm.utils.anthropic_client import AnthropicClient
            self.llm = AnthropicClient(api_key, model)
        else:
            from rlm.utils.llm import OpenAIClient
            self.llm = OpenAIClient(api_key, model)
        
        # Track recursive call depth to prevent infinite loops
        self.repl_env = None
        self.depth = depth # Unused in this version.
        self._max_iterations = max_iterations
        
        # Initialize colorful logger
        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)
        
        self.messages = [] # Initialize messages list
        self.query = None
    
    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None):
        """
        Setup the context for the RLMClient.

        Args:
            context: The large context to analyze in the form of a list of messages, string, or Dict
            query: The user's question
        """
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        # Initialize the conversation with the REPL prompt
        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)
        
        # Initialize REPL environment with context data
        context_data, context_str = utils.convert_context_for_repl(context)

        self.repl_env = REPLEnv(
            context_json=context_data,
            context_str=context_str,
            recursive_model=self.recursive_model,
            provider=self.provider,
        )
        
        return self.messages

    def completion(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None) -> str:
        """
        Given a query and a (potentially long) context, recursively call the LM
        to explore the context and provide an answer using a REPL environment.
        """
        self.messages = self.setup_context(context, query)
        
        # Main loop runs for fixed # of root LM iterations
        for iteration in range(self._max_iterations):
            
            # Query root LM to interact with REPL environment
            response = self.llm.completion(self.messages + [next_action_prompt(query, iteration)])
            
            # Check for code blocks
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)
            
            # Process code execution or add assistant message
            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env, 
                    self.repl_env_logger, self.logger
                )
            else:
                # Add assistant message when there are no code blocks
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                self.messages.append(assistant_message)
            
            # Check that model produced a final answer
            final_answer = utils.check_for_final_answer(
                response, self.repl_env, self.logger,
            )

            # In practice, you may need some guardrails here.
            if final_answer:
                self.logger.log_final_response(final_answer)
                return final_answer

            
        # If we reach here, no final answer was found in any iteration
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(query, iteration, final_answer=True))
        final_answer = self.llm.completion(self.messages)
        self.logger.log_final_response(final_answer)

        return final_answer
    
    def cost_summary(self) -> Dict[str, Any]:
        """Get the cost summary of the Root LM + Sub-RLM Calls."""
        root_cost_info = {}
        sub_llm_cost_info = {}

        # Get root LLM cost
        if hasattr(self.llm, 'get_cost_summary'):
            root_cost_info = self.llm.get_cost_summary()

        # Get sub-LLM cost if REPL env exists
        if self.repl_env and hasattr(self.repl_env.sub_rlm, 'client'):
            if hasattr(self.repl_env.sub_rlm.client, 'get_cost_summary'):
                sub_llm_cost_info = self.repl_env.sub_rlm.client.get_cost_summary()

        # Combine costs
        total_cost = root_cost_info.get('total_cost', 0) + sub_llm_cost_info.get('total_cost', 0)

        return {
            'root_cost': root_cost_info.get('total_cost', 0),
            'root_tokens': root_cost_info.get('total_tokens', 0),
            'sub_llm_cost': sub_llm_cost_info.get('total_cost', 0),
            'sub_llm_tokens': sub_llm_cost_info.get('total_tokens', 0),
            'total_cost': total_cost,
            'total_tokens': root_cost_info.get('total_tokens', 0) + sub_llm_cost_info.get('total_tokens', 0),
        }

    def reset(self):
        """Reset the (REPL) environment and message history."""
        self.repl_env = REPLEnv(
            recursive_model=self.recursive_model,
            provider=self.provider,
        )
        self.messages = []
        self.query = None


if __name__ == "__main__":
    pass
