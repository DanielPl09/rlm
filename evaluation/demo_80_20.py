#!/usr/bin/env python3
"""
Simple demonstration of 80/20 principle with realistic simulated data.
Shows what you would expect from real RLM iterative refinement experiments.
"""
import json
import os


def create_realistic_demo_results():
    """
    Create realistic demo results showing 80/20 principle.

    Based on typical patterns in iterative refinement:
    - First 20% of iterations get most of the answer (rapid convergence)
    - Remaining 80% fine-tune and verify (diminishing returns)
    """

    # Realistic progression example 1: Fast early convergence
    example1 = {
        "question": "What is the capital of the country where the Eiffel Tower is located?",
        "ground_truth": "Paris",
        "iterations": [
            {"pct": 10, "time_s": 2.3, "calls": 1, "hypothesis": "Eiffel Tower is in Paris", "f1": 0.67},
            {"pct": 20, "time_s": 4.8, "calls": 2, "hypothesis": "Paris is the capital", "f1": 0.80},  # 20% time → 80% quality!
            {"pct": 30, "time_s": 7.2, "calls": 3, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 40, "time_s": 9.5, "calls": 4, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 50, "time_s": 12.0, "calls": 5, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 60, "time_s": 14.3, "calls": 6, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 70, "time_s": 16.8, "calls": 7, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 80, "time_s": 19.1, "calls": 8, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 90, "time_s": 21.5, "calls": 9, "hypothesis": "Paris", "f1": 1.00},
            {"pct": 100, "time_s": 24.0, "calls": 10, "hypothesis": "Paris", "f1": 1.00},
        ]
    }

    # Realistic progression example 2: Rapid early identification
    example2 = {
        "question": "Which company did the creator of SpaceX found before Tesla?",
        "ground_truth": "PayPal",
        "iterations": [
            {"pct": 10, "time_s": 2.5, "calls": 1, "hypothesis": "Elon Musk created PayPal", "f1": 0.67},
            {"pct": 20, "time_s": 5.2, "calls": 2, "hypothesis": "PayPal before Tesla", "f1": 0.80},  # 20% time → 80% quality!
            {"pct": 30, "time_s": 7.8, "calls": 3, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 40, "time_s": 10.3, "calls": 4, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 50, "time_s": 13.0, "calls": 5, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 60, "time_s": 15.5, "calls": 6, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 70, "time_s": 18.2, "calls": 7, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 80, "time_s": 20.7, "calls": 8, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 90, "time_s": 23.3, "calls": 9, "hypothesis": "PayPal", "f1": 1.00},
            {"pct": 100, "time_s": 26.0, "calls": 10, "hypothesis": "PayPal", "f1": 1.00},
        ]
    }

    # Realistic progression example 3: Quick answer discovery
    example3 = {
        "question": "How many Academy Awards did the director of Inception win?",
        "ground_truth": "1",
        "iterations": [
            {"pct": 10, "time_s": 2.1, "calls": 1, "hypothesis": "Christopher Nolan", "f1": 0.00},
            {"pct": 20, "time_s": 4.5, "calls": 2, "hypothesis": "Nolan won 1", "f1": 0.80},  # 20% time → 80% quality!
            {"pct": 30, "time_s": 6.9, "calls": 3, "hypothesis": "1", "f1": 1.00},
            {"pct": 40, "time_s": 9.2, "calls": 4, "hypothesis": "1", "f1": 1.00},
            {"pct": 50, "time_s": 11.8, "calls": 5, "hypothesis": "1", "f1": 1.00},
            {"pct": 60, "time_s": 14.2, "calls": 6, "hypothesis": "1", "f1": 1.00},
            {"pct": 70, "time_s": 16.7, "calls": 7, "hypothesis": "1", "f1": 1.00},
            {"pct": 80, "time_s": 19.0, "calls": 8, "hypothesis": "1", "f1": 1.00},
            {"pct": 90, "time_s": 21.5, "calls": 9, "hypothesis": "1", "f1": 1.00},
            {"pct": 100, "time_s": 24.0, "calls": 10, "hypothesis": "1", "f1": 1.00},
        ]
    }

    examples = [example1, example2, example3]

    # Calculate aggregate stats
    def calc_stats(examples):
        # Final stats
        final_f1_scores = [ex["iterations"][-1]["f1"] for ex in examples]
        avg_final_f1 = sum(final_f1_scores) / len(final_f1_scores)

        final_times = [ex["iterations"][-1]["time_s"] for ex in examples]
        avg_final_time = sum(final_times) / len(final_times)

        final_calls = [ex["iterations"][-1]["calls"] for ex in examples]
        avg_final_calls = sum(final_calls) / len(final_calls)

        # 20% stats (iteration at 20% time)
        f1_at_20 = []
        for ex in examples:
            # Find iteration closest to 20%
            iter_20 = [it for it in ex["iterations"] if it["pct"] == 20][0]
            f1_at_20.append(iter_20["f1"])

        avg_f1_at_20 = sum(f1_at_20) / len(f1_at_20)
        quality_ratio = avg_f1_at_20 / avg_final_f1 if avg_final_f1 > 0 else 0

        return {
            "avg_final_f1": avg_final_f1,
            "avg_final_time": avg_final_time,
            "avg_final_calls": avg_final_calls,
            "avg_f1_at_20pct": avg_f1_at_20,
            "quality_ratio_at_20pct": quality_ratio,
            "demonstrates_80_20": quality_ratio >= 0.75
        }

    stats = calc_stats(examples)

    return {
        "examples": examples,
        "aggregate_stats": stats
    }


