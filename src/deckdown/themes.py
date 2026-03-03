"""Theme definitions for presentation styling."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Theme:
    """Color and style theme for presentations."""
    name: str = "default"

    # Background
    bg: str = ""  # Empty = terminal default

    # Text colors
    heading1: str = "bold bright_cyan"
    heading2: str = "bold bright_green"
    heading3: str = "bold bright_yellow"
    heading4: str = "bold bright_magenta"
    heading5: str = "bold bright_blue"
    heading6: str = "bold white"

    paragraph: str = "white"
    bold: str = "bold white"
    italic: str = "italic white"
    code_inline: str = "bold bright_yellow on grey23"

    # Lists
    bullet_marker: str = "bright_cyan"
    bullet_text: str = "white"
    ordered_marker: str = "bright_green"
    ordered_text: str = "white"

    # Blockquote
    blockquote_border: str = "bright_yellow"
    blockquote_text: str = "italic grey78"

    # Code blocks
    code_border: str = "bright_blue"
    code_theme: str = "monokai"  # Pygments theme name
    code_exec_border: str = "bright_green"
    code_interactive_border: str = "bright_magenta"

    # Chrome
    header: str = "bold bright_white on grey15"
    footer: str = "dim white on grey15"
    progress_bar_filled: str = "bright_cyan"
    progress_bar_empty: str = "grey30"
    slide_number: str = "dim white"

    # Dividers
    thematic_break: str = "grey50"


# Predefined themes
THEMES: dict[str, Theme] = {
    "default": Theme(),
    "dark": Theme(
        name="dark",
        heading1="bold bright_white",
        heading2="bold grey78",
        heading3="bold grey62",
        paragraph="grey78",
        bullet_marker="grey62",
        bullet_text="grey78",
        code_theme="native",
        progress_bar_filled="grey78",
    ),
    "ocean": Theme(
        name="ocean",
        heading1="bold bright_cyan",
        heading2="bold cyan",
        heading3="bold dark_cyan",
        paragraph="light_sky_blue1",
        bullet_marker="bright_cyan",
        bullet_text="light_sky_blue1",
        blockquote_border="cyan",
        blockquote_text="italic light_sky_blue1",
        code_border="cyan",
        code_theme="monokai",
        progress_bar_filled="bright_cyan",
    ),
    "forest": Theme(
        name="forest",
        heading1="bold bright_green",
        heading2="bold green",
        heading3="bold dark_green",
        paragraph="pale_green1",
        bullet_marker="bright_green",
        bullet_text="pale_green1",
        blockquote_border="green",
        code_border="green",
        code_theme="monokai",
        progress_bar_filled="bright_green",
    ),
}


def get_theme(name: str) -> Theme:
    """Get a theme by name, falling back to default."""
    return THEMES.get(name, THEMES["default"])
