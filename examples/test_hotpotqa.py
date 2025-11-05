"""
Test query-driven iterative refinement with HotpotQA dataset.
HotpotQA is a multi-document QA dataset requiring reasoning across paragraphs.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.rlm_repl import RLM_REPL
import json


def load_hotpotqa_sample():
    """
    Load a small sample of HotpotQA examples.
    If datasets library not available, uses hardcoded examples.
    """
    try:
        from datasets import load_dataset
        print("Loading HotpotQA from HuggingFace datasets...")
        dataset = load_dataset("hotpot_qa", "distractor", split="validation")
        print(f"✅ Loaded {len(dataset)} examples from HotpotQA validation set")
        return dataset
    except ImportError:
        print("⚠️  datasets library not installed. Using hardcoded examples.")
        print("   Install with: pip install datasets")
        return get_hardcoded_examples()
    except Exception as e:
        print(f"⚠️  Error loading dataset: {e}")
        print("   Using hardcoded examples instead.")
        return get_hardcoded_examples()


def get_hardcoded_examples():
    """Hardcoded HotpotQA examples for testing without datasets library."""
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


def format_hotpotqa_for_rlm(example):
    """
    Convert HotpotQA example to RLM-compatible format.

    Args:
        example: HotpotQA example dict

    Returns:
        (context_dict, query_str)
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

    query = example['question']

    return context, query


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


def run_hotpotqa_test(num_examples=3, start_idx=0):
    """
    Run RLM on HotpotQA examples.

    Args:
        num_examples: Number of examples to test
        start_idx: Starting index in dataset
    """
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_key")
        sys.exit(1)

    # Load dataset
    dataset = load_hotpotqa_sample()

    # If using hardcoded examples, limit to available
    if isinstance(dataset, list):
        num_examples = min(num_examples, len(dataset))

    # Initialize RLM
    print("\n" + "="*80)
    print("INITIALIZING RLM")
    print("="*80)
    client = RLM_REPL(
        api_key=api_key,
        model="gpt-4o-mini",
        recursive_model="gpt-4o-mini",
        max_iterations=15,
        enable_logging=False  # Set to True for detailed logs
    )
    print("✅ RLM initialized")

    # Run tests
    results = []

    for i in range(start_idx, start_idx + num_examples):
        print("\n" + "="*80)
        print(f"TEST {i - start_idx + 1}/{num_examples} (Example #{i})")
        print("="*80)

        # Get example
        example = dataset[i] if not isinstance(dataset, list) else dataset[i]

        # Format for RLM
        context, query = format_hotpotqa_for_rlm(example)

        print(f"\n📝 Question: {query}")
        print(f"📚 Context: {len(context)} documents")
        for key in context.keys():
            print(f"   - {key}")
        print(f"🎯 Gold Answer: {example['answer']}")

        # Run RLM
        print("\n🔄 Running RLM...")
        try:
            answer = client.completion(context, query)
            print(f"\n✅ RLM Answer: {answer}")

            # Evaluate
            metrics = evaluate_answer(answer, example['answer'])
            print(f"\n📊 Evaluation:")
            print(f"   Exact Match: {'✅' if metrics['exact_match'] else '❌'}")
            print(f"   Contains Answer: {'✅' if metrics['contains_answer'] else '❌'}")
            print(f"   F1 Score: {metrics['f1_score']:.2f}")

            results.append({
                'example_id': i,
                'question': query,
                'gold_answer': example['answer'],
                'rlm_answer': answer,
                'metrics': metrics
            })

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'example_id': i,
                'question': query,
                'gold_answer': example['answer'],
                'rlm_answer': None,
                'error': str(e)
            })

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    successful = [r for r in results if 'error' not in r]
    print(f"Completed: {len(successful)}/{num_examples}")

    if successful:
        avg_f1 = sum(r['metrics']['f1_score'] for r in successful) / len(successful)
        exact_matches = sum(1 for r in successful if r['metrics']['exact_match'])
        contains = sum(1 for r in successful if r['metrics']['contains_answer'])

        print(f"\nMetrics:")
        print(f"  Exact Match: {exact_matches}/{len(successful)} ({exact_matches/len(successful)*100:.1f}%)")
        print(f"  Contains Answer: {contains}/{len(successful)} ({contains/len(successful)*100:.1f}%)")
        print(f"  Average F1: {avg_f1:.3f}")

    # Save results
    output_file = f"hotpotqa_results_{start_idx}-{start_idx+num_examples}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test RLM with HotpotQA dataset")
    parser.add_argument('--num', type=int, default=3, help='Number of examples to test (default: 3)')
    parser.add_argument('--start', type=int, default=0, help='Starting index (default: 0)')

    args = parser.parse_args()

    print("="*80)
    print("HOTPOTQA TESTING WITH QUERY-DRIVEN ITERATIVE REFINEMENT")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Examples to test: {args.num}")
    print(f"  Starting index: {args.start}")
    print(f"  Model: gpt-4o-mini")
    print("\nNote: Each question takes ~30-60 seconds to process")
    print("="*80)

    run_hotpotqa_test(num_examples=args.num, start_idx=args.start)


if __name__ == "__main__":
    main()
