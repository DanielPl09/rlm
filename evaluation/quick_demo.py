#!/usr/bin/env python3
"""
Quick demo script to verify 80/20 evaluation framework and see it in action.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation import (
    create_sample_examples,
    create_tracked_rlm,
    IterationTracker
)


def run_demo(api_key: str = None, model: str = "gpt-5"):
    """
    Run a quick demo with one sample example.

    Args:
        api_key: API key for LLM (or use environment variable)
        model: Model name to use
    """
    # Get API key
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ Error: No API key provided")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        print("Or pass --api_key argument")
        return

    print("="*80)
    print("RLM ITERATIVE REFINEMENT: 80/20 PRINCIPLE DEMO")
    print("="*80)
    print()

    # Get sample examples
    print("📚 Loading sample HotpotQA examples...")
    examples = create_sample_examples()
    example = examples[0]  # Use first example

    print(f"✅ Loaded example: {example.example_id}")
    print()
    print(f"Question: {example.question}")
    print(f"Ground Truth: {example.answer}")
    print()
    print("-"*80)
    print()

    # Create tracker
    tracker = IterationTracker()

    # Create tracked RLM
    print("🤖 Creating tracked RLM...")
    rlm = create_tracked_rlm(
        api_key=api_key,
        model=model,
        tracker=tracker,
        ground_truth=example.answer,
        max_iterations=15,  # Reduced for demo
        enable_logging=True
    )

    print("✅ Tracked RLM created")
    print()
    print("🚀 Running iterative refinement...")
    print("="*80)
    print()

    # Run completion
    try:
        answer = rlm.completion(
            context=example.get_context_dict(),
            query=example.question
        )

        print()
        print("="*80)
        print("📊 RESULTS")
        print("="*80)
        print()

        print(f"Predicted Answer: {answer}")
        print(f"Ground Truth: {example.answer}")
        print()

        # Get trace
        if tracker.traces:
            trace = tracker.traces[0]

            # Final metrics
            final_metrics = trace.get_final_metrics()
            print(f"Final F1 Score: {final_metrics['f1']:.3f}")
            print(f"Exact Match: {final_metrics['exact_match']:.0f}")
            print(f"Total Time: {trace.total_time:.2f}s")
            print(f"Total Sub-RLM Calls: {trace.total_sub_rlm_calls}")
            print()

            # Metrics at 20%
            metrics_20_time = trace.get_metrics_at_time(0.2)
            metrics_20_calls = trace.get_metrics_at_calls(0.2)

            print("-"*80)
            print("⚡ 80/20 PRINCIPLE DEMONSTRATION")
            print("-"*80)
            print()

            if metrics_20_time:
                quality_ratio_time = metrics_20_time['f1'] / final_metrics['f1'] if final_metrics['f1'] > 0 else 0
                time_20 = trace.total_time * 0.2

                print(f"At 20% Time ({time_20:.2f}s):")
                print(f"  F1 Score: {metrics_20_time['f1']:.3f}")
                print(f"  Quality Achieved: {quality_ratio_time:.1%} of final quality")
                print(f"  Demonstrates 80/20: {'✅ YES' if quality_ratio_time >= 0.75 else '❌ NO'}")
                print()

            if metrics_20_calls:
                quality_ratio_calls = metrics_20_calls['f1'] / final_metrics['f1'] if final_metrics['f1'] > 0 else 0
                calls_20 = int(trace.total_sub_rlm_calls * 0.2)

                print(f"At 20% Calls ({calls_20} calls):")
                print(f"  F1 Score: {metrics_20_calls['f1']:.3f}")
                print(f"  Quality Achieved: {quality_ratio_calls:.1%} of final quality")
                print(f"  Demonstrates 80/20: {'✅ YES' if quality_ratio_calls >= 0.75 else '❌ NO'}")
                print()

            # Show progression
            print("-"*80)
            print("📈 QUALITY PROGRESSION")
            print("-"*80)
            print()

            progression = trace.get_quality_progression('f1')
            if progression:
                print(f"{'Time (s)':<12} {'F1 Score':<12} {'Sub-RLM Calls':<15}")
                print("-" * 40)

                # Show first few, middle, and last checkpoints
                checkpoints_to_show = []
                if len(progression) <= 10:
                    checkpoints_to_show = progression
                else:
                    # Show first 3, middle 2, last 3
                    checkpoints_to_show = (
                        progression[:3] +
                        [progression[len(progression)//2 - 1], progression[len(progression)//2]] +
                        progression[-3:]
                    )

                for time_val, f1_val, calls in checkpoints_to_show:
                    print(f"{time_val:<12.2f} {f1_val:<12.3f} {calls:<15}")

                if len(progression) > 10:
                    print(f"... ({len(progression) - 8} more checkpoints) ...")

        print()
        print("="*80)
        print("✅ Demo completed successfully!")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Run full experiment: python -m evaluation.run_experiment")
        print("2. Try more examples: --num_examples 10")
        print("3. Generate visualizations: python -m evaluation.visualize results/experiment_*.json")
        print()

    except Exception as e:
        print()
        print("="*80)
        print("❌ ERROR")
        print("="*80)
        print(f"Error during execution: {str(e)}")
        print()
        import traceback
        traceback.print_exc()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Quick demo of 80/20 evaluation framework")
    parser.add_argument("--api_key", type=str, help="API key (or use environment variable)")
    parser.add_argument("--model", type=str, default="gpt-5", help="Model name (default: gpt-5)")

    args = parser.parse_args()

    run_demo(api_key=args.api_key, model=args.model)


if __name__ == "__main__":
    main()
