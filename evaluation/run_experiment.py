"""
Experiment runner for demonstrating 80/20 principle in iterative refinement.
"""
import os
import json
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from evaluation.hotpotqa_loader import HotpotQALoader, create_sample_examples
from evaluation.iteration_tracker import IterationTracker
from evaluation.tracked_rlm import create_tracked_rlm


def run_single_example(
    example,
    tracker: IterationTracker,
    api_key: str,
    model: str = "gpt-5",
    max_iterations: int = 20,
    enable_logging: bool = True
) -> Dict[str, Any]:
    """
    Run iterative refinement on a single HotpotQA example.

    Args:
        example: HotpotQA example
        tracker: IterationTracker instance
        api_key: API key for LLM
        model: Model name
        max_iterations: Maximum iterations allowed
        enable_logging: Whether to enable console logging

    Returns:
        Dictionary with results
    """
    print(f"\n{'='*80}")
    print(f"Question: {example.question}")
    print(f"Ground Truth: {example.answer}")
    print(f"{'='*80}\n")

    # Create tracked RLM
    rlm = create_tracked_rlm(
        api_key=api_key,
        model=model,
        tracker=tracker,
        ground_truth=example.answer,
        max_iterations=max_iterations,
        enable_logging=enable_logging
    )

    # Get context as dictionary for better slicing
    context = example.get_context_dict()

    # Run completion
    try:
        answer = rlm.completion(context=context, query=example.question)

        result = {
            'question_id': example.example_id,
            'question': example.question,
            'ground_truth': example.answer,
            'predicted_answer': answer,
            'success': True
        }

        # Get final metrics
        if tracker.traces:
            final_metrics = tracker.traces[-1].get_final_metrics()
            result['final_metrics'] = final_metrics
            result['total_time'] = tracker.traces[-1].total_time
            result['total_calls'] = tracker.traces[-1].total_sub_rlm_calls

            # Get 20% metrics
            metrics_20_time = tracker.traces[-1].get_metrics_at_time(0.2)
            metrics_20_calls = tracker.traces[-1].get_metrics_at_calls(0.2)

            result['metrics_at_20pct_time'] = metrics_20_time
            result['metrics_at_20pct_calls'] = metrics_20_calls

        print(f"\n✅ Answer: {answer}")
        print(f"📊 Final F1: {result.get('final_metrics', {}).get('f1', 0):.3f}")

        if result.get('metrics_at_20pct_time'):
            print(f"📊 F1 at 20% time: {result['metrics_at_20pct_time']['f1']:.3f}")
        if result.get('metrics_at_20pct_calls'):
            print(f"📊 F1 at 20% calls: {result['metrics_at_20pct_calls']['f1']:.3f}")

        return result

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'question_id': example.example_id,
            'question': example.question,
            'ground_truth': example.answer,
            'predicted_answer': None,
            'success': False,
            'error': str(e)
        }


