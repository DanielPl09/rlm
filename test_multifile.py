"""
Cost-efficient multi-file RLM test with detailed logging.
This shows iterative refinement over multiple documents.
"""

from rlm.rlm_repl import RLM_REPL
import json

def create_multifile_context():
    """
    Create a realistic multi-file scenario with information spread across documents.
    Much cheaper than 1M lines - only ~1000 lines total.
    """

    # Simulate multiple documents with related information
    documents = {
        "employee_records.txt": """
Employee Database - Q4 2024

ID: 1001, Name: Alice Johnson, Department: Engineering, Salary: 95000, Start Date: 2020-03-15
ID: 1002, Name: Bob Smith, Department: Marketing, Salary: 78000, Start Date: 2019-07-22
ID: 1003, Name: Carol White, Department: Engineering, Salary: 102000, Start Date: 2018-11-03
ID: 1004, Name: David Lee, Department: Sales, Salary: 85000, Start Date: 2021-01-10
ID: 1005, Name: Eve Martinez, Department: HR, Salary: 72000, Start Date: 2022-05-18
ID: 1006, Name: Frank Chen, Department: Engineering, Salary: 110000, Start Date: 2017-09-12
ID: 1007, Name: Grace Kim, Department: Marketing, Salary: 81000, Start Date: 2020-08-25
ID: 1008, Name: Henry Brown, Department: Sales, Salary: 88000, Start Date: 2019-12-01

Total Employees: 8
""",
        "project_assignments.txt": """
Project Assignments - Active Projects

Project: CloudSync v2.0
- Lead: Alice Johnson (ID: 1001)
- Team: Frank Chen (ID: 1006), Carol White (ID: 1003)
- Budget: $450,000
- Status: In Progress (75% complete)
- Deadline: 2024-12-31

Project: Marketing Campaign "Launch2025"
- Lead: Bob Smith (ID: 1002)
- Team: Grace Kim (ID: 1007)
- Budget: $125,000
- Status: Planning (30% complete)
- Deadline: 2025-02-15

Project: Sales Analytics Dashboard
- Lead: David Lee (ID: 1004)
- Team: Henry Brown (ID: 1008)
- Budget: $85,000
- Status: Testing (90% complete)
- Deadline: 2024-11-30

Project: HR Portal Redesign
- Lead: Eve Martinez (ID: 1005)
- Team: None
- Budget: $35,000
- Status: Requirements (15% complete)
- Deadline: 2025-03-31
""",
        "performance_reviews.txt": """
Performance Reviews - 2024 Annual

Employee ID: 1001 (Alice Johnson)
Rating: Excellent (4.8/5.0)
Comments: Outstanding technical leadership on CloudSync project. Mentors junior engineers effectively.
Promotion Recommended: Yes

Employee ID: 1002 (Bob Smith)
Rating: Good (3.9/5.0)
Comments: Solid marketing strategies. Could improve cross-team communication.
Promotion Recommended: No

Employee ID: 1003 (Carol White)
Rating: Excellent (4.6/5.0)
Comments: Exceptional code quality and architecture design.
Promotion Recommended: Yes

Employee ID: 1004 (David Lee)
Rating: Very Good (4.2/5.0)
Comments: Consistently exceeds sales targets. Strong client relationships.
Promotion Recommended: Under Review

Employee ID: 1005 (Eve Martinez)
Rating: Good (3.7/5.0)
Comments: Manages HR processes well. Needs more strategic initiative.
Promotion Recommended: No

Employee ID: 1006 (Frank Chen)
Rating: Outstanding (4.9/5.0)
Comments: Senior engineer with deep technical expertise. Key contributor to CloudSync.
Promotion Recommended: Yes - to Principal Engineer

Employee ID: 1007 (Grace Kim)
Rating: Very Good (4.1/5.0)
Comments: Creative marketing ideas and strong execution.
Promotion Recommended: Under Review

Employee ID: 1008 (Henry Brown)
Rating: Good (4.0/5.0)
Comments: Reliable sales performance. Good team player.
Promotion Recommended: No
""",
        "budget_summary.txt": """
Department Budget Summary - FY 2024

Engineering Department
- Total Headcount: 3
- Personnel Costs: $307,000
- Project Budgets: $450,000 (CloudSync)
- Equipment & Tools: $85,000
- Total: $842,000

Marketing Department
- Total Headcount: 2
- Personnel Costs: $159,000
- Campaign Budgets: $125,000 (Launch2025)
- Advertising & Tools: $220,000
- Total: $504,000

Sales Department
- Total Headcount: 2
- Personnel Costs: $173,000
- Project Budgets: $85,000 (Analytics Dashboard)
- Travel & Entertainment: $45,000
- Total: $303,000

HR Department
- Total Headcount: 1
- Personnel Costs: $72,000
- Project Budgets: $35,000 (Portal Redesign)
- Recruiting & Training: $95,000
- Total: $202,000

Company Total Budget: $1,851,000
""",
        "metadata.json": {
            "company": "TechCorp Industries",
            "fiscal_year": 2024,
            "last_updated": "2024-10-31",
            "total_documents": 4,
            "confidential": True
        }
    }

    # Convert to a single context string with clear separators
    context_parts = []
    context_parts.append("=== COMPANY DATA - MULTIPLE DOCUMENTS ===\n")

    for filename, content in documents.items():
        if filename.endswith('.json'):
            context_parts.append(f"\n--- FILE: {filename} ---")
            context_parts.append(json.dumps(content, indent=2))
        else:
            context_parts.append(f"\n--- FILE: {filename} ---")
            context_parts.append(content)

    return "\n".join(context_parts)


