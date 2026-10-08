"""
Chunking strategies for RAG — matches the video's walkthrough.

Install:
    uv add langchain-text-splitters
    (or) pip install langchain-text-splitters

Strategies covered:
  1. Fixed-size chunking      -> CharacterTextSplitter, no separator
  2. Paragraph-based chunking -> CharacterTextSplitter, separator="\n\n"
  3. Recursive chunking       -> RecursiveCharacterTextSplitter (auto separators + overlap)
  4. Recursive chunking for code -> RecursiveCharacterTextSplitter.from_language()
"""

from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    Language,
)


# ---------------------------------------------------------------------------
# 1. FIXED-SIZE CHUNKING
#    Cuts every N characters, no matter what. Doesn't care if it slices
#    through a word or a sentence — this is the "4 feet swing, 6 foot
#    person gets cut in half" problem from the video.
# ---------------------------------------------------------------------------
def fixed_size_demo(text: str):
    splitter = CharacterTextSplitter(
        separator="",       # no separator -> pure character counting
        chunk_size=100,
        chunk_overlap=0,
    )
    chunks = splitter.split_text(text)
    print("=== 1. FIXED-SIZE CHUNKING (chunk_size=100, no separator) ===")
    for i, c in enumerate(chunks, 1):
        print(f"Chunk {i}: {c!r}")
    print()
    return chunks


# ---------------------------------------------------------------------------
# 2. PARAGRAPH-BASED CHUNKING
#    Splits on "\n\n" (blank line = paragraph boundary in most authored
#    text). Preserves meaning within a paragraph, but a paragraph bigger
#    than chunk_size still gets hard-cut (the Shakespeare problem).
# ---------------------------------------------------------------------------
def paragraph_demo(text: str):
    splitter = CharacterTextSplitter(
        separator="\n\n",   # blank line = paragraph break
        chunk_size=100,
        chunk_overlap=0,
    )
    chunks = splitter.split_text(text)
    print("=== 2. PARAGRAPH-BASED CHUNKING (separator='\\n\\n', chunk_size=100) ===")
    for i, c in enumerate(chunks, 1):
        print(f"Chunk {i}: {c!r}")
    print()
    return chunks


# ---------------------------------------------------------------------------
# 3. RECURSIVE CHUNKING
#    Tries separators in priority order: paragraph -> line -> sentence ->
#    word -> character. Falls back to the next separator only when the
#    current one still produces a chunk that's too big. chunk_overlap
#    carries the tail of one chunk into the start of the next, so a
#    sentence split across chunks still has some shared context.
# ---------------------------------------------------------------------------
def recursive_demo(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=60,
        chunk_overlap=20,   # 20 characters carried over into the next chunk
    )
    chunks = splitter.split_text(text)
    print("=== 3. RECURSIVE CHUNKING (chunk_size=60, chunk_overlap=20) ===")
    for i, c in enumerate(chunks, 1):
        print(f"Chunk {i}: {c!r}")
    print()
    return chunks


# ---------------------------------------------------------------------------
# 4. RECURSIVE CHUNKING FOR CODE
#    Same recursive idea, but the separator list is swapped for
#    language-aware ones (class / def / if / elif / else / return / ...)
#    so a chunk boundary lands on a logical code boundary instead of
#    mid-statement.
# ---------------------------------------------------------------------------
def code_demo(code: str):
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=60,
        chunk_overlap=0,
    )
    chunks = splitter.split_text(code)
    print("=== 4. RECURSIVE CHUNKING FOR PYTHON CODE (chunk_size=60) ===")
    for i, c in enumerate(chunks, 1):
        print(f"Chunk {i}:\n{c}\n---")
    print()
    return chunks


if __name__ == "__main__":
    # Same style of example used in the video: a short mystery-novel-style
    # passage, with two paragraphs, to show fixed vs paragraph vs recursive.
    story_text = """The old detective walked into the dark room and sat down slowly.
He looked at the windows and noticed something was wrong there.

The man who did the crime was John. Nobody suspected him at first because he seemed so calm and quiet."""

    fixed_size_demo(story_text)
    paragraph_demo(story_text)
    recursive_demo(story_text)

    # Code example, same shape as the video's def/if/else walkthrough.
    sample_code = """def sum(a, b):
    c = a + b
    if c % 2 == 0:
        return "even"
    else:
        return "odd"
"""
    code_demo(sample_code)