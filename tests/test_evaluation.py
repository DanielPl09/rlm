"""
Unit tests for evaluation framework.
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import only the core components that don't require full RLM setup
from evaluation.metrics import (
    normalize_answer,
    exact_match_score,
    f1_score,
    evaluate_answer,
    aggregate_metrics
)
from evaluation.iteration_tracker import (
    IterationCheckpoint,
    RefinementTrace,
    IterationTracker
)
from evaluation.hotpotqa_loader import (
    HotpotQALoader,
    create_sample_examples
)

# Note: tracked_rlm tests require full RLM environment setup


class TestMetrics(unittest.TestCase):
    """Test evaluation metrics."""

    def test_normalize_answer(self):
        """Test answer normalization."""
        self.assertEqual(normalize_answer("The Answer"), "answer")
        self.assertEqual(normalize_answer("  A  test  "), "test")
        self.assertEqual(normalize_answer("Hello, World!"), "hello world")

    def test_exact_match(self):
        """Test exact match scoring."""
        self.assertEqual(exact_match_score("Paris", "paris"), 1.0)
        self.assertEqual(exact_match_score("The Paris", "Paris"), 1.0)
        self.assertEqual(exact_match_score("Paris", "London"), 0.0)

    def test_f1_score(self):
        """Test F1 score calculation."""
        # Perfect match
        self.assertEqual(f1_score("Paris", "Paris"), 1.0)

        # Partial match
        score = f1_score("Paris France", "Paris")
        self.assertGreater(score, 0.5)
        self.assertLess(score, 1.0)

        # No match
        self.assertEqual(f1_score("Paris", "London"), 0.0)

    def test_evaluate_answer(self):
        """Test complete answer evaluation."""
        result = evaluate_answer("Paris", "paris")
        self.assertIn('exact_match', result)
        self.assertIn('f1', result)
        self.assertIn('partial_match', result)
        self.assertEqual(result['exact_match'], 1.0)

    def test_aggregate_metrics(self):
        """Test metric aggregation."""
        metrics = [
            {'exact_match': 1.0, 'f1': 1.0},
            {'exact_match': 0.0, 'f1': 0.5},
            {'exact_match': 1.0, 'f1': 0.8}
        ]
        agg = aggregate_metrics(metrics)
        self.assertAlmostEqual(agg['exact_match'], 2/3, places=2)
        self.assertAlmostEqual(agg['f1'], 0.77, places=2)


class TestIterationTracker(unittest.TestCase):
    """Test iteration tracking functionality."""

    def test_refinement_trace_creation(self):
        """Test creating a refinement trace."""
        import time
        trace = RefinementTrace(
            question="What is the capital of France?",
            ground_truth="Paris",
            start_time=time.time()
        )
        self.assertEqual(trace.question, "What is the capital of France?")
        self.assertEqual(trace.ground_truth, "Paris")
        self.assertEqual(len(trace.checkpoints), 0)

    def test_add_checkpoint(self):
        """Test adding checkpoints to trace."""
        import time
        trace = RefinementTrace(
            question="Test question",
            ground_truth="Test answer",
            start_time=time.time()
        )

        # Add checkpoint
        trace.add_checkpoint(
            iteration=1,
            sub_rlm_calls=2,
            current_hypothesis="Test answer",
            final_answer=None
        )

        self.assertEqual(len(trace.checkpoints), 1)
        self.assertEqual(trace.checkpoints[0].iteration, 1)
        self.assertEqual(trace.checkpoints[0].sub_rlm_calls, 2)

    def test_quality_progression(self):
        """Test getting quality progression."""
        import time
        trace = RefinementTrace(
            question="Test",
            ground_truth="Paris",
            start_time=time.time()
        )

        # Add multiple checkpoints
        for i in range(3):
            time.sleep(0.01)  # Small delay
            trace.add_checkpoint(
                iteration=i+1,
                sub_rlm_calls=i+1,
                current_hypothesis="Paris" if i == 2 else "Other"
            )

        progression = trace.get_quality_progression('f1')
        self.assertEqual(len(progression), 3)
        # Last checkpoint should have best F1
        self.assertGreater(progression[-1][1], progression[0][1])

    def test_iteration_tracker(self):
        """Test iteration tracker with multiple traces."""
        tracker = IterationTracker()

        # Start and finish a trace
        trace = tracker.start_trace("Question 1", "Answer 1")
        self.assertIsNotNone(tracker.current_trace)

        tracker.add_checkpoint(1, 1, "Answer 1", final_answer="Answer 1")
        tracker.finish_trace()

        self.assertEqual(len(tracker.traces), 1)
        self.assertIsNone(tracker.current_trace)


class TestHotpotQALoader(unittest.TestCase):
    """Test HotpotQA dataset loading."""

    def test_create_sample_examples(self):
        """Test creating sample examples."""
        examples = create_sample_examples()
        self.assertGreater(len(examples), 0)

        # Check first example
        example = examples[0]
        self.assertTrue(hasattr(example, 'question'))
        self.assertTrue(hasattr(example, 'answer'))
        self.assertTrue(hasattr(example, 'context'))

    def test_example_context_dict(self):
        """Test getting context as dictionary."""
        examples = create_sample_examples()
        example = examples[0]

        context_dict = example.get_context_dict()
        self.assertIsInstance(context_dict, dict)
        self.assertGreater(len(context_dict), 0)

    def test_example_context_text(self):
        """Test getting context as text."""
        examples = create_sample_examples()
        example = examples[0]

        context_text = example.get_context_text()
        self.assertIsInstance(context_text, str)
        self.assertGreater(len(context_text), 0)

    def test_loader_from_dict(self):
        """Test loading examples from dictionaries."""
        data = [
            {
                "question": "Test question?",
                "answer": "Test answer",
                "context": [["Doc1", ["Sentence 1"]]],
                "supporting_facts": [["Doc1", 0]],
                "_id": "test_1",
                "level": "easy",
                "type": "bridge"
            }
        ]

        loader = HotpotQALoader()
        loader.load_from_dict(data)

        self.assertEqual(len(loader), 1)
        example = loader[0]
        self.assertEqual(example.question, "Test question?")
        self.assertEqual(example.answer, "Test answer")


class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""

    def test_full_tracking_workflow(self):
        """Test complete tracking workflow without actual LLM calls."""
        import time

        # Create tracker
        tracker = IterationTracker()

        # Start trace
        trace = tracker.start_trace(
            question="What is the capital of France?",
            ground_truth="Paris"
        )

        # Simulate iterations
        hypotheses = [
            "I don't know",
            "France is in Europe",
            "The capital might be Paris",
            "Paris"
        ]

        for i, hypothesis in enumerate(hypotheses):
            time.sleep(0.01)  # Simulate work
            is_final = (i == len(hypotheses) - 1)
            tracker.add_checkpoint(
                iteration=i+1,
                sub_rlm_calls=i+1,
                current_hypothesis=hypothesis,
                final_answer=hypothesis if is_final else None
            )

        # Finish trace
        tracker.finish_trace()

        # Verify results
        self.assertEqual(len(tracker.traces), 1)
        trace = tracker.traces[0]

        final_metrics = trace.get_final_metrics()
        self.assertEqual(final_metrics['exact_match'], 1.0)
        self.assertEqual(final_metrics['f1'], 1.0)

        # Check quality progression
        progression = trace.get_quality_progression('f1')
        self.assertEqual(len(progression), 4)

        # Quality should improve over time
        self.assertGreaterEqual(progression[-1][1], progression[0][1])

    def test_aggregate_statistics(self):
        """Test aggregate statistics computation."""
        import time

        tracker = IterationTracker()

        # Create multiple traces
        for question_num in range(3):
            trace = tracker.start_trace(
                question=f"Question {question_num}",
                ground_truth="Answer"
            )

            for i in range(5):
                time.sleep(0.01)
                hypothesis = "Answer" if i >= 3 else "Wrong"
                tracker.add_checkpoint(
                    iteration=i+1,
                    sub_rlm_calls=i+1,
                    current_hypothesis=hypothesis,
                    final_answer="Answer" if i == 4 else None
                )

            tracker.finish_trace()

        # Get aggregate stats
        stats = tracker.get_aggregate_stats()

        self.assertEqual(stats['total_traces'], 3)
        self.assertIn('avg_final_f1', stats)
        self.assertIn('avg_total_time', stats)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
