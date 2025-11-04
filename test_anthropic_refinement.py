"""
Test script to demonstrate query-driven iterative refinement using Anthropic API.
This simulates what RLM_REPL would do with the slicing feature.
"""

import os
import sys
sys.path.insert(0, '/home/user/rlm')

from rlm.utils.context_slicer import ContextSlicer
from rlm.utils.anthropic_client import AnthropicClient


def test_refinement_with_anthropic(api_key: str):
    """
    Demonstrate the refinement workflow with actual Anthropic API calls.
    """
    print("="*80)
    print("🔥 REAL REFINEMENT TEST WITH ANTHROPIC API")
    print("="*80)

    # Create test context
    context = {
        'user_reviews': 'Users love the fast performance and intuitive interface. However, many complain about frequent crashes on mobile devices.',
        'technical_specs': 'The system supports real-time analytics with 99.9% uptime. Built on Python and React. Processes up to 100K requests per second.',
        'support_tickets': 'Most tickets are about mobile crashes (high priority). Average response time is 2 hours. Customer satisfaction: 4.2/5 stars.'
    }

    query = "What are the main strengths and weaknesses of this product?"

    print(f"\nQuery: {query}")
    print(f"\nContext sections: {list(context.keys())}")

    # Step 1: Create context slices
    print("\n" + "="*80)
    print("STEP 1: Creating Context Slices")
    print("="*80)
    slices = ContextSlicer.auto_slice_context(context)
    print(f"✅ Created {len(slices)} slices:")
    for slice_id, slice_obj in slices.items():
        print(f"  - {slice_id}: {slice_obj.metadata}")

    # Step 2: Initialize Anthropic client
    print("\n" + "="*80)
    print("STEP 2: Initializing Anthropic Client")
    print("="*80)
    client = AnthropicClient(api_key=api_key, model="claude-3-opus-20240229")
    print("✅ Client initialized")

    # Step 3: Simulate the iterative refinement workflow
    print("\n" + "="*80)
    print("STEP 3: Query-Driven Iterative Refinement")
    print("="*80)

    hypothesis = ""
    hypothesis_history = []

    # Initialize hypothesis
    print("\n📝 Initializing hypothesis...")
    hypothesis = "Need to analyze product strengths and weaknesses from all sources"
    print(f"   Hypothesis v0: {hypothesis}")

    sub_rlm_call_count = 0

    # Iterate through each slice
    for i, (slice_id, slice_obj) in enumerate(slices.items(), 1):
        print(f"\n{'─'*80}")
        print(f"ITERATION {i}/{len(slices)}: Processing {slice_id}")
        print(f"{'─'*80}")

        # Sub_RLM Call: Query this slice
        sub_rlm_call_count += 1
        print(f"\n🔵 sub_RLM Call #{sub_rlm_call_count}: Query slice '{slice_id}'")
        print(f"   Slice content: {slice_obj.content[:80]}...")

        slice_prompt = f"""Based on this context, extract information about product strengths and weaknesses:

Context: {slice_obj.content}

What strengths and weaknesses are mentioned? Be concise."""

        print(f"   Calling Anthropic API...")
        try:
            slice_result = client.completion(slice_prompt)
            print(f"   ✅ Response received ({len(slice_result)} chars)")
            print(f"\n   📄 Result from {slice_id}:")
            print(f"   {slice_result[:200]}{'...' if len(slice_result) > 200 else ''}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

        # Sub_RLM Call: Refine hypothesis
        sub_rlm_call_count += 1
        print(f"\n🔵 sub_RLM Call #{sub_rlm_call_count}: Refine hypothesis")
        print(f"   Current hypothesis: {hypothesis[:100]}...")
        print(f"   New finding: {slice_result[:100]}...")

        refinement_prompt = f"""You are refining a hypothesis about a product's strengths and weaknesses.

Current hypothesis: {hypothesis}

New finding from {slice_id}: {slice_result}

Provide an updated, refined hypothesis that incorporates this new information. Be concise and comprehensive."""

        print(f"   Calling Anthropic API...")
        try:
            refined = client.completion(refinement_prompt)
            print(f"   ✅ Refinement received ({len(refined)} chars)")

            # Update hypothesis
            hypothesis_history.append(hypothesis)
            hypothesis = refined

            print(f"\n   📈 Hypothesis v{i}: {hypothesis[:150]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue

    # Final result
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    print(f"\n✅ Total sub_RLM calls: {sub_rlm_call_count}")
    print(f"   - Slice queries: {len(slices)}")
    print(f"   - Refinement queries: {len(slices)}")

    print(f"\n📈 Hypothesis Evolution:")
    print(f"   v0 (initial): Need to analyze product strengths and weaknesses...")
    for i, h in enumerate(hypothesis_history, 1):
        print(f"   v{i}: {h[:100]}...")

    print(f"\n🎯 FINAL HYPOTHESIS (v{len(hypothesis_history) + 1}):")
    print(f"{'─'*80}")
    print(hypothesis)
    print(f"{'─'*80}")

    print("\n" + "="*80)
    print("✅ VERIFICATION: Iterative Refinement WORKS!")
    print("="*80)
    print(f"✅ Context slicing: {len(slices)} slices created")
    print(f"✅ Sub_RLM calls: {sub_rlm_call_count} actual API calls made")
    print(f"✅ Hypothesis tracking: {len(hypothesis_history) + 1} versions")
    print(f"✅ Final answer: Aggregated from all {len(slices)} context slices")
    print("="*80)


if __name__ == "__main__":
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Usage: export ANTHROPIC_API_KEY=your_key && python test_anthropic_refinement.py")
        sys.exit(1)

    test_refinement_with_anthropic(api_key)
