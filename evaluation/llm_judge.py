"""
LLM-as-Judge for evaluating hypothesis quality.
"""
import re
from typing import Dict, Any
from rlm.utils.anthropic_client import AnthropicClient


class LLMJudge:
    """Use LLM to judge hypothesis quality."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = AnthropicClient(api_key=api_key, model=model)

    def evaluate_hypothesis(
        self,
        question: str,
        hypothesis: str,
        ground_truth: str
    ) -> Dict[str, Any]:
        """
        Evaluate hypothesis completeness and correctness.

        Returns:
            {
                'completeness': float (0-1),
                'correctness': float (0-1),
                'score': float (0-1),
                'reasoning': str
            }
        """
        prompt = f"""Question: {question}

Ground Truth Answer: {ground_truth}

Current Hypothesis: {hypothesis}

Evaluate the hypothesis on two dimensions:

1. COMPLETENESS (0-100): How much of the required information is present?
2. CORRECTNESS (0-100): How accurate is the information?

Provide your evaluation in this EXACT format:
COMPLETENESS: <number 0-100>
CORRECTNESS: <number 0-100>
REASONING: <1-2 sentence explanation>"""

        try:
            response = self.client.completion(prompt).strip()

            completeness = self._extract_number(response, "COMPLETENESS")
            correctness = self._extract_number(response, "CORRECTNESS")
            reasoning = self._extract_reasoning(response)

            completeness_norm = completeness / 100.0
            correctness_norm = correctness / 100.0
            score = (completeness_norm + correctness_norm) / 2

            return {
                'completeness': completeness_norm,
                'correctness': correctness_norm,
                'score': score,
                'reasoning': reasoning,
            }

        except Exception as e:
            print(f"  Error in LLM judge: {e}")
            return {
                'completeness': 0.0,
                'correctness': 0.0,
                'score': 0.0,
                'reasoning': f"Error: {e}",
            }

    def _extract_number(self, text: str, field: str) -> float:
        """Extract number from field."""
        pattern = rf"{field}:\s*(\d+(?:\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning text."""
        pattern = r"REASONING:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
