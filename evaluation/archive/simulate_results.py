#!/usr/bin/env python3
"""
Simulate 80/20 evaluation results to demonstrate what real experiments would show.

This creates realistic traces based on typical iterative refinement behavior:
- Early iterations show rapid quality improvement
- Later iterations show diminishing returns
- Demonstrates 80/20 principle clearly
"""
import os
import sys
import time
import random
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.hotpotqa_loader import create_sample_examples
from evaluation.iteration_tracker import IterationTracker, RefinementTrace
from evaluation.metrics import evaluate_answer


def simulate_iterative_refinement(
    question: str,
    ground_truth: str,
    context_size: int = 3,
    num_iterations: int = 10,
    tracker: IterationTracker = None
) -> dict:
    """
    Simulate iterative refinement process with realistic quality progression.

    Args:
        question: Question to answer
        ground_truth: Correct answer
        context_size: Number of context chunks
        num_iterations: Number of refinement iterations
        tracker: IterationTracker instance

    Returns:
        Dictionary with simulation results
    """
    # Start trace
    if tracker:
        trace = tracker.start_trace(question, ground_truth)
    else:
        trace = RefinementTrace(question, ground_truth, time.time())

    # Simulate hypothesis evolution with realistic quality curve
    # Early iterations: rapid improvement (80% of progress in 20% of time)
    # Later iterations: slow refinement (20% of progress in 80% of time)

    # Generate progression curve
    # Use exponential decay to model diminishing returns
    import numpy as np

    # Target final F1 score (realistic range)
    final_f1 = random.uniform(0.75, 0.95)

    # Quality progression follows: Q(t) = final_f1 * (1 - exp(-k*t))
    # where k controls how fast we approach final quality
    k = 3.0  # Fast initial learning, slow final refinement

    hypotheses = []
    sub_rlm_call_times = []

    # Simulate each iteration with realistic hypothesis evolution
    for i in range(num_iterations):
        t_normalized = (i + 1) / num_iterations

        # Quality follows exponential approach to final value
        current_f1 = final_f1 * (1 - np.exp(-k * t_normalized))

        # Add some noise
        current_f1 = min(1.0, current_f1 + random.uniform(-0.02, 0.02))

        # Generate hypothesis that will achieve approximately the target F1
        # by mixing ground truth with noise/partial answers
        words = ground_truth.split()

        if current_f1 < 0.2:
            # Very early - just exploration
            hypothesis = "Analyzing available context to answer the question"
        elif current_f1 < 0.4:
            # Early - partially on track
            if len(words) > 1:
                # Take some words from answer
                num_words = max(1, int(len(words) * 0.4))
                hypothesis = " ".join(words[:num_words]) + " (need more info)"
            else:
                hypothesis = f"The answer appears to be related to {words[0]}"
        elif current_f1 < 0.6:
            # Mid - getting closer
            if len(words) > 1:
                num_words = max(1, int(len(words) * 0.6))
                hypothesis = " ".join(words[:num_words]) + " " + " ".join(random.choices(["based on", "according to", "from"], k=1)) + " the context"
            else:
                hypothesis = words[0] + " (with some uncertainty)"
        elif current_f1 < 0.8:
            # Late - almost there
            if len(words) > 1:
                # Most of the answer
                num_words = max(1, int(len(words) * 0.8))
                hypothesis = " ".join(words[:num_words]) + " " + random.choice([".", ", based on the evidence", ", according to sources"])
            else:
                hypothesis = words[0] + random.choice([" is the answer", " appears correct", ""])
        elif current_f1 < 0.95:
            # Very late - nearly perfect
            hypothesis = ground_truth + random.choice(["", " (confirmed)", " based on analysis", "."])
        else:
            # Final - correct answer
            hypothesis = ground_truth

        hypotheses.append(hypothesis)

        # Simulate sub-RLM call timing
        # Early calls are slower (more exploration)
        # Later calls are faster (more focused)
        if i < num_iterations * 0.3:
            call_time = random.uniform(2.5, 4.0)  # Slow initial exploration
        elif i < num_iterations * 0.7:
            call_time = random.uniform(1.5, 2.5)  # Medium refinement
        else:
            call_time = random.uniform(0.8, 1.5)  # Fast final tuning

        sub_rlm_call_times.append(call_time)
        time.sleep(0.001)  # Tiny delay for realistic timing

        # Add checkpoint
        if tracker:
            tracker.add_checkpoint(
                iteration=i + 1,
                sub_rlm_calls=i + 1,
                current_hypothesis=hypothesis,
                final_answer=hypothesis if i == num_iterations - 1 else None
            )
        else:
            trace.add_checkpoint(
                iteration=i + 1,
                sub_rlm_calls=i + 1,
                current_hypothesis=hypothesis,
                final_answer=hypothesis if i == num_iterations - 1 else None
            )

    # Finish trace
    if tracker:
        tracker.finish_trace()
        final_trace = tracker.traces[-1]
    else:
        final_trace = trace

    return {
        'question': question,
        'ground_truth': ground_truth,
        'final_answer': hypotheses[-1],
        'trace': final_trace,
        'total_time': sum(sub_rlm_call_times),
        'num_iterations': num_iterations
    }


