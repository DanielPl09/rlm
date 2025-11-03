"""
Example prompt templates for the RLM REPL Client.
"""

from typing import Dict

DEFAULT_QUERY = "Please read through the context and answer any queries or respond to any instructions contained within it."

# System prompt for the REPL environment with explicit final answer checking
REPL_SYSTEM_PROMPT = """You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as possible. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `context` variable that contains extremely important information about your query. You should check the content of the `context` variable to understand what you are working with. Make sure you look through it sufficiently as you answer your query.
2. A `llm_query(prompt, slice_id=None)` function that allows you to query an LLM (that can handle around 500K chars) inside your REPL environment. You can optionally pass a `slice_id` to query with only that specific context slice.
3. Context slice helper functions for iterative refinement:
   - `list_slices()`: Returns list of available context slice IDs
   - `get_slice_info()`: Returns detailed info about all slices (metadata, size, type)
4. Hypothesis tracking functions for iterative refinement:
   - `update_hypothesis(new_hypothesis)`: Update the shared hypothesis based on new findings
   - `get_hypothesis()`: Get the current hypothesis
   - `get_hypothesis_history()`: Get all previous hypothesis versions
5. The ability to use `print()` statements to view the output of your REPL code and continue your reasoning.

## Query-Driven Iterative Refinement Strategy

For complex queries, the context has been PRE-SEGMENTED into chunks. You should use this ITERATIVE REFINEMENT workflow:

1. **Discover slices**: Call `list_slices()` or `get_slice_info()` to see available context chunks
2. **Initialize hypothesis**: Set an initial hypothesis with `update_hypothesis("initial answer or understanding")`
3. **Query per slice**: For each relevant slice, call `llm_query(your_question, slice_id=slice_id)` to get findings from that chunk
4. **Refine hypothesis**: After each sub_RLM response, call `update_hypothesis(refined_answer)` to incorporate new information
5. **Aggregate results**: Once all relevant slices are queried, use the final hypothesis as your answer

Example workflow:
```repl
# Step 1: Check available slices
slices = list_slices()
print(f"Available slices: {slices}")

# Step 2: Initialize hypothesis
update_hypothesis("Initial understanding: investigating the question")

# Step 3: Query each slice and refine
results = []
for slice_id in slices:
    result = llm_query(f"Based on this context, what information relates to [your question]?", slice_id=slice_id)
    results.append(result)

    # Refine hypothesis after each finding
    current = get_hypothesis()
    updated = llm_query(f"Current hypothesis: {current}\\n\\nNew finding: {result}\\n\\nProvide refined hypothesis:")
    update_hypothesis(updated)
    print(f"Updated hypothesis after {slice_id}")

# Step 4: Final answer is the refined hypothesis
final_answer = get_hypothesis()
```

You will only be able to see truncated outputs from the REPL environment, so you should use the query LLM function on variables you want to analyze. You will find this function especially useful when you have to analyze the semantics of the context. Use these variables as buffers to build up your final answer.

You can use the REPL environment to help you understand your context, especially if it is huge. Remember that your sub LLMs are powerful -- they can fit around 500K characters in their context window, so don't be afraid to put a lot of context into them. For example, a viable strategy is to feed 10 documents per sub-LLM query. Analyze your input data and see if it is sufficient to just fit it in a few sub-LLM calls!

When you want to execute Python code in the REPL environment, wrap it in triple backticks with 'repl' language identifier. For example, say we want our recursive model to search for the magic number in the context (assuming the context is a string), and the context is very long, so we want to chunk it:
```repl
chunk = context[:10000]
answer = llm_query(f"What is the magic number in the context? Here is the chunk: {{chunk}}")
print(answer)
```

As an example, after analyzing the context and realizing its separated by Markdown headers, we can maintain state through buffers by chunking the context by headers, and iteratively querying an LLM over it:
```repl
# After finding out the context is separated by Markdown headers, we can chunk, summarize, and answer
import re
sections = re.split(r'### (.+)', context["content"])
buffers = []
for i in range(1, len(sections), 2):
    header = sections[i]
    info = sections[i+1]
    summary = llm_query(f"Summarize this {{header}} section: {{info}}")
    buffers.append(f"{{header}}: {{summary}}")
final_answer = llm_query(f"Based on these summaries, answer the original query: {{query}}\\n\\nSummaries:\\n" + "\\n".join(buffers))
```
In the next step, we can return FINAL_VAR(final_answer).

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer inside a FINAL function when you have completed your task, NOT in code. Do not use these tags unless you have completed your task. You have two options:
1. Use FINAL(your final answer here) to provide the answer directly
2. Use FINAL_VAR(variable_name) to return a variable you have created in the REPL environment as your final output

Think step by step carefully, plan, and execute this plan immediately in your response -- do not just say "I will do this" or "I will do that". Output to the REPL environment and recursive LLMs as much as possible. Remember to explicitly answer the original query in your final answer.
"""

def build_system_prompt() -> list[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": REPL_SYSTEM_PROMPT
        },
    ]


# Prompt at every step to query root LM to make a decision
USER_PROMPT = """Think step-by-step on what to do using the REPL environment (which contains the context) to answer the original query: \"{query}\".\n\nContinue using the REPL environment, which has the `context` variable, and querying sub-LLMs by writing to ```repl``` tags, and determine your answer. Your next action:""" 
def next_action_prompt(query: str, iteration: int = 0, final_answer: bool = False) -> Dict[str, str]:
    if final_answer:
        return {"role": "user", "content": "Based on all the information you have, provide a final answer to the user's query."}
    if iteration == 0:
        safeguard = "You have not interacted with the REPL environment or seen your context yet. Your next action should be to look through, don't just provide a final answer yet.\n\n"
        return {"role": "user", "content": safeguard + USER_PROMPT.format(query=query)}
    else:
        return {"role": "user", "content": "The history before is your previous interactions with the REPL environment. " + USER_PROMPT.format(query=query)}
