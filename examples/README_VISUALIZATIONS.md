# Incremental Refinement Visualizations

Two tools to visualize how the hypothesis evolves through incremental refinement.

## 📊 Tools Available

### 1. ASCII Visualization (No Dependencies)

**File:** `visualize_refinement.py`

Creates a text-based flow diagram showing the complete refinement process.

```bash
export ANTHROPIC_API_KEY=your_key
python examples/visualize_refinement.py
```

**Output Example:**
```
================================================================================
INCREMENTAL REFINEMENT VISUALIZATION: Product Analysis
================================================================================

┌──────────────────────────────────────────────────────────────────────────────┐
│ QUERY: What are the product's main strengths and weaknesses?                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ HYPOTHESIS v0 (Initial)                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Initial: Need to answer 'What are the product's main strengths and           │
│ weaknesses?'                                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

                              ↓
                    ┌────────────────────────────────────────┐
                    │  PROCESS SLICE 1/3: dict_user_reviews             │
                    └────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ 🔵 sub_RLM Query Result from dict_user_reviews:                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ Strengths: - Intuitive interface - Fast response times                       │
│ Weaknesses: - Mobile crashes on iOS                                         │
└──────────────────────────────────────────────────────────────────────────────┘

                              ↓
                         🔄 REFINE
                              ↓

┌──────────────────────────────────────────────────────────────────────────────┐
│ HYPOTHESIS v1 (After dict_user_reviews)                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│ Updated: Product has intuitive interface and fast response times. Major      │
│ weakness is mobile app crashes on iOS.                                      │
└──────────────────────────────────────────────────────────────────────────────┘

[... continues for each slice ...]

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      ✅ FINAL ANSWER (Complete Synthesis)                     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ [Comprehensive answer aggregating all slices...]                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

================================================================================
REFINEMENT STATISTICS:
================================================================================
  Total slices processed:     3
  Total sub_RLM calls:        6 (query + refine per slice)
  Hypothesis versions:        4
  Information sources used:   dict_user_reviews, dict_technical_specs, ...
================================================================================
```

**Shows:**
- ✅ Complete query at the top
- ✅ Initial hypothesis (v0)
- ✅ Each slice being processed
- ✅ sub_RLM result from that slice
- ✅ Refinement step
- ✅ Updated hypothesis version
- ✅ Final synthesized answer
- ✅ Statistics summary

---

### 2. Graphical Visualization (Requires matplotlib)

**File:** `visualize_refinement_graph.py`

Creates a PNG flowchart with colored boxes and arrows.

```bash
# Install matplotlib if needed
pip install matplotlib

# Run visualization
export ANTHROPIC_API_KEY=your_key
python examples/visualize_refinement_graph.py
```

**Output:**
- PNG file: `product_analysis_refinement.png`
- Visual flowchart with:
  - 🔵 Red boxes: Context slices and their findings
  - 🟢 Green boxes: Refined hypotheses
  - 🟡 Gold box: Final answer
  - ➡️ Arrows showing flow
  - 📊 Statistics panel
  - 🎨 Legend

**Features:**
- Color-coded components
- Clear flow direction
- Professional appearance
- Suitable for presentations/reports

---

## 🎯 What These Visualizations Demonstrate

### Key Observations You'll See:

1. **Incremental Growth**
   - v0: Simple initial state
   - v1: Adds info from first slice
   - v2: Adds info from second slice
   - v3: Comprehensive synthesis

2. **Information Isolation**
   - Each sub_RLM only sees its specific slice
   - No cross-contamination between slices
   - Each finding is unique to its source

3. **Refinement Pattern**
   - Query slice → Get finding → Refine hypothesis
   - Repeat for each slice
   - Each iteration builds on previous version

4. **Final Aggregation**
   - Final answer includes information from ALL slices
   - No single slice alone provides complete picture
   - Synthesis creates coherent comprehensive answer

---

## 🔧 Customizing for Your Data

Both scripts can be easily modified to visualize your own refinement tests:

```python
# Your custom context
my_context = {
    'source1': 'Your data here...',
    'source2': 'More data here...',
    'source3': 'Additional data...',
}

# Your query
my_query = "Your question?"

# Run visualization
run_visualization_test(my_context, my_query, api_key, "My Test")
```

---

## 📈 Example Use Cases

### For Presentations
Use the **graphical version** to show:
- How the system processes multi-source data
- Evolution of understanding over iterations
- Final synthesis quality

### For Debugging
Use the **ASCII version** to:
- Quickly check refinement logic
- Verify each slice is processed correctly
- See full text of hypotheses at each step
- Check statistics (calls, versions, sources)

### For Documentation
Both versions help document:
- How the feature works
- What "iterative refinement" means concretely
- Why multiple sources improve answer quality
- The actual refinement pattern in action

---

## 💡 Tips

1. **ASCII version** is faster and requires no dependencies - great for quick checks
2. **Graphical version** looks better for sharing/presentations
3. Both use real API calls - the text shows actual LLM responses
4. Hypothesis evolution shows information accumulation clearly
5. Statistics at the end summarize the process

---

## 📝 What You Learn From These

After running the visualizations, you'll clearly see:

✅ **Each slice contributes unique information**
- Slice 1 might find: "fast performance, crashes"
- Slice 2 adds: "scalable architecture, uptime"
- Slice 3 adds: "support metrics, resolution time"

✅ **Hypothesis gets more detailed each iteration**
- v0: "Need to answer question"
- v1: "Found strengths A and weakness B"
- v2: "Strengths A, C, D; weaknesses B, E"
- v3: "Complete analysis with all details"

✅ **No single slice has the full picture**
- User reviews: subjective experience
- Tech specs: technical capabilities
- Support tickets: actual problems
- **Combined**: Comprehensive understanding

This is exactly what "query-driven iterative refinement" means!
