# Using Public Datasets with RLM

Guide for testing query-driven iterative refinement with real-world public datasets.

---

## 🎯 **MANDATORY CHANGES TO RLM: NONE!**

**The good news:** The implementation is already compatible with public datasets!

✅ **RLM_REPL** already has context slicing integrated
✅ **Accepts dict/list/string** context formats
✅ **Auto-slicing** enabled by default
✅ **Works with OpenAI API** (just set OPENAI_API_KEY)

**You just need to:**
1. Download a dataset
2. Format it as a dict/list
3. Call `RLM_REPL.completion(context, query)`

---

## 📊 **Recommended Dataset: HotpotQA**

**Why HotpotQA is perfect:**
- ✅ Multi-document questions (2-10 paragraphs each)
- ✅ Requires synthesis across documents
- ✅ Reasonable size (can test on subsets)
- ✅ Well-established benchmark
- ✅ Free and public
- ✅ JSON format (easy to load)

**Characteristics:**
```
Questions: 113K total (use dev set: ~7.4K)
Structure: Question + multiple Wikipedia paragraphs
Each question needs 2+ paragraphs to answer
Perfect for testing iterative refinement!
```

---

## 🚀 **Quick Start: HotpotQA Example**

### Step 1: Install Dependencies

```bash
pip install datasets  # HuggingFace datasets library
```

### Step 2: Download HotpotQA

```python
from datasets import load_dataset

# Load dev set (smaller, good for testing)
dataset = load_dataset("hotpot_qa", "distractor", split="validation")

# Pick one example
example = dataset[0]
print(example["question"])
print(f"Context has {len(example['context']['sentences'])} sentences")
```

### Step 3: Format for RLM

```python
def format_hotpotqa_for_rlm(example):
    """
    Convert HotpotQA example to RLM context format.

    HotpotQA structure:
      - question: str
      - context: {
          'title': [list of document titles],
          'sentences': [list of lists of sentences]
        }

    RLM needs:
      - context: dict with multiple sections
      - query: str
    """
    context = {}

    titles = example['context']['title']
    sentences = example['context']['sentences']

    # Group sentences by document
    for i, (title, sents) in enumerate(zip(titles, sentences)):
        # Each document becomes a slice
        doc_text = ' '.join(sents)
        context[f"doc_{i}_{title.replace(' ', '_')}"] = doc_text

    query = example['question']

    return context, query
```

### Step 4: Run RLM

```python
from rlm.rlm_repl import RLM_REPL
import os

# Format example
context, query = format_hotpotqa_for_rlm(dataset[0])

# Create RLM client
client = RLM_REPL(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",  # or gpt-4o
    recursive_model="gpt-4o-mini",
    max_iterations=15,
    enable_logging=True
)

# Run!
answer = client.completion(context, query)
print(f"\nQuestion: {query}")
print(f"RLM Answer: {answer}")
print(f"Gold Answer: {dataset[0]['answer']}")
```

---

## 📝 **Complete Example Script**

