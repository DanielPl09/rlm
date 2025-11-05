import os
"""
Cumulative hypothesis refinement system for gradual F1 convergence.

This implements true iterative refinement where each iteration BUILDS on
previous knowledge rather than answering independently.
"""
import time
from typing import List, Optional
from dataclasses import dataclass

from rlm.utils.anthropic_client import AnthropicClient
from evaluation.iteration_tracker import IterationTracker
from evaluation.metrics import evaluate_answer


@dataclass
class RefinementSlice:
    """A slice of context for progressive refinement."""
    slice_id: str
    content: str
    has_supporting_fact: bool


class CumulativeRefinementSystem:
    """
    System for progressive hypothesis refinement showing gradual convergence.

    Key features:
    - Accumulates context across iterations
    - Each iteration updates previous hypothesis
    - Shows gradual F1 improvement, not sudden jumps
    """

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = AnthropicClient(api_key=api_key, model=model)
        self.hypothesis = ""
        self.context_accumulated = ""
        self.iteration_count = 0

    def extract_answer(self, hypothesis: str, question: str) -> str:
        """
        Extract clean answer from verbose hypothesis for F1 calculation.

        Example:
        Hypothesis: "Based on the context, Robert Zemeckis won the Academy Award for Best Director"
        Extracted: "Academy Award for Best Director"
        """
        if not hypothesis or hypothesis == "Unknown":
            return ""

        prompt = f"""Question: {question}

Hypothesis: {hypothesis}

Extract ONLY the direct answer to the question. Be concise (1-10 words).
Do not include explanations, just the answer.

Answer:"""

        try:
            extracted = self.client.completion(prompt).strip()
            return extracted
        except:
            # Fallback: return last few words of hypothesis
            words = hypothesis.split()
            return " ".join(words[-5:]) if len(words) > 5 else hypothesis

    def refine_hypothesis(self, question: str, new_slice: RefinementSlice) -> tuple[str, str]:
        """
        Update hypothesis based on new context slice.

        Returns:
            (updated_hypothesis, extracted_answer)
        """
        self.iteration_count += 1

        # Accumulate context
        self.context_accumulated += f"\n\n[Context {self.iteration_count}]\n{new_slice.content}"

        # Build refinement prompt
        if not self.hypothesis or self.hypothesis == "Unknown":
            # First iteration
            prompt = f"""Question: {question}

Context:
{new_slice.content}

Based on this context, provide your initial hypothesis for answering the question.
If you don't have enough information yet, say what you've learned so far.

Be concise (1-30 words):"""
        else:
            # Subsequent iterations - UPDATE previous hypothesis
            prompt = f"""Question: {question}

Your current hypothesis: {self.hypothesis}

New context:
{new_slice.content}

All context so far:
{self.context_accumulated}

UPDATE your hypothesis based on the new context. Build on what you already know.
If the new context doesn't add relevant information, keep your current hypothesis.

Updated hypothesis (1-30 words):"""

        try:
            new_hypothesis = self.client.completion(prompt).strip()
        except Exception as e:
            print(f"  Error in refinement: {e}")
            new_hypothesis = self.hypothesis

        # Extract clean answer for F1 calculation
        extracted_answer = self.extract_answer(new_hypothesis, question)

        # Update state
        self.hypothesis = new_hypothesis

        return new_hypothesis, extracted_answer

    def reset(self):
        """Reset for new question."""
        self.hypothesis = ""
        self.context_accumulated = ""
        self.iteration_count = 0


def run_cumulative_refinement_experiment(
    example,
    slices: List[RefinementSlice],
    api_key: str,
    tracker: Optional[IterationTracker] = None
) -> dict:
    """
    Run cumulative refinement experiment showing gradual F1 convergence.

    Args:
        example: HotpotQA example
        slices: List of context slices
        api_key: Anthropic API key
        tracker: Optional iteration tracker

    Returns:
        Dict with experiment results
    """
    print(f"\n{'='*80}")
    print(f"Question: {example.question}")
    print(f"Ground Truth: {example.answer}")
    print(f"Slices: {len(slices)}")
    print(f"{'='*80}\n")

    system = CumulativeRefinementSystem(api_key=api_key)

    if tracker:
        trace = tracker.start_trace(example.question, example.answer)

    results = {
        'question': example.question,
        'ground_truth': example.answer,
        'iterations': []
    }

    print(f"{'Iter':<6} {'%':<6} {'F1':<8} {'Hypothesis':<50}")
    print("-"*80)

    for i, slice_obj in enumerate(slices):
        # Refine hypothesis
        hypothesis, extracted_answer = system.refine_hypothesis(
            example.question,
            slice_obj
        )

        # Calculate F1
        metrics = evaluate_answer(extracted_answer, example.answer)
        f1 = metrics['f1']

        # Track
        if tracker:
            tracker.add_checkpoint(
                iteration=i + 1,
                sub_rlm_calls=i + 1,
                current_hypothesis=extracted_answer,
                final_answer=extracted_answer if i == len(slices) - 1 else None
            )

        # Record
        pct = (i + 1) / len(slices) * 100
        results['iterations'].append({
            'iteration': i + 1,
            'percent': pct,
            'hypothesis': hypothesis,
            'extracted_answer': extracted_answer,
            'f1': f1,
            'has_supporting_fact': slice_obj.has_supporting_fact
        })

        # Print progress
        print(f"{i+1:<6} {pct:<6.1f} {f1:<8.3f} {extracted_answer[:50]}")

    if tracker:
        tracker.finish_trace()

    print()
    return results


if __name__ == "__main__":
    # Test with sample
    from evaluation.real_hotpotqa_examples import create_hard_hotpotqa_examples
    from evaluation.fine_grained_slicer import create_fine_grained_slices

    examples = create_hard_hotpotqa_examples()
    example = examples[0]

    slices = create_fine_grained_slices(example, num_slices=10)

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    results = run_cumulative_refinement_experiment(example, slices, api_key)

    print("\nFinal Results:")
    print(f"  Final F1: {results['iterations'][-1]['f1']:.3f}")
    print(f"  Final Answer: {results['iterations'][-1]['extracted_answer']}")
