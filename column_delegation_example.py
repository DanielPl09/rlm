"""
Column-Based Context Delegation Example

Demonstrates how RLM delegates RELEVANT COLUMNS to different sub-calls,
showing incremental refinement through intermediate results.

Key Concept:
- Structured data (rows × columns)
- Query requires multi-step reasoning across different columns
- Each RLM sub-call gets ONLY the relevant columns
- Intermediates build progressively toward final answer
"""

from rlm import RLM_REPL
import json


def create_customer_data():
    """
    Create structured customer data with multiple columns.

    Small dataset (20 customers) but requires column-based delegation
    to answer the query correctly.
    """
    customers = [
        # West Region - Electronics
        {"id": 1, "name": "Alice Johnson", "region": "West", "product": "Electronics", "amount": 1500, "satisfaction": 4.8, "purchase_date": "2024-01-15"},
        {"id": 5, "name": "Eve Martinez", "region": "West", "product": "Electronics", "amount": 2200, "satisfaction": 4.9, "purchase_date": "2024-02-10"},
        {"id": 9, "name": "Ivan Petrov", "region": "West", "product": "Electronics", "amount": 1800, "satisfaction": 4.7, "purchase_date": "2024-03-05"},

        # West Region - Books
        {"id": 3, "name": "Charlie Brown", "region": "West", "product": "Books", "amount": 450, "satisfaction": 4.5, "purchase_date": "2024-01-20"},
        {"id": 11, "name": "Karen Lee", "region": "West", "product": "Books", "amount": 380, "satisfaction": 4.6, "purchase_date": "2024-02-25"},

        # West Region - Clothing
        {"id": 7, "name": "Grace Wang", "region": "West", "product": "Clothing", "amount": 890, "satisfaction": 4.4, "purchase_date": "2024-01-28"},
        {"id": 15, "name": "Oscar Wilde", "region": "West", "product": "Clothing", "amount": 720, "satisfaction": 4.3, "purchase_date": "2024-03-12"},

        # East Region - Electronics
        {"id": 2, "name": "Bob Smith", "region": "East", "product": "Electronics", "amount": 1300, "satisfaction": 4.2, "purchase_date": "2024-01-18"},
        {"id": 10, "name": "Jane Doe", "region": "East", "product": "Electronics", "amount": 1950, "satisfaction": 4.6, "purchase_date": "2024-02-22"},

        # East Region - Books
        {"id": 4, "name": "David Kim", "region": "East", "product": "Books", "amount": 320, "satisfaction": 4.1, "purchase_date": "2024-01-25"},
        {"id": 12, "name": "Lisa Wong", "region": "East", "product": "Books", "amount": 290, "satisfaction": 4.0, "purchase_date": "2024-03-01"},

        # South Region - Electronics
        {"id": 6, "name": "Frank Lopez", "region": "South", "product": "Electronics", "amount": 1700, "satisfaction": 4.5, "purchase_date": "2024-02-05"},
        {"id": 14, "name": "Nancy Drew", "region": "South", "product": "Electronics", "amount": 2100, "satisfaction": 4.8, "purchase_date": "2024-03-08"},

        # South Region - Clothing
        {"id": 8, "name": "Henry Ford", "region": "South", "product": "Clothing", "amount": 650, "satisfaction": 4.2, "purchase_date": "2024-02-14"},
        {"id": 16, "name": "Paula Abdul", "region": "South", "product": "Clothing", "amount": 810, "satisfaction": 4.4, "purchase_date": "2024-03-15"},

        # North Region - Electronics
        {"id": 13, "name": "Mike Tyson", "region": "North", "product": "Electronics", "amount": 1600, "satisfaction": 4.3, "purchase_date": "2024-02-28"},
        {"id": 17, "name": "Quinn Adams", "region": "North", "product": "Electronics", "amount": 1400, "satisfaction": 4.1, "purchase_date": "2024-03-18"},

        # North Region - Books
        {"id": 18, "name": "Rachel Green", "region": "North", "product": "Books", "amount": 410, "satisfaction": 4.7, "purchase_date": "2024-03-20"},
        {"id": 19, "name": "Steve Jobs", "region": "North", "product": "Books", "amount": 350, "satisfaction": 4.5, "purchase_date": "2024-03-22"},

        # North Region - Clothing
        {"id": 20, "name": "Tina Turner", "region": "North", "product": "Clothing", "amount": 920, "satisfaction": 4.6, "purchase_date": "2024-03-25"},
    ]

    return customers


def create_query():
    """
    Create a query that REQUIRES column-based delegation.

    This query naturally leads to:
    1. Filter by 'region' column → intermediate result
    2. Filter by 'product' column → refined result
    3. Aggregate 'amount' column → find max
    4. Lookup 'name' and 'satisfaction' → final answer
    """

    query = """
Who is the customer in the West region with the highest spending on Electronics,
and what is their satisfaction rating?

REQUIRED: Use llm_query() for these steps:
1. Filter region column for West → get IDs
2. Filter those IDs' product column for Electronics → get IDs
3. Find max amount from those IDs → get top ID
4. Get name + satisfaction for top ID

Print intermediate results after each step to show progressive refinement.
Use FINAL_VAR() at the end.
"""

    return query


def main():
    """
    Execute the column delegation example.
    """

    print("=" * 80)
    print("COLUMN-BASED CONTEXT DELEGATION DEMO")
    print("Demonstrates incremental refinement through RLM sub-calls")
    print("=" * 80)
    print()

    # Create customer data
    customers = create_customer_data()
    print(f"Dataset: {len(customers)} customer records")
    print(f"Columns: id, name, region, product, amount, satisfaction, purchase_date")
    print()

    # Show data preview
    print("Sample records:")
    print("-" * 80)
    for customer in customers[:3]:
        print(f"  ID {customer['id']}: {customer['name']} | {customer['region']} | "
              f"{customer['product']} | ${customer['amount']} | ⭐{customer['satisfaction']}")
    print(f"  ... ({len(customers) - 3} more records)")
    print()

    # Create query
    query = create_query()

    # Initialize RLM
    print("=" * 80)
    print("Initializing RLM_REPL...")
    print("-" * 80)

    # Use Anthropic if available, otherwise OpenAI
    import os
    if os.getenv("ANTHROPIC_API_KEY"):
        print("✅ Using Anthropic Claude")
        print("   Root: claude-3-haiku-20240307 (fast)")
        print("   Sub:  claude-3-haiku-20240307")
        model = "claude-3-haiku-20240307"  # Use Haiku for root too (faster)
        sub_model = "claude-3-haiku-20240307"
    elif os.getenv("OPENAI_API_KEY"):
        print("✅ Using OpenAI")
        print("   Root: gpt-4o")
        print("   Sub:  gpt-4o-mini")
        model = "gpt-4o"
        sub_model = "gpt-4o-mini"
    else:
        print("❌ No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return

    print("-" * 80)
    print()

    rlm = RLM_REPL(
        model=model,
        recursive_model=sub_model,
        max_iterations=20,  # Allow enough iterations for multi-step process
    )

    # Run the completion
    print("=" * 80)
    print("EXECUTING COLUMN DELEGATION")
    print("=" * 80)
    print()
    print("Watch for llm_query() calls that delegate specific columns...")
    print()

    try:
        final_answer = rlm.completion(context=customers, query=query)

        print()
        print("=" * 80)
        print("FINAL ANSWER")
        print("=" * 80)
        print(final_answer)
        print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
