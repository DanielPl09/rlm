"""
Demonstration of query-driven iterative refinement showing actual sub_RLM calls
and hypothesis updates throughout the process.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def demo_with_detailed_logging():
    """
    Example showing the actual refinement process with detailed output.
    This demonstrates how hypothesis evolves through multiple sub_RLM calls.
    """

    # Multi-part context about a fictional product
    context = {
        "user_reviews": """
        Review 1: "The analytics dashboard is amazing! Very intuitive and powerful.
        However, the mobile app crashes frequently."

        Review 2: "Great product overall. The reporting feature is comprehensive but
        takes a long time to generate reports. Customer support is excellent."

        Review 3: "Love the data visualization tools. The integration with our existing
        systems was seamless. Pricing is a bit high for small teams."
        """,

        "technical_specs": """
        Product: DataViz Pro
        - Analytics Engine: Real-time processing up to 1M events/sec
        - Reporting: PDF, Excel, CSV exports with custom templates
        - Mobile Apps: iOS and Android (currently in beta)
        - Integrations: REST API, webhooks, 50+ pre-built connectors
        - Pricing: $99/month (Starter), $299/month (Pro), Custom (Enterprise)
        """,

        "support_tickets": """
        Ticket #1234 (High Priority): Mobile app crashes on iOS when exporting large datasets
        Status: In Progress - Fix scheduled for v2.1.3

        Ticket #1235 (Medium): Report generation takes 5+ minutes for datasets over 100K rows
        Status: Investigating - Optimization in progress

        Ticket #1236 (Low): Feature request for dark mode in web interface
        Status: Planned for Q2 2025
        """
    }

    query = "What are the main strengths and weaknesses of this product based on all available information?"

    print("=" * 100)
    print("DEMONSTRATION: Query-Driven Iterative Refinement")
    print("=" * 100)
    print(f"\nQuery: {query}")
    print(f"\nContext has {len(context)} slices:")
    for key in context.keys():
        print(f"  - {key}")

    print("\n" + "=" * 100)
    print("EXPECTED REFINEMENT PROCESS:")
    print("=" * 100)

    # Simulate what the model would do
    print("\n[STEP 1] Model discovers available slices:")
    print("```python")
    print("slices = list_slices()")
    print("print(slices)")
    print("```")
    print("Output: ['dict_user_reviews', 'dict_technical_specs', 'dict_support_tickets']")

    print("\n[STEP 2] Initialize hypothesis:")
    print("```python")
    print('update_hypothesis("Need to analyze product strengths and weaknesses")')
    print("```")
    print('Hypothesis v0: "Need to analyze product strengths and weaknesses"')

    print("\n[STEP 3] Query first slice (user_reviews):")
    print("```python")
    print('result_1 = llm_query(')
    print('    "What strengths and weaknesses are mentioned in these reviews?",')
    print('    slice_id="dict_user_reviews"')
    print(')')
    print("```")
    print("\n--- sub_RLM Call #1 ---")
    print("Context slice: user_reviews")
    print("Response: ")
    simulated_result_1 = """Strengths:
- Analytics dashboard is intuitive and powerful
- Data visualization tools are excellent
- Seamless system integration
- Excellent customer support

