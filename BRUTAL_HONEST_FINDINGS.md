# Brutal Honest Findings: RLM Verification

## Question: "Did the RLM itself work as expected?"

**Answer: Yes and No.**

---

## ✅ What Works

### 1. RLM Core Mechanism Works
- ✓ REPL environment executes Python code
- ✓ `context` variable is available
- ✓ Model can iterate multiple times
- ✓ Error recovery works (tries different approaches)
- ✓ Can provide final answers
- ✓ Basic test PASSED: Found "Carol, $102,000" correctly

### 2. The Implementation is Correct (for what it does)

**llm_query() implementation (rlm/repl.py:183-185):**
```python
def llm_query(prompt: str) -> str:
    """Query the LLM with the given prompt."""
    return self.sub_rlm.completion(prompt)
```

This is working **as designed**. The design is:
- User must manually include context in queries
- `llm_query()` is just a passthrough to sub-LLM
- No automatic context injection

---

## ❌ What Doesn't Work (For Our Goals)

### 1. llm_query() Doesn't Auto-Include Context

**The Problem:**
```python
# This doesn't work:
llm_query("Find employees with X criteria")

# Sub-LLM receives: "Find employees with X criteria"
# Sub-LLM has NO data to analyze
```

**What you must do:**
```python
# This works:
llm_query(f"Find employees with X criteria\n\nData:\n{context}")

# Sub-LLM receives: "Find employees... Data: [actual data]"
# Sub-LLM can now analyze
```

**Why This is a Problem:**
- Not obvious to users
- Easy to forget
- Our experiments all failed because of this
- Model must remember to include context EVERY time

### 2. Model Prefers Local Parsing Over Sub-LLM Queries

**Critical Finding from Basic Test:**

Even when we explicitly told the model:
```
IMPORTANT: When you use llm_query(), you MUST include the context data like this:
    llm_query(f"Your question here\n\nData:\n{context}")
```

The model IGNORED this instruction and parsed locally instead!

**What happened:**
- Iteration 1: Printed context
- Iteration 2-3: Tried to parse with Python (got errors)
- Final answer: "Carol at $102,000" (correct!)

**Sub-LLM calls made: 0**

The model found the answer without using llm_query() at all.

**Why:**
- Context was small (3 lines)
- Parsing seemed straightforward
- Model preferred direct computation over delegation

### 3. Can't Force Iterative Refinement via Sub-LLM Queries

**The Core Issue:**

We want to demonstrate:
```
Iteration 1: Explore
Iteration 2: Query sub-LLM for criterion 1 → 3 candidates
Iteration 3: Query sub-LLM for criterion 2 → 2 candidates
Iteration 4: Query sub-LLM for criterion 3 → 1 candidate
```

But the model does:
```
Iteration 1: Explore
Iteration 2: Parse everything locally → Final answer
```

OR (if we make it too hard to parse):
```
Iteration 1: Explore
Iteration 2: Query 1, Query 2, Query 3, Query 4 all in sequence
Iteration 3: Synthesize
```

**We can't get** progressive sub-LLM queries spread across iterations naturally.

---

## 🔍 Root Cause Analysis

### Why Model Avoids Sub-LLM Queries

**Occam's Razor:** Model chooses simplest approach.

When context is small:
- Direct parsing is simpler than llm_query()
- Less overhead
- Faster
- Fewer dependencies

**The model is being smart**, not broken.

### Why Model Batches Queries

When context is large and requires sub-queries:
- Model plans ahead (smart!)
- Sees it needs 4 pieces of information
- Executes all 4 queries in one iteration
- Efficient, but not "iterative"

**The model is being efficient**, not broken.

### The Fundamental Problem

**We're fighting against the model's natural behavior.**

Claude Opus is:
- Planning ahead (good!)
- Being efficient (good!)
- Minimizing sub-calls (good!)

But we want to demonstrate:
- Step-by-step refinement (different goal)
- Progressive querying (different pattern)
- Spread across iterations (artificial constraint)

