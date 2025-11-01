"""
Basic RLM Verification Test

Tests if RLM core functionality works when llm_query() is used correctly
(i.e., manually including context in the query).
"""

from rlm.rlm_repl import RLM_REPL

def test_rlm_basic():
    """Simple test: Can RLM use llm_query() successfully when context is included?"""

    print("="*80)
    print("BASIC RLM VERIFICATION TEST")
    print("="*80)

    # Very simple context
    context = """
Employee: Alice, Salary: 95000
Employee: Bob, Salary: 78000
Employee: Carol, Salary: 102000
    """

    # Simple query that SHOULD work if RLM works
    query = """
Find the employee with the highest salary.

IMPORTANT: When you use llm_query(), you MUST include the context data like this:
    llm_query(f"Your question here\\n\\nData:\\n{context}")

The llm_query() function does NOT automatically include context!
    """

    print(f"\nContext:\n{context}")
    print(f"\nQuery: {query}\n")
    print("="*80)
    print("Running RLM...\n")

    rlm = RLM_REPL(
        model="claude-3-opus-20240229",
        recursive_model="claude-3-5-haiku-20241022",
        enable_logging=True,
        max_iterations=10,
        provider="anthropic"
    )

    result = rlm.completion(context=context, query=query)

    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(result)
    print("="*80)

    # Check if result is correct
    if "Carol" in result or "102000" in result:
        print("\n✓ SUCCESS: RLM found the correct answer (Carol, $102,000)")
        return True
    else:
        print("\n✗ FAIL: RLM did not find the correct answer")
        print(f"Expected: Carol with $102,000")
        print(f"Got: {result[:200]}")
        return False

if __name__ == "__main__":
    success = test_rlm_basic()
    print(f"\nBasic RLM Test: {'PASSED' if success else 'FAILED'}")
