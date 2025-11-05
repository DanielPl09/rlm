"""
Test HotpotQA dataset with Anthropic API using query-driven iterative refinement.
Uses the same proven pattern as verify_refinement.py.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.utils.context_slicer import ContextSlicer
from rlm.utils.anthropic_client import AnthropicClient
import json


def get_hotpotqa_examples():
    """Hardcoded HotpotQA examples for testing."""
    return [
        {
            "question": "Which magazine was started first, Arthur's Magazine or First for Women?",
            "context": {
                "title": ["Arthur's Magazine", "First for Women"],
                "sentences": [
                    [
                        "Arthur's Magazine (1844–1846) was an American literary periodical published in Philadelphia in the 19th century.",
                        "Edited by Timothy Shay Arthur, it featured essays, stories, and poetry."
                    ],
                    [
                        "First for Women is a woman's magazine published by Bauer Media Group in the USA.",
                        "The magazine was started in 1989.",
                        "It is based in Englewood Cliffs, New Jersey."
                    ]
                ]
            },
            "answer": "Arthur's Magazine"
        },
        {
            "question": "The Oberoi family is part of a hotel company that has a head office in what city?",
            "context": {
                "title": ["Oberoi family", "The Oberoi Group"],
                "sentences": [
                    [
                        "The Oberoi family is an Indian family that is famous for its involvement in hotels, namely through The Oberoi Group."
                    ],
                    [
                        "The Oberoi Group is a hotel company with its head office in Delhi.",
                        "It was founded in 1934 and operates luxury hotels and resorts."
                    ]
                ]
            },
            "answer": "Delhi"
        },
        {
            "question": "What is the name of the airport in the city where the 2004 Summer Olympics were held?",
            "context": {
                "title": ["2004 Summer Olympics", "Athens International Airport"],
                "sentences": [
                    [
                        "The 2004 Summer Olympics, officially known as the Games of the XXVIII Olympiad, were held in Athens, Greece.",
                        "The event took place from August 13 to August 29, 2004."
                    ],
                    [
                        "Athens International Airport, commonly known as Eleftherios Venizelos International Airport, is the primary airport serving Athens.",
                        "It began operations in 2001."
                    ]
                ]
            },
            "answer": "Eleftherios Venizelos International Airport"
        }
    ]


def format_hotpotqa_for_slicing(example):
    """
    Convert HotpotQA example to dict format for context slicing.

    Args:
        example: HotpotQA example dict

    Returns:
        context_dict suitable for ContextSlicer
    """
    context = {}

    titles = example['context']['title']
    sentences = example['context']['sentences']

    # Each document becomes a context slice
    for i, (title, sents) in enumerate(zip(titles, sentences)):
        doc_text = ' '.join(sents)
        # Use title as key (cleaned)
        key = f"doc_{i}_{title.replace(' ', '_').replace(',', '')[:30]}"
        context[key] = doc_text

    return context


def evaluate_answer(rlm_answer, gold_answer):
    """Simple evaluation metrics."""
    rlm_lower = rlm_answer.strip().lower()
    gold_lower = gold_answer.strip().lower()

    # Exact match
    exact_match = rlm_lower == gold_lower

    # Contains answer
    contains = gold_lower in rlm_lower

    # Token overlap (simple F1)
    rlm_tokens = set(rlm_lower.split())
    gold_tokens = set(gold_lower.split())

    if len(rlm_tokens) == 0 or len(gold_tokens) == 0:
        f1 = 0.0
    else:
        overlap = len(rlm_tokens & gold_tokens)
        precision = overlap / len(rlm_tokens) if len(rlm_tokens) > 0 else 0
        recall = overlap / len(gold_tokens) if len(gold_tokens) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'exact_match': exact_match,
        'contains_answer': contains,
        'f1_score': f1
    }


def run_hotpotqa_refinement(example, api_key: str, example_num: int):
    """
    Run iterative refinement on a single HotpotQA example.

    Args:
        example: HotpotQA example dict
        api_key: Anthropic API key
        example_num: Example number for display

    Returns:
        Result dict with answer and metrics
    """
    question = example['question']
    gold_answer = example['answer']

    print("\n" + "="*80)
    print(f"HOTPOTQA EXAMPLE #{example_num}")
    print("="*80)
    print(f"Question: {question}")
    print(f"Gold Answer: {gold_answer}")

    # Format context for slicing
    context = format_hotpotqa_for_slicing(example)
    print(f"\nContext documents: {list(context.keys())}")

    # Create slices
    slices = ContextSlicer.auto_slice_context(context)
    print(f"✅ Created {len(slices)} slices")

    # Initialize Anthropic client
    client = AnthropicClient(api_key=api_key, model="claude-3-opus-20240229")

    # Iterative refinement
    hypothesis = f"Need to answer: {question}"
    hypothesis_history = [hypothesis]
    sub_rlm_calls = 0

    print("\n" + "-"*80)
    print("ITERATIVE REFINEMENT PROCESS")
    print("-"*80)

    for i, (slice_id, slice_obj) in enumerate(slices.items(), 1):
        print(f"\n[{i}/{len(slices)}] Processing {slice_id}...")
        print(f"  Document content: {slice_obj.content[:100]}...")

        # Query this slice
        sub_rlm_calls += 1
        slice_prompt = f"""You are answering a multi-document question. Here is one document.

