"""
ACTUAL RLM integration with HotpotQA using real sub-calls.

This demonstrates:
1. Using RLM_REPL (not a standalone system)
2. Making actual sub-LLM calls via llm_query() on different context slices
3. Cumulative knowledge building through hypothesis tracking
"""
import os
import sys
sys.path.insert(0, '/home/user/rlm')

from rlm.rlm_repl import RLM_REPL
from evaluation.hotpotqa_loader import HotpotQAExample
from evaluation.real_hotpotqa_examples import create_hard_hotpotqa_examples
from evaluation.metrics import evaluate_answer
from dataclasses import dataclass


@dataclass
class ContextSlice:
    """Context slice for RLM."""
    content: dict | str
    metadata: dict


def create_rlm_context_slices(example: HotpotQAExample, num_slices: int = 6) -> dict:
    """
    Create context slices from HotpotQA example for RLM.

    Each slice contains part of the context, with supporting facts
    distributed across middle slices.

    Returns dict of {slice_id: ContextSlice}
    """
    # Flatten context into sentences
    all_sentences = []
    supporting_set = set(tuple(sf) for sf in example.supporting_facts)

    for doc_title, sentences in example.context:
        for sent_idx, sentence in enumerate(sentences):
            all_sentences.append({
                'title': doc_title,
                'sentence': sentence,
                'sent_idx': sent_idx,
                'is_supporting': (doc_title, sent_idx) in supporting_set
            })

    # Separate supporting and distractor sentences
    supporting = [s for s in all_sentences if s['is_supporting']]
    distractors = [s for s in all_sentences if not s['is_supporting']]

    # Create slices
    slices = {}
    sentences_per_slice = max(1, len(all_sentences) // num_slices)

    # Distribute supporting facts in middle slices (33-66%)
    support_start = num_slices // 3
    support_end = (num_slices * 2) // 3

    supporting_slices = list(range(support_start, support_end))
    support_per_slice = max(1, len(supporting) // len(supporting_slices))

    for i in range(num_slices):
        slice_id = f"slice_{i+1}"

        # Determine content for this slice
        if i in supporting_slices:
            # Include some supporting facts
            support_idx = supporting_slices.index(i)
            start_support = support_idx * support_per_slice
            end_support = min(start_support + support_per_slice, len(supporting))

            slice_sentences = supporting[start_support:end_support]

            # Add some distractors too
            distractor_count = sentences_per_slice - len(slice_sentences)
            if distractor_count > 0 and distractors:
                slice_sentences.extend(distractors[:distractor_count])
                distractors = distractors[distractor_count:]
        else:
            # Only distractors
            slice_sentences = distractors[:sentences_per_slice]
            distractors = distractors[sentences_per_slice:]

        # Format slice content
        content_lines = []
        for s in slice_sentences:
            content_lines.append(f"[{s['title']}] {s['sentence']}")

        slices[slice_id] = ContextSlice(
            content="\n".join(content_lines),
            metadata={
                'slice_num': i + 1,
                'percent': (i + 1) / num_slices * 100,
                'has_supporting': any(s['is_supporting'] for s in slice_sentences),
                'num_sentences': len(slice_sentences)
            }
        )

    return slices


def run_rlm_on_hotpotqa(
    example: HotpotQAExample,
    api_key: str,
    num_slices: int = 6,
    max_iterations: int = 10
) -> dict:
    """
    Run actual RLM on HotpotQA example with sub-calls on different context slices.

    This uses:
    - RLM_REPL (actual RLM system)
    - llm_query() for sub-LLM calls
    - Context slices for progressive information release
    - Hypothesis tracking for cumulative knowledge building
    """
    print(f"\n{'='*80}")
    print(f"Running RLM on HotpotQA")
    print(f"{'='*80}")
    print(f"Question: {example.question}")
    print(f"Ground Truth: {example.answer}")
    print(f"Context Slices: {num_slices}")
    print(f"{'='*80}\n")

    # Create context slices
    context_slices = create_rlm_context_slices(example, num_slices)

    print(f"📎 Created {len(context_slices)} context slices:")
    for slice_id, slice_obj in context_slices.items():
        has_support = "✓" if slice_obj.metadata['has_supporting'] else " "
        print(f"  [{has_support}] {slice_id}: {slice_obj.metadata['num_sentences']} sentences ({slice_obj.metadata['percent']:.1f}%)")
    print()

    # Initialize RLM_REPL with context slices
    # Note: RLM uses OpenAI, so we need OPENAI_API_KEY
    os.environ['OPENAI_API_KEY'] = api_key

    rlm = RLM_REPL(
        api_key=api_key,
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini",
        max_iterations=max_iterations,
        enable_logging=True
    )

    # Setup context with slices
    # Convert slices to dict format expected by RLM
    rlm.setup_context(
        context={},  # Empty main context, we'll use slices
        query=example.question,
        enable_slicing=False  # We provide our own slices
    )

    # Manually set context slices in REPL environment
    rlm.repl_env.context_slices = context_slices

    # Add helper for getting slice content
    def get_slice_content(slice_id: str) -> str:
        """Get content of a specific slice."""
        if slice_id in context_slices:
            return context_slices[slice_id].content
        return f"Slice {slice_id} not found"

    rlm.repl_env.globals['get_slice_content'] = get_slice_content

    print("🚀 Starting RLM iteration with sub-calls...")
    print("-" * 80)

    # Track sub-call results
    sub_call_results = []

    # Run RLM completion
    try:
        result = rlm.completion(
            context={},
            query=example.question
        )

        print(f"\n{'='*80}")
        print("RLM FINAL RESULT")
        print(f"{'='*80}")
        print(f"Answer: {result}")
        print(f"Ground Truth: {example.answer}")

        # Evaluate
        metrics = evaluate_answer(result, example.answer)
        print(f"\nMetrics:")
        print(f"  F1: {metrics['f1']:.3f}")
        print(f"  EM: {metrics['em']:.3f}")

        # Get hypothesis history
        hypothesis_history = rlm.repl_env.get_hypothesis_history()
        current_hypothesis = rlm.repl_env.get_hypothesis()

        print(f"\n{'='*80}")
        print("CUMULATIVE HYPOTHESIS BUILDING")
        print(f"{'='*80}")
        print(f"Hypothesis updates: {len(hypothesis_history)}")
        for i, hyp in enumerate(hypothesis_history):
            print(f"\n{i+1}. {hyp}")

        if current_hypothesis:
            print(f"\nFinal hypothesis: {current_hypothesis}")

        return {
            'question': example.question,
            'ground_truth': example.answer,
            'rlm_answer': result,
            'metrics': metrics,
            'hypothesis_history': hypothesis_history,
            'current_hypothesis': current_hypothesis,
            'num_slices': num_slices,
        }

    except Exception as e:
        print(f"\n❌ Error running RLM: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'question': example.question,
        }


if __name__ == "__main__":
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    # Load HotpotQA examples
    print("Loading HotpotQA examples...")
    examples = create_hard_hotpotqa_examples()

    # Run on first example
    example = examples[0]

    result = run_rlm_on_hotpotqa(
        example=example,
        api_key=api_key,
        num_slices=6,
        max_iterations=10
    )

    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)
