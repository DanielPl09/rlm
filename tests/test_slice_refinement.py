"""
Unit tests for query-driven iterative refinement with context slicing.
"""

import unittest
from rlm.utils.context_slicer import ContextSlicer, ContextSlice


class TestContextSlice(unittest.TestCase):
    """Test ContextSlice class."""

    def test_context_slice_creation(self):
        """Test creating a context slice."""
        slice_obj = ContextSlice("test_id", "test content", {"type": "test"})
        self.assertEqual(slice_obj.slice_id, "test_id")
        self.assertEqual(slice_obj.content, "test content")
        self.assertEqual(slice_obj.metadata["type"], "test")

    def test_context_slice_repr(self):
        """Test ContextSlice string representation."""
        slice_obj = ContextSlice("test_id", "short content", {})
        repr_str = repr(slice_obj)
        self.assertIn("test_id", repr_str)
        self.assertIn("short content", repr_str)


class TestContextSlicer(unittest.TestCase):
    """Test ContextSlicer class."""

    def test_add_and_get_slice(self):
        """Test adding and retrieving slices."""
        slicer = ContextSlicer()
        slicer.add_slice("slice1", "content1", {"type": "doc"})
        slicer.add_slice("slice2", "content2", {"type": "code"})

        self.assertEqual(len(slicer.slices), 2)
        slice1 = slicer.get_slice("slice1")
        self.assertIsNotNone(slice1)
        self.assertEqual(slice1.content, "content1")

    def test_list_slices(self):
        """Test listing slice IDs."""
        slicer = ContextSlicer()
        slicer.add_slice("slice1", "content1")
        slicer.add_slice("slice2", "content2")

        slice_ids = slicer.list_slices()
        self.assertEqual(len(slice_ids), 2)
        self.assertIn("slice1", slice_ids)
        self.assertIn("slice2", slice_ids)

    def test_get_slice_info(self):
        """Test getting slice information."""
        slicer = ContextSlicer()
        slicer.add_slice("slice1", "content1", {"category": "docs"})

        info = slicer.get_slice_info()
        self.assertEqual(len(info), 1)
        self.assertEqual(info[0]["slice_id"], "slice1")
        self.assertEqual(info[0]["metadata"]["category"], "docs")
        self.assertEqual(info[0]["content_type"], "str")

    def test_auto_slice_dict(self):
        """Test auto-slicing a dictionary context."""
        context = {
            "introduction": "Intro text",
            "methodology": "Method text",
            "results": "Results text"
        }

        slices = ContextSlicer.auto_slice_context(context)
        self.assertEqual(len(slices), 3)
        self.assertIn("dict_introduction", slices)
        self.assertIn("dict_methodology", slices)
        self.assertIn("dict_results", slices)

        # Check content
        intro_slice = slices["dict_introduction"]
        self.assertEqual(intro_slice.content, "Intro text")
        self.assertEqual(intro_slice.metadata["type"], "dict_value")

    def test_auto_slice_small_list(self):
        """Test auto-slicing a small list (individual items)."""
        context = ["item1", "item2", "item3"]

        slices = ContextSlicer.auto_slice_context(context)
        self.assertEqual(len(slices), 3)
        self.assertIn("item_0", slices)
        self.assertIn("item_1", slices)
        self.assertIn("item_2", slices)

        # Check content and metadata
        item0 = slices["item_0"]
        self.assertEqual(item0.content, "item1")
        self.assertEqual(item0.metadata["type"], "list_item")
        self.assertEqual(item0.metadata["index"], 0)

    def test_auto_slice_large_list(self):
        """Test auto-slicing a large list (chunked)."""
        context = [f"item{i}" for i in range(25)]

        slices = ContextSlicer.auto_slice_context(context)
        # Should create 3 chunks: [0-9], [10-19], [20-24]
        self.assertEqual(len(slices), 3)
        self.assertIn("chunk_0", slices)
        self.assertIn("chunk_1", slices)
        self.assertIn("chunk_2", slices)

        # Check first chunk
        chunk0 = slices["chunk_0"]
        self.assertEqual(len(chunk0.content), 10)
        self.assertEqual(chunk0.metadata["type"], "list_chunk")
        self.assertEqual(chunk0.metadata["start_index"], 0)
        self.assertEqual(chunk0.metadata["end_index"], 10)

        # Check last chunk
        chunk2 = slices["chunk_2"]
        self.assertEqual(len(chunk2.content), 5)
        self.assertEqual(chunk2.metadata["start_index"], 20)
        self.assertEqual(chunk2.metadata["end_index"], 25)

    def test_auto_slice_markdown_string(self):
        """Test auto-slicing a markdown string."""
        context = """
# Introduction
This is the introduction.

## Background
Background information here.

# Conclusion
Final thoughts.
"""

        slices = ContextSlicer.auto_slice_context(context)
        # Should find markdown sections
        self.assertGreater(len(slices), 0)

        # Check that section IDs are created
        slice_ids = list(slices.keys())
        self.assertTrue(any("section_" in sid for sid in slice_ids))

    def test_auto_slice_plain_string(self):
        """Test auto-slicing a plain string (no markdown)."""
        # Create a long string that will be chunked
        context = "a" * 25000  # 25k characters

        slices = ContextSlicer.auto_slice_context(context)
        # Should create 3 chunks of ~10k chars each
        self.assertEqual(len(slices), 3)

        # Check chunk metadata
        chunk0 = slices["chunk_0"]
        self.assertEqual(chunk0.metadata["type"], "string_chunk")
        self.assertEqual(chunk0.metadata["start_char"], 0)
        self.assertEqual(len(chunk0.content), 10000)


class TestSubRLMSlicing(unittest.TestCase):
    """Test Sub_RLM slice integration."""

    def test_sub_rlm_accepts_slices(self):
        """Test that Sub_RLM can be initialized with context slices."""
        # Skip if no API key (just test initialization structure)
        import os
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set")

        from rlm.repl import Sub_RLM
        from rlm.utils.context_slicer import ContextSlicer

        context = {"doc1": "content1"}
        slices = ContextSlicer.auto_slice_context(context)

        # Should not raise an error
        sub_rlm = Sub_RLM(model="gpt-4o-mini", context_slices=slices)
        self.assertIsNotNone(sub_rlm)
        self.assertEqual(len(sub_rlm.context_slices), 1)


if __name__ == "__main__":
    unittest.main()
