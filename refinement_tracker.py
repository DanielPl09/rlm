"""
Refinement Tracker - Logs Content Knowledge Gained Per Iteration

This helps visualize WHAT the model learns at each step,
focusing on content understanding, not code debugging.
"""

class RefinementTracker:
    """Tracks content knowledge accumulated across RLM iterations"""

    def __init__(self):
        self.iterations = []
        self.knowledge_base = {}

    def log_iteration(self, iteration_num, action, knowledge_gained, source_doc=None):
        """
        Log what content knowledge was gained in this iteration.

        Args:
            iteration_num: Which iteration (1, 2, 3...)
            action: What the model did (e.g., "Queried for promotion candidates")
            knowledge_gained: Dict of facts learned (e.g., {"promoted_employees": ["Alice", "Carol", "Frank"]})
            source_doc: Which document was the source (e.g., "performance_reviews.txt")
        """
        self.iterations.append({
            "iteration": iteration_num,
            "action": action,
            "knowledge": knowledge_gained,
            "source": source_doc
        })

        # Add to cumulative knowledge base
        if knowledge_gained:
            self.knowledge_base.update(knowledge_gained)

    def print_summary(self):
        """Print a visual summary of iterative refinement"""
        print("\n" + "="*80)
        print("ITERATIVE CONTENT REFINEMENT SUMMARY")
        print("="*80)

        for iter_data in self.iterations:
            print(f"\n📍 ITERATION {iter_data['iteration']}:")
            print(f"   Action: {iter_data['action']}")
            if iter_data['source']:
                print(f"   Source: {iter_data['source']}")
            if iter_data['knowledge']:
                print(f"   Knowledge Gained:")
                for key, value in iter_data['knowledge'].items():
                    if isinstance(value, list):
                        print(f"      • {key}: {len(value)} items")
                        for item in value[:3]:  # Show first 3
                            print(f"        - {item}")
                        if len(value) > 3:
                            print(f"        - ... and {len(value)-3} more")
                    else:
                        print(f"      • {key}: {value}")

        print("\n" + "="*80)
        print("CUMULATIVE KNOWLEDGE GAINED:")
        print("="*80)
        total_facts = len(self.knowledge_base)
        print(f"Total facts learned: {total_facts}")
        for key, value in self.knowledge_base.items():
            if isinstance(value, list):
                print(f"  • {key}: {len(value)} items")
            else:
                print(f"  • {key}: {value}")
        print("="*80 + "\n")


def demo_tracker():
    """Demo of what the tracker would show for good iterative refinement"""

    tracker = RefinementTracker()

    # Simulate what GOOD refinement looks like

    tracker.log_iteration(
        iteration_num=1,
        action="Explored context structure",
        knowledge_gained={
            "documents_found": ["employee_records", "performance_reviews", "project_assignments", "budget_summary"],
            "total_employees": 8
        },
        source_doc="All documents"
    )

    tracker.log_iteration(
        iteration_num=2,
        action="Queried sub-LLM to find promotion candidates",
        knowledge_gained={
            "promoted_employees": ["Alice Johnson", "Carol White", "Frank Chen"],
            "under_review": ["David Lee", "Grace Kim"]
        },
        source_doc="performance_reviews.txt"
    )

    tracker.log_iteration(
        iteration_num=3,
        action="Queried sub-LLM to get salaries for promoted employees",
        knowledge_gained={
            "Alice_salary": 95000,
            "Carol_salary": 102000,
            "Frank_salary": 110000,
            "total_current_cost": 307000
        },
        source_doc="employee_records.txt"
    )

    tracker.log_iteration(
        iteration_num=4,
        action="Queried sub-LLM to find their projects",
        knowledge_gained={
            "Alice_project": "CloudSync v2.0 (Lead)",
            "Carol_project": "CloudSync v2.0 (Team)",
            "Frank_project": "CloudSync v2.0 (Team)",
            "all_on_same_project": True
        },
        source_doc="project_assignments.txt"
    )

    tracker.log_iteration(
        iteration_num=5,
        action="Synthesized findings into final answer",
        knowledge_gained={
            "key_insight": "All 3 promotion candidates work on CloudSync - critical project",
            "department_impact": "Engineering (100% of promotions)",
            "project_risk": "High - losing any would impact CloudSync v2.0"
        },
        source_doc="Synthesis"
    )

    tracker.print_summary()


if __name__ == "__main__":
    print("Demo: What Iterative Content Refinement Should Look Like\n")
    demo_tracker()