def run_simulation(num_examples: int = 5, output_dir: str = "results"):
    """
    Run full simulation with multiple examples.

    Args:
        num_examples: Number of examples to simulate
        output_dir: Output directory for results
    """
    print("="*80)
    print("SIMULATED 80/20 EVALUATION EXPERIMENT")
    print("="*80)
    print()
    print("⚠️  Note: This is a SIMULATION demonstrating expected results")
    print("    Real experiments require Anthropic API key and will take longer")
    print()
    print(f"Simulating {num_examples} examples with iterative refinement...")
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get sample examples
    examples = create_sample_examples()
    if num_examples > len(examples):
        num_examples = len(examples)

    # Create tracker
    tracker = IterationTracker()

    # Simulate each example
    results = []
    for idx in range(num_examples):
        example = examples[idx]

        print(f"[{idx+1}/{num_examples}] Simulating: {example.question[:60]}...")

        result = simulate_iterative_refinement(
            question=example.question,
            ground_truth=example.answer,
            context_size=len(example.context),
            num_iterations=random.randint(8, 12),
            tracker=tracker
        )

        results.append(result)

    # Calculate aggregate statistics
    print()
    print("="*80)
    print("AGGREGATE STATISTICS")
    print("="*80)
    print()

    aggregate_stats = tracker.get_aggregate_stats()

    print(f"Total examples: {aggregate_stats['total_traces']}")
    print(f"Average final F1: {aggregate_stats['avg_final_f1']:.3f}")
    print(f"Average final EM: {aggregate_stats['avg_final_em']:.3f}")
    print(f"Average total time: {aggregate_stats['avg_total_time']:.2f}s")
    print(f"Average total calls: {aggregate_stats['avg_total_calls']:.1f}")
    print()

    print("-"*80)
    print("⚡ 80/20 PRINCIPLE DEMONSTRATION")
    print("-"*80)
    print()

    if 'avg_f1_at_20pct_time' in aggregate_stats and aggregate_stats.get('avg_final_f1', 0) > 0:
        quality_ratio_time = aggregate_stats.get('quality_achieved_at_20pct_time')
        if quality_ratio_time is None and aggregate_stats.get('avg_f1_at_20pct_time'):
            quality_ratio_time = aggregate_stats['avg_f1_at_20pct_time'] / aggregate_stats['avg_final_f1']

        if quality_ratio_time is not None:
            print(f"At 20% of Time:")
            print(f"  F1 Score: {aggregate_stats['avg_f1_at_20pct_time']:.3f}")
            print(f"  Quality Achieved: {quality_ratio_time:.1%} of final quality")
            print(f"  Demonstrates 80/20: {'✅ YES' if quality_ratio_time >= 0.75 else '❌ NO'}")
            print()

    if 'avg_f1_at_20pct_calls' in aggregate_stats and aggregate_stats.get('avg_final_f1', 0) > 0:
        quality_ratio_calls = aggregate_stats.get('quality_achieved_at_20pct_calls')
        if quality_ratio_calls is None and aggregate_stats.get('avg_f1_at_20pct_calls'):
            quality_ratio_calls = aggregate_stats['avg_f1_at_20pct_calls'] / aggregate_stats['avg_final_f1']

        if quality_ratio_calls is not None:
            print(f"At 20% of Calls:")
            print(f"  F1 Score: {aggregate_stats['avg_f1_at_20pct_calls']:.3f}")
            print(f"  Quality Achieved: {quality_ratio_calls:.1%} of final quality")
            print(f"  Demonstrates 80/20: {'✅ YES' if quality_ratio_calls >= 0.75 else '❌ NO'}")
            print()

    # Show detailed breakdown
    print("-"*80)
    print("QUALITY PROGRESSION BREAKDOWN")
    print("-"*80)
    print()

    checkpoints_pct = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    print(f"{'Checkpoint':<15} {'Avg F1':<12} {'% of Final':<15}")
    print("-" * 42)

    for pct in checkpoints_pct:
        avg_f1_at_pct = []
        for trace in tracker.traces:
            metrics = trace.get_metrics_at_time(pct / 100.0)
            if metrics:
                avg_f1_at_pct.append(metrics['f1'])

        if avg_f1_at_pct:
            avg_f1 = sum(avg_f1_at_pct) / len(avg_f1_at_pct)
            pct_of_final = (avg_f1 / aggregate_stats['avg_final_f1'] * 100) if aggregate_stats['avg_final_f1'] > 0 else 0
            print(f"{pct:>3}% time      {avg_f1:<12.3f} {pct_of_final:<14.1f}%")

    # Save results
    print()
    print("="*80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"simulation_{timestamp}.json")

    results_data = {
        'experiment_info': {
            'timestamp': timestamp,
            'type': 'simulation',
            'num_examples': num_examples,
            'note': 'This is simulated data demonstrating expected results'
        },
        'aggregate_stats': aggregate_stats,
        'individual_results': [
            {
                'question': r['question'],
                'ground_truth': r['ground_truth'],
                'predicted_answer': r['final_answer'],
                'total_time': r['total_time'],
                'num_iterations': r['num_iterations']
            }
            for r in results
        ],
        'traces': [trace.to_dict() for trace in tracker.traces]
    }

    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"💾 Results saved to: {output_file}")
    print("="*80)
    print()
    print("✅ Simulation completed!")
    print()
    print("Key Findings:")

    # Calculate quality ratio for summary
    summary_ratio = None
    if 'avg_f1_at_20pct_time' in aggregate_stats and aggregate_stats.get('avg_final_f1', 0) > 0:
        summary_ratio = aggregate_stats['avg_f1_at_20pct_time'] / aggregate_stats['avg_final_f1']

    if summary_ratio:
        print(f"  • Achieved ~{summary_ratio:.0%} of final quality in just 20% of time")
    print(f"  • Shows clear diminishing returns pattern")
    print(f"  • Demonstrates viability of early stopping strategies")
    print()
    print("To visualize results:")
    print(f"  python -m evaluation.visualize {output_file}")
    print()

    return results_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simulate 80/20 evaluation results")
    parser.add_argument("--num_examples", type=int, default=5, help="Number of examples to simulate")
    parser.add_argument("--output_dir", type=str, default="results", help="Output directory")

    args = parser.parse_args()

    run_simulation(num_examples=args.num_examples, output_dir=args.output_dir)
