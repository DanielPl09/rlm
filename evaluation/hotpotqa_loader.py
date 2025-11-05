"""
HotpotQA dataset loader for iterative refinement evaluation.
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HotpotQAExample:
    """Single HotpotQA example."""
    question: str
    answer: str
    context: List[tuple]  # List of (title, sentences) tuples
    supporting_facts: List[tuple]  # List of (title, sentence_idx) tuples
    example_id: str
    level: str  # 'easy', 'medium', 'hard'
    question_type: str  # 'comparison', 'bridge', etc.

    def get_context_dict(self) -> Dict[str, Any]:
        """
        Format context as a dictionary suitable for RLM.

        Returns:
            Dictionary where keys are document titles and values are the content.
        """
        context_dict = {}

        for title, sentences in self.context:
            # Join sentences into a single passage
            if isinstance(sentences, list):
                content = ' '.join(sentences)
            else:
                content = sentences

            context_dict[title] = content

        return context_dict

    def get_context_text(self) -> str:
        """
        Format context as a single text string.

        Returns:
            All context concatenated with document separators.
        """
        parts = []

        for title, sentences in self.context:
            if isinstance(sentences, list):
                content = ' '.join(sentences)
            else:
                content = sentences

            parts.append(f"=== {title} ===\n{content}")

        return '\n\n'.join(parts)

    def get_supporting_context(self) -> Dict[str, Any]:
        """
        Get only the supporting (gold) context.

        Returns:
            Dictionary with only the documents that contain supporting facts.
        """
        supporting_titles = set(title for title, _ in self.supporting_facts)
        context_dict = {}

        for title, sentences in self.context:
            if title in supporting_titles:
                if isinstance(sentences, list):
                    content = ' '.join(sentences)
                else:
                    content = sentences

                context_dict[title] = content

        return context_dict


class HotpotQALoader:
    """Loader for HotpotQA dataset."""

    def __init__(self, file_path: Optional[str] = None):
        """
        Initialize loader.

        Args:
            file_path: Path to HotpotQA JSON file (optional)
        """
        self.file_path = file_path
        self.examples: List[HotpotQAExample] = []

        if file_path:
            self.load(file_path)

    def load(self, file_path: str):
        """Load HotpotQA dataset from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.examples = []

        for item in data:
            example = HotpotQAExample(
                question=item['question'],
                answer=item['answer'],
                context=item['context'],
                supporting_facts=item.get('supporting_facts', []),
                example_id=item.get('_id', ''),
                level=item.get('level', 'unknown'),
                question_type=item.get('type', 'unknown')
            )
            self.examples.append(example)

    def load_from_dict(self, data: List[Dict[str, Any]]):
        """Load examples from a list of dictionaries."""
        self.examples = []

        for item in data:
            example = HotpotQAExample(
                question=item['question'],
                answer=item['answer'],
                context=item['context'],
                supporting_facts=item.get('supporting_facts', []),
                example_id=item.get('_id', str(len(self.examples))),
                level=item.get('level', 'unknown'),
                question_type=item.get('type', 'unknown')
            )
            self.examples.append(example)

    def get_example(self, idx: int) -> HotpotQAExample:
        """Get example by index."""
        return self.examples[idx]

    def get_examples(self, start: int = 0, end: Optional[int] = None) -> List[HotpotQAExample]:
        """Get a range of examples."""
        if end is None:
            end = len(self.examples)
        return self.examples[start:end]

    def filter_by_level(self, level: str) -> List[HotpotQAExample]:
        """Get examples of a specific difficulty level."""
        return [ex for ex in self.examples if ex.level == level]

    def filter_by_type(self, question_type: str) -> List[HotpotQAExample]:
        """Get examples of a specific question type."""
        return [ex for ex in self.examples if ex.question_type == question_type]

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> HotpotQAExample:
        return self.examples[idx]


def create_sample_examples() -> List[HotpotQAExample]:
    """
    Create sample HotpotQA examples for testing.

    Returns:
        List of sample examples with realistic multi-hop questions.
    """
    samples = [
        {
            "_id": "sample_001",
            "question": "What is the capital of the country where the Eiffel Tower is located?",
            "answer": "Paris",
            "type": "bridge",
            "level": "easy",
            "context": [
                ["Eiffel Tower", ["The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, France.",
                                  "It is named after the engineer Gustave Eiffel.",
                                  "The tower is 324 metres tall."]],
                ["Paris", ["Paris is the capital and most populous city of France.",
                          "Since the 17th century, Paris has been one of Europe's major centres of finance, diplomacy, commerce, fashion, science and arts.",
                          "The City of Paris has a population of 2.1 million."]],
                ["France", ["France is a country in Western Europe.",
                           "Its capital is Paris.",
                           "France is the largest country in the European Union."]]
            ],
            "supporting_facts": [["Eiffel Tower", 0], ["France", 1]]
        },
        {
            "_id": "sample_002",
            "question": "Which company did the creator of SpaceX found before Tesla?",
            "answer": "PayPal",
            "type": "bridge",
            "level": "medium",
            "context": [
                ["SpaceX", ["SpaceX is an American aerospace manufacturer and space transportation company.",
                           "It was founded in 2002 by Elon Musk.",
                           "The company has developed the Falcon 9 rocket."]],
                ["Elon Musk", ["Elon Musk is a business magnate and entrepreneur.",
                              "He co-founded PayPal in 1999.",
                              "Later he founded SpaceX in 2002 and joined Tesla Motors in 2004.",
                              "He became CEO of Tesla in 2008."]],
                ["Tesla Inc", ["Tesla Inc is an American electric vehicle and clean energy company.",
                              "It was founded in 2003 by Martin Eberhard and Marc Tarpenning.",
                              "Elon Musk joined in 2004 as chairman."]],
                ["PayPal", ["PayPal is an American company operating a worldwide online payments system.",
                           "It was established in 1998 as Confinity.",
                           "The company was co-founded by Max Levchin, Peter Thiel, and Elon Musk among others."]]
            ],
            "supporting_facts": [["SpaceX", 1], ["Elon Musk", 1], ["Elon Musk", 2]]
        },
        {
            "_id": "sample_003",
            "question": "How many Academy Awards did the director of Inception win?",
            "answer": "1",
            "type": "bridge",
            "level": "medium",
            "context": [
                ["Inception", ["Inception is a 2010 science fiction action film.",
                              "It was written and directed by Christopher Nolan.",
                              "The film stars Leonardo DiCaprio as a professional thief."]],
                ["Christopher Nolan", ["Christopher Nolan is a British-American film director, producer, and screenwriter.",
                                      "He has received numerous accolades including an Academy Award.",
                                      "His films have grossed over $5 billion worldwide."]],
                ["Academy Awards", ["The Academy Awards, also known as the Oscars, are awards for artistic and technical merit in film.",
                                   "They are presented annually by the Academy of Motion Picture Arts and Sciences."]]
            ],
            "supporting_facts": [["Inception", 1], ["Christopher Nolan", 1]]
        }
    ]

    loader = HotpotQALoader()
    loader.load_from_dict(samples)

    return loader.examples
