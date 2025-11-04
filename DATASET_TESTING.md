# Dataset Testing Branch

This branch is for testing the query-driven iterative refinement feature with custom datasets.

## Purpose

Test the refinement implementation with datasets that have similar characteristics to ensure the feature generalizes well across different domains:

- **Multi-source data**: Context split across multiple documents/sections
- **Related information**: Each slice contains complementary information
- **Aggregation required**: Final answer needs synthesis from all slices

## Branch Structure

```
Parent: claude/rlm-query-iterative-refinement-011CUmpy3fterRMaeFZnjwB7
This:   claude/rlm-dataset-testing-011CUmpy3fterRMaeFZnjwB7
```

## Test Files

### `examples/test_custom_datasets.py`

Contains template and examples for testing custom datasets:

**Included Examples:**
1. **Medical Case Analysis** - Patient history + lab results + physical exam
2. **System Performance Analysis** - API logs + DB metrics + infrastructure status
3. **Financial Health Analysis** - Income statement + balance sheet + operational metrics

**How to Add Your Dataset:**

```python
# 1. Add your dataset (follow the template)
my_dataset = {
    'section1': 'Content describing aspect 1...',
    'section2': 'Content describing aspect 2...',
    'section3': 'Content describing aspect 3...',
}

# 2. Add test call in main()
run_test(
    my_dataset,
    "Your question here?",
    api_key,
    "Your Test Name"
)
```

## Running Tests

```bash
# Set API key
export ANTHROPIC_API_KEY=your_key

# Run all custom dataset tests
python examples/test_custom_datasets.py
```

## What to Test

### Good Dataset Characteristics:

✅ **Multi-part context** - 3+ distinct sections/documents
✅ **Complementary info** - Each section adds unique information
✅ **Related domain** - All sections about the same topic
✅ **Synthesis needed** - Answer requires combining all slices

### Examples of Good Datasets:

- **Medical**: Symptoms + Lab tests + Medical history
- **Legal**: Case facts + Precedents + Expert opinions
- **Technical**: Error logs + System metrics + Configuration
- **Research**: Abstract + Methodology + Results
- **Business**: Sales data + Market analysis + Customer feedback

### What to Verify:

1. ✅ Each slice is queried independently (no cross-contamination)
2. ✅ Hypothesis evolves after each slice
3. ✅ Final answer includes information from ALL slices
4. ✅ Answer quality is better than querying any single slice

## Merging Back

When testing is complete and you've verified the feature works with your datasets:

```bash
# Commit your test results
git add examples/test_custom_datasets.py
git commit -m "Add custom dataset tests: [describe your datasets]"

# Push to this sub-branch
git push -u origin claude/rlm-dataset-testing-011CUmpy3fterRMaeFZnjwB7

# Optional: Merge back to parent branch if you want to keep the tests
git checkout claude/rlm-query-iterative-refinement-011CUmpy3fterRMaeFZnjwB7
git merge claude/rlm-dataset-testing-011CUmpy3fterRMaeFZnjwB7
```

## Results Format

Each test will show:

```
TEST: Your Test Name
================================================================================
Query: Your question
Context has 3 sections: ['section1', 'section2', 'section3']
Created 3 slices

[1/3] Processing dict_section1...
  ✅ Result: Finding from section 1...
  ✅ Hypothesis refined

[2/3] Processing dict_section2...
  ✅ Result: Finding from section 2...
  ✅ Hypothesis refined

[3/3] Processing dict_section3...
  ✅ Result: Finding from section 3...
  ✅ Hypothesis refined

================================================================================
RESULTS: Your Test Name
================================================================================
Slices processed: 3
Hypothesis versions: 4

Final Answer:
[Comprehensive answer synthesizing all 3 slices]
================================================================================
```

## Notes

- This branch is for testing only - main implementation is in parent branch
- Add as many custom datasets as you want
- Tests are independent - failures don't affect other tests
- Results help validate the feature generalizes across domains
