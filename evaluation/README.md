# RLM Iterative Refinement: 80/20 Principle Evaluation

This evaluation framework demonstrates that **iterative refinement can achieve 80% of quality in 20% of time**, addressing the main constraint of long query times in RLM systems.

## Overview

The framework evaluates RLM's iterative refinement approach on multi-hop question answering (HotpotQA) and tracks:
- **Quality metrics** (F1, Exact Match) at each iteration
- **Time consumption** at each checkpoint
- **Sub-RLM call counts** throughout the process

The goal is to demonstrate the **Pareto principle (80/20 rule)**: that most of the answer quality is achieved early in the refinement process, making the approach practical despite longer total query times.

## Key Components

### 1. Metrics (`metrics.py`)
Implements standard QA evaluation metrics:
- **Exact Match (EM)**: Binary match after normalization
- **F1 Score**: Token-level overlap between prediction and ground truth
- **Partial Match**: Substring containment check

### 2. Iteration Tracking (`iteration_tracker.py`)
Tracks quality and time throughout refinement:
- **IterationCheckpoint**: Records state at each step
- **RefinementTrace**: Complete trace for one question
- **IterationTracker**: Aggregates multiple traces

### 3. HotpotQA Loader (`hotpotqa_loader.py`)
Loads and formats HotpotQA examples:
- Parses multi-hop questions with supporting documents
- Formats context for RLM consumption
- Includes sample examples for testing

### 4. Tracked RLM (`tracked_rlm.py`)
RLM wrapper with integrated tracking:
- Monitors each iteration and sub-RLM call
- Evaluates hypothesis quality in real-time
- Records timing information

### 5. Experiment Runner (`run_experiment.py`)
Orchestrates experiments:
- Runs multiple examples with tracking
- Computes aggregate statistics
- Saves detailed results in JSON format

### 6. Visualization (`visualize.py`)
Generates plots demonstrating 80/20 principle:
- Quality vs Time curves
- Quality vs Sub-RLM calls
- Efficiency comparison charts

## Usage

### Quick Start with Sample Examples

```bash
# Run experiment with sample examples
python -m evaluation.run_experiment \
    --model gpt-5 \
    --max_iterations 20 \
    --output_dir results/sample_run

# Generate visualizations
python -m evaluation.visualize results/sample_run/experiment_*.json
```

### Using Real HotpotQA Dataset

```bash
# Download HotpotQA dataset first
# Then run with dataset file
python -m evaluation.run_experiment \
    --dataset path/to/hotpotqa_dev.json \
    --num_examples 10 \
    --model gpt-5 \
    --output_dir results/hotpotqa_eval

# Visualize results
python -m evaluation.visualize results/hotpotqa_eval/experiment_*.json
```

### Command Line Options

**run_experiment.py:**
- `--dataset`: Path to HotpotQA JSON file (default: use samples)
- `--num_examples`: Number of examples to evaluate
- `--model`: Model name (default: gpt-5)
- `--max_iterations`: Max iterations per example (default: 20)
- `--output_dir`: Output directory (default: results)
- `--api_key`: API key (or use env variable)
- `--no_logging`: Disable console logging

**visualize.py:**
- `results_file`: Path to experiment JSON
- `--output_dir`: Output directory for plots

## Programmatic Usage

### Running Single Example

```python
from evaluation import create_tracked_rlm, IterationTracker
from evaluation.hotpotqa_loader import create_sample_examples

# Get a sample example
examples = create_sample_examples()
example = examples[0]

# Create tracker
tracker = IterationTracker()

# Create tracked RLM
rlm = create_tracked_rlm(
    api_key="your-api-key",
    model="gpt-5",
    tracker=tracker,
    ground_truth=example.answer,
    max_iterations=20,
    enable_logging=True
)

# Run completion
answer = rlm.completion(
    context=example.get_context_dict(),
    query=example.question
)

# Get metrics
trace = tracker.traces[0]
final_metrics = trace.get_final_metrics()
metrics_at_20 = trace.get_metrics_at_time(0.2)

print(f"Final F1: {final_metrics['f1']:.3f}")
print(f"F1 at 20% time: {metrics_at_20['f1']:.3f}")
print(f"Efficiency: {metrics_at_20['f1'] / final_metrics['f1']:.1%}")
```

### Batch Evaluation

```python
from evaluation.run_experiment import run_experiment
from evaluation.hotpotqa_loader import create_sample_examples

# Run batch experiment
examples = create_sample_examples()
results = run_experiment(
    examples=examples,
    api_key="your-api-key",
    model="gpt-5",
    max_iterations=20,
    output_dir="results/batch",
    enable_logging=False
)

# Check aggregate stats
stats = results['aggregate_stats']
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg final F1: {stats['avg_final_f1']:.3f}")
print(f"Avg F1 at 20% time: {stats['avg_f1_at_20pct_time']:.3f}")
print(f"Quality achieved: {stats['quality_achieved_at_20pct_time']:.1%}")
```

