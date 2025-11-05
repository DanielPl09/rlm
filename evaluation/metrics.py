"""
Evaluation metrics for measuring answer quality in iterative refinement.
"""
import re
from typing import List, Dict, Any
from collections import Counter


def normalize_answer(s: str) -> str:
    """
    Normalize answer string for comparison.
    - Lowercase
    - Remove punctuation
    - Remove articles (a, an, the)
    - Remove extra whitespace
    """
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def exact_match_score(prediction: str, ground_truth: str) -> float:
    """
    Compute exact match score (1.0 if exact match, 0.0 otherwise).
    """
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def f1_score(prediction: str, ground_truth: str) -> float:
    """
    Compute token-level F1 score between prediction and ground truth.
    """
    pred_tokens = normalize_answer(prediction).split()
    truth_tokens = normalize_answer(ground_truth).split()

    if len(pred_tokens) == 0 and len(truth_tokens) == 0:
        return 1.0
    if len(pred_tokens) == 0 or len(truth_tokens) == 0:
        return 0.0

    common = Counter(pred_tokens) & Counter(truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0.0

    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)

    return f1


def partial_match_score(prediction: str, ground_truth: str) -> float:
    """
    Compute partial match score - checks if ground truth is contained in prediction.
    Returns 1.0 if ground truth is a substring of prediction, 0.0 otherwise.
    """
    pred_norm = normalize_answer(prediction)
    truth_norm = normalize_answer(ground_truth)

    if truth_norm in pred_norm:
        return 1.0
    return 0.0


def evaluate_answer(prediction: str, ground_truth: str) -> Dict[str, float]:
    """
    Compute all metrics for a prediction against ground truth.

    Returns:
        Dictionary with keys: 'exact_match', 'f1', 'partial_match'
    """
    return {
        'exact_match': exact_match_score(prediction, ground_truth),
        'f1': f1_score(prediction, ground_truth),
        'partial_match': partial_match_score(prediction, ground_truth)
    }


def aggregate_metrics(metric_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate metrics across multiple examples.

    Returns:
        Dictionary with average scores for each metric.
    """
    if not metric_list:
        return {'exact_match': 0.0, 'f1': 0.0, 'partial_match': 0.0}

    result = {}
    keys = metric_list[0].keys()

    for key in keys:
        result[key] = sum(m[key] for m in metric_list) / len(metric_list)

    return result
