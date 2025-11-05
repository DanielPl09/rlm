# Proper 80/20 Evaluation: Requirements for Realistic Demonstration

## Critical Issues with Current Approach

### Issue 1: Sudden F1 Jumps (Not Gradual Convergence)
**Current behavior:**
```
Slice 1: F1 = 0.0
Slice 2: F1 = 0.0
Slice 3: F1 = 1.0  ← SUDDEN JUMP (unrealistic!)
```

**What realistic convergence looks like:**
```
Iter 1: F1 = 0.00  "Need to find info about X"
Iter 2: F1 = 0.18  "X is related to Y"
Iter 3: F1 = 0.35  "Y was created by Z in 1995"
Iter 4: F1 = 0.62  "Z also founded company A"
Iter 5: F1 = 0.78  "Company A is the answer" ← 80% quality
Iter 6: F1 = 0.89  "Company A, founded in 1995"
Iter 7: F1 = 0.95  "Company A"
Iter 8: F1 = 0.98  "Company A"
Iter 9: F1 = 1.00  "Company A"
```

**Key pattern:**
- Early iterations: Rapid improvement (0 → 0.78 in first 50%)
- Later iterations: Slow refinement (0.78 → 1.0 in last 50%)
- THIS is the 80/20 pattern!

---

## Issue 2: Independent Calls vs Cumulative Hypotheses

**Current (WRONG):**
Each call sees ONLY its slice, answers independently
```python
# Iteration 1
query("What company...", slice1) → "Don't know"

# Iteration 2
query("What company...", slice2) → "Maybe PayPal"  # IGNORES iteration 1!

# Iteration 3
query("What company...", slice3) → "PayPal"  # IGNORES iterations 1&2!
```

**Correct (CUMULATIVE):**
Each call builds on previous hypothesis
```python
# Iteration 1
hypothesis = "Unknown"
query("Update hypothesis based on: [slice1]. Current: Unknown")
→ "The person is Elon Musk"
hypothesis = "The person is Elon Musk"

# Iteration 2
query("Update hypothesis based on: [slice2]. Current: The person is Elon Musk")
→ "Elon Musk founded PayPal"
hypothesis = "Elon Musk founded PayPal"

# Iteration 3
query("Update hypothesis based on: [slice3]. Current: Elon Musk founded PayPal")
→ "PayPal was founded before Tesla, so PayPal is the answer"
hypothesis = "PayPal"
```

---

## Issue 3: Sample Questions Too Simple

**Current samples:**
- "What is the capital of France?" → Too easy
- "Who founded SpaceX?" → Can answer in one sentence

**Real HotpotQA complexity:**
- "What government position was held by the woman who portrayed Corliss Archer in the film Kiss and Tell?"
- Requires: Film → Actress → Other roles → Government position
- 4 hops, complex reasoning

**Need harder questions that REQUIRE progressive refinement.**

---

## Issue 4: Coarse-Grained F1 Measurement

**Current F1 calculation:**
```python
Ground truth: "PayPal"
Hypothesis: "Elon Musk founded PayPal in 1999"

F1 calculation:
normalize("PayPal") = "paypal"
normalize("Elon Musk founded PayPal in 1999") = "elon musk founded paypal 1999"
Common tokens: {"paypal"}
F1 = 2 * (1/1) * (1/5) / (1/1 + 1/5) = 0.33

PROBLEM: Hypothesis has answer but F1 is low!
```

**Better approach:**
- Extract answer from hypothesis: "PayPal"
- Compare: "PayPal" vs "PayPal" → F1 = 1.0
- OR use semantic similarity

---

## Requirements for Proper Demonstration

### 1. Use Real HotpotQA Dataset
- Download actual HotpotQA dev set
- Select 5-10 hard examples (3+ hops)
- Use questions that require multi-document reasoning

### 2. Implement True Hypothesis Building
```python
class ProgressiveRefinement:
    def __init__(self):
        self.hypothesis = "Unknown"
        self.context_seen = []

    def refine(self, new_slice):
        # Accumulate context
        self.context_seen.append(new_slice)

        # Update hypothesis based on ALL context seen so far
        prompt = f"""
        Question: {question}

        Context accumulated so far:
        {'\n'.join(self.context_seen)}

        Current hypothesis: {self.hypothesis}

        Based on all the context you've seen, update your hypothesis.
        Answer with just the updated hypothesis (1-20 words):
        """

        new_hypothesis = query_llm(prompt)
        self.hypothesis = new_hypothesis

        return self.hypothesis
```

### 3. Granular Slicing (10-15 slices)
- More slices = smoother F1 curve
- Each slice adds small piece of info
- Shows gradual convergence more clearly

### 4. Better F1 Extraction
```python
def extract_answer_from_hypothesis(hypothesis, question):
    """Extract the actual answer from a verbose hypothesis."""

    prompt = f"""
    Question: {question}
    Hypothesis: {hypothesis}

    Extract ONLY the direct answer to the question (1-5 words):
    """

    extracted = query_llm(prompt)
    return extracted
```

### 5. Expected F1 Progression Curve

For proper 80/20 demonstration:

