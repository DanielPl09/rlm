"""
Guided Iterative Refinement Test

This version uses improved prompting to encourage the model to:
1. Use llm_query() for content analysis (not manual parsing)
2. Build knowledge incrementally across iterations
3. Store findings in variables
4. Synthesize at the end

The key: delegate semantic understanding to sub-LLMs!
"""

from rlm.rlm_repl import RLM_REPL
import json


def create_multifile_context():
    """Multi-file company data"""

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
╔════════════════════════════════════════════════════════════════════════════╗
║          ITERATIVE CONTENT REFINEMENT - GUIDED VERSION                     ║
║                                                                            ║
║  This test shows how RLM should work:                                      ║
║  - Use llm_query() to extract information (don't parse manually!)         ║
║  - Build knowledge step-by-step across iterations                         ║
║  - Store findings in REPL variables                                       ║
║  - Synthesize everything at the end                                        ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)

    context = create_multifile_context()
    print(f"\nContext: {len(context)} characters\n")

    # Simpler query that naturally leads to step-by-step exploration
    query = """
    TASK: Find all employees recommended for promotion, then for each one tell me:
    - Their name and current salary
    - What project they're working on
    - Their department

    Finally, calculate the total salary cost and identify which department is most affected.

    IMPORTANT: Use llm_query() to extract this information - the context is small enough
    to send directly to the sub-LLM. Build up your answer step by step.
    """

    print("QUERY:", query)
    print("\n" + "="*80 + "\n")

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


if __name__ == "__main__":
    main()
