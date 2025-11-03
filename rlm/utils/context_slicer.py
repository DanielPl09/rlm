"""
Context slicing utilities for pre-segmenting context into chunks.
"""

from typing import Dict, List, Any, Optional
import json


class ContextSlice:
    """Represents a single slice of context with metadata."""

    def __init__(self, slice_id: str, content: Any, metadata: Optional[Dict] = None):
        self.slice_id = slice_id
        self.content = content
        self.metadata = metadata or {}

    def __repr__(self):
        content_preview = str(self.content)[:100] + "..." if len(str(self.content)) > 100 else str(self.content)
        return f"ContextSlice(id='{self.slice_id}', content='{content_preview}', metadata={self.metadata})"


class ContextSlicer:
    """
    Pre-segments context into named chunks that can be queried independently.
    """

    def __init__(self):
        self.slices: Dict[str, ContextSlice] = {}

    def add_slice(self, slice_id: str, content: Any, metadata: Optional[Dict] = None):
        """Add a pre-segmented context slice."""
        self.slices[slice_id] = ContextSlice(slice_id, content, metadata)

    def get_slice(self, slice_id: str) -> Optional[ContextSlice]:
        """Retrieve a specific context slice by ID."""
        return self.slices.get(slice_id)

    def list_slices(self) -> List[str]:
        """List all available slice IDs."""
        return list(self.slices.keys())

    def get_slice_info(self) -> List[Dict[str, Any]]:
        """Get information about all slices."""
        return [
            {
                "slice_id": slice_id,
                "metadata": slice_obj.metadata,
                "content_type": type(slice_obj.content).__name__,
                "content_size": len(str(slice_obj.content))
            }
            for slice_id, slice_obj in self.slices.items()
        ]

    @staticmethod
    def auto_slice_context(context: Any, strategy: str = "auto") -> Dict[str, ContextSlice]:
        """
        Automatically slice context based on structure.

        Args:
            context: The context to slice (dict, list, or str)
            strategy: Slicing strategy - "auto", "dict_keys", "list_chunks", "markdown_sections"

        Returns:
            Dictionary mapping slice_id to ContextSlice
        """
        slices = {}

        if isinstance(context, dict):
            # Slice by dictionary keys
            for key, value in context.items():
                slice_id = f"dict_{key}"
                slices[slice_id] = ContextSlice(
                    slice_id,
                    value,
                    metadata={"type": "dict_value", "key": key}
                )

        elif isinstance(context, list):
            # Slice into chunks or individual items
            if len(context) <= 10:
                # Small list - slice by items
                for idx, item in enumerate(context):
                    slice_id = f"item_{idx}"
                    slices[slice_id] = ContextSlice(
                        slice_id,
                        item,
                        metadata={"type": "list_item", "index": idx}
                    )
            else:
                # Large list - slice into chunks of 10
                chunk_size = 10
                for i in range(0, len(context), chunk_size):
                    chunk = context[i:i+chunk_size]
                    slice_id = f"chunk_{i//chunk_size}"
                    slices[slice_id] = ContextSlice(
                        slice_id,
                        chunk,
                        metadata={
                            "type": "list_chunk",
                            "start_index": i,
                            "end_index": min(i+chunk_size, len(context)),
                            "size": len(chunk)
                        }
                    )

        elif isinstance(context, str):
            # Try markdown section splitting
            import re
            sections = re.split(r'\n(#{1,3})\s+(.+)', context)

            if len(sections) > 1:
                # Markdown sections found
                for i in range(1, len(sections), 3):
                    if i+2 < len(sections):
                        header_level = sections[i]
                        header_text = sections[i+1]
                        content = sections[i+2]
                        slice_id = f"section_{header_text.replace(' ', '_').lower()}"
                        slices[slice_id] = ContextSlice(
                            slice_id,
                            content.strip(),
                            metadata={
                                "type": "markdown_section",
                                "header": header_text,
                                "level": len(header_level)
                            }
                        )
            else:
                # No markdown - split by character count (chunks of ~10k chars)
                chunk_size = 10000
                num_chunks = (len(context) + chunk_size - 1) // chunk_size
                for i in range(num_chunks):
                    start = i * chunk_size
                    end = min((i+1) * chunk_size, len(context))
                    chunk = context[start:end]
                    slice_id = f"chunk_{i}"
                    slices[slice_id] = ContextSlice(
                        slice_id,
                        chunk,
                        metadata={
                            "type": "string_chunk",
                            "start_char": start,
                            "end_char": end,
                            "size": len(chunk)
                        }
                    )

        return slices
