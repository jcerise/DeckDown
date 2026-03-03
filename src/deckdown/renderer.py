"""Terminal rendering engine for slides.

Uses Rich to render parsed slide elements into beautiful terminal output.
Handles centering, formatting, code highlighting, and chrome elements.
"""

from __future__ import annotations

import re
from typing import Any

from rich.align import Align
from rich.console import Console, Group
from rich.columns import Columns
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .parser import (
    CodeBlockMode,
    ElementType,
    Presentation,
    Slide,
    SlideElement,
)
from .themes import Theme, get_theme


def _apply_inline_formatting(raw: str, theme: Theme) -> Text:
    """Convert markdown inline formatting to Rich Text.

    Handles **bold**, *italic*, `code`, and ~~strikethrough~~.
    """
    text = Text()
    i = 0

    while i < len(raw):
        # Bold: **text**
        if raw[i:i+2] == "**":
            end = raw.find("**", i + 2)
            if end != -1:
                text.append(raw[i+2:end], style=theme.bold)
                i = end + 2
                continue

        # Italic: *text*
        if raw[i] == "*" and (i + 1 < len(raw) and raw[i+1] != "*"):
            end = raw.find("*", i + 1)
            if end != -1:
                text.append(raw[i+1:end], style=theme.italic)
                i = end + 1
                continue

        # Inline code: `text`
        if raw[i] == "`":
            end = raw.find("`", i + 1)
            if end != -1:
                text.append(f" {raw[i+1:end]} ", style=theme.code_inline)
                i = end + 1
                continue

        # Strikethrough: ~~text~~
        if raw[i:i+2] == "~~":
            end = raw.find("~~", i + 2)
            if end != -1:
                text.append(raw[i+2:end], style="strike")
                i = end + 2
                continue

        # Regular character
        text.append(raw[i], style=theme.paragraph)
        i += 1

    return text


def _render_heading(elem: SlideElement, theme: Theme, width: int) -> Align:
    """Render a heading element."""
    style_map = {
        1: theme.heading1,
        2: theme.heading2,
        3: theme.heading3,
        4: theme.heading4,
        5: theme.heading5,
        6: theme.heading6,
    }
    style = style_map.get(elem.level, theme.heading1)

    # Scale heading size with decorations
    if elem.level == 1:
        heading_text = Text(elem.content.upper(), style=style, justify="center")
        # Add decorative lines around H1
        rule_top = Rule(style=style)
        rule_bottom = Rule(style=style)
        group = Group(
            rule_top,
            Text(""),
            heading_text,
            Text(""),
            rule_bottom,
        )
        return Align.center(group, width=min(width, 80))
    elif elem.level == 2:
        heading_text = Text(elem.content, style=style, justify="center")
        rule = Rule(style=style)
        group = Group(heading_text, rule)
        return Align.center(group, width=min(width, 80))
    else:
        heading_text = Text(elem.content, style=style, justify="center")
        return Align.center(heading_text, width=min(width, 80))


def _render_paragraph(elem: SlideElement, theme: Theme, width: int) -> Align:
    """Render a paragraph element with inline formatting."""
    text = _apply_inline_formatting(elem.content, theme)
    text.justify = "center"
    return Align.center(text, width=min(width, 80))


def _render_bullet_list(elem: SlideElement, theme: Theme, width: int) -> Align:
    """Render a bullet list."""
    lines = Text()
    for i, item in enumerate(elem.items):
        marker = Text("  • ", style=theme.bullet_marker)
        item_text = _apply_inline_formatting(item, theme)
        lines.append_text(marker)
        lines.append_text(item_text)
        if i < len(elem.items) - 1:
            lines.append("\n")
    return Align.center(lines, width=min(width, 70))


def _render_ordered_list(elem: SlideElement, theme: Theme, width: int) -> Align:
    """Render an ordered list."""
    lines = Text()
    for i, item in enumerate(elem.items):
        marker = Text(f"  {i+1}. ", style=theme.ordered_marker)
        item_text = _apply_inline_formatting(item, theme)
        lines.append_text(marker)
        lines.append_text(item_text)
        if i < len(elem.items) - 1:
            lines.append("\n")
    return Align.center(lines, width=min(width, 70))


def _render_blockquote(elem: SlideElement, theme: Theme, width: int) -> Align:
    """Render a blockquote with a left border."""
    quote_text = Text(elem.content, style=theme.blockquote_text)
    panel = Panel(
        quote_text,
        border_style=theme.blockquote_border,
        width=min(width - 10, 60),
        padding=(0, 2),
    )
    return Align.center(panel)


