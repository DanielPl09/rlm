"""
Visualization tools for demonstrating 80/20 principle in iterative refinement.
"""
import json
import os
import argparse
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


def load_experiment_results(results_file: str) -> Dict[str, Any]:
    """Load experiment results from JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)


def plot_quality_vs_time(
    traces: List[Dict[str, Any]],
    output_file: str = "quality_vs_time.png",
    show_80_20: bool = True
):
    """
    Plot quality (F1 score) vs cumulative time across all traces.

    Args:
        traces: List of trace dictionaries
        output_file: Output file path for plot
        show_80_20: Whether to highlight 80/20 points
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot each trace
    for i, trace in enumerate(traces):
        checkpoints = trace['checkpoints']

        if not checkpoints:
            continue

        times = [cp['cumulative_time'] for cp in checkpoints]
        f1_scores = [cp['metrics']['f1'] for cp in checkpoints]

        # Normalize time to percentage
        max_time = times[-1] if times else 1
        time_pct = [t / max_time * 100 for t in times]

        # Plot trace
        ax.plot(time_pct, f1_scores, alpha=0.3, linewidth=1, color='blue')

        # Mark final point
        if times:
            ax.scatter([time_pct[-1]], [f1_scores[-1]], alpha=0.5, s=30, color='blue')

    # Calculate and plot average curve
    # Interpolate all traces to common time points
    time_points = np.linspace(0, 100, 100)
    all_interpolated = []

    for trace in traces:
        checkpoints = trace['checkpoints']
        if not checkpoints or not trace.get('total_time'):
            continue

        times = [cp['cumulative_time'] for cp in checkpoints]
        f1_scores = [cp['metrics']['f1'] for cp in checkpoints]

        # Normalize time
        max_time = trace['total_time']
        time_pct = [t / max_time * 100 for t in times]

        # Interpolate
        if len(time_pct) > 1:
            interpolated = np.interp(time_points, time_pct, f1_scores)
            all_interpolated.append(interpolated)

    if all_interpolated:
        avg_curve = np.mean(all_interpolated, axis=0)
        ax.plot(time_points, avg_curve, color='red', linewidth=3, label='Average', zorder=10)

        # Highlight 80/20 point
        if show_80_20:
            f1_at_20 = avg_curve[20]  # At 20% time
            f1_at_100 = avg_curve[-1]  # At 100% time

            # Draw vertical line at 20%
            ax.axvline(x=20, color='green', linestyle='--', linewidth=2, alpha=0.7, label='20% Time')

            # Draw horizontal lines for quality comparison
            ax.axhline(y=f1_at_20, color='orange', linestyle=':', linewidth=2, alpha=0.7)
            ax.axhline(y=f1_at_100, color='purple', linestyle=':', linewidth=2, alpha=0.7)

            # Add annotation
            ratio = (f1_at_20 / f1_at_100 * 100) if f1_at_100 > 0 else 0
            ax.text(
                22, f1_at_20 + 0.02,
                f'20% time: {f1_at_20:.2f} F1\n({ratio:.0f}% of final quality)',
                fontsize=11, color='green', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )

            ax.text(
                75, f1_at_100 + 0.02,
                f'100% time: {f1_at_100:.2f} F1',
                fontsize=11, color='purple', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )

    ax.set_xlabel('Time (% of total)', fontsize=14, fontweight='bold')
    ax.set_ylabel('F1 Score', fontsize=14, fontweight='bold')
    ax.set_title('Quality vs Time: Demonstrating 80/20 Principle', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=12)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved plot to {output_file}")
    plt.close()


