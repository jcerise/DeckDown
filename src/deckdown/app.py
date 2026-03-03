"""Main Textual application for the presentation TUI.

Handles full-screen rendering, keyboard navigation, and the main event loop.
"""

from __future__ import annotations

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Footer, Input, Static, TextArea

from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderableType, Group
from rich.text import Text

from .parser import (
    CodeBlockMode,
    ElementType,
    Presentation,
    Slide,
)
from .renderer import render_slide, render_chrome
from .themes import Theme, get_theme
from .code_exec import execute_code


class SlideWidget(Widget):
    """Widget that renders a single slide with vertical centering."""

    DEFAULT_CSS = """
    SlideWidget {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(
        self,
        slide: Slide,
        theme: Theme,
        current: int,
        total: int,
        config: dict,
        exec_outputs: dict[int, str] | None = None,
    ) -> None:
        super().__init__()
        self.slide = slide
        self.theme = theme
        self.current = current
        self.total = total
        self.config = config
        self.exec_outputs = exec_outputs or {}

    def render(self) -> RenderableType:
        width = self.size.width
        height = self.size.height

        # Render chrome
        header, footer, progress = render_chrome(
            self.current, self.total, self.config, self.theme, width
        )

        # Render slide content
        content_renderables = render_slide(
            self.slide, self.theme, width, height, self.exec_outputs
        )

        # Build the full slide layout
        parts = []
        if header:
            parts.append(header)
            parts.append(Text(""))

        # Add top padding for vertical centering
        # Estimate content height (rough: 1 line per renderable)
        content_lines = len(content_renderables)
        chrome_lines = (2 if header else 0) + (1 if footer else 0) + (1 if progress else 0)
        available = height - chrome_lines
        top_pad = max(0, (available - content_lines) // 3)  # 1/3 from top

        for _ in range(top_pad):
            parts.append(Text(""))

        parts.extend(content_renderables)

        # Fill remaining space
        bottom_pad = max(0, available - top_pad - content_lines)
        for _ in range(bottom_pad):
            parts.append(Text(""))

        if progress:
            parts.append(progress)
        if footer:
            parts.append(footer)

        return Group(*parts)


class GoToSlideScreen(ModalScreen[int | None]):
    """Modal screen for jumping to a specific slide number."""

    DEFAULT_CSS = """
    GoToSlideScreen {
        align: center middle;
    }

    GoToSlideScreen > Container {
        width: 40;
        height: 7;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    GoToSlideScreen Input {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, total: int) -> None:
        super().__init__()
        self.total = total

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(f"Go to slide (1-{self.total}):")
            yield Input(placeholder="Slide number...", type="integer")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            num = int(event.value)
            if 1 <= num <= self.total:
                self.dismiss(num - 1)  # Convert to 0-based
            else:
                self.dismiss(None)
        except ValueError:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class CodeEditorScreen(ModalScreen[str | None]):
    """Modal screen for interactively editing and running code."""

    DEFAULT_CSS = """
    CodeEditorScreen {
        align: center middle;
    }

    CodeEditorScreen > Vertical {
        width: 80%;
        height: 80%;
        max-width: 100;
        border: thick $accent;
        background: $surface;
    }

    CodeEditorScreen TextArea {
        height: 1fr;
    }

    CodeEditorScreen .output-area {
        height: auto;
        max-height: 10;
        background: $surface-darken-1;
        padding: 0 1;
        overflow-y: auto;
    }

    CodeEditorScreen .editor-header {
        dock: top;
        height: 1;
        background: $accent;
        padding: 0 1;
    }

    CodeEditorScreen .editor-footer {
        dock: bottom;
        height: 1;
        background: $accent;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("ctrl+r", "run_code", "Run"),
    ]

    def __init__(self, code: str, language: str = "python") -> None:
        super().__init__()
        self.initial_code = code
        self.language = language
        self._output = ""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(
                f" Interactive Editor [{self.language}] — Ctrl+R: Run | Esc: Close ",
                classes="editor-header",
            )
            yield TextArea(self.initial_code, language=self.language, id="code-editor")
            yield Static("", id="code-output", classes="output-area")
            yield Static(
                " Edit code above, then press Ctrl+R to execute ",
                classes="editor-footer",
            )

    def action_run_code(self) -> None:
        editor = self.query_one("#code-editor", TextArea)
        code = editor.text
        result = execute_code(code, self.language)
        output_widget = self.query_one("#code-output", Static)
        output_widget.update(f"Output:\n{result}")
        self._output = result

    def action_close(self) -> None:
        editor = self.query_one("#code-editor", TextArea)
        self.dismiss(editor.text)


class DeckdownApp(App):
    """Main presentation application."""

    TITLE = "deckdown"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("right,l,space", "next_slide", "Next", show=False),
        Binding("left,h", "prev_slide", "Previous", show=False),
        Binding("g", "go_to_slide", "Go to slide", show=False),
        Binding("home", "first_slide", "First slide", show=False),
        Binding("end", "last_slide", "Last slide", show=False),
        Binding("q", "quit", "Quit", show=False),
        Binding("ctrl+r", "run_code", "Run code", show=False),
        Binding("ctrl+e", "edit_code", "Edit code", show=False),
        Binding("t", "cycle_theme", "Cycle theme", show=False),
        Binding("question_mark", "show_help", "Help", show=False),
    ]

    def __init__(
        self,
        presentation: Presentation,
        theme_name: str | None = None,
        start_slide: int = 0,
    ) -> None:
        super().__init__()
        self.presentation = presentation
        self.current_slide = max(0, min(start_slide, presentation.total_slides - 1))
        self._theme_name = theme_name or presentation.config.get("theme", "default")
        self.slide_theme = get_theme(self._theme_name)
        # Track code execution output per slide: {slide_idx: {element_idx: output}}
        self.exec_outputs: dict[int, dict[int, str]] = {}
        self._available_themes = ["default", "dark", "ocean", "forest"]

    def compose(self) -> ComposeResult:
        yield self._make_slide_widget()

    def _make_slide_widget(self) -> SlideWidget:
        slide = self.presentation.slides[self.current_slide]
        outputs = self.exec_outputs.get(self.current_slide, {})
        return SlideWidget(
            slide=slide,
            theme=self.slide_theme,
            current=self.current_slide,
            total=self.presentation.total_slides,
            config=self.presentation.config,
            exec_outputs=outputs,
        )

    def _refresh_slide(self) -> None:
        """Replace the slide widget with updated content."""
        old = self.query_one(SlideWidget)
        new_widget = self._make_slide_widget()
        old.replace(new_widget)

    def action_next_slide(self) -> None:
        if self.current_slide < self.presentation.total_slides - 1:
            self.current_slide += 1
            self._refresh_slide()

    def action_prev_slide(self) -> None:
        if self.current_slide > 0:
            self.current_slide -= 1
            self._refresh_slide()

    def action_first_slide(self) -> None:
        self.current_slide = 0
        self._refresh_slide()

    def action_last_slide(self) -> None:
        self.current_slide = self.presentation.total_slides - 1
        self._refresh_slide()

    def action_go_to_slide(self) -> None:
        def on_result(slide_idx: int | None) -> None:
            if slide_idx is not None:
                self.current_slide = slide_idx
                self._refresh_slide()

        self.push_screen(
            GoToSlideScreen(self.presentation.total_slides),
            callback=on_result,
        )

    def action_run_code(self) -> None:
        """Execute all executable code blocks on the current slide."""
        slide = self.presentation.slides[self.current_slide]
        outputs: dict[int, str] = {}

        for i, elem in enumerate(slide.elements):
            if (
                elem.type == ElementType.CODE_BLOCK
                and elem.code_block
                and elem.code_block.mode in (CodeBlockMode.EXECUTABLE, CodeBlockMode.INTERACTIVE)
            ):
                result = execute_code(
                    elem.code_block.code,
                    elem.code_block.language,
                )
                outputs[i] = result

        if outputs:
            self.exec_outputs[self.current_slide] = outputs
            self._refresh_slide()

    def action_edit_code(self) -> None:
        """Open interactive editor for interactive code blocks."""
        slide = self.presentation.slides[self.current_slide]

        # Find the first interactive code block
        for i, elem in enumerate(slide.elements):
            if (
                elem.type == ElementType.CODE_BLOCK
                and elem.code_block
                and elem.code_block.mode == CodeBlockMode.INTERACTIVE
            ):
                def on_editor_close(updated_code: str | None, idx: int = i, elem=elem) -> None:
                    if updated_code is not None:
                        # Update the code block with edited code
                        elem.code_block.code = updated_code
                        elem.content = updated_code
                        # Run it and store output
                        result = execute_code(updated_code, elem.code_block.language)
                        if self.current_slide not in self.exec_outputs:
                            self.exec_outputs[self.current_slide] = {}
                        self.exec_outputs[self.current_slide][idx] = result
                        self._refresh_slide()

                self.push_screen(
                    CodeEditorScreen(
                        code=elem.code_block.code,
                        language=elem.code_block.language,
                    ),
                    callback=on_editor_close,
                )
                break

    def action_cycle_theme(self) -> None:
        """Cycle through available themes."""
        try:
            idx = self._available_themes.index(self._theme_name)
            idx = (idx + 1) % len(self._available_themes)
        except ValueError:
            idx = 0
        self._theme_name = self._available_themes[idx]
        self.slide_theme = get_theme(self._theme_name)
        self._refresh_slide()

    def action_show_help(self) -> None:
        """Show help overlay (simple notification for now)."""
        self.notify(
            "←/→: Navigate  |  g: Go to slide  |  q: Quit\n"
            "Ctrl+R: Run code  |  Ctrl+E: Edit code  |  t: Theme",
            title="Keyboard Shortcuts",
            timeout=5,
        )

    def on_resize(self, event: events.Resize) -> None:
        self._refresh_slide()
