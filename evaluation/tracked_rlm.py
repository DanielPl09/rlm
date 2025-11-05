"""
RLM wrapper with iteration tracking for 80/20 evaluation.
"""
from typing import Optional, Any, List, Dict
import time

from rlm.rlm_repl import RLM_REPL
from evaluation.iteration_tracker import IterationTracker, RefinementTrace


class TrackedRLM(RLM_REPL):
    """
    RLM with integrated iteration tracking for quality vs time analysis.
    """

    def __init__(
        self,
        tracker: Optional[IterationTracker] = None,
        ground_truth: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize tracked RLM.

        Args:
            tracker: IterationTracker instance for recording progress
            ground_truth: Ground truth answer for quality evaluation
            **kwargs: Arguments passed to RLM_REPL
        """
        super().__init__(**kwargs)
        self.tracker = tracker
        self.ground_truth = ground_truth
        self.current_trace: Optional[RefinementTrace] = None
        self.sub_rlm_call_count = 0

    def completion(
        self,
        context: List[str] | str | List[Dict[str, str]],
        query: Optional[str] = None
    ) -> str:
        """
        Execute completion with tracking enabled.

        Args:
            context: Context for the query
            query: The question to answer

        Returns:
            Final answer string
        """
        # Start tracking trace if tracker is provided
        if self.tracker and self.ground_truth:
            self.current_trace = self.tracker.start_trace(query, self.ground_truth)

        # Reset sub-RLM call counter
        self.sub_rlm_call_count = 0

        # Setup and run completion
        self.messages = self.setup_context(context, query)

        # Wrap the REPL environment's llm_query to track calls
        if self.repl_env:
            original_llm_query = self.repl_env.sub_rlm.completion

            def tracked_llm_query(prompt: str, ctx_slice_id: Optional[str] = None) -> str:
                """Wrapper to track sub-RLM calls."""
                self.sub_rlm_call_count += 1
                result = original_llm_query(prompt, ctx_slice_id)

                # Record checkpoint after each sub-RLM call
                if self.current_trace and self.repl_env:
                    hypothesis = self.repl_env.hypothesis or "No hypothesis yet"
                    self.current_trace.add_checkpoint(
                        iteration=len(self.messages),  # Approximate iteration count
                        sub_rlm_calls=self.sub_rlm_call_count,
                        current_hypothesis=hypothesis
                    )

                return result

            # Monkey-patch the completion method
            self.repl_env.sub_rlm.completion = tracked_llm_query

        # Main iteration loop (from parent class)
        for iteration in range(self._max_iterations):
            from rlm.utils.prompts import next_action_prompt
            import rlm.utils.utils as utils

            # Query root LM
            response = self.llm.completion(self.messages + [next_action_prompt(self.query, iteration)])

            # Check for code blocks
            code_blocks = utils.find_code_blocks(response)
            self.logger.log_model_response(response, has_tool_calls=code_blocks is not None)

            # Process code execution
            if code_blocks is not None:
                self.messages = utils.process_code_execution(
                    response, self.messages, self.repl_env,
                    self.repl_env_logger, self.logger
                )
            else:
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                self.messages.append(assistant_message)

            # Record checkpoint after each root iteration
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
                # Record final checkpoint with answer
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

        # No final answer found
        print("No final answer found in any iteration")
        from rlm.utils.prompts import next_action_prompt
        self.messages.append(next_action_prompt(self.query, iteration, final_answer=True))
        final_answer = self.llm.completion(self.messages)

        # Record final checkpoint
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


def create_tracked_rlm(
    api_key: Optional[str] = None,
    model: str = "gpt-5",
    tracker: Optional[IterationTracker] = None,
    ground_truth: Optional[str] = None,
    **kwargs
) -> TrackedRLM:
    """
    Factory function to create a TrackedRLM instance.

    Args:
        api_key: API key for LLM provider
        model: Model name to use
        tracker: IterationTracker for recording progress
        ground_truth: Ground truth answer for evaluation
        **kwargs: Additional arguments for RLM_REPL

    Returns:
        TrackedRLM instance
    """
    return TrackedRLM(
        api_key=api_key,
        model=model,
        recursive_model=model,
        tracker=tracker,
        ground_truth=ground_truth,
        **kwargs
    )
