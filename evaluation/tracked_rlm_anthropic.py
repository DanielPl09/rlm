"""
RLM wrapper that uses Anthropic models for experiments.
"""
from typing import Optional, Any, List, Dict
import time

from rlm import RLM
from rlm.repl import REPLEnv
from rlm.utils.anthropic_client import AnthropicClient
from rlm.utils.prompts import DEFAULT_QUERY, next_action_prompt, build_system_prompt
from rlm.utils.context_slicer import ContextSlicer
import rlm.utils.utils as utils

from rlm.logger.root_logger import ColorfulLogger
from rlm.logger.repl_logger import REPLEnvLogger
from evaluation.iteration_tracker import IterationTracker, RefinementTrace


class TrackedRLM_Anthropic(RLM):
    """
    RLM using Anthropic with integrated iteration tracking.
    """

    def __init__(
        self,
        tracker: Optional[IterationTracker] = None,
        ground_truth: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        recursive_model: str = "claude-3-opus-20240229",
        max_iterations: int = 20,
        enable_logging: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.recursive_model = recursive_model
        self.llm = AnthropicClient(api_key, model)

        self.repl_env = None
        self._max_iterations = max_iterations

        self.logger = ColorfulLogger(enabled=enable_logging)
        self.repl_env_logger = REPLEnvLogger(enabled=enable_logging)

        self.messages = []
        self.query = None

        # Tracking
        self.tracker = tracker
        self.ground_truth = ground_truth
        self.current_trace: Optional[RefinementTrace] = None
        self.sub_rlm_call_count = 0

    def setup_context(self, context: List[str] | str | List[Dict[str, str]], query: Optional[str] = None, enable_slicing: bool = True):
        if query is None:
            query = DEFAULT_QUERY

        self.query = query
        self.logger.log_query_start(query)

        self.messages = build_system_prompt()
        self.logger.log_initial_messages(self.messages)

        context_data, context_str = utils.convert_context_for_repl(context)

        context_slices = {}
        if enable_slicing:
            slice_input = context_data if context_data is not None else context_str
            if slice_input is not None:
                context_slices = ContextSlicer.auto_slice_context(slice_input)
                if self.logger.enabled:
                    print(f"📎 Created {len(context_slices)} context slices for iterative refinement")

        self.repl_env = REPLEnv(
            context_json=context_data,
            context_str=context_str,
            recursive_model=self.recursive_model,
            context_slices=context_slices,
        )

        return self.messages

    def completion(
        self,
        context: List[str] | str | List[Dict[str, str]],
        query: Optional[str] = None
    ) -> str:
        # Start tracking
        if self.tracker and self.ground_truth:
            self.current_trace = self.tracker.start_trace(query, self.ground_truth)

        self.sub_rlm_call_count = 0
        self.messages = self.setup_context(context, query)

        # Wrap sub_rlm if tracking
        if self.repl_env and self.tracker:
            original_completion = self.repl_env.sub_rlm.completion

            def tracked_completion(prompt: str, ctx_slice_id: Optional[str] = None) -> str:
                self.sub_rlm_call_count += 1
                result = original_completion(prompt, ctx_slice_id)

                # Record checkpoint
                if self.current_trace and self.repl_env:
                    hypothesis = self.repl_env.hypothesis or "No hypothesis yet"
                    self.current_trace.add_checkpoint(
                        iteration=len(self.messages),
                        sub_rlm_calls=self.sub_rlm_call_count,
                        current_hypothesis=hypothesis
                    )

                return result

            self.repl_env.sub_rlm.completion = tracked_completion

        # Main loop
        for iteration in range(self._max_iterations):
            response = self.llm.completion(self.messages + [next_action_prompt(self.query, iteration)])

            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)

            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env,
                    self.repl_env_logger, self.logger
                )
            else:
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                self.messages.append(assistant_message)

            # Record checkpoint after root iteration
            if self.current_trace and self.repl_env:
                hypothesis = self.repl_env.hypothesis or "No hypothesis yet"
                self.current_trace.add_checkpoint(
                    iteration=iteration + 1,
                    sub_rlm_calls=self.sub_rlm_call_count,
                    current_hypothesis=hypothesis
                )

            # Check for final answer
            final_answer = utils.check_for_final_answer(response, self.repl_env, self.logger)

            if final_answer:
                if self.current_trace:
                    hypothesis = self.repl_env.hypothesis or final_answer
                    self.current_trace.add_checkpoint(
                        iteration=iteration + 1,
                        sub_rlm_calls=self.sub_rlm_call_count,
                        current_hypothesis=hypothesis,
                        final_answer=final_answer
                    )
                    self.tracker.finish_trace()

                self.logger.log_final_response(final_answer)
                return final_answer

        # No final answer
        print("No final answer found in any iteration")
        self.messages.append(next_action_prompt(self.query, iteration, final_answer=True))
        final_answer = self.llm.completion(self.messages)

        if self.current_trace:
            hypothesis = self.repl_env.hypothesis or final_answer
            self.current_trace.add_checkpoint(
                iteration=self._max_iterations,
                sub_rlm_calls=self.sub_rlm_call_count,
                current_hypothesis=hypothesis,
                final_answer=final_answer
            )
            self.tracker.finish_trace()

        self.logger.log_final_response(final_answer)
        return final_answer

    def cost_summary(self) -> Dict[str, Any]:
        raise NotImplementedError("Cost tracking not implemented.")

    def reset(self):
        self.repl_env = REPLEnv()
        self.messages = []
        self.query = None