Weaknesses:
- Mobile app crashes frequently
- Report generation is slow for large datasets
- Pricing is high for small teams"""
    print(simulated_result_1)

    print("\n[STEP 4] Refine hypothesis with finding #1:")
    print("```python")
    print('refined_1 = llm_query(f"""')
    print('Current hypothesis: {get_hypothesis()}')
    print('New finding from user reviews: {result_1}')
    print('Provide a refined hypothesis incorporating this information.')
    print('""")')
    print('update_hypothesis(refined_1)')
    print("```")
    print("\nHypothesis v1:")
    simulated_hyp_1 = """Based on user reviews:
STRENGTHS: Powerful analytics, great visualization, seamless integration, excellent support
WEAKNESSES: Mobile app stability issues, slow report generation, high pricing for small teams"""
    print(simulated_hyp_1)

    print("\n[STEP 5] Query second slice (technical_specs):")
    print("```python")
    print('result_2 = llm_query(')
    print('    "What technical capabilities and pricing information are provided?",')
    print('    slice_id="dict_technical_specs"')
    print(')')
    print("```")
    print("\n--- sub_RLM Call #2 ---")
    print("Context slice: technical_specs")
    print("Response:")
    simulated_result_2 = """Technical Capabilities:
- Real-time analytics (1M events/sec) - strong performance
- Comprehensive export formats (PDF, Excel, CSV)
- Mobile apps available but noted as "beta"
- Extensive integration options (REST API, 50+ connectors)

Pricing:
- $99/month (Starter), $299/month (Pro), Enterprise (Custom)
- Multiple tiers available"""
    print(simulated_result_2)

    print("\n[STEP 6] Refine hypothesis with finding #2:")
    print("```python")
    print('refined_2 = llm_query(f"""')
    print('Current hypothesis: {get_hypothesis()}')
    print('New finding from technical specs: {result_2}')
    print('Provide a refined hypothesis.')
    print('""")')
    print('update_hypothesis(refined_2)')
    print("```")
    print("\nHypothesis v2:")
    simulated_hyp_2 = """STRENGTHS:
- Powerful real-time analytics (1M events/sec)
- Excellent visualization and intuitive dashboard
- Comprehensive integrations (50+ connectors, REST API)
- Multiple export formats
- Excellent customer support

WEAKNESSES:
- Mobile apps still in beta (explains crash issues from reviews)
- Report generation performance issues with large datasets
- Pricing may be high for small teams ($99-299/month)"""
    print(simulated_hyp_2)

    print("\n[STEP 7] Query third slice (support_tickets):")
    print("```python")
    print('result_3 = llm_query(')
    print('    "What issues are being tracked and their status?",')
    print('    slice_id="dict_support_tickets"')
    print(')')
    print("```")
    print("\n--- sub_RLM Call #3 ---")
    print("Context slice: support_tickets")
    print("Response:")
    simulated_result_3 = """Active Issues:
- Mobile app iOS crash (High Priority) - Fix scheduled for v2.1.3
- Slow report generation for large datasets (Medium) - Optimization in progress
- Dark mode requested (Low) - Planned for Q2 2025

Shows: Company is actively addressing the main weaknesses"""
    print(simulated_result_3)

    print("\n[STEP 8] Final hypothesis refinement:")
    print("```python")
    print('final = llm_query(f"""')
    print('Current hypothesis: {get_hypothesis()}')
    print('New finding from support tickets: {result_3}')
    print('Provide final comprehensive answer.')
    print('""")')
    print('update_hypothesis(final)')
    print("```")
    print("\nHypothesis v3 (FINAL):")
    simulated_final = """PRODUCT STRENGTHS:
1. Powerful real-time analytics engine (1M events/sec)
2. Intuitive and excellent data visualization tools
3. Seamless integration capabilities (50+ connectors, REST API)
4. Comprehensive export formats (PDF, Excel, CSV)
5. Excellent customer support

PRODUCT WEAKNESSES:
1. Mobile apps still in beta with stability issues (iOS crash bug being fixed in v2.1.3)
2. Report generation performance problems with large datasets (>100K rows, optimization in progress)
3. Pricing may be challenging for small teams ($99-299/month)

POSITIVE NOTE: The company is actively addressing the main technical issues, with fixes
scheduled/in progress for both the mobile crashes and report generation performance."""
    print(simulated_final)

    print("\n[STEP 9] Return final answer:")
    print("```python")
    print('FINAL(get_hypothesis())')
    print("```")

    print("\n" + "=" * 100)
    print("REFINEMENT SUMMARY:")
    print("=" * 100)
    print(f"\nTotal sub_RLM calls made: 6")
    print(f"  - 3 calls to query slices (one per context chunk)")
    print(f"  - 3 calls to refine hypothesis (one after each finding)")
    print(f"\nHypothesis evolution:")
    print(f"  v0: Initial understanding (empty)")
    print(f"  v1: After user_reviews slice → identified core strengths/weaknesses")
    print(f"  v2: After technical_specs slice → added technical depth and pricing context")
    print(f"  v3: After support_tickets slice → added mitigation info and active fixes")
    print(f"\nFinal answer: Comprehensive analysis aggregating all 3 context slices")

    print("\n" + "=" * 100)
    print("To see this in REAL execution with actual LLM calls:")
    print("=" * 100)
    print("""
    export OPENAI_API_KEY=your_key
    python -c "
    from rlm.rlm_repl import RLM_REPL

    context = {
        'user_reviews': '...',
        'technical_specs': '...',
        'support_tickets': '...'
    }

    client = RLM_REPL(
        model='gpt-4o-mini',
        recursive_model='gpt-4o-mini',
        enable_logging=True  # Enable to see all REPL interactions
    )

    result = client.completion(
        context,
        'What are the main strengths and weaknesses?'
    )
    print(result)
    "
    """)


def show_hypothesis_tracking():
    """
    Demonstrate hypothesis tracking functionality.
    """
    print("\n" + "=" * 100)
    print("HYPOTHESIS TRACKING DEMONSTRATION")
    print("=" * 100)

    from rlm.repl import REPLEnv
    from rlm.utils.context_slicer import ContextSlicer

    # Create slices
    context = {
        "doc1": "First document",
        "doc2": "Second document"
    }
    slices = ContextSlicer.auto_slice_context(context)

    # Note: This will fail without API key, but shows the structure
    print("\nHypothesis tracking allows you to maintain state across sub_RLM calls:")
    print("""
# In REPL environment:

# Start with initial hypothesis
update_hypothesis("Initial: Need to analyze documents")
print(get_hypothesis())
# Output: "Initial: Need to analyze documents"

# After processing first slice
update_hypothesis("After doc1: Found key insight A")
print(get_hypothesis())
# Output: "After doc1: Found key insight A"

# After processing second slice
update_hypothesis("After doc2: Insights A and B, conclusion C")
print(get_hypothesis())
# Output: "After doc2: Insights A and B, conclusion C"

# View evolution
print(get_hypothesis_history())
# Output: ["Initial: Need to analyze documents", "After doc1: Found key insight A"]
""")


if __name__ == "__main__":
    # Run simulation
    demo_with_detailed_logging()

    # Show hypothesis tracking
    show_hypothesis_tracking()
