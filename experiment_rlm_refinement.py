"""
RLM Iterative Refinement Experiment - Structured Output

Demonstrates iterative content refinement with structured JSON logging
for easy analysis and experiment defense.
"""

from rlm.rlm_repl import RLM_REPL
import json
import time
from datetime import datetime


class StructuredExperimentLogger:
    """Logs experiment with structured data for analysis"""

    def __init__(self):
        self.experiment = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "test_name": "RLM Iterative Refinement Experiment",
                "model_root": "claude-3-opus-20240229",
                "model_sub": "claude-3-5-haiku-20241022",
            },
            "query": None,
            "context": {
                "size_chars": 0,
                "size_tokens_approx": 0,
                "documents": []
            },
            "iterations": [],
            "refinement_timeline": [],
            "final_result": None,
            "analysis": {
                "total_iterations": 0,
                "total_sub_llm_calls": 0,
                "sub_calls_by_iteration": {},
                "knowledge_accumulated": []
            }
        }
        self.current_iteration = 0

    def log_query(self, query: str):
        self.experiment["query"] = query

    def log_context(self, context: str, documents: list):
        self.experiment["context"]["size_chars"] = len(context)
        self.experiment["context"]["size_tokens_approx"] = len(context) // 4
        self.experiment["context"]["documents"] = documents

    def log_iteration_start(self, iteration_num: int):
        self.current_iteration = iteration_num
        self.experiment["iterations"].append({
            "iteration": iteration_num,
            "sub_llm_calls": [],
            "knowledge_gained": {},
            "candidate_count": None
        })

    def log_sub_llm_call(self, query: str, response: str, context_source: str):
        """Log a sub-LLM query and response"""
        call_data = {
            "query": query[:200] + "..." if len(query) > 200 else query,
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            "context_source": context_source,
            "timestamp": time.time()
        }

        if self.experiment["iterations"]:
            self.experiment["iterations"][-1]["sub_llm_calls"].append(call_data)
            self.experiment["analysis"]["total_sub_llm_calls"] += 1

    def log_knowledge(self, key: str, value: any):
        """Log knowledge gained in this iteration"""
        if self.experiment["iterations"]:
            self.experiment["iterations"][-1]["knowledge_gained"][key] = value

            # Track cumulative knowledge
            self.experiment["analysis"]["knowledge_accumulated"].append({
                "iteration": self.current_iteration,
                "key": key,
                "value": str(value)[:100]
            })

    def log_candidate_count(self, count: int):
        """Log number of candidates remaining after filtering"""
        if self.experiment["iterations"]:
            self.experiment["iterations"][-1]["candidate_count"] = count

    def log_refinement_step(self, step: str, candidates_before: int, candidates_after: int, criterion: str):
        """Log a refinement/filtering step"""
        self.experiment["refinement_timeline"].append({
            "iteration": self.current_iteration,
            "step": step,
            "criterion": criterion,
            "candidates_before": candidates_before,
            "candidates_after": candidates_after,
            "filtered_out": candidates_before - candidates_after
        })

    def log_final_result(self, result: str):
        self.experiment["final_result"] = result

    def finalize(self):
        """Compute final statistics"""
        self.experiment["analysis"]["total_iterations"] = len(self.experiment["iterations"])

        # Sub-calls by iteration
        for iter_data in self.experiment["iterations"]:
            iter_num = iter_data["iteration"]
            self.experiment["analysis"]["sub_calls_by_iteration"][f"iteration_{iter_num}"] = len(iter_data["sub_llm_calls"])

    def save_json(self, filename: str):
        """Save experiment data as JSON"""
        self.finalize()
        with open(filename, 'w') as f:
            json.dump(self.experiment, f, indent=2)
        print(f"\n✓ Experiment data saved to: {filename}")

    def print_summary(self):
        """Print human-readable summary"""
        print("\n" + "="*80)
        print("EXPERIMENT SUMMARY")
        print("="*80)
        print(f"Total Iterations: {self.experiment['analysis']['total_iterations']}")
        print(f"Total Sub-LLM Calls: {self.experiment['analysis']['total_sub_llm_calls']}")
        print(f"\nSub-LLM Calls by Iteration:")
        for iter_key, count in self.experiment['analysis']['sub_calls_by_iteration'].items():
            print(f"  {iter_key}: {count} calls")

        print(f"\nRefinement Timeline:")
        for step in self.experiment['refinement_timeline']:
            print(f"  Iteration {step['iteration']}: {step['criterion']} → "
                  f"{step['candidates_before']} → {step['candidates_after']} candidates")

        print(f"\nKnowledge Accumulated:")
        for knowledge in self.experiment['analysis']['knowledge_accumulated']:
            print(f"  Iter {knowledge['iteration']}: {knowledge['key']} = {knowledge['value']}")

        print("="*80)


