"""Markdown parsing and slide splitting.

Reads a markdown file, extracts YAML frontmatter for configuration,
and splits the remaining content into individual slides using '---'
(thematic breaks) as delimiters.

Each slide's markdown content is further parsed into structured elements
(headings, paragraphs, code blocks, lists, etc.) using markdown-it-py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import frontmatter
from markdown_it import MarkdownIt


class ElementType(Enum):
    """Types of content elements within a slide."""
    HEADING = auto()
    PARAGRAPH = auto()
    CODE_BLOCK = auto()
    BULLET_LIST = auto()
    ORDERED_LIST = auto()
    BLOCKQUOTE = auto()
    THEMATIC_BREAK = auto()
    HTML_BLOCK = auto()


class CodeBlockMode(Enum):
    """Execution mode for code blocks."""
    STATIC = auto()       # Just display with syntax highlighting
    EXECUTABLE = auto()   # Can be run with a hotkey
    INTERACTIVE = auto()  # Can be edited and run live


@dataclass
class CodeBlock:
    """A fenced code block with optional execution capabilities."""
    language: str = ""
    code: str = ""
    mode: CodeBlockMode = CodeBlockMode.STATIC


@dataclass
class SlideElement:
    """A single content element within a slide."""
    type: ElementType
    content: str = ""
    level: int = 0  # For headings (1-6)
    items: list[str] = field(default_factory=list)  # For lists
    code_block: CodeBlock | None = None


@dataclass
class Slide:
    """A single slide parsed from the markdown file."""
    raw_markdown: str
    elements: list[SlideElement] = field(default_factory=list)
    index: int = 0  # 0-based


@dataclass
class Presentation:
    """A complete parsed presentation."""
    slides: list[Slide] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    title: str = ""

    @property
    def total_slides(self) -> int:
        return len(self.slides)


def _parse_code_fence_info(info: str) -> tuple[str, CodeBlockMode]:
    """Parse a code fence info string like 'python exec' or 'js interactive'.

    Returns (language, mode).
    """
    parts = info.strip().split()
    language = parts[0] if parts else ""
    mode = CodeBlockMode.STATIC

    for part in parts[1:]:
        part_lower = part.lower().strip("{}")
        if part_lower in ("exec", "execute", "run"):
            mode = CodeBlockMode.EXECUTABLE
        elif part_lower in ("interactive", "edit", "live"):
            mode = CodeBlockMode.INTERACTIVE

    return language, mode


def _collect_inline_text(token_children: list | None) -> str:
    """Recursively collect text from inline token children."""
    if not token_children:
        return ""
    parts = []
    for child in token_children:
        if child.type == "text":
            parts.append(child.content)
        elif child.type == "code_inline":
            parts.append(f"`{child.content}`")
        elif child.type == "softbreak":
            parts.append("\n")
        elif child.type == "hardbreak":
            parts.append("\n")
        elif child.type in ("strong_open",):
            parts.append("**")
        elif child.type in ("strong_close",):
            parts.append("**")
        elif child.type in ("em_open",):
            parts.append("*")
        elif child.type in ("em_close",):
            parts.append("*")
        elif child.type in ("s_open",):
            parts.append("~~")
        elif child.type in ("s_close",):
            parts.append("~~")
        elif child.type == "link_open":
            pass  # We'll just show the text
        elif child.type == "link_close":
            pass
        elif child.type == "image":
            parts.append(f"[image: {child.content}]")
        else:
            # Fallback: include content if present
            if child.content:
                parts.append(child.content)
    return "".join(parts)


def _parse_slide_tokens(tokens: list) -> list[SlideElement]:
    """Convert markdown-it tokens into SlideElement objects."""
    elements: list[SlideElement] = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token.type == "heading_open":
            level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
            # Next token is the inline content
            i += 1
            if i < len(tokens) and tokens[i].type == "inline":
                content = _collect_inline_text(tokens[i].children)
                elements.append(SlideElement(
                    type=ElementType.HEADING,
                    content=content,
                    level=level,
                ))
            # Skip heading_close
            i += 1

        elif token.type == "paragraph_open":
            i += 1
            if i < len(tokens) and tokens[i].type == "inline":
                content = _collect_inline_text(tokens[i].children)
                elements.append(SlideElement(
                    type=ElementType.PARAGRAPH,
                    content=content,
                ))
            # Skip paragraph_close
            i += 1

        elif token.type == "fence":
            language, mode = _parse_code_fence_info(token.info)
            code_block = CodeBlock(
                language=language,
                code=token.content.rstrip("\n"),
                mode=mode,
            )
            elements.append(SlideElement(
                type=ElementType.CODE_BLOCK,
                content=token.content.rstrip("\n"),
                code_block=code_block,
            ))

        elif token.type == "code_block":
            code_block = CodeBlock(code=token.content.rstrip("\n"))
            elements.append(SlideElement(
                type=ElementType.CODE_BLOCK,
                content=token.content.rstrip("\n"),
                code_block=code_block,
            ))

        elif token.type == "bullet_list_open":
            items = []
            i += 1
            while i < len(tokens) and tokens[i].type != "bullet_list_close":
                if tokens[i].type == "list_item_open":
                    i += 1
                    # Collect all inline content within this list item
                    item_parts = []
                    while i < len(tokens) and tokens[i].type != "list_item_close":
                        if tokens[i].type == "inline":
                            item_parts.append(_collect_inline_text(tokens[i].children))
                        elif tokens[i].type == "paragraph_open":
                            pass  # skip, content is in inline
                        elif tokens[i].type == "paragraph_close":
                            pass
                        i += 1
                    items.append(" ".join(item_parts))
                i += 1
            elements.append(SlideElement(
                type=ElementType.BULLET_LIST,
                items=items,
            ))

        elif token.type == "ordered_list_open":
            items = []
            i += 1
            while i < len(tokens) and tokens[i].type != "ordered_list_close":
                if tokens[i].type == "list_item_open":
                    i += 1
                    item_parts = []
                    while i < len(tokens) and tokens[i].type != "list_item_close":
                        if tokens[i].type == "inline":
                            item_parts.append(_collect_inline_text(tokens[i].children))
                        elif tokens[i].type in ("paragraph_open", "paragraph_close"):
                            pass
                        i += 1
                    items.append(" ".join(item_parts))
                i += 1
            elements.append(SlideElement(
                type=ElementType.ORDERED_LIST,
                items=items,
            ))

        elif token.type == "blockquote_open":
            i += 1
            quote_parts = []
            while i < len(tokens) and tokens[i].type != "blockquote_close":
                if tokens[i].type == "inline":
                    quote_parts.append(_collect_inline_text(tokens[i].children))
                elif tokens[i].type in ("paragraph_open", "paragraph_close"):
                    pass
                i += 1
            elements.append(SlideElement(
                type=ElementType.BLOCKQUOTE,
                content="\n".join(quote_parts),
            ))

        elif token.type == "hr":
            elements.append(SlideElement(type=ElementType.THEMATIC_BREAK))

        elif token.type == "html_block":
            elements.append(SlideElement(
                type=ElementType.HTML_BLOCK,
                content=token.content,
            ))

        i += 1

    return elements


def split_slides(markdown_body: str) -> list[str]:
    """Split markdown content into slides using --- as delimiter.

    We look for lines that are exactly '---' (with optional whitespace)
    that act as thematic breaks / slide separators. We distinguish between
    separators and frontmatter delimiters by context.
    """
    # Split on lines that are just '---' (possibly with whitespace)
    # These must be on their own line, not inside code blocks
    slides = []
    current_lines: list[str] = []
    in_code_block = False

    for line in markdown_body.split("\n"):
        # Track if we're inside a fenced code block
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        # Check for slide separator (--- on its own line, not in code)
        if not in_code_block and re.match(r"^\s*---\s*$", line) and current_lines:
            slide_text = "\n".join(current_lines).strip()
            if slide_text:
                slides.append(slide_text)
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget the last slide
    slide_text = "\n".join(current_lines).strip()
    if slide_text:
        slides.append(slide_text)

    return slides


def parse_presentation(filepath: str) -> Presentation:
    """Parse a markdown file into a full Presentation object.

    Extracts YAML frontmatter for config, splits into slides,
    and parses each slide's content into structured elements.
    """
    # Read and parse frontmatter
    post = frontmatter.load(filepath)
    config = dict(post.metadata) if post.metadata else {}
    body = post.content

    # Split into slide texts
    slide_texts = split_slides(body)

    # Set up markdown-it parser
    md = MarkdownIt("commonmark", {"typographer": True})

    # Parse each slide
    slides = []
    for idx, raw_md in enumerate(slide_texts):
        tokens = md.parse(raw_md)
        elements = _parse_slide_tokens(tokens)
        slides.append(Slide(
            raw_markdown=raw_md,
            elements=elements,
            index=idx,
        ))

    # Extract title from config or first heading
    title = config.get("title", "")
    if not title and slides and slides[0].elements:
        for elem in slides[0].elements:
            if elem.type == ElementType.HEADING:
                title = elem.content
                break

    return Presentation(
        slides=slides,
        config=config,
        title=title,
    )
