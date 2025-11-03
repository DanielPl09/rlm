# Query-Driven Iterative Refinement in RLM

## Overview

This feature enables RLM to perform **query-driven iterative refinement** over pre-segmented context chunks. For a single user query, the RLM_REPL orchestrates multiple `sub_RLM(query, ctx_slice_id)` calls over distinct context slices, allowing the model to:

1. Process different context chunks independently
2. Maintain a shared hypothesis that gets refined after each sub_RLM call
3. Aggregate findings from all slices into a final coherent answer

## Architecture

### Components

#### 1. Context Slicing (`context_slicer.py`)

**ContextSlice**: Represents a single chunk of context with metadata
```python
class ContextSlice:
    slice_id: str         # Unique identifier
    content: Any          # The actual content (str, dict, list, etc.)
    metadata: dict        # Additional information about the slice
```

**ContextSlicer**: Manages and creates context slices
```python
class ContextSlicer:
    def add_slice(slice_id, content, metadata)  # Manual slice creation
    def get_slice(slice_id) -> ContextSlice     # Retrieve specific slice
    def list_slices() -> List[str]              # List all slice IDs
    def get_slice_info() -> List[dict]          # Get slice metadata

    @staticmethod
    def auto_slice_context(context, strategy="auto") -> Dict[str, ContextSlice]
```

**Auto-Slicing Strategies**:
- **Dictionary**: Creates one slice per key-value pair
- **Small List** (≤10 items): Creates one slice per item
- **Large List** (>10 items): Creates chunks of 10 items each
- **Markdown String**: Splits by headers (`#`, `##`, `###`)
- **Plain String**: Chunks by character count (~10k chars/chunk)

#### 2. Enhanced Sub_RLM (`repl.py`)

Extended to accept context slices and slice-specific queries:

```python
class Sub_RLM(RLM):
    def __init__(self, model: str, context_slices: dict = None):
        self.context_slices = context_slices  # Available slices

    def completion(self, prompt: str, ctx_slice_id: str = None) -> str:
        # If ctx_slice_id provided, prepend that slice to the prompt
        # Otherwise, perform standard LLM query
```

#### 3. Enhanced REPLEnv (`repl.py`)

Extended with slice-aware functions and hypothesis tracking:

**New Instance Variables**:
```python
self.context_slices: dict           # All available context slices
self.hypothesis: str                # Current hypothesis/answer
self.hypothesis_history: list       # History of all hypothesis updates
```

**New REPL Functions Available to Model**:

```python
# Slice Discovery
list_slices() -> list              # Get all available slice IDs
get_slice_info() -> list           # Get detailed info about slices

# Slice-Based Querying
llm_query(prompt, slice_id=None)   # Query LLM with optional slice

# Hypothesis Tracking
update_hypothesis(new_hypothesis)  # Update shared hypothesis
get_hypothesis()                   # Get current hypothesis
get_hypothesis_history()           # Get all previous versions
```

#### 4. Updated RLM_REPL (`rlm_repl.py`)

The main RLM client now automatically creates context slices:

```python
def setup_context(self, context, query, enable_slicing=True):
    # Convert context to REPL format
    context_data, context_str = utils.convert_context_for_repl(context)

    # Auto-create slices if enabled
    if enable_slicing:
        slice_input = context_data if context_data else context_str
        context_slices = ContextSlicer.auto_slice_context(slice_input)

    # Initialize REPL with slices
    self.repl_env = REPLEnv(
        context_json=context_data,
        context_str=context_str,
        context_slices=context_slices
    )
```

## Usage

### Basic Usage (Automatic Slicing)

```python
from rlm.rlm_repl import RLM_REPL

# Context will be automatically sliced
context = {
    "documentation": "API docs here...",
    "code_examples": "Example code here...",
    "chat_history": [{"role": "user", "content": "..."}]
}

client = RLM_REPL(
    model="gpt-4o",
    recursive_model="gpt-4o-mini",
    enable_logging=True
)

# RLM will automatically:
# 1. Slice context into chunks
# 2. Make them available via list_slices()
# 3. Allow slice-based queries via llm_query(prompt, slice_id)
result = client.completion(context, query="Your question here")
```

### Model-Side Workflow (What RLM Does)

The system prompt guides the model to use this workflow:

```python
# Step 1: Discover available slices
slices = list_slices()
print(f"Available slices: {slices}")

# Step 2: Initialize hypothesis
update_hypothesis("Initial understanding: [your initial thoughts]")

# Step 3: Query each relevant slice
results = []
for slice_id in slices:
    # Query this specific slice
    result = llm_query(
        f"Based on this context, what info relates to [question]?",
        slice_id=slice_id
    )
    results.append(result)

    # Refine hypothesis with new finding
    current = get_hypothesis()
    refined = llm_query(f"""
        Current hypothesis: {current}
        New finding: {result}
        Provide refined hypothesis incorporating this finding:
    """)
    update_hypothesis(refined)

# Step 4: Final answer is the refined hypothesis
final_answer = get_hypothesis()
FINAL(final_answer)
```

