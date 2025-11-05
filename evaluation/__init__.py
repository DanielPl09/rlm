"""
Evaluation framework for demonstrating 80/20 principle in RLM iterative refinement.
"""

from evaluation.metrics import (
    normalize_answer,
    exact_match_score,
    f1_score,
    partial_match_score,
    evaluate_answer,
    aggregate_metrics
)

from evaluation.iteration_tracker import (
    IterationCheckpoint,
    RefinementTrace,
    IterationTracker
)

from evaluation.hotpotqa_loader import (
    HotpotQAExample,
    HotpotQALoader,
    create_sample_examples
)

# Try to import tracked_rlm (requires full RLM environment)
try:
    from evaluation.tracked_rlm import (
        TrackedRLM,
        create_tracked_rlm
    )
    _HAS_TRACKED_RLM = True
except ImportError:
    _HAS_TRACKED_RLM = False
    TrackedRLM = None
    create_tracked_rlm = None

__all__ = [
    # Metrics
    'normalize_answer',
    'exact_match_score',
    'f1_score',
    'partial_match_score',
    'evaluate_answer',
    'aggregate_metrics',

    # Tracking
    'IterationCheckpoint',
    'RefinementTrace',
    'IterationTracker',

    # Data loading
    'HotpotQAExample',
    'HotpotQALoader',
    'create_sample_examples',

    # Tracked RLM (may be None if dependencies not available)
    'TrackedRLM',
    'create_tracked_rlm',
]
