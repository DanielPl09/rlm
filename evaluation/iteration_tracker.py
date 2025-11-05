"""
Tracker for monitoring quality and time at each iteration of refinement.
"""
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from evaluation.metrics import evaluate_answer


@dataclass
class IterationCheckpoint:
    """Data for a single iteration checkpoint."""
    iteration: int
    sub_rlm_calls: int
    timestamp: float
    cumulative_time: float
    current_hypothesis: str
    metrics: Dict[str, float]
    final_answer: Optional[str] = None


@dataclass
class RefinementTrace:
    """Complete trace of a refinement session."""
    question: str
    ground_truth: str
    start_time: float
    checkpoints: List[IterationCheckpoint] = field(default_factory=list)
    final_answer: Optional[str] = None
    total_time: Optional[float] = None
    total_iterations: int = 0
    total_sub_rlm_calls: int = 0

    def add_checkpoint(
        self,
        iteration: int,
        sub_rlm_calls: int,
        current_hypothesis: str,
        final_answer: Optional[str] = None
    ):
        """Add a checkpoint with quality evaluation."""
        current_time = time.time()
        cumulative_time = current_time - self.start_time

        # Evaluate current hypothesis against ground truth
        metrics = evaluate_answer(current_hypothesis, self.ground_truth)

        checkpoint = IterationCheckpoint(
            iteration=iteration,
            sub_rlm_calls=sub_rlm_calls,
            timestamp=current_time,
            cumulative_time=cumulative_time,
            current_hypothesis=current_hypothesis,
            metrics=metrics,
            final_answer=final_answer
        )

        self.checkpoints.append(checkpoint)

        if final_answer is not None:
            self.final_answer = final_answer
            self.total_time = cumulative_time
            self.total_iterations = iteration
            self.total_sub_rlm_calls = sub_rlm_calls

    def get_quality_progression(self, metric_name: str = 'f1') -> List[tuple]:
        """
        Get quality progression over time.

        Returns:
            List of (cumulative_time, metric_value, sub_rlm_calls) tuples
        """
        return [
            (cp.cumulative_time, cp.metrics[metric_name], cp.sub_rlm_calls)
            for cp in self.checkpoints
        ]

    def get_final_metrics(self) -> Dict[str, float]:
        """Get metrics for the final answer."""
        if not self.checkpoints:
            return {'exact_match': 0.0, 'f1': 0.0, 'partial_match': 0.0}

        return self.checkpoints[-1].metrics

    def get_metrics_at_time(self, time_fraction: float) -> Optional[Dict[str, float]]:
        """
        Get best metrics achieved by a given fraction of total time.

        Args:
            time_fraction: Fraction of total time (e.g., 0.2 for 20%)

        Returns:
            Metrics at that time point, or None if not available
        """
        if not self.total_time or not self.checkpoints:
            return None

        target_time = self.total_time * time_fraction

        # Find checkpoint closest to target time
        valid_checkpoints = [cp for cp in self.checkpoints if cp.cumulative_time <= target_time]

        if not valid_checkpoints:
            return None

        # Return metrics from last checkpoint within time budget
        return valid_checkpoints[-1].metrics

    def get_metrics_at_calls(self, call_fraction: float) -> Optional[Dict[str, float]]:
        """
        Get best metrics achieved by a given fraction of total sub_RLM calls.

        Args:
            call_fraction: Fraction of total calls (e.g., 0.2 for 20%)

        Returns:
            Metrics at that call count, or None if not available
        """
        if not self.total_sub_rlm_calls or not self.checkpoints:
            return None

        target_calls = self.total_sub_rlm_calls * call_fraction

        # Find checkpoint closest to target calls
        valid_checkpoints = [cp for cp in self.checkpoints if cp.sub_rlm_calls <= target_calls]

        if not valid_checkpoints:
            return None

        # Return metrics from last checkpoint within call budget
        return valid_checkpoints[-1].metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'question': self.question,
            'ground_truth': self.ground_truth,
            'final_answer': self.final_answer,
            'total_time': self.total_time,
            'total_iterations': self.total_iterations,
            'total_sub_rlm_calls': self.total_sub_rlm_calls,
            'checkpoints': [
                {
                    'iteration': cp.iteration,
                    'sub_rlm_calls': cp.sub_rlm_calls,
                    'cumulative_time': cp.cumulative_time,
                    'current_hypothesis': cp.current_hypothesis,
                    'metrics': cp.metrics,
                    'final_answer': cp.final_answer
                }
                for cp in self.checkpoints
            ]
        }