def run_experiment(
    examples: List,
    api_key: str,
    model: str = "gpt-5",
    max_iterations: int = 20,
    output_dir: str = "results",
    enable_logging: bool = True
) -> Dict[str, Any]:
    """
    Run experiment on multiple HotpotQA examples.

    Args:
        examples: List of HotpotQA examples
        api_key: API key for LLM
        model: Model name
        max_iterations: Maximum iterations per example
        output_dir: Directory to save results
        enable_logging: Whether to enable console logging

    Returns:
        Dictionary with aggregate results
    """
    print(f"\n🚀 Starting experiment with {len(examples)} examples")
    print(f"Model: {model}")
    print(f"Max iterations: {max_iterations}")
    print(f"Output directory: {output_dir}\n")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize tracker
    tracker = IterationTracker()

    # Run each example
    results = []
    for idx, example in enumerate(examples):
        print(f"\n[{idx+1}/{len(examples)}] Running example {example.example_id}")

        result = run_single_example(
            example=example,
            tracker=tracker,
            api_key=api_key,
            model=model,
            max_iterations=max_iterations,
            enable_logging=enable_logging
        )

        results.append(result)

        # Save intermediate results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(output_dir, f"results_{timestamp}.json")

        with open(results_file, 'w') as f:
            json.dump({
                'results': results,
                'completed': idx + 1,
                'total': len(examples)
            }, f, indent=2)

    # Calculate aggregate statistics
    aggregate_stats = tracker.get_aggregate_stats()

    # Add success rate
    successful = [r for r in results if r.get('success', False)]
    aggregate_stats['success_rate'] = len(successful) / len(results) if results else 0
    aggregate_stats['total_examples'] = len(results)

    # Calculate 80/20 demonstration metrics
    if aggregate_stats.get('avg_f1_at_20pct_time') and aggregate_stats.get('avg_final_f1'):
        quality_ratio_time = aggregate_stats['avg_f1_at_20pct_time'] / aggregate_stats['avg_final_f1']
        aggregate_stats['quality_achieved_at_20pct_time'] = quality_ratio_time
        aggregate_stats['demonstrates_80_20_time'] = quality_ratio_time >= 0.75  # 75% is close to 80%

    if aggregate_stats.get('avg_f1_at_20pct_calls') and aggregate_stats.get('avg_final_f1'):
        quality_ratio_calls = aggregate_stats['avg_f1_at_20pct_calls'] / aggregate_stats['avg_final_f1']
        aggregate_stats['quality_achieved_at_20pct_calls'] = quality_ratio_calls
        aggregate_stats['demonstrates_80_20_calls'] = quality_ratio_calls >= 0.75

    # Print summary
    print(f"\n{'='*80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    print(f"Total examples: {aggregate_stats['total_examples']}")
    print(f"Success rate: {aggregate_stats['success_rate']:.1%}")
    print(f"\n📊 Final Performance:")
    print(f"  Average F1: {aggregate_stats.get('avg_final_f1', 0):.3f}")
    print(f"  Average EM: {aggregate_stats.get('avg_final_em', 0):.3f}")
    print(f"  Average time: {aggregate_stats.get('avg_total_time', 0):.2f}s")
    print(f"  Average calls: {aggregate_stats.get('avg_total_calls', 0):.1f}")

    if aggregate_stats.get('avg_f1_at_20pct_time'):
        print(f"\n⚡ Performance at 20% Time:")
        print(f"  F1 score: {aggregate_stats['avg_f1_at_20pct_time']:.3f}")
        print(f"  Quality ratio: {aggregate_stats['quality_achieved_at_20pct_time']:.1%}")
        print(f"  Demonstrates 80/20: {'✅ YES' if aggregate_stats.get('demonstrates_80_20_time') else '❌ NO'}")

    if aggregate_stats.get('avg_f1_at_20pct_calls'):
        print(f"\n⚡ Performance at 20% Calls:")
        print(f"  F1 score: {aggregate_stats['avg_f1_at_20pct_calls']:.3f}")
        print(f"  Quality ratio: {aggregate_stats['quality_achieved_at_20pct_calls']:.1%}")
        print(f"  Demonstrates 80/20: {'✅ YES' if aggregate_stats.get('demonstrates_80_20_calls') else '❌ NO'}")

    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_results = {
        'experiment_info': {
            'timestamp': timestamp,
            'model': model,
            'max_iterations': max_iterations,
            'num_examples': len(examples)
        },
        'aggregate_stats': aggregate_stats,
        'individual_results': results,
        'traces': [trace.to_dict() for trace in tracker.traces]
    }

    output_file = os.path.join(output_dir, f"experiment_{timestamp}.json")
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")
    print(f"{'='*80}\n")

    return final_results


def main():
    parser = argparse.ArgumentParser(
        description="Run 80/20 evaluation experiment on HotpotQA"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to HotpotQA JSON file (default: use sample examples)"
    )
    parser.add_argument(
        "--num_examples",
        type=int,
        default=None,
        help="Number of examples to run (default: all)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5",
        help="Model name to use (default: gpt-5)"
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=20,
        help="Maximum iterations per example (default: 20)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="results",
        help="Output directory for results (default: results)"
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="API key (default: use environment variable)"
    )
    parser.add_argument(
        "--no_logging",
        action="store_true",
        help="Disable console logging"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API key must be provided via --api_key or environment variable")

    # Load examples
    if args.dataset:
        loader = HotpotQALoader(args.dataset)
        examples = loader.get_examples(end=args.num_examples)
        print(f"Loaded {len(examples)} examples from {args.dataset}")
    else:
        examples = create_sample_examples()
        if args.num_examples:
            examples = examples[:args.num_examples]
        print(f"Using {len(examples)} sample examples")

    # Run experiment
    results = run_experiment(
        examples=examples,
        api_key=api_key,
        model=args.model,
        max_iterations=args.max_iterations,
        output_dir=args.output_dir,
        enable_logging=not args.no_logging
    )

    return results


if __name__ == "__main__":
    main()