def test_simple_query():
    """Test 1: Simple information retrieval"""
    print("\n" + "="*80)
    print("TEST 1: Simple Information Retrieval")
    print("="*80)

    context = create_multifile_context()
    print(f"Context size: ~{len(context)} characters (~{len(context.split())} words)")

    rlm = RLM_REPL(
        model="gpt-4o-mini",  # Cheap model for root LM
        recursive_model="gpt-4o-mini",  # Same cheap model for sub-calls
        enable_logging=True,
        max_iterations=5  # Limit iterations to control cost
    )

    query = "Who is the highest paid employee and what project are they working on?"
    print(f"\nQuery: {query}\n")

    result = rlm.completion(context=context, query=query)
    print(f"\n{'='*80}")
    print(f"FINAL ANSWER: {result}")
    print(f"{'='*80}\n")

    return result


def test_complex_analysis():
    """Test 2: Complex multi-document analysis"""
    print("\n" + "="*80)
    print("TEST 2: Complex Multi-Document Analysis")
    print("="*80)

    context = create_multifile_context()
    print(f"Context size: ~{len(context)} characters")

    rlm = RLM_REPL(
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini",
        enable_logging=True,
        max_iterations=8  # More iterations for complex task
    )

    query = """Identify all employees recommended for promotion and calculate:
1. Their total current salary cost
2. Which projects they're leading or contributing to
3. Total budget of those projects"""

    print(f"\nQuery: {query}\n")

    result = rlm.completion(context=context, query=query)
    print(f"\n{'='*80}")
    print(f"FINAL ANSWER: {result}")
    print(f"{'='*80}\n")

    return result


def main():
    """Run cost-efficient tests showing iterative refinement"""

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  RLM Multi-File Test with Logging                          ║
║                                                                            ║
║  This test demonstrates how RLM iteratively refines its understanding     ║
║  across multiple documents using recursive sub-calls.                      ║
║                                                                            ║
║  Cost Control:                                                             ║
║  - Using gpt-4o-mini (~$0.15/$0.60 per 1M tokens)                        ║
║  - Small context (~1000 lines vs 1M in original)                          ║
║  - Limited iterations (5-8 vs unlimited)                                   ║
║                                                                            ║
║  Watch for:                                                                ║
║  - How the model explores documents in REPL                                ║
║  - Recursive llm_query() calls to sub-LLMs                                ║
║  - Iterative refinement over multiple steps                                ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    # Run tests
    test_simple_query()

    print("\n" + "="*80)
    print("Ready for complex test? (This will use more tokens)")
    print("="*80)

    # Uncomment to run complex test:
    # test_complex_analysis()


if __name__ == "__main__":
    main()