### Advanced: Manual Slicing

```python
from rlm.utils.context_slicer import ContextSlicer

# Create custom slices
slicer = ContextSlicer()
slicer.add_slice(
    "technical_docs",
    "Technical documentation content...",
    metadata={"type": "docs", "priority": "high"}
)
slicer.add_slice(
    "user_feedback",
    "User feedback and reviews...",
    metadata={"type": "feedback", "priority": "medium"}
)

# Use with RLM by passing slices to REPLEnv
from rlm.repl import REPLEnv

repl = REPLEnv(
    context_json={"data": "..."},
    context_slices=slicer.slices  # Pass custom slices
)
```

## Key Benefits

1. **Explicit Control**: REPL chooses which slices to query (no automatic chunking hidden from the model)
2. **Iterative Refinement**: Hypothesis updated after each sub_RLM call, building knowledge incrementally
3. **Scalability**: Can process large contexts by distributing across multiple sub_RLM calls
4. **Transparency**: Full visibility into which slices are queried and when
5. **Flexibility**: Works with any context type (dict, list, string)

## Main Control Flow

The main control flow remains intact - only extended with new capabilities:

```
User Query + Context
    ↓
RLM_REPL.completion()
    ↓
setup_context()
    ├─ Convert context to REPL format
    ├─ Auto-slice context → context_slices
    └─ Initialize REPLEnv(context_slices)
    ↓
Main Iteration Loop (up to max_iterations)
    ├─ Root LM decides what to do
    ├─ Model can call:
    │   ├─ list_slices() → see available chunks
    │   ├─ llm_query(prompt, slice_id) → query specific chunk
    │   ├─ update_hypothesis(new) → refine answer
    │   └─ get_hypothesis() → retrieve current answer
    ├─ Execute code in REPL
    └─ Check for FINAL() answer
    ↓
Return final refined answer
```

## Example: Multi-Document Analysis

```python
context = {
    "research_paper_1": "Paper about topic A...",
    "research_paper_2": "Paper about topic B...",
    "research_paper_3": "Paper about topic C...",
}

query = "What are the common themes across all papers?"

# RLM will:
# 1. Auto-slice into 3 slices (dict_research_paper_1, etc.)
# 2. Query each paper individually: llm_query("What themes?", "dict_research_paper_1")
# 3. Update hypothesis after each paper
# 4. Provide synthesized final answer combining all themes
```

## Implementation Details

### Slice ID Naming Conventions

- **Dictionary slices**: `dict_{key_name}`
- **List item slices**: `item_{index}`
- **List chunk slices**: `chunk_{chunk_number}`
- **Markdown section slices**: `section_{header_name_lowercased}`
- **String chunk slices**: `chunk_{chunk_number}`

### Hypothesis Tracking

Hypothesis tracking provides:
- **Current state**: `get_hypothesis()` returns the latest refined answer
- **History**: `get_hypothesis_history()` shows evolution of understanding
- **Incremental refinement**: Each `update_hypothesis()` call appends previous version to history

### Backward Compatibility

The feature is **fully backward compatible**:
- `enable_slicing=True` by default in `RLM_REPL.setup_context()`
- If slicing is disabled, RLM works exactly as before
- Existing code requires no changes

## Testing

Run unit tests:
```bash
python -m unittest tests.test_slice_refinement -v
```

Run example:
```bash
export OPENAI_API_KEY=your_key
python examples/example_slice_refinement.py
```

## Files Modified/Created

### New Files
- `rlm/utils/context_slicer.py` - Context slicing utilities
- `examples/example_slice_refinement.py` - Example usage
- `tests/test_slice_refinement.py` - Unit tests
- `docs/QUERY_DRIVEN_REFINEMENT.md` - This documentation

### Modified Files
- `rlm/repl.py` - Enhanced Sub_RLM and REPLEnv
- `rlm/rlm_repl.py` - Integration of slicing
- `rlm/utils/prompts.py` - Updated system prompt with slice-based workflow

## Future Enhancements

Potential improvements:
- **Adaptive slicing**: Model can request custom slice boundaries
- **Parallel queries**: Query multiple slices concurrently
- **Slice caching**: Cache sub_RLM results for repeated slice queries
- **Smart routing**: Automatically determine relevant slices for query
- **Cross-slice references**: Track information flow between slices