def _render_code_block(
    elem: SlideElement,
    theme: Theme,
    width: int,
    exec_output: str | None = None,
) -> Align:
    """Render a code block with syntax highlighting."""
    cb = elem.code_block
    if cb is None:
        return Align.center(Text(elem.content))

    # Choose border style based on mode
    if cb.mode == CodeBlockMode.EXECUTABLE:
        border_style = theme.code_exec_border
        title = f" {cb.language} [exec] " if cb.language else " [exec] "
        subtitle = " Ctrl+R to run "
    elif cb.mode == CodeBlockMode.INTERACTIVE:
        border_style = theme.code_interactive_border
        title = f" {cb.language} [interactive] " if cb.language else " [interactive] "
        subtitle = " Ctrl+E to edit & run "
    else:
        border_style = theme.code_border
        title = f" {cb.language} " if cb.language else None
        subtitle = None

    syntax = Syntax(
        cb.code,
        lexer=cb.language or "text",
        theme=theme.code_theme,
        line_numbers=False,
        word_wrap=True,
    )

    code_panel = Panel(
        syntax,
        title=title,
        subtitle=subtitle,
        border_style=border_style,
        width=min(width - 6, 72),
        padding=(0, 1),
    )

    if exec_output is not None:
        output_text = Text(exec_output, style="bright_white on grey11")
        output_panel = Panel(
            output_text,
            title=" Output ",
            border_style="bright_green",
            width=min(width - 6, 72),
            padding=(0, 1),
        )
        group = Group(code_panel, output_panel)
        return Align.center(group)

    return Align.center(code_panel)


def _render_thematic_break(theme: Theme, width: int) -> Align:
    """Render a horizontal rule / thematic break."""
    rule = Rule(style=theme.thematic_break)
    return Align.center(rule, width=min(width, 60))


def render_slide(
    slide: Slide,
    theme: Theme,
    width: int,
    height: int,
    exec_outputs: dict[int, str] | None = None,
) -> list:
    """Render a slide's elements into Rich renderables.

    Returns a list of Rich renderables that can be printed by a Console.
    """
    renderables = []

    for i, elem in enumerate(slide.elements):
        if elem.type == ElementType.HEADING:
            renderables.append(_render_heading(elem, theme, width))
            renderables.append(Text(""))  # spacing

        elif elem.type == ElementType.PARAGRAPH:
            renderables.append(_render_paragraph(elem, theme, width))
            renderables.append(Text(""))

        elif elem.type == ElementType.BULLET_LIST:
            renderables.append(_render_bullet_list(elem, theme, width))
            renderables.append(Text(""))

        elif elem.type == ElementType.ORDERED_LIST:
            renderables.append(_render_ordered_list(elem, theme, width))
            renderables.append(Text(""))

        elif elem.type == ElementType.BLOCKQUOTE:
            renderables.append(_render_blockquote(elem, theme, width))
            renderables.append(Text(""))

        elif elem.type == ElementType.CODE_BLOCK:
            output = (exec_outputs or {}).get(i)
            renderables.append(_render_code_block(elem, theme, width, output))
            renderables.append(Text(""))

        elif elem.type == ElementType.THEMATIC_BREAK:
            renderables.append(_render_thematic_break(theme, width))
            renderables.append(Text(""))

    return renderables


def render_chrome(
    current: int,
    total: int,
    config: dict[str, Any],
    theme: Theme,
    width: int,
) -> tuple[Text | None, Text | None, Any | None]:
    """Render chrome elements: header, footer, progress.

    Returns (header_renderable, footer_renderable, progress_renderable).
    """
    header_text = None
    footer_text = None
    progress_renderable = None

    # Header
    header_str = config.get("header", "")
    if header_str:
        h = Text(header_str, style=theme.header, justify="center")
        h.pad(width)
        header_text = h

    # Footer
    footer_str = config.get("footer", "")
    show_numbers = config.get("slide_numbers", False)

    if footer_str or show_numbers:
        footer_parts = Text(style=theme.footer)
        if footer_str:
            footer_parts.append(footer_str)
        if show_numbers:
            slide_num = f"  {current + 1}/{total}"
            if footer_str:
                # Right-align slide number
                padding = width - len(footer_str) - len(slide_num)
                footer_parts.append(" " * max(padding, 2))
            footer_parts.append(slide_num, style=theme.slide_number)
        footer_parts.pad(width)
        footer_text = footer_parts

    # Progress bar
    progress_style = config.get("progress", "")
    if progress_style:
        fraction = (current + 1) / total if total > 0 else 0
        if progress_style == "bar":
            bar_width = width - 4
            filled = int(bar_width * fraction)
            empty = bar_width - filled
            bar = Text()
            bar.append(" " + "━" * filled, style=theme.progress_bar_filled)
            bar.append("━" * empty + " ", style=theme.progress_bar_empty)
            progress_renderable = bar
        elif progress_style == "fraction":
            frac = Text(
                f" {current + 1} / {total} ",
                style=theme.slide_number,
                justify="center",
            )
            progress_renderable = Align.center(frac)

    return header_text, footer_text, progress_renderable
