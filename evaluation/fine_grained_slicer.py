"""
Fine-grained context slicer for smooth F1 convergence demonstration.

Creates 10-15 small slices with progressive information release to show
gradual quality improvement rather than sudden jumps.
"""
from typing import List
from evaluation.hotpotqa_loader import HotpotQAExample
from evaluation.cumulative_refinement import RefinementSlice


def create_fine_grained_slices(
    example: HotpotQAExample,
    num_slices: int = 12
) -> List[RefinementSlice]:
    """
    Create fine-grained slices for smooth convergence.

    Strategy:
    - Extract all sentences
    - Separate supporting facts from distractors
    - Distribute supporting facts evenly across middle slices (30-70%)
    - Early slices (0-30%): mostly distractors, some context setting
    - Middle slices (30-70%): supporting facts gradually revealed
    - Late slices (70-100%): remaining distractors, verification

    Expected F1 progression:
    - 0-20%: F1 ~0.0-0.2 (exploring)
    - 20-40%: F1 ~0.2-0.5 (first hops)
    - 40-60%: F1 ~0.5-0.8 (connecting hops) ← Most value!
    - 60-80%: F1 ~0.8-0.95 (refinement)
    - 80-100%: F1 ~0.95-1.0 (polish)
    """

    # Extract all sentences with metadata
    all_sentences = []
    supporting_set = set(tuple(sf) for sf in example.supporting_facts)

    for doc_title, sentences in example.context:
        for sent_idx, sent in enumerate(sentences):
            is_supporting = (doc_title, sent_idx) in supporting_set
            all_sentences.append({
                'text': sent,
                'doc_title': doc_title,
                'sent_idx': sent_idx,
                'is_supporting': is_supporting,
                'supporting_idx': list(supporting_set).index((doc_title, sent_idx)) if is_supporting else None
            })

    # Separate
    supporting = [s for s in all_sentences if s['is_supporting']]
    distractors = [s for s in all_sentences if not s['is_supporting']]

    print(f"\n📊 Slicing strategy:")
    print(f"   Total sentences: {len(all_sentences)}")
    print(f"   Supporting facts: {len(supporting)}")
    print(f"   Distractors: {len(distractors)}")
    print(f"   Creating {num_slices} fine-grained slices\n")

    slices = []

    # Calculate slice boundaries for progressive release
    # Supporting facts should appear in slices 3-8 (25-75% range)
    supporting_start_slice = max(2, num_slices // 4)  # ~25%
    supporting_end_slice = min(num_slices - 2, 3 * num_slices // 4)  # ~75%

    supporting_slot_count = supporting_end_slice - supporting_start_slice + 1
    supporting_per_slot = max(1, len(supporting) // supporting_slot_count)

    supporting_used = 0

    for i in range(num_slices):
        slice_sentences = []
        has_supporting = False

        # Determine if this slice gets supporting facts
        if supporting_start_slice <= i <= supporting_end_slice and supporting_used < len(supporting):
            # Add 1-2 supporting facts to this slice
            num_supporting_here = min(supporting_per_slot, len(supporting) - supporting_used)

            for j in range(num_supporting_here):
                if supporting_used < len(supporting):
                    sup = supporting[supporting_used]
                    slice_sentences.append(f"[{sup['doc_title']}] {sup['text']}")
                    has_supporting = True
                    supporting_used += 1

        # Add distractors to fill the slice
        # Distribute distractors across all slices
        distractor_per_slice = max(1, len(distractors) // num_slices)
        start_idx = i * len(distractors) // num_slices
        end_idx = min(start_idx + distractor_per_slice, len(distractors))

        for dist in distractors[start_idx:end_idx]:
            slice_sentences.append(f"[{dist['doc_title']}] {dist['text']}")

        # Create slice
        content = "\n".join(slice_sentences) if slice_sentences else "[No new information]"

        slice_obj = RefinementSlice(
            slice_id=f"slice_{i+1:02d}",
            content=content,
            has_supporting_fact=has_supporting
        )

        slices.append(slice_obj)

        # Print slice info
        pct = (i + 1) / num_slices * 100
        supporting_mark = "✓" if has_supporting else " "
        print(f"   Slice {i+1:2d} ({pct:5.1f}%) [{supporting_mark}] {len(slice_sentences):2d} sentences")

    print()
    return slices


def analyze_slice_distribution(slices: List[RefinementSlice]):
    """Analyze the distribution of supporting facts across slices."""
    print("\n📊 Supporting Fact Distribution:")
    print("-"*80)

    supporting_slices = [i+1 for i, s in enumerate(slices) if s.has_supporting_fact]

    if supporting_slices:
        print(f"Supporting facts appear in slices: {supporting_slices}")
        print(f"First supporting fact at: {supporting_slices[0]}/{len(slices)} ({supporting_slices[0]/len(slices)*100:.1f}%)")
        print(f"Last supporting fact at: {supporting_slices[-1]}/{len(slices)} ({supporting_slices[-1]/len(slices)*100:.1f}%)")
        print(f"Concentration: {supporting_slices[0]/len(slices)*100:.0f}%-{supporting_slices[-1]/len(slices)*100:.0f}% range")

    print("-"*80)


if __name__ == "__main__":
    from evaluation.real_hotpotqa_examples import create_hard_hotpotqa_examples

    examples = create_hard_hotpotqa_examples()

    for example in examples[:1]:  # Test first example
        print(f"\nExample: {example.question}")
        print(f"Answer: {example.answer}")

        slices = create_fine_grained_slices(example, num_slices=12)
        analyze_slice_distribution(slices)

        print(f"\nSample slices:")
        for i in [0, 3, 6, 9, 11]:  # Show representative slices
            print(f"\n--- Slice {i+1} ---")
            print(slices[i].content[:200])