def create_multifile_context():
    """Create multi-file company data"""

    documents = {
        "employee_records.txt": """Employee Database - Q4 2024

ID: 1001, Name: Alice Johnson, Department: Engineering, Salary: 95000, Tenure: 4.7 years
ID: 1002, Name: Bob Smith, Department: Marketing, Salary: 78000, Tenure: 5.3 years
ID: 1003, Name: Carol White, Department: Engineering, Salary: 102000, Tenure: 6.0 years
ID: 1004, Name: David Lee, Department: Sales, Salary: 85000, Tenure: 3.8 years
ID: 1005, Name: Eve Martinez, Department: HR, Salary: 72000, Tenure: 2.5 years
ID: 1006, Name: Frank Chen, Department: Engineering, Salary: 110000, Tenure: 7.1 years
ID: 1007, Name: Grace Kim, Department: Marketing, Salary: 81000, Tenure: 4.2 years
ID: 1008, Name: Henry Brown, Department: Sales, Salary: 88000, Tenure: 5.0 years""",

        "project_assignments.txt": """Project Assignments - Active Projects

Project: CloudSync v2.0
- Lead: Alice Johnson (ID: 1001)
- Team: Frank Chen (ID: 1006), Carol White (ID: 1003)
- Status: In Progress (75% complete)
- Critical: Yes
- Team Size: 3

Project: Marketing Campaign Launch2025
- Lead: Bob Smith (ID: 1002)
- Team: Grace Kim (ID: 1007)
- Status: Planning (30% complete)
- Critical: No
- Team Size: 2

Project: Sales Analytics Dashboard
- Lead: David Lee (ID: 1004)
- Team: Henry Brown (ID: 1008)
- Status: Testing (90% complete)
- Critical: No
- Team Size: 2

Project: HR Portal Redesign
- Lead: Eve Martinez (ID: 1005)
- Status: Requirements (15% complete)
- Critical: No
- Team Size: 1""",

        "performance_reviews.txt": """Performance Reviews - 2024 Annual

ID: 1001 (Alice Johnson) - Rating: Excellent (4.8/5.0) - Promotion: Yes - Leadership Ready: Yes
ID: 1002 (Bob Smith) - Rating: Good (3.9/5.0) - Promotion: No - Leadership Ready: Not Yet
ID: 1003 (Carol White) - Rating: Excellent (4.6/5.0) - Promotion: Yes - Leadership Ready: Under Evaluation
ID: 1004 (David Lee) - Rating: Very Good (4.2/5.0) - Promotion: Under Review - Leadership Ready: Yes
ID: 1005 (Eve Martinez) - Rating: Good (3.7/5.0) - Promotion: No - Leadership Ready: Not Yet
ID: 1006 (Frank Chen) - Rating: Outstanding (4.9/5.0) - Promotion: Yes - Leadership Ready: Yes
ID: 1007 (Grace Kim) - Rating: Very Good (4.1/5.0) - Promotion: Under Review - Leadership Ready: Under Evaluation
ID: 1008 (Henry Brown) - Rating: Good (4.0/5.0) - Promotion: No - Leadership Ready: Not Yet""",

        "department_budgets.txt": """Department Budget Allocations - FY 2024

Engineering: Promotion Budget Available = $75,000 (Can accommodate 2 promotions)
Marketing: Promotion Budget Available = $0 (Budget frozen)
Sales: Promotion Budget Available = $30,000 (Can accommodate 1 promotion)
HR: Promotion Budget Available = $0 (Budget frozen)"""
    }

    context_parts = ["=== COMPANY DATA - MULTIPLE DOCUMENTS ===\n"]
    doc_list = []

    for filename, content in documents.items():
        context_parts.append(f"\n--- FILE: {filename} ---")
        context_parts.append(content)
        doc_list.append(filename)

    return "\n".join(context_parts), doc_list


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              RLM ITERATIVE REFINEMENT EXPERIMENT                             ║
║                    Structured Data Output                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Initialize logger
    logger = StructuredExperimentLogger()

    # Create context
    context, doc_list = create_multifile_context()
    logger.log_context(context, doc_list)

    # Define query
    query = """Identify the TOP PROMOTION CANDIDATE based on these criteria:

MUST meet ALL of the following:
1. Has "Excellent" or "Outstanding" performance rating
2. Is marked as "Leadership Ready: Yes"
3. Works on a project marked "Critical: Yes"
4. Their department has promotion budget available

Among those meeting all criteria, rank by tenure (prefer longer tenure).

Provide the name of the single best candidate and explain the filtering process."""

    logger.log_query(query)

    print(f"Context: {len(context)} characters, {len(doc_list)} documents")
    print(f"\nQuery: {query}\n")
    print("="*80 + "\n")

    # Run RLM with logging enabled
    print("Running RLM (logging enabled for visibility)...\n")

    rlm = RLM_REPL(
        model="claude-3-opus-20240229",
        recursive_model="claude-3-5-haiku-20241022",
        enable_logging=True,  # Enable to see the process
        max_iterations=20,
        provider="anthropic"
    )

    start_time = time.time()
    result = rlm.completion(context=context, query=query)
    elapsed_time = time.time() - start_time

    logger.log_final_result(result)
    logger.experiment["metadata"]["execution_time_seconds"] = round(elapsed_time, 2)

    print("\n" + "="*80)
    print("FINAL ANSWER:")
    print("="*80)
    print(result)
    print("="*80)

    # Save structured data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"experiment_results_{timestamp}.json"

    # Add expected answer for comparison
    logger.experiment["expected_answer"] = {
        "candidate": "Frank Chen",
        "reasoning": "Meets all criteria: Outstanding (4.9), Leadership Ready: Yes, CloudSync (Critical), Engineering has budget, 7.1 years tenure (longest)"
    }

    logger.save_json(output_file)
    logger.print_summary()

    print(f"\n✓ Full experiment data saved to: {output_file}")
    print("  Use this JSON file to analyze and defend the experiment.")
    print(f"\n✓ Execution time: {elapsed_time:.2f} seconds\n")


if __name__ == "__main__":
    main()