class IterationTracker:
    """Manages tracking across multiple refinement sessions."""

    def __init__(self):
        self.traces: List[RefinementTrace] = []
        self.current_trace: Optional[RefinementTrace] = None

    def start_trace(self, question: str, ground_truth: str) -> RefinementTrace:
        """Start tracking a new refinement session."""
        self.current_trace = RefinementTrace(
            question=question,
            ground_truth=ground_truth,
            start_time=time.time()
        )
        return self.current_trace

    def add_checkpoint(
        self,
        iteration: int,
        sub_rlm_calls: int,
        current_hypothesis: str,
        final_answer: Optional[str] = None
    ):
        """Add checkpoint to current trace."""
        if self.current_trace is None:
            raise ValueError("No active trace. Call start_trace() first.")

        self.current_trace.add_checkpoint(
            iteration, sub_rlm_calls, current_hypothesis, final_answer
        )

    def finish_trace(self):
        """Complete current trace and add to history."""
        if self.current_trace is not None:
            self.traces.append(self.current_trace)
            self.current_trace = None

    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all traces."""
        if not self.traces:
            return {}

        # Calculate 80/20 statistics
        stats = {
            'total_traces': len(self.traces),
            'avg_final_f1': sum(t.get_final_metrics()['f1'] for t in self.traces) / len(self.traces),
            'avg_final_em': sum(t.get_final_metrics()['exact_match'] for t in self.traces) / len(self.traces),
            'avg_total_time': sum(t.total_time for t in self.traces if t.total_time) / len([t for t in self.traces if t.total_time]),
            'avg_total_calls': sum(t.total_sub_rlm_calls for t in self.traces) / len(self.traces)
        }

        # Calculate quality at 20% time
        metrics_at_20_time = [t.get_metrics_at_time(0.2) for t in self.traces]
        metrics_at_20_time = [m for m in metrics_at_20_time if m is not None]

        if metrics_at_20_time:
            stats['avg_f1_at_20pct_time'] = sum(m['f1'] for m in metrics_at_20_time) / len(metrics_at_20_time)
            stats['avg_em_at_20pct_time'] = sum(m['exact_match'] for m in metrics_at_20_time) / len(metrics_at_20_time)

        # Calculate quality at 20% calls
        metrics_at_20_calls = [t.get_metrics_at_calls(0.2) for t in self.traces]
        metrics_at_20_calls = [m for m in metrics_at_20_calls if m is not None]

        if metrics_at_20_calls:
            stats['avg_f1_at_20pct_calls'] = sum(m['f1'] for m in metrics_at_20_calls) / len(metrics_at_20_calls)
            stats['avg_em_at_20pct_calls'] = sum(m['exact_match'] for m in metrics_at_20_calls) / len(metrics_at_20_calls)

        # Calculate efficiency ratio
        if 'avg_f1_at_20pct_time' in stats and stats['avg_final_f1'] > 0:
            stats['efficiency_ratio_time'] = stats['avg_f1_at_20pct_time'] / stats['avg_final_f1']

        if 'avg_f1_at_20pct_calls' in stats and stats['avg_final_f1'] > 0:
            stats['efficiency_ratio_calls'] = stats['avg_f1_at_20pct_calls'] / stats['avg_final_f1']

        return stats