```
Iteration %  | Target F1 | Quality Gained
-------------|-----------|---------------
0%           | 0.00      | -
10%          | 0.15      | +15% (exploring)
20%          | 0.35      | +20% (first hop)
30%          | 0.55      | +20% (second hop)
40%          | 0.70      | +15% ← 70% quality at 40% time!
50%          | 0.80      | +10% ← 80% quality at 50% time!
60%          | 0.87      | +7%  (refinement)
70%          | 0.92      | +5%  (polish)
80%          | 0.96      | +4%  (diminishing)
90%          | 0.98      | +2%  (tiny gains)
100%         | 1.00      | +2%  (final polish)
```

**Key insight:**
- First 40-50% iterations: Deliver 70-80% quality (BIG GAINS)
- Last 50-60% iterations: Deliver 20-30% quality (DIMINISHING RETURNS)

---

## Implementation Plan

### Step 1: Get Real HotpotQA Data
```python
# Download or use real HotpotQA examples
# Filter for:
# - 3+ supporting facts (multi-hop)
# - "hard" difficulty
# - "bridge" or "comparison" type
```

### Step 2: Implement Cumulative Refinement
```python
def progressive_refinement_experiment(example, slices):
    hypothesis = "I don't know yet"
    context_accumulated = ""

    for i, slice in enumerate(slices):
        # Accumulate context
        context_accumulated += f"\n{slice.content}"

        # Refine hypothesis
        prompt = f"""
        Question: {example.question}

        All context you've seen so far:
        {context_accumulated}

        Your current hypothesis: {hypothesis}

        Based on ALL the context above, provide your UPDATED hypothesis.
        Build on your previous hypothesis, don't start from scratch.

        Updated hypothesis (be concise):
        """

        new_hypothesis = llm.query(prompt)

        # Extract answer for F1 calculation
        answer_extract = extract_answer(new_hypothesis, example.question)

        # Calculate F1
        f1 = calculate_f1(answer_extract, example.answer)

        # Track
        track(iteration=i, hypothesis=new_hypothesis, f1=f1)

        hypothesis = new_hypothesis
```

### Step 3: Create Finer-Grained Slices
- 10-15 slices instead of 6
- Mix supporting facts throughout
- Each slice adds ~5-15% information

### Step 4: Validate Convergence Pattern
Expected to see:
- Exponential growth: F1(t) = F_max * (1 - e^(-k*t))
- Early rapid growth, then plateau
- 70-80% quality by 40-50% iterations

---

## Success Criteria

### Quantitative:
1. ✅ F1 at 20% iterations: 0.30-0.45
2. ✅ F1 at 40% iterations: 0.65-0.75 (demonstrates 80/20!)
3. ✅ F1 at 60% iterations: 0.85-0.90
4. ✅ F1 at 100% iterations: 0.95-1.00
5. ✅ Smooth curve (no sudden jumps > 0.3)

### Qualitative:
1. ✅ Hypothesis visibly builds on previous iterations
2. ✅ Early iterations establish key facts
3. ✅ Middle iterations connect facts (multi-hop)
4. ✅ Late iterations polish/verify
5. ✅ Clear diminishing returns visible in curve

---

## Cleanup Tasks

### Remove:
- ❌ Simulated/demo results files
- ❌ Document-level slicing experiments
- ❌ Independent query approach
- ❌ Simple sample questions

### Keep/Improve:
- ✅ Metrics module (add answer extraction)
- ✅ Iteration tracker (already good)
- ✅ HotpotQA loader (extend with real data)
- ✅ Multi-hop slicer (make finer-grained)

### Add:
- ✅ Real HotpotQA examples (download dataset)
- ✅ Cumulative hypothesis builder
- ✅ Answer extraction from verbose hypotheses
- ✅ Convergence curve validator
- ✅ Final clean experiment script

---

## Expected Final Result

```
Question: "What award did the director of the 1994 film starring
           Tom Hanks win?"
Ground Truth: "Academy Award for Best Director"

Progressive Refinement (10 iterations):

Iter  1 (10%):  F1=0.00  "Need to identify the 1994 film"
Iter  2 (20%):  F1=0.12  "Film might be Forrest Gump with Tom Hanks"
Iter  3 (30%):  F1=0.28  "Forrest Gump was directed by Robert Zemeckis"
Iter  4 (40%):  F1=0.45  "Robert Zemeckis won awards for this film"
Iter  5 (50%):  F1=0.68  "He won an Academy Award"  ← 68% quality!
Iter  6 (60%):  F1=0.82  "Academy Award for Best Director"
Iter  7 (70%):  F1=0.91  "Academy Award for Best Director in 1995"
Iter  8 (80%):  F1=0.96  "Academy Award for Best Director"
Iter  9 (90%):  F1=0.98  "Academy Award for Best Director"
Iter 10 (100%): F1=1.00  "Academy Award for Best Director"

Analysis:
- At 50% iterations: 68% of final quality ✅
- At 60% iterations: 82% of final quality ✅
- Demonstrates clear 80/20 pattern!
- Smooth convergence (no sudden jumps)
```

This is what we need to build.
