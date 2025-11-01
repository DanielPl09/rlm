# 3 CRITICAL PROBLEMS WITH CURRENT EXPERIMENT

## ❌ CRITICISM 1: All Refinement in ONE Iteration (Not Iterative!)

### The Problem:
Looking at the actual logs:
- **Iteration 1:** Just explored context
- **Iteration 2:** Made ALL 4 sub-LLM calls in sequence
- **Iteration 3:** Tried to synthesize

This is **batched refinement**, not **iterative refinement**.

### Why This is Bad:
The model made all decisions at once in Iteration 2:
```python
# All in one iteration block:
promotion_results = llm_query(...)      # Sub-call 1
employee_info = llm_query(...)           # Sub-call 2
most_promoted_dept = llm_query(...)      # Sub-call 3
total_salary = llm_query(...)            # Sub-call 4
```

There's no **feedback loop** between iterations. The model doesn't:
- Observe results from Sub-call 1
- **Then decide** what to do in next iteration
- Observe those results
- **Then decide** what to do next

It just executes a pre-planned sequence.

### What We Should See:
```
Iteration 1: Explore context
Iteration 2: Query for promotion candidates → Get 3 names
             [Model observes results, decides next step]
Iteration 3: Query for Alice's details → Get salary, project
             [Model observes, decides next step]
Iteration 4: Query for Carol's details → Get salary, project
             [Model observes, decides next step]
Iteration 5: Calculate total → Get $307K
             [Model observes, provides answer]
```

---

## ❌ CRITICISM 2: Query is Prescriptive (Forces the Solution)

### The Problem:
The query says:
```
IMPORTANT: Use llm_query() to extract this information - the context is small enough
to send directly to the sub-LLM. Build up your answer step by step.
```

We're **telling the model HOW to solve it**!

### Why This is Bad:
- Not demonstrating that RLM **discovers** the need for sub-queries
- We're forcing the approach instead of letting it emerge naturally
- In real usage, users won't know to say "use llm_query()"
- This is a demo artifact, not genuine problem-solving

### What We Should Do:
Give a query that:
1. **Requires** cross-document synthesis
2. **Doesn't mention** llm_query() or sub-LLMs
3. Is naturally **impossible to answer** from one document alone
4. **Forces** the model to break it down iteratively

Example bad query (current):
```
Find employees for promotion. Use llm_query() to extract info.
```

Example good query:
```
For each employee recommended for promotion, I need their performance review
score, their current salary, their project's budget, and whether their project
is on track. Then rank them by promotion urgency considering all factors.
```

This FORCES synthesis without telling the model how to do it.

---

## ❌ CRITICISM 3: Context is Too Small & Simple

### The Problem:
Context: 2,994 characters (3 documents)

This fits comfortably in Claude Haiku's 200K token window.

### Why This is Bad:
Claude could theoretically answer this in **ONE SHOT**:
```python
# This would work fine:
answer = single_llm_call(query + context)
```

There's no **forcing function** that makes RLM necessary.

### The Numbers:
- Current context: ~3K chars = ~750 tokens
- Claude Haiku window: 200K tokens
- Usage: 0.375% of available context

We're not demonstrating RLM's value for **long contexts**.

### What We Should Do:
Either:

**Option A: Larger Context**
- 10-20 documents instead of 3
- 50K-100K characters
- Forces chunking strategy

**Option B: Complex Synthesis**
- Keep small context
- But make query require **temporal reasoning** or **multi-hop inference**
- Example: "Find employees whose current salary is below market rate for their
  performance level, cross-reference with their project's profitability, and
  recommend which ones to promote first considering budget constraints"

This can't be answered by sending full context to one sub-LLM - requires
**building up understanding** through multiple queries.

---

## SUMMARY: What's Wrong

| Aspect | Current Setup | What It Should Be |
|--------|---------------|-------------------|
| **Iteration spread** | All in Iteration 2 | Spread across 4-5 iterations |
| **Feedback loops** | None (pre-planned) | Each iteration observes previous results |
| **Query design** | Prescriptive | Natural problem that requires decomposition |
| **Context size** | Too small (3K chars) | Large enough to need chunking OR complex enough to need multi-step |
| **RLM necessity** | Optional (could solve in 1 shot) | Required (impossible in 1 shot) |

---

## HOW TO FIX

### Fix 1: Design Query That Forces Multi-Step
Make query impossible to answer with one sub-LLM call:
```
"Identify promotion candidates who:
1. Have 'Excellent' or 'Outstanding' reviews
2. Work on projects >50% complete
3. Are in departments with budget remaining
4. Would create no single point of failure on their project

Then rank them by promotion priority."
```

This requires:
- Iteration 1: Explore context
- Iteration 2: Find excellent performers → 4 candidates
- Iteration 3: Check project completion for those 4 → 3 remain
- Iteration 4: Check department budgets → 2 remain
- Iteration 5: Check team composition → 1 best candidate
- Iteration 6: Provide final ranked answer

### Fix 2: Remove Prescriptive Instructions
Don't say "use llm_query()". Just give the task.

### Fix 3: Either Make Context Bigger OR Query More Complex
- If keeping small context: Make query require complex reasoning
- If keeping simple query: Make context 10x larger

---

## THE REAL ISSUE

We're not showing **iterative decision-making**.

We're showing **batched sub-queries in one iteration**.

For TRUE iterative refinement, each iteration should:
1. **Observe** what was learned so far
2. **Decide** what to ask next based on that
3. **Query** for new information
4. **Accumulate** and repeat

Currently we're doing:
1. **Plan** all queries upfront
2. **Execute** them all at once
3. **Done**

This is more like "recursive decomposition" than "iterative refinement".
