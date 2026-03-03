"""Presentation configuration from YAML frontmatter.

Supported frontmatter keys:
  title:         Presentation title (shown in terminal title bar)
  author:        Author name (shown in footer if configured)
  theme:         Theme name: default, dark, ocean, forest
  progress:      Progress indicator style: "bar", "fraction", or "" (none)
  slide_numbers: Show slide numbers (true/false)
  header:        Text to display at top of every slide
  footer:        Text to display at bottom of every slide
  date:          Date string (can be used in footer)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PresentationConfig:
    """Validated presentation configuration."""
    title: str = ""
    author: str = ""
    theme: str = "default"
    progress: str = "bar"       # "bar", "fraction", or ""
    slide_numbers: bool = True
    header: str = ""
    footer: str = ""
    date: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresentationConfig:
        """Create config from frontmatter dictionary, with defaults."""
        return cls(
            title=str(data.get("title", "")),
            author=str(data.get("author", "")),
            theme=str(data.get("theme", "default")),
            progress=str(data.get("progress", "bar")),
            slide_numbers=bool(data.get("slide_numbers", True)),
            header=str(data.get("header", "")),
            footer=str(data.get("footer", "")),
            date=str(data.get("date", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert back to a dictionary for the renderer."""
        return {
            "title": self.title,
            "author": self.author,
            "theme": self.theme,
            "progress": self.progress,
            "slide_numbers": self.slide_numbers,
            "header": self.header,
            "footer": self.footer,
            "date": self.date,
        }


# Default config when no frontmatter is present
DEFAULT_CONFIG = PresentationConfig()
