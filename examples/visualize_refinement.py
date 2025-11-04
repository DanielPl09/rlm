"""
Visualize the incremental refinement process showing how hypothesis evolves.
Creates a visual diagram showing each step of the refinement.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.utils.context_slicer import ContextSlicer
from rlm.utils.anthropic_client import AnthropicClient
import textwrap


def wrap_text(text, width=60):
    """Wrap text to specified width."""
    return '\n'.join(textwrap.wrap(text, width))


def create_ascii_visualization(test_name, query, slices_info, hypothesis_evolution):
    """
    Create ASCII art visualization of the refinement process.

    Args:
        test_name: Name of the test
        query: Original query
        slices_info: List of (slice_id, finding) tuples
        hypothesis_evolution: List of hypothesis versions
    """
    width = 80

    print("\n" + "="*width)
    print(f"INCREMENTAL REFINEMENT VISUALIZATION: {test_name}")
    print("="*width)

    # Query
    print("\n┌" + "─"*(width-2) + "┐")
    print("│" + f" QUERY: {query}".ljust(width-2) + "│")
    print("└" + "─"*(width-2) + "┘")

    # Initial state
    print("\n" + "┌" + "─"*(width-2) + "┐")
    print("│" + " HYPOTHESIS v0 (Initial)".ljust(width-2) + "│")
    print("├" + "─"*(width-2) + "┤")
    for line in wrap_text(hypothesis_evolution[0], width-4).split('\n'):
        print("│ " + line.ljust(width-3) + "│")
    print("└" + "─"*(width-2) + "┘")

    # Process each slice
    for i, ((slice_id, finding), new_hypothesis) in enumerate(zip(slices_info, hypothesis_evolution[1:]), 1):
        print("\n" + " "*30 + "↓")
        print(" "*20 + "┌" + "─"*40 + "┐")
        print(" "*20 + f"│  PROCESS SLICE {i}/{len(slices_info)}: {slice_id[:30].ljust(30)}│")
        print(" "*20 + "└" + "─"*40 + "┘")

        # Show finding from this slice
        print("\n" + "┌" + "─"*(width-2) + "┐")
        print("│" + f" 🔵 sub_RLM Query Result from {slice_id}:".ljust(width-2) + "│")
        print("├" + "─"*(width-2) + "┤")
        for line in wrap_text(finding, width-4).split('\n')[:3]:  # Show first 3 lines
            print("│ " + line.ljust(width-3) + "│")
        if len(finding) > width*3:
            print("│ " + "...".ljust(width-3) + "│")
        print("└" + "─"*(width-2) + "┘")

        print("\n" + " "*30 + "↓")
        print(" "*25 + "🔄 REFINE")
        print(" "*30 + "↓")

        # Show refined hypothesis
        print("\n" + "┌" + "─"*(width-2) + "┐")
        print("│" + f" HYPOTHESIS v{i} (After {slice_id})".ljust(width-2) + "│")
        print("├" + "─"*(width-2) + "┤")
        for line in wrap_text(new_hypothesis, width-4).split('\n')[:4]:  # Show first 4 lines
            print("│ " + line.ljust(width-3) + "│")
        if len(new_hypothesis) > width*4:
            print("│ " + "...".ljust(width-3) + "│")
        print("└" + "─"*(width-2) + "┘")

    # Final summary
    print("\n" + " "*30 + "↓")
    print("\n" + "┏" + "━"*(width-2) + "┓")
    print("┃" + " ✅ FINAL ANSWER (Complete Synthesis)".center(width-2) + "┃")
    print("┣" + "━"*(width-2) + "┫")
    for line in wrap_text(hypothesis_evolution[-1], width-4).split('\n'):
        print("┃ " + line.ljust(width-3) + "┃")
    print("┗" + "━"*(width-2) + "┛")

    # Statistics
    print("\n" + "="*width)
    print("REFINEMENT STATISTICS:")
    print("="*width)
    print(f"  Total slices processed:     {len(slices_info)}")
    print(f"  Total sub_RLM calls:        {len(slices_info) * 2} (query + refine per slice)")
    print(f"  Hypothesis versions:        {len(hypothesis_evolution)}")
    print(f"  Information sources used:   {', '.join([s[0] for s in slices_info])}")
    print("="*width)


def run_visualization_test(context, query, api_key, test_name):
    """
    Run a test and create visualization of the refinement process.
    """
    print("\n" + "="*80)
    print(f"RUNNING TEST: {test_name}")
    print("="*80)

    # Create slices
    slices = ContextSlicer.auto_slice_context(context)
    print(f"Created {len(slices)} slices: {list(slices.keys())}")

    # Initialize client
    client = AnthropicClient(api_key=api_key, model="claude-3-opus-20240229")

    # Track evolution
    hypothesis = f"Initial: Need to answer '{query}'"
    hypothesis_evolution = [hypothesis]
    slices_info = []

    print("\nProcessing slices...")
    for i, (slice_id, slice_obj) in enumerate(slices.items(), 1):
        print(f"  [{i}/{len(slices)}] {slice_id}...", end=" ")

        # Query slice
        slice_prompt = f"Based on this context, answer: {query}\n\nContext: {slice_obj.content}\n\nBe concise."
        try:
            finding = client.completion(slice_prompt)
            print(f"✓ ({len(finding)} chars)", end=" ")
        except Exception as e:
            print(f"✗ Error: {e}")
            continue

        # Refine hypothesis
        refinement_prompt = f"Current: {hypothesis}\n\nNew finding from {slice_id}: {finding}\n\nProvide updated hypothesis. Be concise."
        try:
            refined = client.completion(refinement_prompt)
            hypothesis = refined
            hypothesis_evolution.append(hypothesis)
            slices_info.append((slice_id, finding))
            print("✓ Refined")
        except Exception as e:
            print(f"✗ Error: {e}")
            continue

    # Create visualization
    print("\n" + "="*80)
    print("GENERATING VISUALIZATION...")
    print("="*80)

    create_ascii_visualization(test_name, query, slices_info, hypothesis_evolution)

    return hypothesis_evolution


def main():
    """Run visualization tests."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Usage: export ANTHROPIC_API_KEY=your_key && python visualize_refinement.py")
        sys.exit(1)

    # Example 1: Simple product analysis
    context1 = {
        'user_reviews': 'Users praise the intuitive interface and fast response times. Common complaints: mobile app crashes frequently, especially on iOS devices.',
        'technical_specs': 'Built with React frontend, Node.js backend. Supports 10K concurrent users. 99.5% uptime SLA. AWS infrastructure.',
        'support_tickets': 'Top issues: mobile crashes (35%), login problems (20%), slow reports (15%). Average resolution: 4 hours.'
    }

    result1 = run_visualization_test(
        context1,
        "What are the product's main strengths and weaknesses?",
        api_key,
        "Product Analysis"
    )

    print("\n\n" + "="*80)
    print("VISUALIZATION COMPLETE")
    print("="*80)
    print("\nKey Observations:")
    print("  • Each slice adds NEW information to the hypothesis")
    print("  • Hypothesis becomes MORE comprehensive with each iteration")
    print("  • Final answer SYNTHESIZES information from ALL slices")
    print("  • No single slice alone would provide the complete picture")
    print("="*80)


if __name__ == "__main__":
    main()