### Creating Visualizations

```python
from evaluation.visualize import create_all_visualizations

# Generate all plots from results
create_all_visualizations(
    results_file="results/experiment_20250101_120000.json",
    output_dir="plots"
)
```

## Output Structure

### Experiment Results JSON

```json
{
  "experiment_info": {
    "timestamp": "20250101_120000",
    "model": "gpt-5",
    "max_iterations": 20,
    "num_examples": 3
  },
  "aggregate_stats": {
    "total_traces": 3,
    "avg_final_f1": 0.85,
    "avg_final_em": 0.67,
    "avg_total_time": 45.2,
    "avg_total_calls": 8.3,
    "avg_f1_at_20pct_time": 0.72,
    "avg_f1_at_20pct_calls": 0.68,
    "quality_achieved_at_20pct_time": 0.847,
    "demonstrates_80_20_time": true
  },
  "individual_results": [...],
  "traces": [...]
}
```

### Key Metrics

- **avg_final_f1**: Average F1 score at completion
- **avg_f1_at_20pct_time**: Average F1 at 20% of total time
- **quality_achieved_at_20pct_time**: Ratio showing % of quality at 20% time
- **demonstrates_80_20_time**: Boolean indicating if 80/20 principle holds (≥75%)

## Interpreting Results

### Success Criteria

The 80/20 principle is demonstrated if:
- `quality_achieved_at_20pct_time ≥ 0.75` (75%+ of quality in 20% time)
- OR `quality_achieved_at_20pct_calls ≥ 0.75` (75%+ of quality in 20% calls)

### Visualization Insights

**Quality vs Time Plot:**
- Shows how F1 score increases over time
- Individual traces (blue) + average curve (red)
- Green line marks 20% time point
- Annotations show quality achieved

**Quality vs Calls Plot:**
- Similar to time plot but based on sub-RLM calls
- Demonstrates efficiency of early iterations

**Efficiency Comparison:**
- Bar charts comparing 20% vs 100% checkpoints
- Shows percentage of final quality achieved early

## Example Interpretation

```
Average Final F1: 0.85
Average F1 at 20% Time: 0.72
Quality Achieved: 84.7%
```

**Interpretation:** The system achieves **84.7% of final quality** in just **20% of the time**, strongly demonstrating the 80/20 principle. This means:
- Early iterations capture most of the answer
- Remaining 80% of time provides only 15.3% quality improvement
- The approach is practical despite longer total times

## Adding Custom Metrics

```python
from evaluation.metrics import evaluate_answer

def custom_metric(prediction: str, ground_truth: str) -> float:
    """Your custom metric implementation."""
    # Implement your metric
    return score

# Use in evaluation
result = evaluate_answer(prediction, ground_truth)
result['custom'] = custom_metric(prediction, ground_truth)
```

## Extending to Other Datasets

To use with other datasets:

1. **Create a loader** similar to `HotpotQALoader`
2. **Format examples** with: question, answer, context
3. **Run experiment** using the loader

```python
class MyDatasetLoader:
    def __init__(self, file_path):
        # Load your dataset
        pass

    def get_examples(self):
        # Return list of examples with:
        # - question
        # - answer
        # - get_context_dict() method
        pass
```

## Performance Tips

1. **Start small**: Test with 3-5 examples first
2. **Use samples**: Sample examples are fast and free
3. **Adjust iterations**: Reduce `max_iterations` for faster runs
4. **Disable logging**: Use `--no_logging` for batch runs
5. **Parallel execution**: Run multiple experiments in parallel

## Troubleshooting

**No tracking data:**
- Ensure `tracker` is passed to `create_tracked_rlm()`
- Verify `ground_truth` is provided

**Low quality scores:**
- Check answer normalization (articles, punctuation removed)
- Verify ground truth format matches dataset
- Review hypothesis updates in trace

**Missing checkpoints:**
- Ensure iterations are running (check logs)
- Verify sub-RLM calls are being made
- Check for early termination

## Requirements

```bash
pip install matplotlib numpy
```

## Related Documentation

- Main RLM documentation: `/docs/QUERY_DRIVEN_REFINEMENT.md`
- RLM REPL: `/rlm/rlm_repl.py`
- Context slicing: `/rlm/utils/context_slicer.py`

## Citation

When using this evaluation framework, please reference:
- HotpotQA dataset: Yang et al., 2018
- F1/EM metrics: Rajpurkar et al., 2016 (SQuAD)