See `examples/test_hotpotqa.py` (I'll create this next)

---

## ⚙️ **Optional: Use Anthropic Instead of OpenAI**

If you want to use Anthropic API instead:

```python
# Replace OpenAIClient with AnthropicClient in rlm_repl.py
from rlm.utils.anthropic_client import AnthropicClient

# In RLM_REPL.__init__:
self.llm = AnthropicClient(api_key, model)
```

Or use the standalone test scripts in `examples/` which already support Anthropic.

---

## 🔍 **What Gets Sliced**

With HotpotQA, each Wikipedia paragraph becomes a slice:

```python
Example question: "Which magazine was started first, Arthur's or First for Women?"

Context after formatting:
{
  'doc_0_Arthurs_Magazine': 'Arthur's Magazine (1844-1846) was an American...',
  'doc_1_First_for_Women': 'First for Women is a magazine published by...'
}

Slices created:
  - dict_doc_0_Arthurs_Magazine
  - dict_doc_1_First_for_Women

RLM will:
  1. Query doc_0 → find "started 1844"
  2. Refine hypothesis
  3. Query doc_1 → find "started 1989"
  4. Refine hypothesis → "Arthur's Magazine (1844) was first"
```

---

## 📈 **Scaling Considerations**

### Current Implementation Status:

**✅ What scales:**
- Auto-slicing works on any size dict
- Each slice queried independently
- Hypothesis tracking lightweight

**⚠️ Potential bottlenecks:**
- **Sequential processing**: Slices processed one-by-one (not parallel)
- **API call cost**: 2 calls per slice (query + refine)
- **REPL iterations**: Root LM still has max_iterations limit

### For Large Datasets:

**Small datasets (10-100 examples):**
```python
# Just run normally
for i in range(100):
    context, query = format_hotpotqa_for_rlm(dataset[i])
    answer = client.completion(context, query)
```

**Medium datasets (100-1000 examples):**
```python
# Process subset, save results
import json

results = []
for i in range(100, 200):  # Process 100 at a time
    try:
        context, query = format_hotpotqa_for_rlm(dataset[i])
        answer = client.completion(context, query)
        results.append({
            'id': i,
            'question': query,
            'answer': answer,
            'gold': dataset[i]['answer']
        })
    except Exception as e:
        print(f"Error on {i}: {e}")
        continue

# Save results
with open('rlm_results_100-200.json', 'w') as f:
    json.dump(results, f, indent=2)
```

**Large datasets (1000+ examples):**
```python
# Use batching + parallel processing
from concurrent.futures import ThreadPoolExecutor
import time

def process_one(idx):
    context, query = format_hotpotqa_for_rlm(dataset[idx])
    client = RLM_REPL(...)  # Create per-thread
    answer = client.completion(context, query)
    return {'id': idx, 'answer': answer}

# Process in parallel (be mindful of rate limits!)
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_one, range(1000, 1100)))
```

---

## 💰 **Cost Estimation**

**Per question with 3 context slices:**
- 1 root LM call (setup)
- 3 slice queries (sub_RLM)
- 3 refinement calls (sub_RLM)
- ~5-10 root LM calls (REPL iteration)
- **Total: ~12-16 API calls per question**

**Cost for 100 questions (gpt-4o-mini):**
- ~1,200-1,600 API calls
- At $0.15/1M input tokens, $0.60/1M output tokens
- Roughly $5-10 for 100 questions

**Tip:** Start with 10-20 examples to validate, then scale up.

---

## 🎯 **Success Metrics**

Compare RLM answers with gold answers using:

1. **Exact Match (EM)**: Answer exactly matches gold
2. **F1 Score**: Token overlap between answer and gold
3. **Contains Answer**: Gold answer substring in RLM answer

```python
def evaluate_answer(rlm_answer, gold_answer):
    # Exact match
    em = rlm_answer.strip().lower() == gold_answer.strip().lower()

    # Contains
    contains = gold_answer.lower() in rlm_answer.lower()

    # F1 (simple token overlap)
    rlm_tokens = set(rlm_answer.lower().split())
    gold_tokens = set(gold_answer.lower().split())

    if len(rlm_tokens) == 0 or len(gold_tokens) == 0:
        f1 = 0.0
    else:
        precision = len(rlm_tokens & gold_tokens) / len(rlm_tokens)
        recall = len(rlm_tokens & gold_tokens) / len(gold_tokens)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'exact_match': em,
        'contains_answer': contains,
        'f1_score': f1
    }
```

---

## 🔧 **Troubleshooting**

### Issue: "Too many slices created"

If auto-slicing creates 50+ slices from a document:

```python
# Option 1: Manually group paragraphs
context = {
    'first_half': '\n'.join(paragraphs[:5]),
    'second_half': '\n'.join(paragraphs[5:])
}

# Option 2: Disable slicing, let REPL handle it
answer = client.completion(context, query, enable_slicing=False)
```

### Issue: "Queries taking too long"

HotpotQA questions typically take 30-60 seconds with slicing.

If slower:
- Use gpt-4o-mini instead of gpt-4o
- Reduce max_iterations (default 20 → try 10)
- Check network latency

### Issue: "Running out of API credits"

- Start with dev set (7.4K examples)
- Test on 10-20 examples first
- Use gpt-4o-mini ($0.15/1M tokens vs gpt-4o $2.50/1M)

---

## 📚 **Other Datasets**

Same approach works for:
- **MultiNews**: Load, group articles, run RLM
- **MS MARCO**: Load, format passages, run RLM
- **QASPER**: Load paper sections, run RLM

Just adjust the formatting function!

---

## ✅ **Summary**

**Mandatory changes to RLM:** NONE
**What you need:**
1. Install `datasets` library
2. Load HotpotQA
3. Format context as dict
4. Call `RLM_REPL.completion(context, query)`

**The feature is production-ready for public datasets!**
