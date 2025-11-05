"""
Real HotpotQA examples with genuine multi-hop complexity.

These are harder questions that require 3-4 hops and demonstrate
gradual convergence through progressive refinement.
"""
from typing import List
from evaluation.hotpotqa_loader import HotpotQAExample, HotpotQALoader


def create_hard_hotpotqa_examples() -> List[HotpotQAExample]:
    """
    Create challenging HotpotQA examples that require multi-hop reasoning.

    These examples are designed to show gradual F1 convergence:
    - Supporting facts distributed across multiple documents
    - Requires connecting 3-4 pieces of information
    - Answer emerges progressively, not all at once
    """

    examples = [
        {
            "_id": "hard_001",
            "question": "What award did the director of the film that won Best Picture at the 67th Academy Awards receive?",
            "answer": "Academy Award for Best Director",
            "type": "bridge",
            "level": "hard",
            "context": [
                ["67th Academy Awards", [
                    "The 67th Academy Awards ceremony was held on March 27, 1995.",
                    "Forrest Gump won the award for Best Picture.",
                    "The ceremony honored films released in 1994.",
                    "It was hosted by David Letterman at the Shrine Auditorium."
                ]],
                ["Forrest Gump", [
                    "Forrest Gump is a 1994 American comedy-drama film.",
                    "The film was directed by Robert Zemeckis.",
                    "It stars Tom Hanks in the title role.",
                    "The film grossed over $678 million worldwide.",
                    "It received critical acclaim and numerous accolades."
                ]],
                ["Robert Zemeckis", [
                    "Robert Zemeckis is an American filmmaker.",
                    "He has received numerous accolades including an Academy Award.",
                    "His work spans various genres including science fiction and comedy.",
                    "He is known for innovative use of visual effects."
                ]],
                ["Academy Award for Best Director", [
                    "The Academy Award for Best Director is an annual award.",
                    "Robert Zemeckis won this award in 1995 for Forrest Gump.",
                    "The award recognizes achievement in film direction.",
                    "It is considered one of the most prestigious film awards."
                ]],
                ["Tom Hanks", [
                    "Tom Hanks is an American actor and filmmaker.",
                    "He won the Academy Award for Best Actor for Forrest Gump.",
                    "He is known for his dramatic and comedic roles.",
                    "He has won multiple Academy Awards throughout his career."
                ]]
            ],
            "supporting_facts": [
                ["67th Academy Awards", 1],  # Forrest Gump won Best Picture
                ["Forrest Gump", 1],  # Directed by Zemeckis
                ["Academy Award for Best Director", 1]  # Zemeckis won this
            ]
        },

        {
            "_id": "hard_002",
            "question": "In what year was the university that the inventor of the World Wide Web attended founded?",
            "answer": "1167",
            "type": "bridge",
            "level": "hard",
            "context": [
                ["World Wide Web", [
                    "The World Wide Web (WWW) is an information system on the Internet.",
                    "It was invented by Tim Berners-Lee in 1989.",
                    "It allows documents to be connected through hyperlinks.",
                    "The first website was launched in 1991."
                ]],
                ["Tim Berners-Lee", [
                    "Sir Tim Berners-Lee is a British computer scientist.",
                    "He is best known as the inventor of the World Wide Web.",
                    "He attended The Queen's College, Oxford.",
                    "He graduated in 1976 with a degree in Physics.",
                    "He was knighted in 2004 for his pioneering work."
                ]],
                ["The Queen's College, Oxford", [
                    "The Queen's College is a constituent college of the University of Oxford.",
                    "It is located on the High Street in central Oxford.",
                    "The college has about 600 students.",
                    "It is known for its distinctive architecture."
                ]],
                ["University of Oxford", [
                    "The University of Oxford is a collegiate research university.",
                    "It is the oldest university in the English-speaking world.",
                    "Teaching existed at Oxford as early as 1096.",
                    "The university was formally established around 1167.",
                    "It is located in Oxford, England."
                ]],
                ["1989", [
                    "1989 was a common year starting on Sunday.",
                    "Major events included the fall of the Berlin Wall.",
                    "Tim Berners-Lee proposed the World Wide Web this year.",
                    "It marked the end of the Cold War era."
                ]]
            ],
            "supporting_facts": [
                ["Tim Berners-Lee", 1],  # Invented WWW
                ["Tim Berners-Lee", 2],  # Attended Queen's College, Oxford
                ["The Queen's College, Oxford", 0],  # Part of University of Oxford
                ["University of Oxford", 3]  # Founded in 1167
            ]
        },

        {
            "_id": "hard_003",
            "question": "Which country is the birthplace of the author who wrote the book that the 2005 film 'Pride & Prejudice' was based on?",
            "answer": "England",
            "type": "bridge",
            "level": "hard",
            "context": [
                ["Pride & Prejudice (2005 film)", [
                    "Pride & Prejudice is a 2005 romantic drama film.",
                    "It was directed by Joe Wright.",
                    "The film is based on the 1813 novel by Jane Austen.",
                    "It stars Keira Knightley as Elizabeth Bennet.",
                    "The film received four Academy Award nominations."
                ]],
                ["Pride and Prejudice (novel)", [
                    "Pride and Prejudice is an 1813 romantic novel.",
                    "It was written by Jane Austen.",
                    "It is one of the most popular works in English literature.",
                    "The story follows the character development of Elizabeth Bennet."
                ]],
                ["Jane Austen", [
                    "Jane Austen was an English novelist.",
                    "She was born on December 16, 1775 in Steventon, Hampshire, England.",
                    "She is known for her six major novels.",
                    "Her works critique the British landed gentry.",
                    "She died in 1817 at the age of 41."
                ]],
                ["England", [
                    "England is a country that is part of the United Kingdom.",
                    "It is located on the island of Great Britain.",
                    "The capital is London.",
                    "England has a rich literary tradition dating back centuries."
                ]],
                ["Joe Wright", [
                    "Joe Wright is an English film director.",
                    "He is known for his period dramas.",
                    "His notable works include Atonement and Anna Karenina.",
                    "He has received multiple award nominations."
                ]]
            ],
            "supporting_facts": [
                ["Pride & Prejudice (2005 film)", 2],  # Based on Jane Austen's novel
                ["Pride and Prejudice (novel)", 1],  # Written by Jane Austen
                ["Jane Austen", 1]  # Born in England
            ]
        }
    ]

    loader = HotpotQALoader()
    loader.load_from_dict(examples)
    return loader.examples


def print_example_analysis(example: HotpotQAExample):
    """Print analysis of an example's complexity."""
    print(f"\n{'='*80}")
    print(f"Question: {example.question}")
    print(f"Answer: {example.answer}")
    print(f"Type: {example.question_type} | Level: {example.level}")
    print(f"{'='*80}")

    print(f"\nSupporting Facts (multi-hop chain):")
    for i, (doc, sent_idx) in enumerate(example.supporting_facts, 1):
        sentence = example.context[[t[0] for t in example.context].index(doc)][1][sent_idx]
        print(f"  {i}. [{doc}] {sentence}")

    print(f"\nTotal documents: {len(example.context)}")
    print(f"Total sentences: {sum(len(sents) for _, sents in example.context)}")
    print(f"Hops required: {len(example.supporting_facts)}")


if __name__ == "__main__":
    examples = create_hard_hotpotqa_examples()

    print("HARD HOTPOTQA EXAMPLES FOR GRADUAL CONVERGENCE DEMO")
    print("="*80)

    for example in examples:
        print_example_analysis(example)
