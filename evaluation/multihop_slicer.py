"""
Multi-hop context slicer for proper iterative refinement demonstration.

This slicer distributes supporting facts across different slices to force
multi-hop reasoning and demonstrate progressive quality improvement.
"""
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from evaluation.hotpotqa_loader import HotpotQAExample


@dataclass
class MultiHopSlice:
    """A slice containing sentences for multi-hop reasoning."""
    slice_id: str
    sentences: List[Tuple[str, str, int]]  # (sentence, doc_title, sent_idx)
    has_supporting_fact: bool
    supporting_fact_indices: List[int]  # Indices into supporting_facts list

    def get_content(self) -> str:
        """Get formatted content for this slice."""
        parts = []
        for sent, doc_title, _ in self.sentences:
            parts.append(f"[{doc_title}] {sent}")
        return "\n".join(parts)


def create_multihop_slices(example: HotpotQAExample, num_slices: int = 6) -> List[MultiHopSlice]:
    """
    Create slices that force multi-hop reasoning by distributing supporting facts.

    Strategy:
    1. Separate supporting facts from distractor sentences
    2. Place each supporting fact in a different slice
    3. Add distractors to each slice
    4. Early slices get mostly distractors (low quality)
    5. Middle slices get supporting facts (quality jumps)
    6. Late slices get remaining context (diminishing returns)

    Args:
        example: HotpotQA example
        num_slices: Number of slices to create

    Returns:
        List of MultiHopSlice objects
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
                'is_supporting': is_supporting
            })

    # Separate supporting and distractor sentences
    supporting_sentences = [s for s in all_sentences if s['is_supporting']]
    distractor_sentences = [s for s in all_sentences if not s['is_supporting']]

    print(f"📊 Sentence distribution:")
    print(f"   Supporting facts: {len(supporting_sentences)}")
    print(f"   Distractors: {len(distractor_sentences)}")

    # Create slices
    slices = []
    sentences_per_slice = max(1, len(all_sentences) // num_slices)

    # Distribute supporting facts across slices
    # Early slices: mostly distractors
    # Middle slices: supporting facts (this is where quality jumps!)
    # Late slices: remaining content

    num_supporting = len(supporting_sentences)

    for i in range(num_slices):
        slice_sentences = []
        supporting_fact_indices = []

        # Determine if this slice should get a supporting fact
        # Distribute them evenly across slices 2-5 (not first, not last)
        if num_supporting > 0 and 1 <= i < num_slices - 1:
            # Calculate which supporting fact goes here
            supporting_idx = (i - 1) * num_supporting // (num_slices - 2)
            if supporting_idx < num_supporting:
                sup_sent = supporting_sentences[supporting_idx]
                slice_sentences.append((sup_sent['text'], sup_sent['doc_title'], sup_sent['sent_idx']))
                supporting_fact_indices.append(supporting_idx)

        # Add distractors to fill the slice
        distractors_needed = sentences_per_slice - len(slice_sentences)
        start_idx = i * len(distractor_sentences) // num_slices
        end_idx = min(start_idx + distractors_needed, len(distractor_sentences))

        for dist_sent in distractor_sentences[start_idx:end_idx]:
            slice_sentences.append((dist_sent['text'], dist_sent['doc_title'], dist_sent['sent_idx']))

        # Create slice
        slice_obj = MultiHopSlice(
            slice_id=f"slice_{i+1}",
            sentences=slice_sentences,
            has_supporting_fact=len(supporting_fact_indices) > 0,
            supporting_fact_indices=supporting_fact_indices
        )

        slices.append(slice_obj)

        print(f"   Slice {i+1}: {len(slice_sentences)} sentences, supporting: {len(supporting_fact_indices)}")

    return slices


def create_progressive_slices(example: HotpotQAExample) -> List[MultiHopSlice]:
    """
    Create slices with controlled information release for 80/20 demonstration.

    Slice distribution strategy:
    - Slice 1 (0-17%): Pure distractors → F1 ~0.0
    - Slice 2 (17-33%): First supporting fact + distractors → F1 ~0.3-0.5
    - Slice 3 (33-50%): Second supporting fact + distractors → F1 ~0.6-0.8 ⚡
    - Slice 4 (50-67%): Third supporting fact + distractors → F1 ~0.9
    - Slice 5 (67-83%): Remaining distractors → F1 ~0.95
    - Slice 6 (83-100%): Final distractors → F1 ~1.0

    By 50% time, should have 70-80% quality (demonstrates 80/20)
    """
    all_sentences = []
    supporting_set = set(tuple(sf) for sf in example.supporting_facts)

    for doc_title, sentences in example.context:
        for sent_idx, sent in enumerate(sentences):
            is_supporting = (doc_title, sent_idx) in supporting_set
            all_sentences.append({
                'text': sent,
                'doc_title': doc_title,
                'sent_idx': sent_idx,
                'is_supporting': is_supporting
            })

    supporting = [s for s in all_sentences if s['is_supporting']]
    distractors = [s for s in all_sentences if not s['is_supporting']]

    slices = []

    # Slice 1: Pure distractors (0-17%)
    slice1_sents = [(d['text'], d['doc_title'], d['sent_idx']) for d in distractors[:2]]
    slices.append(MultiHopSlice(
        slice_id="slice_1_distractors",
        sentences=slice1_sents,
        has_supporting_fact=False,
        supporting_fact_indices=[]
    ))

    # Slices 2-4: Each gets one supporting fact (17-67%)
    for i, sup in enumerate(supporting[:3], start=2):
        slice_sents = [(sup['text'], sup['doc_title'], sup['sent_idx'])]

        # Add some distractors
        dist_start = i * 2
        dist_end = min(dist_start + 2, len(distractors))
        for d in distractors[dist_start:dist_end]:
            slice_sents.append((d['text'], d['doc_title'], d['sent_idx']))

        slices.append(MultiHopSlice(
            slice_id=f"slice_{i}_supporting_{i-1}",
            sentences=slice_sents,
            has_supporting_fact=True,
            supporting_fact_indices=[i-2]
        ))

    # Slices 5-6: Remaining content (67-100%)
    remaining_distractors = distractors[len(slices)*2:]
    mid_point = len(remaining_distractors) // 2

    if remaining_distractors:
        slices.append(MultiHopSlice(
            slice_id="slice_5_final_context",
            sentences=[(d['text'], d['doc_title'], d['sent_idx']) for d in remaining_distractors[:mid_point]],
            has_supporting_fact=False,
            supporting_fact_indices=[]
        ))

        slices.append(MultiHopSlice(
            slice_id="slice_6_final_context",
            sentences=[(d['text'], d['doc_title'], d['sent_idx']) for d in remaining_distractors[mid_point:]],
            has_supporting_fact=False,
            supporting_fact_indices=[]
        ))

    return slices


def print_slice_analysis(slices: List[MultiHopSlice]):
    """Print analysis of created slices."""
    print("\n📊 Slice Analysis:")
    print("="*80)

    for i, slice_obj in enumerate(slices):
        pct = (i + 1) / len(slices) * 100
        print(f"\n{slice_obj.slice_id} ({pct:.0f}% mark):")
        print(f"  Sentences: {len(slice_obj.sentences)}")
        print(f"  Has supporting fact: {'✅' if slice_obj.has_supporting_fact else '❌'}")
        print(f"  Content preview:")
        for sent, doc, _ in slice_obj.sentences[:2]:  # Show first 2
            print(f"    [{doc}] {sent[:60]}...")
        if len(slice_obj.sentences) > 2:
            print(f"    ... ({len(slice_obj.sentences) - 2} more)")

    print("="*80)
