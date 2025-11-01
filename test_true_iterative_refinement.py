"""
TRUE Iterative Refinement Test - Addresses All 3 Criticisms

FIXES:
1. Query forces multi-step reasoning (can't answer in one shot)
2. No prescriptive instructions (doesn't mention llm_query)
3. Query is complex enough to require iterative narrowing

The query requires filtering candidates through multiple criteria,
each requiring a different document. Model must:
- Query → Get results → Observe → Decide next step → Query again
"""

from rlm.rlm_repl import RLM_REPL
import json


def create_multifile_context():
    """Multi-file company data"""

    documents = {
        "employee_records.txt": """
Employee Database - Q4 2024

ID: 1001, Name: Alice Johnson, Department: Engineering, Salary: 95000, Start Date: 2020-03-15, Tenure: 4.7 years
ID: 1002, Name: Bob Smith, Department: Marketing, Salary: 78000, Start Date: 2019-07-22, Tenure: 5.3 years
ID: 1003, Name: Carol White, Department: Engineering, Salary: 102000, Start Date: 2018-11-03, Tenure: 6.0 years
ID: 1004, Name: David Lee, Department: Sales, Salary: 85000, Start Date: 2021-01-10, Tenure: 3.8 years
ID: 1005, Name: Eve Martinez, Department: HR, Salary: 72000, Start Date: 2022-05-18, Tenure: 2.5 years
ID: 1006, Name: Frank Chen, Department: Engineering, Salary: 110000, Start Date: 2017-09-12, Tenure: 7.1 years
ID: 1007, Name: Grace Kim, Department: Marketing, Salary: 81000, Start Date: 2020-08-25, Tenure: 4.2 years
ID: 1008, Name: Henry Brown, Department: Sales, Salary: 88000, Start Date: 2019-12-01, Tenure: 5.0 years

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
- Critical: Yes
- Team Size: 3

Project: Marketing Campaign "Launch2025"
- Lead: Bob Smith (ID: 1002)
- Team: Grace Kim (ID: 1007)
- Budget: $125,000
- Status: Planning (30% complete)
- Deadline: 2025-02-15
- Critical: No
- Team Size: 2

Project: Sales Analytics Dashboard
- Lead: David Lee (ID: 1004)
- Team: Henry Brown (ID: 1008)
- Budget: $85,000
- Status: Testing (90% complete)
- Deadline: 2024-11-30
- Critical: No
- Team Size: 2

Project: HR Portal Redesign
- Lead: Eve Martinez (ID: 1005)
- Team: None
- Budget: $35,000
- Status: Requirements (15% complete)
- Deadline: 2025-03-31
- Critical: No
- Team Size: 1
""",
        "performance_reviews.txt": """
Performance Reviews - 2024 Annual

Employee ID: 1001 (Alice Johnson)
Rating: Excellent (4.8/5.0)
Comments: Outstanding technical leadership on CloudSync project. Mentors junior engineers effectively.
Promotion Recommended: Yes
Ready for Leadership: Yes

Employee ID: 1002 (Bob Smith)
Rating: Good (3.9/5.0)
Comments: Solid marketing strategies. Could improve cross-team communication.
Promotion Recommended: No
Ready for Leadership: Not Yet

Employee ID: 1003 (Carol White)
Rating: Excellent (4.6/5.0)
Comments: Exceptional code quality and architecture design.
Promotion Recommended: Yes
Ready for Leadership: Under Evaluation

Employee ID: 1004 (David Lee)
Rating: Very Good (4.2/5.0)
Comments: Consistently exceeds sales targets. Strong client relationships.
Promotion Recommended: Under Review
Ready for Leadership: Yes

Employee ID: 1005 (Eve Martinez)
Rating: Good (3.7/5.0)
Comments: Manages HR processes well. Needs more strategic initiative.
Promotion Recommended: No
Ready for Leadership: Not Yet

Employee ID: 1006 (Frank Chen)
Rating: Outstanding (4.9/5.0)
Comments: Senior engineer with deep technical expertise. Key contributor to CloudSync.
Promotion Recommended: Yes - to Principal Engineer
Ready for Leadership: Yes

Employee ID: 1007 (Grace Kim)
Rating: Very Good (4.1/5.0)
Comments: Creative marketing ideas and strong execution.
Promotion Recommended: Under Review
Ready for Leadership: Under Evaluation

Employee ID: 1008 (Henry Brown)
Rating: Good (4.0/5.0)
Comments: Reliable sales performance. Good team player.
Promotion Recommended: No
Ready for Leadership: Not Yet
""",
        "department_budgets.txt": """
Department Budget Allocations - FY 2024

Engineering Department
- Total Budget: $842,000
- Spent to Date: $680,000
- Remaining: $162,000
- Promotion Budget Available: $75,000
- Can Accommodate Promotions: 2 people max

Marketing Department
- Total Budget: $504,000
- Spent to Date: $480,000
- Remaining: $24,000
- Promotion Budget Available: $15,000
- Can Accommodate Promotions: 0 people (budget frozen)

Sales Department
- Total Budget: $303,000
- Spent to Date: $250,000
- Remaining: $53,000
- Promotion Budget Available: $30,000
- Can Accommodate Promotions: 1 person max

HR Department
- Total Budget: $202,000
- Spent to Date: $180,000
- Remaining: $22,000
- Promotion Budget Available: $12,000
- Can Accommodate Promotions: 0 people (budget frozen)
"""
    }

    # Build context string
    context_parts = []
    context_parts.append("=== COMPANY DATA - MULTIPLE DOCUMENTS ===\n")

    for filename, content in documents.items():
        context_parts.append(f"\n--- FILE: {filename} ---")
        context_parts.append(content)

    return "\n".join(context_parts)


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  TRUE ITERATIVE REFINEMENT EXPERIMENT                        ║
║                                                                              ║
║  This addresses the 3 criticisms:                                           ║
║  1. Query forces multi-step filtering (can't batch all at once)            ║
║  2. No prescriptive instructions (doesn't mention llm_query)                ║
║  3. Complex enough to require iterative narrowing                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    context = create_multifile_context()
    print(f"\nContext: {len(context)} characters across 4 documents\n")

    # Complex query requiring multi-step filtering
    # NO mention of llm_query() or how to solve it
    query = """
I need to identify the TOP PROMOTION CANDIDATE based on these criteria:

MUST meet ALL of the following (filtering criteria):
1. Has "Excellent" or "Outstanding" performance review rating
2. Is marked as "Ready for Leadership: Yes" in their review
3. Works on a project that is marked "Critical: Yes"
4. Their department has promotion budget available (not frozen)

Then among those who meet all criteria:
- Rank by tenure (longer is better)
- Consider team size (prefer those not working alone)

Provide the name of the single best candidate and explain why they were chosen
over others, showing your step-by-step filtering process.
    """

    print("QUERY:")
    print(query)
    print("\n" + "="*80)
    print("Expected behavior: Model should iteratively filter:")
    print("  Iter 1: Explore structure")
    print("  Iter 2: Find excellent/outstanding performers → ~3 candidates")
    print("  Iter 3: Filter for leadership ready → ~2-3 candidates")
    print("  Iter 4: Filter for critical projects → ~2 candidates")
    print("  Iter 5: Filter for budget availability → ~1-2 candidates")
    print("  Iter 6: Rank by tenure/team size → 1 final candidate")
    print("="*80 + "\n")

    rlm = RLM_REPL(
        model="claude-3-opus-20240229",
        recursive_model="claude-3-5-haiku-20241022",
        enable_logging=True,
        max_iterations=20,
        provider="anthropic"
    )

    result = rlm.completion(context=context, query=query)

    print("\n" + "="*80)
    print("FINAL ANSWER:")
    print("="*80)
    print(result)
    print("="*80 + "\n")

    print("\n" + "="*80)
    print("EXPECTED FILTERING PATH:")
    print("="*80)
    print("""
Step 1: Excellent/Outstanding performers
  → Alice (4.8), Carol (4.6), Frank (4.9)

Step 2: Ready for Leadership = Yes
  → Alice (Yes), Frank (Yes)
  → Carol filtered out (Under Evaluation)

Step 3: Works on Critical project
  → Both Alice and Frank work on CloudSync (Critical: Yes)
  → No filtering

Step 4: Department has budget
  → Engineering has $75K promotion budget for 2 people
  → No filtering

Step 5: Rank by tenure
  → Alice: 4.7 years
  → Frank: 7.1 years
  → Winner: FRANK CHEN (longer tenure, critical project, leadership ready)

Final Answer: Frank Chen
Reasoning: Outstanding performer (4.9), leadership ready, 7.1 years tenure,
works on critical CloudSync project, department has budget for promotion.
    """)


if __name__ == "__main__":
    main()
