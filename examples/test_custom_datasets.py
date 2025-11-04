"""
Custom dataset testing for query-driven iterative refinement.
Add your own datasets here to test with similar characteristics.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.utils.context_slicer import ContextSlicer
from rlm.utils.anthropic_client import AnthropicClient


def run_test(context: dict, query: str, api_key: str, test_name: str):
    """
    Run a refinement test on custom dataset.

    Args:
        context: Dictionary with context sections
        query: Query to answer
        api_key: Anthropic API key
        test_name: Name for this test
    """
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Query: {query}")
    print(f"Context has {len(context)} sections: {list(context.keys())}")

    # Create slices
    slices = ContextSlicer.auto_slice_context(context)
    print(f"Created {len(slices)} slices")

    # Initialize client
    client = AnthropicClient(api_key=api_key, model="claude-3-opus-20240229")

    # Run iterative refinement
    hypothesis = f"Initial: Need to answer '{query}'"
    hypothesis_history = []
    results = []

    for i, (slice_id, slice_obj) in enumerate(slices.items(), 1):
        print(f"\n[{i}/{len(slices)}] Processing {slice_id}...")

        # Query slice
        slice_prompt = f"Based on this context, answer: {query}\n\nContext: {slice_obj.content}\n\nBe concise."
        try:
            result = client.completion(slice_prompt)
            results.append((slice_id, result))
            print(f"  ✅ Result: {result[:100]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

        # Refine hypothesis
        refinement_prompt = f"Current: {hypothesis}\n\nNew finding from {slice_id}: {result}\n\nProvide updated hypothesis. Be concise."
        try:
            refined = client.completion(refinement_prompt)
            hypothesis_history.append(hypothesis)
            hypothesis = refined
            print(f"  ✅ Hypothesis refined")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Results
    print(f"\n{'='*80}")
    print(f"RESULTS: {test_name}")
    print(f"{'='*80}")
    print(f"Slices processed: {len(slices)}")
    print(f"Hypothesis versions: {len(hypothesis_history) + 1}")
    print(f"\nFinal Answer:\n{hypothesis}\n")
    print(f"{'='*80}")

    return hypothesis


# ============================================================================
# ADD YOUR CUSTOM DATASETS HERE
# ============================================================================

# Template for adding new datasets:
# dataset_name = {
#     'section1': 'Content for section 1...',
#     'section2': 'Content for section 2...',
#     'section3': 'Content for section 3...',
# }


# Example 1: Medical case study (multi-source patient data)
medical_case = {
    'patient_history': '''
    Patient: 45-year-old male
    Chief complaint: Persistent fatigue and joint pain (3 months)
    Past medical: Hypertension (controlled), No diabetes
    Family history: Father had rheumatoid arthritis
    Medications: Lisinopril 10mg daily
    ''',

    'lab_results': '''
    Complete Blood Count:
    - WBC: 12.5 (elevated, normal 4-10)
    - Hemoglobin: 11.2 (low, normal 13.5-17.5)
    - Platelets: Normal

    Inflammatory markers:
    - ESR: 45 mm/hr (elevated, normal <20)
    - CRP: 28 mg/L (elevated, normal <10)
    - RF factor: Positive
    ''',

    'physical_exam': '''
    Vital signs: BP 135/85, HR 82, Temp 37.2°C
    General: Appears fatigued, no acute distress
    Musculoskeletal:
    - Bilateral hand swelling (MCP joints)
    - Morning stiffness >1 hour
    - Reduced range of motion in wrists
    - No visible deformities
    '''
}

# Example 2: Software system analysis (distributed system logs)
system_logs = {
    'api_server_logs': '''
    [2024-11-04 10:15:23] INFO: Request processed in 45ms
    [2024-11-04 10:15:27] ERROR: Database timeout after 5000ms
    [2024-11-04 10:15:29] WARNING: Retry attempt 1/3 for request ID 7829
    [2024-11-04 10:15:35] ERROR: Database timeout after 5000ms
    [2024-11-04 10:15:41] ERROR: Max retries exceeded, request failed
    [2024-11-04 10:16:12] INFO: Request processed in 52ms
    ''',

    'database_metrics': '''
    Time range: 10:00-11:00
    - Average query time: 250ms (baseline: 100ms)
    - Connection pool: 95% utilized (normal: 60-70%)
    - Slow queries: 234 (>1s execution time)
    - Deadlocks detected: 12
    - Replication lag: 2.5 seconds (normal: <500ms)
    ''',

    'infrastructure_status': '''
    Database primary:
    - CPU: 92% utilized
    - Memory: 87% utilized (28GB/32GB)
    - Disk I/O: 450 IOPS (capacity: 500 IOPS)
    - Network: Normal

    Application servers (3 instances):
    - All healthy, CPU 35-40%
    - Memory usage normal
    - No errors in health checks
    '''
}

# Example 3: Financial analysis (quarterly performance data)
financial_data = {
    'income_statement': '''
    Q3 2024 vs Q3 2023:
    Revenue: $45M (+15% YoY)
    Cost of Revenue: $22M (+20% YoY)
    Gross Profit: $23M (+10% YoY)
    Operating Expenses: $18M (+12% YoY)
    Operating Income: $5M (+2% YoY)
    Net Income: $3.5M (-5% YoY)
    ''',

    'balance_sheet': '''
    Assets:
    - Cash: $12M (down from $18M last quarter)
    - Accounts Receivable: $8M (+$3M)
    - Inventory: $15M (+$5M)

    Liabilities:
    - Accounts Payable: $6M (+$2M)
    - Short-term Debt: $10M (+$5M new credit line)
    - Long-term Debt: $20M (unchanged)
    ''',

    'operational_metrics': '''
    Customer metrics:
    - New customers: 450 (+25% vs Q2)
    - Churn rate: 8% (up from 5% in Q2)
    - Average contract value: $100K (down from $115K)

    Efficiency:
    - Days Sales Outstanding: 65 days (up from 45)
    - Inventory turnover: 4x (down from 6x)
    - Customer acquisition cost: $12K (up from $8K)
    '''
}


def main():
    """Run tests on custom datasets."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Usage: export ANTHROPIC_API_KEY=your_key && python test_custom_datasets.py")
        sys.exit(1)

    print("="*80)
    print("CUSTOM DATASET TESTING")
    print("="*80)

    # Test 1: Medical case
    run_test(
        medical_case,
        "What is the likely diagnosis and what additional tests should be ordered?",
        api_key,
        "Medical Case Analysis"
    )

    # Test 2: System logs
    run_test(
        system_logs,
        "What is causing the system performance issues and how should they be resolved?",
        api_key,
        "System Performance Analysis"
    )

    # Test 3: Financial data
    run_test(
        financial_data,
        "What is the financial health of the company and what are the key concerns?",
        api_key,
        "Financial Health Analysis"
    )

    print("\n" + "="*80)
    print("✅ ALL CUSTOM DATASET TESTS COMPLETED")
    print("="*80)
    print("\nTo add your own datasets:")
    print("1. Add a new dictionary above (follow the template)")
    print("2. Add a run_test() call in main()")
    print("3. Run: export ANTHROPIC_API_KEY=key && python test_custom_datasets.py")
    print("="*80)


if __name__ == "__main__":
    main()
