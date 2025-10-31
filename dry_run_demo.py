"""
Informative Dry Run - Shows RLM execution flow without API calls.

This simulates what happens when RLM processes a multi-file context,
showing each iteration, REPL execution, and how refinement works.
"""

import json
from typing import List, Dict


class DryRunVisualizer:
    """Visualizes RLM execution flow without making real API calls"""

    def __init__(self):
        self.iteration = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.sub_llm_calls = 0

    def print_header(self, title: str):
        print("\n" + "╔" + "═" * 78 + "╗")
        print(f"║ {title:^76} ║")
        print("╚" + "═" * 78 + "╝")

    def print_box(self, title: str, content: str, color: str = "blue"):
        symbols = {
            "blue": "│",
            "green": "┃",
            "yellow": "┊",
            "red": "║"
        }
        symbol = symbols.get(color, "│")

        print(f"\n{symbol} {title}")
        print(f"{symbol} " + "─" * 76)
        for line in content.split("\n"):
            print(f"{symbol} {line}")

    def simulate_iteration(self, iteration: int, context_size: int, query: str):
        """Simulate one RLM iteration"""
        self.iteration = iteration

        print("\n" + "━" * 80)
        print(f"ITERATION {iteration + 1}")
        print("━" * 80)

        # Show what the root LM sees
        if iteration == 0:
            system_prompt_tokens = 450  # Approximate
            context_tokens = context_size // 4  # Rough estimate: 1 token ≈ 4 chars
            query_tokens = len(query.split()) * 1.3

            total_input = system_prompt_tokens + context_tokens + query_tokens
            self.total_input_tokens += total_input

            self.print_box(
                "ROOT LM INPUT (Iteration 1)",
                f"""System Prompt: ~{system_prompt_tokens} tokens
  - Explains REPL environment
  - Instructs on using llm_query() for sub-calls
  - Explains FINAL() and FINAL_VAR() for answering

Context: ~{context_tokens} tokens
  - 4 text files (employees, projects, reviews, budgets)
  - 1 JSON file (metadata)

User Query: ~{int(query_tokens)} tokens
  - "{query}"

TOTAL INPUT: ~{int(total_input)} tokens""",
                "blue"
            )
        else:
            # Subsequent iterations include conversation history
            history_tokens = iteration * 300  # Grows with each iteration
            prompt_tokens = 100

            total_input = history_tokens + prompt_tokens
            self.total_input_tokens += total_input

            self.print_box(
                f"ROOT LM INPUT (Iteration {iteration + 1})",
                f"""Conversation History: ~{history_tokens} tokens
  - Previous REPL executions and outputs
  - Prior sub-LLM query results

Next Action Prompt: ~{prompt_tokens} tokens
  - Asks model to continue exploring

TOTAL INPUT: ~{int(total_input)} tokens""",
                "blue"
            )

        # Show what the root LM decides to do
        self.simulate_root_lm_response(iteration, query)

    def simulate_root_lm_response(self, iteration: int, query: str):
        """Simulate what the root LM would output"""

        response_tokens = 200  # Typical response length
        self.total_output_tokens += response_tokens

        if iteration == 0:
            # First iteration: explore the context
            self.print_box(
                "ROOT LM RESPONSE",
                f"""OUTPUT (~{response_tokens} tokens):

"I need to explore the context to answer the query about the highest paid
employee and their project. Let me start by examining the structure of the
available data."

```repl
# First, check what type of data we have
print(type(context))
print(len(context))

# Look at the first 500 characters to understand structure
preview = context[:500]
print(preview)
```

The model writes REPL code to explore the context.""",
                "green"
            )

            # Execute REPL code
            self.simulate_repl_execution(
                code="""print(type(context))
print(len(context))
preview = context[:500]
print(preview)""",
                output="""<class 'str'>
2847
=== COMPANY DATA - MULTIPLE DOCUMENTS ===

--- FILE: employee_records.txt ---

Employee Database - Q4 2024

ID: 1001, Name: Alice Johnson, Department: Engineering, Salary: 95000, Start Date: 2020-03-15
ID: 1002, Name: Bob Smith, Department: Marketing, Salary: 78000, Start Date: 2019-07-22
ID: 1003, Name: Carol White, Department: Engineering, Salary: 102000, Start Date: 2018-11-03
ID: 1004, Name: David Lee, Department: Sales, Sal"""
            )

        elif iteration == 1:
            # Second iteration: chunk and query
            self.print_box(
                "ROOT LM RESPONSE",
                f"""OUTPUT (~{response_tokens} tokens):

"I can see the context contains multiple files separated by '--- FILE: ---'
markers. I'll split by these markers and use llm_query() to find the highest
paid employee in the employee records."

```repl
# Split context by file markers
import re
files = re.split(r'--- FILE: (.+?) ---', context)

# Find employee records
for i in range(1, len(files), 2):
    if 'employee_records' in files[i]:
        employee_data = files[i+1]
        break

# Query sub-LLM to find highest paid employee
highest_paid_query = f'''From this employee data, identify the highest paid
employee. Return just their ID and name.

Data:
{{employee_data}}'''

highest_paid = llm_query(highest_paid_query)
print(f"Highest paid employee: {{highest_paid}}")
```""",
                "green"
            )

            # Show sub-LLM call
            self.simulate_sub_llm_call(
                prompt="""From this employee data, identify the highest paid employee.
Return just their ID and name.

Data: [~800 characters of employee records]""",
                response="ID: 1006, Name: Frank Chen (Salary: $110,000)"
            )

            # Execute REPL
            self.simulate_repl_execution(
                code="""# [File splitting code executed]
highest_paid = llm_query(highest_paid_query)
print(f"Highest paid employee: {highest_paid}")""",
                output="Highest paid employee: ID: 1006, Name: Frank Chen (Salary: $110,000)"
            )

        elif iteration == 2:
            # Third iteration: find their project
            self.print_box(
                "ROOT LM RESPONSE",
                f"""OUTPUT (~{response_tokens} tokens):

"Now I know Frank Chen (ID: 1006) is the highest paid employee. Let me find
which project he's working on by querying the project assignments."

```repl
# Find project assignments file
for i in range(1, len(files), 2):
    if 'project_assignments' in files[i]:
        project_data = files[i+1]
        break

# Query sub-LLM to find Frank Chen's project
project_query = f'''Find which project employee ID 1006 (Frank Chen) is
assigned to. Return the project name and his role.

Project Data:
{{project_data}}'''

frank_project = llm_query(project_query)
print(f"Frank's project: {{frank_project}}")
```""",
                "green"
            )

            # Show sub-LLM call
            self.simulate_sub_llm_call(
                prompt="""Find which project employee ID 1006 (Frank Chen) is assigned to.
Return the project name and his role.

Project Data: [~600 characters of project assignments]""",
                response="Project: CloudSync v2.0, Role: Team Member (working under Alice Johnson)"
            )

            # Execute REPL
            self.simulate_repl_execution(
                code="""# [File splitting code executed]
frank_project = llm_query(project_query)
print(f"Frank's project: {frank_project}")""",
                output="Frank's project: Project: CloudSync v2.0, Role: Team Member"
            )

        elif iteration == 3:
            # Fourth iteration: provide final answer
            self.print_box(
                "ROOT LM RESPONSE",
                f"""OUTPUT (~{response_tokens} tokens):

"I now have all the information needed to answer the query. Let me provide
the final answer."

FINAL(Frank Chen (ID: 1006) is the highest paid employee with a salary of
$110,000. He is working on the CloudSync v2.0 project as a team member,
contributing to the engineering team under the leadership of Alice Johnson.)""",
                "green"
            )

            print("\n✓ FINAL() detected - RLM will return this answer and stop iterating")

    def simulate_repl_execution(self, code: str, output: str):
        """Simulate REPL code execution"""

        exec_time = 0.05  # Simulated execution time

        self.print_box(
            "REPL EXECUTION",
            f"""Executing Python code in isolated environment...

Code:
{code}

Output:
{output}

Execution time: {exec_time}s

✓ Results saved to REPL environment and added to conversation history""",
            "yellow"
        )

    def simulate_sub_llm_call(self, prompt: str, response: str):
        """Simulate a sub-LLM query"""

        self.sub_llm_calls += 1

        # Estimate tokens
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(response.split()) * 1.3

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        self.print_box(
            f"SUB-LLM CALL #{self.sub_llm_calls}",
            f"""llm_query() called - delegating to sub-model

INPUT (~{int(input_tokens)} tokens):
{prompt[:200]}{"..." if len(prompt) > 200 else ""}

OUTPUT (~{int(output_tokens)} tokens):
{response}

✓ Response returned to REPL environment""",
            "red"
        )

    def print_cost_summary(self, model: str = "gpt-4o-mini"):
        """Print estimated costs"""

        self.print_header("COST SUMMARY")

        # Pricing (per 1M tokens)
        pricing = {
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-5": {"input": 5.00, "output": 15.00}  # Hypothetical pricing
        }

        rates = pricing.get(model, pricing["gpt-4o-mini"])

        input_cost = (self.total_input_tokens / 1_000_000) * rates["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * rates["output"]
        total_cost = input_cost + output_cost

        print(f"""
Model: {model}
Pricing: ${rates['input']:.3f} / ${rates['output']:.3f} per 1M tokens (input/output)

Token Usage:
  Input Tokens:  {self.total_input_tokens:>8,} tokens  →  ${input_cost:.4f}
  Output Tokens: {self.total_output_tokens:>8,} tokens  →  ${output_cost:.4f}
  ─────────────────────────────────────────────────────
  Total Cost:                             ${total_cost:.4f}

Statistics:
  Total Iterations:     {self.iteration + 1}
  Sub-LLM Calls:        {self.sub_llm_calls}
  Avg Tokens/Iteration: {int((self.total_input_tokens + self.total_output_tokens) / (self.iteration + 1)):,}
""")

        # Compare with other models
        print("Cost Comparison (same usage):")
        for model_name, model_rates in pricing.items():
            if model_name != model:
                alt_input_cost = (self.total_input_tokens / 1_000_000) * model_rates["input"]
                alt_output_cost = (self.total_output_tokens / 1_000_000) * model_rates["output"]
                alt_total = alt_input_cost + alt_output_cost
                diff = ((alt_total - total_cost) / total_cost) * 100
                print(f"  {model_name:>12}: ${alt_total:.4f} ({diff:+.0f}%)")


def main():
    """Run the informative dry run"""

    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                         RLM DRY RUN DEMONSTRATION                          ║
║                                                                            ║
║  This simulates exactly what happens when you run test_multifile.py       ║
║  without making actual API calls. Watch how the model:                    ║
║                                                                            ║
║    1. Explores the context iteratively using REPL code                    ║
║    2. Makes recursive sub-LLM calls to analyze chunks                     ║
║    3. Builds understanding over multiple iterations                       ║
║    4. Provides a final answer based on accumulated knowledge              ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

    # Create visualizer
    viz = DryRunVisualizer()

    # Simulate the test scenario
    viz.print_header("TEST SCENARIO: Simple Information Retrieval")

    query = "Who is the highest paid employee and what project are they working on?"
    context_size = 2847  # Actual size from our test

    print(f"""
Query: {query}

Context: Multi-file company data (~{context_size} characters)
  - employee_records.txt (8 employees with salaries)
  - project_assignments.txt (4 active projects)
  - performance_reviews.txt (annual reviews)
  - budget_summary.txt (department budgets)
  - metadata.json (company info)

Model Configuration:
  - Root Model: gpt-4o-mini (cheap, fast)
  - Sub Model: gpt-4o-mini (same)
  - Max Iterations: 5
  - Logging: Enabled
""")

    input("\nPress Enter to start simulation...")

    # Simulate iterations
    for i in range(4):  # Will stop at iteration 3 when FINAL() is found
        viz.simulate_iteration(i, context_size, query)

        if i < 3:
            input(f"\nPress Enter for Iteration {i + 2}...")
        else:
            break

    # Show final result
    viz.print_header("FINAL RESULT")
    print("""
The RLM successfully answered the query in 4 iterations:

  ✓ Iteration 1: Explored context structure
  ✓ Iteration 2: Found highest paid employee (Frank Chen, $110K)
  ✓ Iteration 3: Found his project (CloudSync v2.0)
  ✓ Iteration 4: Provided complete final answer

Answer: "Frank Chen (ID: 1006) is the highest paid employee with a salary
of $110,000. He is working on the CloudSync v2.0 project as a team member,
contributing to the engineering team under the leadership of Alice Johnson."
""")

    # Show cost summary
    viz.print_cost_summary(model="gpt-4o-mini")

    # Show what happens with complex query
    viz.print_header("COMPLEX QUERY EXAMPLE")
    print("""
For a more complex query like:
"Identify all employees recommended for promotion and calculate their total
salary cost and project budgets"

Expected behavior:
  - More iterations (6-8 instead of 4)
  - More sub-LLM calls (8-12 instead of 2)
  - Needs to query multiple files:
    * performance_reviews.txt to find promotion candidates
    * employee_records.txt to get their salaries
    * project_assignments.txt to find their projects
    * budget_summary.txt to get project budgets
  - Must aggregate results across multiple sub-LLM responses

Estimated cost: $0.03-0.05 (still very cheap!)
""")

    viz.print_header("KEY INSIGHTS")
    print("""
1. ITERATIVE REFINEMENT
   - Each iteration builds on previous knowledge
   - REPL environment maintains state (variables persist)
   - Model can "plan" by examining data before querying

2. RECURSIVE SUB-CALLS
   - Sub-LLMs handle ~500K character chunks
   - Each sub-call is focused on a specific task
   - Results are accumulated in REPL variables

3. COST EFFICIENCY
   - Only sends relevant chunks to sub-LLMs (not entire context each time)
   - Reuses accumulated knowledge (stored in REPL variables)
   - Stops as soon as answer is found (no wasted iterations)

4. COMPARISON TO NAIVE APPROACH
   Naive: Send all 2847 chars × 8 iterations = ~22,776 chars repeatedly
   RLM:   Send only relevant chunks when needed = ~5,000 chars total

   For the original 1M line example:
   Naive: Would exceed context window entirely (impossible!)
   RLM:   Chunks into manageable pieces (totally feasible)
""")

    print("\n" + "═" * 80)
    print("Dry run complete! Ready to run with real API key when you provide it.")
    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
