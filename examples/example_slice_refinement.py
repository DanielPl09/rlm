"""
Example demonstrating query-driven iterative refinement with context slicing.

This example shows how RLM uses pre-segmented context chunks and hypothesis
tracking to iteratively refine answers across multiple sub_RLM calls.
"""

import os
from rlm.rlm_repl import RLM_REPL


def example_with_sliced_context():
    """
    Example showing how RLM handles multi-part context with iterative refinement.
    """
    # Example: Multi-document context about different topics
    context = {
        "documentation": """
        # API Documentation

        ## Authentication
        Our API uses OAuth 2.0 for authentication. You need to obtain an access token
        before making any API calls. Tokens expire after 1 hour.

        ## Rate Limits
        - Free tier: 100 requests/hour
        - Pro tier: 1000 requests/hour
        - Enterprise: Unlimited
        """,
        "code_examples": """
        # Python Example
        import requests

        def get_user_data(user_id, token):
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"https://api.example.com/users/{user_id}", headers=headers)
            return response.json()

        # Rate limit handling
        def handle_rate_limit(response):
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                return True
            return False
        """,
        "chat_history": [
            {"role": "user", "content": "How do I authenticate with the API?"},
            {"role": "assistant", "content": "You need to use OAuth 2.0 to get an access token."},
            {"role": "user", "content": "What are the rate limits?"},
            {"role": "assistant", "content": "It depends on your tier - Free has 100/hr, Pro has 1000/hr."}
        ]
    }

    # Query that requires information from multiple slices
    query = "Write a complete guide on how to use the API, including authentication, rate limits, and example code."

    # Initialize RLM with slicing enabled (default)
    client = RLM_REPL(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini",
        max_iterations=15,
        enable_logging=True
    )

    print("=" * 80)
    print("Example: Query-Driven Iterative Refinement with Context Slicing")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"\nContext has {len(context)} sections: {list(context.keys())}")
    print("\nThe RLM will:")
    print("1. Auto-slice the context into chunks")
    print("2. Query each relevant chunk with sub_RLM")
    print("3. Update hypothesis after each sub_RLM call")
    print("4. Provide final refined answer\n")

    # Run completion with slicing
    result = client.completion(context, query)

    print("\n" + "=" * 80)
    print("FINAL RESULT:")
    print("=" * 80)
    print(result)

    return result


def example_manual_slicing():
    """
    Example showing how to manually create and use context slices.
    """
    from rlm.utils.context_slicer import ContextSlicer

    # Create custom slices
    slicer = ContextSlicer()

    slicer.add_slice(
        "product_docs",
        "Our product offers three features: Analytics, Reporting, and Integration.",
        metadata={"type": "documentation", "category": "features"}
    )

    slicer.add_slice(
        "pricing_info",
        "Pricing: Starter ($10/mo), Professional ($50/mo), Enterprise (custom)",
        metadata={"type": "documentation", "category": "pricing"}
    )

    slicer.add_slice(
        "customer_feedback",
        "Users love the analytics feature but find reporting complex.",
        metadata={"type": "feedback", "sentiment": "mixed"}
    )

    print("\n" + "=" * 80)
    print("Manual Context Slicing Example")
    print("=" * 80)
    print(f"\nCreated {len(slicer.list_slices())} custom slices:")
    for info in slicer.get_slice_info():
        print(f"  - {info['slice_id']}: {info['metadata']}")

    # These slices would be passed to REPLEnv for slice-based querying
    # In actual usage, this happens automatically in RLM_REPL.setup_context()

    return slicer


def example_auto_slicing():
    """
    Example showing automatic context slicing strategies.
    """
    from rlm.utils.context_slicer import ContextSlicer

    print("\n" + "=" * 80)
    print("Auto-Slicing Examples")
    print("=" * 80)

    # Example 1: Dictionary context (sliced by keys)
    dict_context = {
        "introduction": "This is an intro...",
        "methodology": "Our methodology involves...",
        "results": "We found that...",
        "conclusion": "In conclusion..."
    }

    slices_dict = ContextSlicer.auto_slice_context(dict_context)
    print(f"\n1. Dictionary context → {len(slices_dict)} slices:")
    for sid in slices_dict:
        print(f"   - {sid}")

    # Example 2: List context (sliced into chunks)
    list_context = [f"Document {i}" for i in range(25)]
    slices_list = ContextSlicer.auto_slice_context(list_context)
    print(f"\n2. List context (25 items) → {len(slices_list)} chunks:")
    for sid, slice_obj in slices_list.items():
        print(f"   - {sid}: items {slice_obj.metadata['start_index']}-{slice_obj.metadata['end_index']}")

    # Example 3: Markdown string (sliced by sections)
    markdown_context = """
# Introduction
This is the introduction section.

## Background
Here's the background information.

## Methods
Our methodology is described here.

# Results
The results section contains findings.
"""

    slices_markdown = ContextSlicer.auto_slice_context(markdown_context)
    print(f"\n3. Markdown context → {len(slices_markdown)} sections:")
    for sid in slices_markdown:
        print(f"   - {sid}")

    return slices_dict, slices_list, slices_markdown


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RLM Query-Driven Iterative Refinement Examples")
    print("=" * 80)

    # Show auto-slicing capabilities
    example_auto_slicing()

    # Show manual slicing
    example_manual_slicing()

    # Run full example with RLM (requires API key)
    if os.getenv("OPENAI_API_KEY"):
        example_with_sliced_context()
    else:
        print("\n[Skipping full RLM example - OPENAI_API_KEY not set]")
