"""
Create a graphical visualization of incremental refinement using matplotlib.
Shows hypothesis evolution as a flow diagram.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.utils.context_slicer import ContextSlicer
from rlm.utils.anthropic_client import AnthropicClient

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib not installed. Install with: pip install matplotlib")


def create_graphical_visualization(test_name, query, slices_info, hypothesis_evolution, output_file="refinement_flow.png"):
    """
    Create a graphical flowchart showing the refinement process.
    """
    if not HAS_MATPLOTLIB:
        print("❌ Cannot create graphical visualization without matplotlib")
        return

    fig, ax = plt.subplots(figsize=(14, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(slices_info) * 4 + 5)
    ax.axis('off')

    # Title
    ax.text(5, len(slices_info) * 4 + 4, f"Incremental Refinement: {test_name}",
            ha='center', va='top', fontsize=16, fontweight='bold')

    # Query box at top
    query_box = FancyBboxPatch((0.5, len(slices_info) * 4 + 1.5), 9, 1.5,
                                boxstyle="round,pad=0.1",
                                facecolor='lightblue',
                                edgecolor='darkblue',
                                linewidth=2)
    ax.add_patch(query_box)
    ax.text(5, len(slices_info) * 4 + 2.25, f"QUERY:\n{query[:80]}...",
            ha='center', va='center', fontsize=10, wrap=True)

    y_pos = len(slices_info) * 4

    # Initial hypothesis
    hyp_box = FancyBboxPatch((1, y_pos), 8, 0.8,
                              boxstyle="round,pad=0.05",
                              facecolor='lightyellow',
                              edgecolor='orange',
                              linewidth=1.5)
    ax.add_patch(hyp_box)
    ax.text(5, y_pos + 0.4, f"Hypothesis v0: {hypothesis_evolution[0][:60]}...",
            ha='center', va='center', fontsize=9)

    # Arrow down
    arrow = FancyArrowPatch((5, y_pos), (5, y_pos - 0.5),
                            arrowstyle='->', mutation_scale=20,
                            linewidth=2, color='black')
    ax.add_patch(arrow)

    # Process each slice
    for i, ((slice_id, finding), new_hyp) in enumerate(zip(slices_info, hypothesis_evolution[1:]), 1):
        y_pos -= 1

        # Slice box
        slice_box = FancyBboxPatch((0.5, y_pos - 0.8), 4, 0.6,
                                    boxstyle="round,pad=0.05",
                                    facecolor='lightcoral',
                                    edgecolor='darkred',
                                    linewidth=1.5)
        ax.add_patch(slice_box)
        ax.text(2.5, y_pos - 0.5, f"🔵 {slice_id}\n{finding[:40]}...",
                ha='center', va='center', fontsize=8)

        # Arrow to refinement
        arrow = FancyArrowPatch((4.5, y_pos - 0.5), (5.5, y_pos - 0.5),
                                arrowstyle='->', mutation_scale=15,
                                linewidth=1.5, color='green')
        ax.add_patch(arrow)

        # Refinement indicator
        refine_circle = plt.Circle((5, y_pos - 0.5), 0.15, color='lightgreen', ec='darkgreen', linewidth=2)
        ax.add_patch(refine_circle)
        ax.text(5, y_pos - 0.5, "🔄", ha='center', va='center', fontsize=10)

        # Updated hypothesis box
        hyp_box = FancyBboxPatch((1, y_pos - 1.5), 8, 0.6,
                                  boxstyle="round,pad=0.05",
                                  facecolor='lightgreen',
                                  edgecolor='darkgreen',
                                  linewidth=1.5)
        ax.add_patch(hyp_box)
        ax.text(5, y_pos - 1.2, f"Hypothesis v{i}: {new_hyp[:70]}...",
                ha='center', va='center', fontsize=8)

        # Arrow down to next
        if i < len(slices_info):
            arrow = FancyArrowPatch((5, y_pos - 1.5), (5, y_pos - 2),
                                    arrowstyle='->', mutation_scale=20,
                                    linewidth=2, color='black')
            ax.add_patch(arrow)
            y_pos -= 1.5

    # Final answer box
    y_pos -= 2
    final_box = FancyBboxPatch((0.5, y_pos), 9, 1,
                                boxstyle="round,pad=0.1",
                                facecolor='gold',
                                edgecolor='darkgoldenrod',
                                linewidth=3)
    ax.add_patch(final_box)
    ax.text(5, y_pos + 0.5, f"✅ FINAL ANSWER\n{hypothesis_evolution[-1][:100]}...",
            ha='center', va='center', fontsize=9, fontweight='bold')

    # Statistics box
    stats_box = FancyBboxPatch((0.5, 0.2), 4, 1.5,
                                boxstyle="round,pad=0.05",
                                facecolor='lightgray',
                                edgecolor='black',
                                linewidth=1)
    ax.add_patch(stats_box)
    stats_text = f"STATISTICS:\nSlices: {len(slices_info)}\nAPI Calls: {len(slices_info) * 2}\nVersions: {len(hypothesis_evolution)}"
    ax.text(2.5, 0.95, stats_text, ha='center', va='center', fontsize=9)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='lightcoral', edgecolor='darkred', label='Context Slice'),
        mpatches.Patch(facecolor='lightgreen', edgecolor='darkgreen', label='Refined Hypothesis'),
        mpatches.Patch(facecolor='gold', edgecolor='darkgoldenrod', label='Final Answer')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n✅ Graph saved to: {output_file}")

    return output_file


def run_and_visualize(context, query, api_key, test_name):
    """Run refinement test and create both visualizations."""
    print(f"\nRunning test: {test_name}")

    # Create slices
    slices = ContextSlicer.auto_slice_context(context)
    client = AnthropicClient(api_key=api_key, model="claude-3-opus-20240229")

    # Run refinement
    hypothesis = f"Initial: {query}"
    hypothesis_evolution = [hypothesis]
    slices_info = []

    for slice_id, slice_obj in slices.items():
        # Query slice
        slice_prompt = f"Answer: {query}\n\nContext: {slice_obj.content}\n\nBe concise."
        try:
            finding = client.completion(slice_prompt)
        except Exception as e:
            print(f"Error querying {slice_id}: {e}")
            continue

        # Refine
        refinement_prompt = f"Current: {hypothesis}\n\nNew: {finding}\n\nProvide updated hypothesis."
        try:
            refined = client.completion(refinement_prompt)
            hypothesis = refined
            hypothesis_evolution.append(hypothesis)
            slices_info.append((slice_id, finding))
        except Exception as e:
            print(f"Error refining after {slice_id}: {e}")
            continue

    # Create visualization
    if HAS_MATPLOTLIB:
        output_file = f"{test_name.lower().replace(' ', '_')}_refinement.png"
        create_graphical_visualization(test_name, query, slices_info, hypothesis_evolution, output_file)

    return hypothesis_evolution


def main():
    """Run visualization."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if not HAS_MATPLOTLIB:
        print("Installing matplotlib...")
        os.system("pip install matplotlib -q")
        print("Please re-run this script after matplotlib is installed.")
        sys.exit(1)

    context = {
        'user_reviews': 'Users praise intuitive interface and speed. Main complaint: mobile crashes on iOS.',
        'technical_specs': 'React + Node.js. Supports 10K concurrent users. 99.5% uptime. AWS hosted.',
        'support_tickets': 'Top issues: mobile crashes (35%), login (20%), slow reports (15%). Avg resolution: 4hrs.'
    }

    run_and_visualize(
        context,
        "What are the product's strengths and weaknesses?",
        api_key,
        "Product Analysis"
    )

    print("\n" + "="*80)
    print("✅ Graphical visualization complete!")
    print("="*80)


if __name__ == "__main__":
    main()
