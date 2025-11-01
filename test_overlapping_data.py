"""
Test RLM with partially overlapping data for iterative refinement.

This test demonstrates:
1. Processing separate but overlapping data chunks
2. Using sub-RLM calls via llm_query() to analyze each chunk
3. Storing intermediate results in REPL variables
4. Combining results for best final answer
5. Built-in logger showing the process
"""

from rlm.rlm_repl import RLM_REPL


def create_overlapping_articles():
    """
    Create overlapping news articles about a tech conference.
    Each article has some unique info and some overlapping info.
    """

    article_1 = """
    TechConf 2025 Conference Report - Day 1

    The annual TechConf 2025 opened yesterday in San Francisco with over 5,000 attendees.
    The keynote speaker was Dr. Sarah Chen, who announced a breakthrough in quantum computing.
    She revealed that her team achieved 99.9% qubit stability at room temperature.

    The conference venue is the Moscone Center, featuring 12 simultaneous tracks.
    Notable sessions include "Future of AI" and "Quantum Breakthroughs".

    Conference dates: March 15-17, 2025
    Main sponsors: TechCorp, QuantumSys, and DataFlow Industries
    """

    article_2 = """
    TechConf 2025: Quantum Computing Breakthrough Announced

    Dr. Sarah Chen's keynote at TechConf 2025 made headlines with a major announcement.
    Her research team at QuantumLabs achieved 99.9% qubit stability at room temperature,
    a result that could revolutionize the quantum computing industry.

    The breakthrough uses a novel error-correction algorithm called "StableQ".
    Chen mentioned the research took 4 years and involved 25 scientists.
    The full paper will be published in Nature Quantum next month.

    Industry experts called it "the most significant quantum advancement in a decade."
    Potential applications include drug discovery and climate modeling.
    """

    article_3 = """
    TechConf 2025 Conference Schedule and Highlights

    The conference runs March 15-17, 2025 at the Moscone Center in San Francisco.
    Over 5,000 attendees registered, making it the largest TechConf to date.

    Day 1 Highlights:
    - Opening keynote by Dr. Sarah Chen on quantum computing
    - Panel discussion: "AI Ethics in 2025"
    - Workshop: "Hands-on Machine Learning"

    Day 2 Preview:
    - Keynote: "The Future of Sustainable Tech" by Prof. James Liu
    - 50+ technical sessions across 12 tracks
    - Networking reception sponsored by DataFlow Industries

    Day 3 Preview:
    - Closing keynote: "Next Decade of Innovation"
    - Award ceremony for best research papers

    Registration fee: $499 (early bird), $699 (regular)
    """

    # Return as a list of documents (overlapping data)
    return [
        {"source": "TechNews Daily", "content": article_1},
        {"source": "Quantum Computing Weekly", "content": article_2},
        {"source": "Conference Digest", "content": article_3},
    ]


def main():
    print("=" * 80)
    print("RLM TEST: Iterative Refinement with Overlapping Data")
    print("=" * 80)
    print()

    # Create RLM instance with logging enabled
    rlm = RLM_REPL(
        model="gpt-5-nano",  # Fast model for root planning
        recursive_model="gpt-5",  # Powerful model for sub-queries
        enable_logging=True,  # Enable built-in logger
        max_iterations=15,
    )

    # Create overlapping articles as context
    articles = create_overlapping_articles()

    # The query requires synthesizing information across overlapping articles
    query = """
    Based on the conference articles provided, create a comprehensive summary that includes:
    1. What was the main breakthrough announced?
    2. Who announced it and what are the technical details?
    3. What is the significance and potential applications?
    4. What are the conference logistics (dates, location, attendance)?

    Use sub-RLM calls to analyze each article separately, then combine the best information.
    """

    print("Context: 3 overlapping news articles about TechConf 2025")
    print(f"Query: {query[:150]}...")
    print()
    print("=" * 80)
    print("STARTING RLM PROCESSING (Watch the logger output below)")
    print("=" * 80)
    print()

    # Call RLM with articles as context
    result = rlm.completion(context=articles, query=query)

    print()
    print("=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(result)
    print()

    # Show cost summary
    cost = rlm.cost_summary()
    print("=" * 80)
    print("COST SUMMARY")
    print("=" * 80)
    print(f"Total Cost: ${cost.get('total_cost', 0):.4f}")
    print(f"Root Model Cost: ${cost.get('root_cost', 0):.4f}")
    print(f"Sub-LLM Cost: ${cost.get('sub_llm_cost', 0):.4f}")
    print()


if __name__ == "__main__":
    main()