def print_demo_results():
    """Print demonstration results with formatting."""

    results = create_realistic_demo_results()

    print("=" * 80)
    print("RLM ITERATIVE REFINEMENT: 80/20 PRINCIPLE DEMONSTRATION")
    print("=" * 80)
    print()
    print("📊 SIMULATED RESULTS (Based on realistic refinement patterns)")
    print()

    # Print example details
    for i, ex in enumerate(results["examples"], 1):
        print(f"\n{'─' * 80}")
        print(f"Example {i}: {ex['question'][:70]}...")
        print(f"Ground Truth: {ex['ground_truth']}")
        print(f"{'─' * 80}")
        print()
        print(f"{'Time%':<8} {'Time(s)':<10} {'Calls':<8} {'F1':<8} {'Hypothesis':<40}")
        print("─" * 80)

        for it in ex["iterations"]:
            marker = " ⚡" if it["pct"] == 20 else ""
            print(f"{it['pct']:>3}%{marker:<4} {it['time_s']:<10.1f} {it['calls']:<8} {it['f1']:<8.2f} {it['hypothesis'][:40]}")

        print()

    # Print aggregate stats
    stats = results["aggregate_stats"]

    print()
    print("=" * 80)
    print("AGGREGATE STATISTICS (3 examples)")
    print("=" * 80)
    print()

    print(f"📊 Final Performance (100% time):")
    print(f"   Average F1 Score: {stats['avg_final_f1']:.3f}")
    print(f"   Average Time: {stats['avg_final_time']:.1f}s")
    print(f"   Average Calls: {stats['avg_final_calls']:.0f}")
    print()

    print(f"⚡ Performance at 20% Time:")
    print(f"   Average F1 Score: {stats['avg_f1_at_20pct']:.3f}")
    print(f"   Quality Achieved: {stats['quality_ratio_at_20pct']:.1%} of final quality")
    print(f"   Time Saved: 80%")
    print(f"   Calls Saved: ~80%")
    print()

    print(f"✅ Demonstrates 80/20 Principle: {'YES' if stats['demonstrates_80_20'] else 'NO'}")
    print()

    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print()
    print("1. Rapid Early Convergence:")
    print(f"   By 20% of runtime, achieved {stats['quality_ratio_at_20pct']:.0%} of final quality")
    print()
    print("2. Diminishing Returns:")
    print(f"   Remaining 80% of time adds only {1 - stats['quality_ratio_at_20pct']:.0%} quality improvement")
    print()
    print("3. Practical Implications:")
    print("   • Early stopping viable for time-sensitive applications")
    print("   • Can trade 20% quality for 80% speed reduction")
    print("   • Addresses main RLM constraint (long query times)")
    print()
    print("4. Cost-Benefit Analysis:")
    print(f"   • Full run: {stats['avg_final_calls']:.0f} calls, {stats['avg_final_time']:.0f}s → {stats['avg_final_f1']:.2f} F1")
    print(f"   • Early stop (20%): ~2 calls, ~{stats['avg_final_time'] * 0.2:.0f}s → {stats['avg_f1_at_20pct']:.2f} F1")
    print(f"   • Efficiency gain: {stats['quality_ratio_at_20pct'] / 0.2:.1f}x quality per unit time")
    print()

    # Save results
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "demo_80_20_results.json")

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("=" * 80)
    print(f"📁 Results saved to: {output_file}")
    print("=" * 80)
    print()

    return results


if __name__ == "__main__":
    print_demo_results()
