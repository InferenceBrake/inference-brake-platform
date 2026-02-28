"""
Long Content Handler.

Processes arbitrarily long reasoning traces by chunking
and extracting the most relevant portions for analysis.

For loop detection, the most recent content is most relevant -
loops appear in current reasoning, not in content from 50k tokens ago.

Strategies:
    1. Tail chunking: Extract last N tokens
    2. Sliding window: Overlap chunks to avoid boundary artifacts
    3. Summary extraction: Key phrases and structure from full content
"""

from __future__ import annotations

import re


class LongContentHandler:
    """
    Handle long reasoning traces for loop detection.

    Default strategy: extract the last chunk_size tokens
    with overlap from the previous chunk for context.
    """

    def __init__(self, chunk_size: int = 2000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process(self, reasoning: str) -> str:
        """
        Process reasoning text, returning the portion
        most relevant for loop detection.

        For short text (< chunk_size tokens): return as-is.
        For long text: return last chunk with context overlap.
        """
        words = reasoning.split()
        if len(words) <= self.chunk_size:
            return reasoning

        # Extract last chunk with overlap
        start = max(0, len(words) - self.chunk_size - self.overlap)
        return " ".join(words[start:])

    def chunk(self, reasoning: str) -> list[str]:
        """
        Split long text into overlapping chunks.

        Useful when you need to analyze the full content
        (e.g., for comprehensive similarity search).
        """
        words = reasoning.split()
        if len(words) <= self.chunk_size:
            return [reasoning]

        chunks = []
        step = self.chunk_size - self.overlap
        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            chunks.append(chunk)
            if i + self.chunk_size >= len(words):
                break

        return chunks

    def extract_key_phrases(self, reasoning: str, max_phrases: int = 20) -> list[str]:
        """
        Extract key phrases from long reasoning for quick comparison.

        Uses a simple heuristic: sentences starting with action verbs
        or containing decision language are most indicative of loops.
        """
        action_patterns = [
            r"(?:I (?:should|need to|will|must|want to|am going to))\s+.+?[.!?\n]",
            r"(?:Let me|Let's)\s+.+?[.!?\n]",
            r"(?:The (?:answer|solution|result|output) is)\s+.+?[.!?\n]",
            r"(?:I (?:think|believe|conclude|determine))\s+.+?[.!?\n]",
            r"(?:(?:First|Next|Then|Finally),?\s+).+?[.!?\n]",
        ]

        phrases = []
        for pattern in action_patterns:
            matches = re.findall(pattern, reasoning, re.IGNORECASE)
            phrases.extend(matches)

        # Deduplicate and limit
        seen = set()
        unique = []
        for p in phrases:
            p_stripped = p.strip()[:200]
            if p_stripped not in seen:
                seen.add(p_stripped)
                unique.append(p_stripped)
        return unique[:max_phrases]
