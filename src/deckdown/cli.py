"""CLI entry point for deckdown."""

from __future__ import annotations

import click

from .parser import parse_presentation
from .app import DeckdownApp


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--theme", default=None, help="Presentation theme (default, dark, ocean, forest)")
@click.option("--start", default=1, type=int, help="Starting slide number (1-based)")
def main(file: str, theme: str | None, start: int) -> None:
    """Present Markdown slides in the terminal.

    FILE is the path to a Markdown presentation file.

    \b
    Navigation:
      ←/→ or h/l    Previous/Next slide
      Space          Next slide
      g              Go to slide number
      Home/End       First/Last slide
      Ctrl+R         Run executable code blocks
      Ctrl+E         Edit interactive code blocks
      t              Cycle theme
      ?              Show help
      q              Quit
    """
    presentation = parse_presentation(file)

    if presentation.total_slides == 0:
        click.echo("No slides found in the presentation file.")
        raise SystemExit(1)

    app = DeckdownApp(
        presentation=presentation,
        theme_name=theme,
        start_slide=start - 1,  # Convert to 0-based
    )
    app.run()


if __name__ == "__main__":
    main()