Question: {question}

Document: {slice_obj.content}

Based ONLY on this document, what information is relevant to answering the question? Be concise and specific."""

        try:
            slice_result = client.completion(slice_prompt)
            print(f"  ✅ sub_RLM call #{sub_rlm_calls}: {slice_result[:100]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

        # Refine hypothesis
        sub_rlm_calls += 1
        refinement_prompt = f"""You are building an answer by examining multiple documents sequentially.

Current hypothesis: {hypothesis}

New finding from document '{slice_id}': {slice_result}

Provide an updated hypothesis that incorporates this new information. If you now have enough information to answer the question "{question}", provide the final answer. Be concise."""

        try:
            refined = client.completion(refinement_prompt)
            hypothesis_history.append(hypothesis)
            hypothesis = refined
            print(f"  ✅ sub_RLM call #{sub_rlm_calls}: Hypothesis refined")
            print(f"  New hypothesis: {hypothesis[:150]}...")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Final answer extraction
    print("\n" + "-"*80)
    print("EXTRACTING FINAL ANSWER")
    print("-"*80)

    final_prompt = f"""Based on all the information gathered, provide a concise final answer to this question:

Question: {question}

Your refined hypothesis: {hypothesis}

Provide ONLY the direct answer, no explanation."""

    try:
        final_answer = client.completion(final_prompt)
        sub_rlm_calls += 1
    except Exception as e:
        print(f"❌ Error getting final answer: {e}")
        final_answer = hypothesis

    # Evaluate
    metrics = evaluate_answer(final_answer, gold_answer)

    # Results
    print("\n" + "="*80)
    print(f"RESULTS - EXAMPLE #{example_num}")
    print("="*80)
    print(f"Question: {question}")
    print(f"Gold Answer: {gold_answer}")
    print(f"RLM Answer: {final_answer}")
    print(f"\nTotal sub_RLM calls: {sub_rlm_calls}")
    print(f"Hypothesis versions: {len(hypothesis_history) + 1}")
    print(f"\nEvaluation:")
    print(f"  Exact Match: {'✅' if metrics['exact_match'] else '❌'}")
    print(f"  Contains Answer: {'✅' if metrics['contains_answer'] else '❌'}")
    print(f"  F1 Score: {metrics['f1_score']:.2f}")
    print("="*80)

    return {
        'question': question,
        'gold_answer': gold_answer,
        'rlm_answer': final_answer,
        'num_slices': len(slices),
        'num_calls': sub_rlm_calls,
        'hypothesis_versions': len(hypothesis_history) + 1,
        'metrics': metrics,
        'hypothesis_history': hypothesis_history
    }


def main():
    """Run HotpotQA tests with Anthropic."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Usage: export ANTHROPIC_API_KEY=your_key && python test_hotpotqa_anthropic.py")
        sys.exit(1)

    print("="*80)
    print("HOTPOTQA TESTING WITH QUERY-DRIVEN ITERATIVE REFINEMENT")
    print("Using Anthropic API (claude-3-opus-20240229)")
    print("="*80)

    # Load examples
    examples = get_hotpotqa_examples()
    print(f"\nLoaded {len(examples)} HotpotQA examples")

    # Run tests
    results = []
    for i, example in enumerate(examples, 1):
        result = run_hotpotqa_refinement(example, api_key, i)
        results.append(result)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY - ALL EXAMPLES")
    print("="*80)

    total_calls = sum(r['num_calls'] for r in results)
    total_versions = sum(r['hypothesis_versions'] for r in results)
    exact_matches = sum(1 for r in results if r['metrics']['exact_match'])
    contains = sum(1 for r in results if r['metrics']['contains_answer'])
    avg_f1 = sum(r['metrics']['f1_score'] for r in results) / len(results)

    print(f"Examples tested: {len(results)}")
    print(f"Total sub_RLM calls: {total_calls}")
    print(f"Total hypothesis versions: {total_versions}")
    print(f"\nAccuracy Metrics:")
    print(f"  Exact Match: {exact_matches}/{len(results)} ({exact_matches/len(results)*100:.1f}%)")
    print(f"  Contains Answer: {contains}/{len(results)} ({contains/len(results)*100:.1f}%)")
    print(f"  Average F1: {avg_f1:.3f}")

    # Save results
    output_file = "hotpotqa_anthropic_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")
    print("="*80)

    return results


if __name__ == "__main__":
    main()