def plot_quality_vs_calls(
    traces: List[Dict[str, Any]],
    output_file: str = "quality_vs_calls.png",
    show_80_20: bool = True
):
    """
    Plot quality (F1 score) vs number of sub-RLM calls.

    Args:
        traces: List of trace dictionaries
        output_file: Output file path for plot
        show_80_20: Whether to highlight 80/20 points
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    # Plot each trace
    for trace in traces:
        checkpoints = trace['checkpoints']

        if not checkpoints:
            continue

        calls = [cp['sub_rlm_calls'] for cp in checkpoints]
        f1_scores = [cp['metrics']['f1'] for cp in checkpoints]

        # Normalize calls to percentage
        max_calls = calls[-1] if calls else 1
        calls_pct = [c / max_calls * 100 for c in calls]

        # Plot trace
        ax.plot(calls_pct, f1_scores, alpha=0.3, linewidth=1, color='blue')

        # Mark final point
        if calls:
            ax.scatter([calls_pct[-1]], [f1_scores[-1]], alpha=0.5, s=30, color='blue')

    # Calculate and plot average curve
    calls_points = np.linspace(0, 100, 100)
    all_interpolated = []

    for trace in traces:
        checkpoints = trace['checkpoints']
        if not checkpoints or not trace.get('total_sub_rlm_calls'):
            continue

        calls = [cp['sub_rlm_calls'] for cp in checkpoints]
        f1_scores = [cp['metrics']['f1'] for cp in checkpoints]

        # Normalize calls
        max_calls = trace['total_sub_rlm_calls']
        calls_pct = [c / max_calls * 100 for c in calls]

        # Interpolate
        if len(calls_pct) > 1:
            interpolated = np.interp(calls_points, calls_pct, f1_scores)
            all_interpolated.append(interpolated)

    if all_interpolated:
        avg_curve = np.mean(all_interpolated, axis=0)
        ax.plot(calls_points, avg_curve, color='red', linewidth=3, label='Average', zorder=10)

        # Highlight 80/20 point
        if show_80_20:
            f1_at_20 = avg_curve[20]  # At 20% calls
            f1_at_100 = avg_curve[-1]  # At 100% calls

            # Draw vertical line at 20%
            ax.axvline(x=20, color='green', linestyle='--', linewidth=2, alpha=0.7, label='20% Calls')

            # Draw horizontal lines for quality comparison
            ax.axhline(y=f1_at_20, color='orange', linestyle=':', linewidth=2, alpha=0.7)
            ax.axhline(y=f1_at_100, color='purple', linestyle=':', linewidth=2, alpha=0.7)

            # Add annotation
            ratio = (f1_at_20 / f1_at_100 * 100) if f1_at_100 > 0 else 0
            ax.text(
                22, f1_at_20 + 0.02,
                f'20% calls: {f1_at_20:.2f} F1\n({ratio:.0f}% of final quality)',
                fontsize=11, color='green', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )

            ax.text(
                75, f1_at_100 + 0.02,
                f'100% calls: {f1_at_100:.2f} F1',
                fontsize=11, color='purple', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )

    ax.set_xlabel('Sub-RLM Calls (% of total)', fontsize=14, fontweight='bold')
    ax.set_ylabel('F1 Score', fontsize=14, fontweight='bold')
    ax.set_title('Quality vs Sub-RLM Calls: Demonstrating 80/20 Principle', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=12)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved plot to {output_file}")
    plt.close()


def plot_efficiency_comparison(
    aggregate_stats: Dict[str, Any],
    output_file: str = "efficiency_comparison.png"
):
    """
    Create a bar chart comparing efficiency at different checkpoints.

    Args:
        aggregate_stats: Aggregate statistics dictionary
        output_file: Output file path for plot
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Time-based comparison
    if aggregate_stats.get('avg_final_f1'):
        categories_time = ['20% Time', '100% Time']
        f1_scores_time = [
            aggregate_stats.get('avg_f1_at_20pct_time', 0),
            aggregate_stats['avg_final_f1']
        ]
        colors_time = ['orange', 'purple']

        bars1 = ax1.bar(categories_time, f1_scores_time, color=colors_time, alpha=0.7, edgecolor='black', linewidth=2)

        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2., height + 0.02,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold'
            )

        # Add efficiency annotation
        if f1_scores_time[1] > 0:
            efficiency = f1_scores_time[0] / f1_scores_time[1] * 100
            ax1.text(
                0.5, 0.5,
                f'{efficiency:.0f}%\nof quality',
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='green',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3)
            )

        ax1.set_ylabel('F1 Score', fontsize=13, fontweight='bold')
        ax1.set_title('Quality at 20% vs 100% Time', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, 1.05)
        ax1.grid(True, alpha=0.3, axis='y')

    # Calls-based comparison
    if aggregate_stats.get('avg_final_f1'):
        categories_calls = ['20% Calls', '100% Calls']
        f1_scores_calls = [
            aggregate_stats.get('avg_f1_at_20pct_calls', 0),
            aggregate_stats['avg_final_f1']
        ]
        colors_calls = ['orange', 'purple']

        bars2 = ax2.bar(categories_calls, f1_scores_calls, color=colors_calls, alpha=0.7, edgecolor='black', linewidth=2)

        # Add value labels on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2., height + 0.02,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=12, fontweight='bold'
            )

        # Add efficiency annotation
        if f1_scores_calls[1] > 0:
            efficiency = f1_scores_calls[0] / f1_scores_calls[1] * 100
            ax2.text(
                0.5, 0.5,
                f'{efficiency:.0f}%\nof quality',
                ha='center', va='center', fontsize=16, fontweight='bold',
                color='green',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3)
            )

        ax2.set_ylabel('F1 Score', fontsize=13, fontweight='bold')
        ax2.set_title('Quality at 20% vs 100% Calls', fontsize=14, fontweight='bold')
        ax2.set_ylim(0, 1.05)
        ax2.grid(True, alpha=0.3, axis='y')

    plt.suptitle('80/20 Efficiency Demonstration', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Saved plot to {output_file}")
    plt.close()


def create_all_visualizations(
    results_file: str,
    output_dir: Optional[str] = None
):
    """
    Create all visualizations from experiment results.

    Args:
        results_file: Path to experiment results JSON
        output_dir: Output directory (default: same as results file)
    """
    # Load results
    print(f"Loading results from {results_file}")
    results = load_experiment_results(results_file)

    # Determine output directory
    if output_dir is None:
        output_dir = os.path.dirname(results_file)
    os.makedirs(output_dir, exist_ok=True)

    # Extract data
    traces = results.get('traces', [])
    aggregate_stats = results.get('aggregate_stats', {})

    if not traces:
        print("⚠️  No traces found in results file")
        return

    print(f"\nGenerating visualizations for {len(traces)} traces...\n")

    # Generate plots
    base_name = os.path.splitext(os.path.basename(results_file))[0]

    plot_quality_vs_time(
        traces,
        output_file=os.path.join(output_dir, f"{base_name}_quality_vs_time.png")
    )

    plot_quality_vs_calls(
        traces,
        output_file=os.path.join(output_dir, f"{base_name}_quality_vs_calls.png")
    )

    plot_efficiency_comparison(
        aggregate_stats,
        output_file=os.path.join(output_dir, f"{base_name}_efficiency.png")
    )

    print(f"\n✅ All visualizations saved to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate visualizations from experiment results"
    )
    parser.add_argument(
        "results_file",
        type=str,
        help="Path to experiment results JSON file"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory for plots (default: same as results file)"
    )

    args = parser.parse_args()

    create_all_visualizations(args.results_file, args.output_dir)


if __name__ == "__main__":
    main()
