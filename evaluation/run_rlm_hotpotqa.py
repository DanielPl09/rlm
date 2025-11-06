"""
Run ACTUAL RLM on HotpotQA with sub-calls on different context slices.

Uses:
- RLM_REPL with Anthropic (actual RLM system, not standalone)
- llm_query() for sub-LLM calls on different data parts
- Cumulative hypothesis building through update_hypothesis()
"""
import os
import sys
sys.path.insert(0, '/home/user/rlm')

from evaluation.tracked_rlm_anthropic import TrackedRLM_Anthropic
from evaluation.iteration_tracker import IterationTracker
from evaluation.hotpotqa_loader import HotpotQAExample
from evaluation.real_hotpotqa_examples import create_hard_hotpotqa_examples
from evaluation.metrics import evaluate_answer
from evaluation.anthropic_repl import create_anthropic_repl_env
from dataclasses import dataclass
import time


@dataclass
class ContextSlice:
    """Context slice for RLM."""
    content: str
    metadata: dict


def create_hotpotqa_slices(example: HotpotQAExample, num_slices: int = 6) -> dict:
    """
    Create context slices from HotpotQA for RLM sub-calls.

    Strategy:
    - Split context into multiple slices
    - Distribute supporting facts across middle slices (33-66%)
    - Add distractors to each slice
    """
    # Flatten all sentences
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

    # Separate
    supporting = [s for s in all_sentences if s['is_supporting']]
    distractors = [s for s in all_sentences if not s['is_supporting']]

    # Create slices
    slices = {}

    # Distribute supporting facts in middle slices
    support_start_slice = num_slices // 3
    support_end_slice = (num_slices * 2) // 3
    supporting_slice_indices = list(range(support_start_slice, support_end_slice))

    support_per_slice = max(1, len(supporting) // len(supporting_slice_indices))

    for i in range(num_slices):
        slice_id = f"slice_{i+1}"

        slice_sentences = []

        # Add supporting facts if in middle range
        if i in supporting_slice_indices:
            support_idx = supporting_slice_indices.index(i)
            start = support_idx * support_per_slice
            end = min(start + support_per_slice, len(supporting))
            slice_sentences.extend(supporting[start:end])

        # Add distractors (2-3 per slice)
        distractor_count = 2
        if len(distractors) >= distractor_count:
            slice_sentences.extend(distractors[:distractor_count])
            distractors = distractors[distractor_count:]

        # Format content
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


def run_rlm_hotpotqa_experiment(
    example: HotpotQAExample,
    api_key: str,
    num_slices: int = 6
) -> dict:
    """
    Run RLM on HotpotQA with sub-calls on different context slices.

    This demonstrates:
    1. Using actual RLM (TrackedRLM_Anthropic)
    2. Making sub-calls via llm_query() on different data parts
    3. Cumulative knowledge building via update_hypothesis()
    """
    print(f"\n{'='*80}")
    print(f"RLM + HotpotQA Experiment")
    print(f"{'='*80}")
    print(f"Question: {example.question}")
    print(f"Answer: {example.answer}")
    print(f"Context slices: {num_slices}")
    print(f"{'='*80}\n")

    # Create context slices
    context_slices = create_hotpotqa_slices(example, num_slices)

    print(f"📎 Created {len(context_slices)} context slices:")
    for slice_id, slice_obj in context_slices.items():
        marker = "✓" if slice_obj.metadata['has_supporting'] else " "
        print(f"  [{marker}] {slice_id}: {slice_obj.metadata['num_sentences']} sentences ({slice_obj.metadata['percent']:.1f}%)")
    print()

    # Initialize tracker
    tracker = IterationTracker()

    # Initialize RLM with Anthropic
    rlm = TrackedRLM_Anthropic(
        api_key=api_key,
        model="claude-3-opus-20240229",
        recursive_model="claude-3-opus-20240229",
        tracker=tracker,
        ground_truth=example.answer,
        max_iterations=15,
        enable_logging=True
    )

    # Set query and messages manually (bypass setup_context which creates OpenAI sub_rlm)
    from rlm.utils.prompts import build_system_prompt
    rlm.query = example.question
    rlm.messages = build_system_prompt()

    # Create REPL env with Anthropic sub-RLM
    rlm.repl_env = create_anthropic_repl_env(
        api_key=api_key,
        context_slices=context_slices,
        model="claude-3-opus-20240229"
    )

    print("🚀 Running RLM with sub-calls on different context slices...")
    print("-" * 80)
    print()

    try:
        # Run RLM  (already setup, just run the main loop)
        start_time = time.time()

        # Run the main RLM loop directly
        from rlm.utils.prompts import next_action_prompt
        import rlm.utils.utils as utils

        for iteration in range(rlm._max_iterations):
            response = rlm.llm.completion(rlm.messages + [next_action_prompt(rlm.query, iteration)])

            code_blocks = utils.find_code_blocks(response)
            rlm.logger.log_model_response(response, has_tool_calls=code_blocks is not None)

            if code_blocks is not None:
                rlm.messages = utils.process_code_execution(
                    response, rlm.messages, rlm.repl_env,
                    rlm.repl_env_logger, rlm.logger
                )
            else:
                assistant_message = {"role": "assistant", "content": "You responded with:\n" + response}
                rlm.messages.append(assistant_message)

            # Check for final answer
            final_answer = utils.check_for_final_answer(response, rlm.repl_env, rlm.logger)

            if final_answer:
                rlm.logger.log_final_response(final_answer)
                break

        if not final_answer:
            # Force final answer
            rlm.messages.append(next_action_prompt(rlm.query, iteration, final_answer=True))
            final_answer = rlm.llm.completion(rlm.messages)
            rlm.logger.log_final_response(final_answer)

        end_time = time.time()

        print(f"\n{'='*80}")
        print("RLM RESULTS")
        print(f"{'='*80}")
        print(f"Final Answer: {final_answer}")
        print(f"Ground Truth: {example.answer}")
        print(f"Time: {end_time - start_time:.2f}s")
        print(f"Sub-LLM calls: {rlm.sub_rlm_call_count}")

        # Evaluate
        metrics = evaluate_answer(final_answer, example.answer)
        print(f"\nMetrics:")
        print(f"  F1: {metrics['f1']:.3f}")
        print(f"  EM: {metrics['em']:.3f}")

        # Get hypothesis history (cumulative building)
        hypothesis_history = rlm.repl_env.get_hypothesis_history()
        current_hypothesis = rlm.repl_env.get_hypothesis()

        print(f"\n{'='*80}")
        print("CUMULATIVE HYPOTHESIS BUILDING")
        print(f"{'='*80}")
        print(f"Total updates: {len(hypothesis_history)}")

        if hypothesis_history:
            for i, hyp in enumerate(hypothesis_history, 1):
                print(f"\n{i}. {hyp[:100]}{'...' if len(hyp) > 100 else ''}")

        if current_hypothesis:
            print(f"\nFinal hypothesis:")
            print(f"  {current_hypothesis}")

        # Get iteration tracker results
        if tracker.traces:
            trace = tracker.traces[0]
            print(f"\n{'='*80}")
            print("ITERATION BREAKDOWN")
            print(f"{'='*80}")

            for checkpoint in trace.checkpoints:
                print(f"\nIteration {checkpoint.iteration} (sub-calls: {checkpoint.sub_rlm_calls}):")
                print(f"  Time: {checkpoint.cumulative_time:.2f}s")
                print(f"  F1: {checkpoint.metrics.get('f1', 0):.3f}")
                print(f"  Hypothesis: {checkpoint.current_hypothesis[:80]}...")

        return {
            'question': example.question,
            'ground_truth': example.answer,
            'rlm_answer': final_answer,
            'metrics': metrics,
            'time': end_time - start_time,
            'sub_rlm_calls': rlm.sub_rlm_call_count,
            'hypothesis_history': hypothesis_history,
            'current_hypothesis': current_hypothesis,
            'trace': trace if tracker.traces else None,
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


if __name__ == "__main__":
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        print("Set it: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    # Load HotpotQA
    print("Loading HotpotQA examples...")
    examples = create_hard_hotpotqa_examples()

    # Run on first example
    example = examples[0]

    result = run_rlm_hotpotqa_experiment(
        example=example,
        api_key=api_key,
        num_slices=6
    )

    print(f"\n{'='*80}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*80}")

    if 'error' not in result:
        print(f"✅ RLM successfully ran with {result['sub_rlm_calls']} sub-calls")
        print(f"✅ Cumulative hypothesis updated {len(result['hypothesis_history'])} times")
        print(f"✅ Final F1: {result['metrics']['f1']:.3f}")