**This is like asking a human to work inefficiently to demonstrate a process.**

---

## 💡 What This Means

### 1. RLM Works, But Not How We Hoped

**Expected behavior:**
- Model naturally discovers need for iterative refinement
- Sub-queries spread across iterations
- Progressive knowledge building

**Actual behavior:**
- Model prefers local parsing when possible
- Batches sub-queries when necessary
- Solves problem efficiently, not demonstratively

### 2. Our Previous Experiments Failed for Valid Reasons

**Failure 1:** Sub-LLM queries had no context
- **Our fault:** Didn't know llm_query() design
- **RLM fault:** None (working as designed)

**Failure 2:** Queries batched in one iteration
- **Our fault:** Fighting natural model behavior
- **RLM fault:** None (model being efficient)

**Failure 3:** Model tried parsing instead of querying
- **Our fault:** Context too small/simple
- **RLM fault:** None (model being smart)

### 3. To Demonstrate Iterative Refinement...

We need to either:

**Option A: Make it impossible to parse locally**
- Context so large parsing is impractical
- Or: Context so complex parsing would fail
- Forces sub-LLM queries

**Option B: Explicitly constrain the approach**
```
RULES:
1. You MUST make exactly ONE llm_query() per iteration
2. You CANNOT parse locally
3. You MUST wait for results before deciding next query
```

This feels artificial, but might be only way.

**Option C: Accept that RLM isn't naturally iterative**
- Model solves problems efficiently
- Batching is smart, not wrong
- Iterative refinement is forced, not natural

---

## 📊 Test Results Summary

| Test | Context Size | Sub-LLM Calls | Spread Across Iters? | Result |
|------|--------------|---------------|----------------------|--------|
| experiment_rlm_refinement.py | 2,690 chars | 4+ | No (all Iter 4) | FAILED* |
| test_rlm_basic.py | 3 lines | 0 | N/A | PASSED** |

\* Failed to demonstrate iterative refinement (sub-queries failed + batched)
\** Passed at finding answer (but didn't use sub-queries at all)

---

## ✅ Honest Verdict

### Is RLM Broken?
**No.** RLM works as designed.

### Is RLM Suitable for Demonstrating Iterative Refinement?
**Not naturally.**

The model is too smart and efficient. It:
- Prefers local computation when possible
- Batches sub-queries when necessary
- Solves problems optimally, not demonstratively

### Can We Make It Work?
**Maybe**, with artificial constraints:
- Force one query per iteration
- Make parsing impossible
- Explicitly require sub-LLM usage

But this feels like forcing a demo rather than showing natural behavior.

---

## 🎯 Recommendations

### 1. For Honest Demo
Accept that:
- Model will batch queries (that's efficient)
- Model will parse when possible (that's smart)
- Iterative refinement is not natural behavior

Document: "RLM enables sub-LLM queries and REPL iteration. While the model typically solves problems efficiently (batching queries), we can observe the mechanism..."

### 2. For Forced Demo
Add explicit rules:
```
You MUST:
- Make ONE llm_query() per iteration
- Include context in every query
- Wait for results before next decision
- NOT parse locally
```

Document: "Under constrained conditions, RLM can demonstrate step-by-step refinement..."

### 3. For Real Use Case
RLM works fine! Use it naturally:
- Let model choose approach
- Trust batching decisions
- Accept efficient problem-solving

Don't force iterative refinement if batching is more efficient.

---

## 🔑 Key Insight

**The model is working correctly. Our expectations were wrong.**

We expected:
- Natural iterative refinement
- Progressive sub-querying
- Spread across iterations

Reality:
- Efficient problem-solving
- Batched sub-querying
- Concentrated in one iteration

**Both are valid. One is just more efficient.**

RLM enables the mechanism. The model chooses how to use it.

---

## Next Steps

1. **Accept reality:** Model won't naturally iterate the way we want
2. **Choose approach:** Forced demo vs honest documentation
3. **Plan accordingly:** Design experiment that works with model behavior, not against it

Your call on which path to take.
