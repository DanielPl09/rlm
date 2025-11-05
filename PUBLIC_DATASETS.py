"""
Public datasets suitable for testing query-driven iterative refinement.
These datasets have multi-document contexts requiring synthesis.
"""

# ============================================================================
# RECOMMENDED PUBLIC DATASETS
# ============================================================================

"""
1. HotpotQA (Best Match - Multi-hop QA)
   - URL: https://hotpotqa.github.io/
   - Structure: Questions with 2-10 supporting Wikipedia paragraphs
   - Why good: Explicitly requires multi-document reasoning
   - Size: ~113K questions
   - Format: JSON with question + multiple context paragraphs
   - Example:
     {
       "question": "Which magazine was started first, Arthur's Magazine or First for Women?",
       "context": [
         ["Arthur's Magazine", "Arthur's Magazine (1844-1846) was an American..."],
         ["First for Women", "First for Women is a woman's magazine published..."]
       ],
       "answer": "Arthur's Magazine"
     }

2. MultiNews (Multi-document Summarization)
   - URL: https://github.com/Alex-Fabbri/Multi-News
   - Structure: News articles from multiple sources about same event
   - Why good: Requires aggregating info from multiple sources
   - Size: ~56K article clusters
   - Format: Multiple articles → summary

3. MS MARCO (Microsoft Machine Reading Comprehension)
   - URL: https://microsoft.github.io/msmarco/
   - Structure: Web search results (multiple passages) → answer
   - Why good: Multiple retrieved passages per question
   - Size: ~1M queries
   - Format: Query + 10 passages + answer

4. ELI5 (Explain Like I'm 5)
   - URL: https://facebookresearch.github.io/ELI5/
   - Structure: Reddit questions + multiple comment explanations
   - Why good: Multiple perspectives on same question
   - Size: ~270K questions
   - Format: Question + multiple reddit comments/sources

5. QASPER (Question Answering on Scientific Papers)
   - URL: https://allenai.org/data/qasper
   - Structure: Scientific papers (abstract, sections) + questions
   - Why good: Natural multi-section document structure
   - Size: ~1,585 papers, 5,049 questions
   - Format: Paper sections + question + answer
"""

# ============================================================================
# DATASET CHARACTERISTICS COMPARISON
# ============================================================================

DATASET_STATS = {
    "HotpotQA": {
        "sections_per_query": "2-10 paragraphs",
        "avg_section_length": "~100-300 words",
        "requires_synthesis": True,
        "domain": "Wikipedia (general knowledge)",
        "difficulty": "Medium",
        "recommended": "⭐⭐⭐⭐⭐ BEST MATCH"
    },
    "MultiNews": {
        "sections_per_query": "2-10 articles",
        "avg_section_length": "~200-500 words",
        "requires_synthesis": True,
        "domain": "News",
        "difficulty": "Medium-Hard",
        "recommended": "⭐⭐⭐⭐"
    },
    "MS MARCO": {
        "sections_per_query": "10 passages",
        "avg_section_length": "~50-200 words",
        "requires_synthesis": True,
        "domain": "Web search",
        "difficulty": "Medium",
        "recommended": "⭐⭐⭐⭐"
    },
    "QASPER": {
        "sections_per_query": "5-10 paper sections",
        "avg_section_length": "~200-1000 words",
        "requires_synthesis": True,
        "domain": "Scientific papers",
        "difficulty": "Hard",
        "recommended": "⭐⭐⭐"
    }
}

# ============================================================================
# EXAMPLE: HOTPOTQA (RECOMMENDED)
# ============================================================================

HOTPOTQA_EXAMPLE = {
    "query": "Which magazine was started first, Arthur's Magazine or First for Women?",

    "context": {
        "arthurs_magazine": """Arthur's Magazine (1844–1846) was an American literary
        periodical published in Philadelphia in the 19th century. It was edited by
        Timothy Shay Arthur and published by T.S. Arthur & Co. The magazine featured
        essays, stories, and poetry, focused on moral and social issues.""",

        "first_for_women": """First for Women is a woman's magazine published by
        Bauer Media Group in the USA. The magazine was started in 1989. It is based
        in Englewood Cliffs, New Jersey. The magazine has a circulation of 1.3 million
        readers."""
    },

    "expected_answer": "Arthur's Magazine (started 1844, First for Women started 1989)"
}

# ============================================================================
# DOWNLOAD INSTRUCTIONS
# ============================================================================

DOWNLOAD_HOTPOTQA = """
# Option 1: Direct download
wget http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json

# Option 2: Using datasets library
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('hotpot_qa', 'distractor'); print(ds)"

# Option 3: Git clone
git clone https://github.com/hotpotqa/hotpot.git
cd hotpot/data
# Download from the links in README
"""

DOWNLOAD_MSMARCO = """
# Using datasets library (easiest)
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('ms_marco', 'v2.1'); print(ds)"
"""

DOWNLOAD_MULTINEWS = """
# Using datasets library
pip install datasets
python -c "from datasets import load_dataset; ds = load_dataset('multi_news'); print(ds)"
"""

# ============================================================================
# WHY HOTPOTQA IS THE BEST MATCH
# ============================================================================

"""
HotpotQA matches our test characteristics perfectly:

✅ Multi-document structure: 2-10 supporting paragraphs per question
✅ Requires synthesis: Answer needs info from multiple paragraphs
✅ Clear sections: Each paragraph is a distinct "slice"
✅ Reasonable size: Not too large (can test on subset)
✅ Well-studied: Established benchmark, easy to compare
✅ Publicly available: Free download, no signup needed
✅ JSON format: Easy to parse and use
✅ Similar to our tests: Like product analysis with user_reviews + specs + tickets

Example mapping:
  user_reviews → Wikipedia article 1
  technical_specs → Wikipedia article 2
  support_tickets → Wikipedia article 3
"""

if __name__ == "__main__":
    print("="*80)
    print("RECOMMENDED PUBLIC DATASETS FOR ITERATIVE REFINEMENT TESTING")
    print("="*80)

    print("\n🏆 TOP RECOMMENDATION: HotpotQA")
    print("-" * 80)
    print("Why: Multi-document QA explicitly requiring synthesis")
    print("URL: https://hotpotqa.github.io/")
    print("\nExample structure:")
    print(f"  Query: {HOTPOTQA_EXAMPLE['query']}")
    print(f"  Context sections: {len(HOTPOTQA_EXAMPLE['context'])}")
    for key, val in HOTPOTQA_EXAMPLE['context'].items():
        print(f"    - {key}: {val[:80]}...")

    print("\n" + "="*80)
    print("DOWNLOAD HOTPOTQA:")
    print("="*80)
    print(DOWNLOAD_HOTPOTQA)

    print("\n" + "="*80)
    print("ALTERNATIVE DATASETS:")
    print("="*80)
    for name, stats in DATASET_STATS.items():
        print(f"\n{name}: {stats['recommended']}")
        for key, val in stats.items():
            if key != 'recommended':
                print(f"  {key}: {val}")
