# Deckdown

A CLI-based presentation framework that renders Markdown slides in the terminal.

Think PowerPoint, but in your terminal — powered by Markdown.

## Features

- **Markdown-powered slides** — Write your presentation in a single `.md` file
- **Slide navigation** — Arrow keys, vim-style (`h`/`l`), spacebar, jump-to-slide
- **Syntax-highlighted code blocks** — Pygments-based highlighting for 100+ languages
- **Executable code blocks** — Run code directly from your slides with `Ctrl+R`
- **Interactive code blocks** — Edit and run code live during your presentation
- **Themes** — Built-in themes (default, dark, ocean, forest) with live cycling
- **Chrome elements** — Progress bar, slide numbers, persistent header/footer
- **YAML frontmatter** — Configure your presentation with simple YAML

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd cli-presentation-framework

# Create a virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
# Run the demo presentation
deckdown examples/demo.md

# Start from a specific slide
deckdown examples/demo.md --start 3

# Use a specific theme
deckdown examples/demo.md --theme ocean
```

## Writing Presentations

Create a Markdown file with YAML frontmatter and `---` slide separators:

```markdown
---
title: "My Presentation"
author: "Your Name"
theme: default
progress: bar
slide_numbers: true
header: "My Talk"
footer: "Conference 2026"
---

# Welcome

This is the first slide!

---

## Second Slide

- Point one
- Point two
- Point three

---

## Code Demo

\```python exec
print("Hello, World!")
\```
```

### Frontmatter Options

| Key | Values | Description |
|-----|--------|-------------|
| `title` | string | Presentation title |
| `author` | string | Author name |
| `theme` | `default`, `dark`, `ocean`, `forest` | Color theme |
| `progress` | `bar`, `fraction`, `""` | Progress indicator style |
| `slide_numbers` | `true`/`false` | Show slide numbers |
| `header` | string | Persistent header text |
| `footer` | string | Persistent footer text |

### Markdown Support

- **Headings** (H1–H6) — H1 gets decorative rules, H2 gets underlines
- **Bold**, *italic*, `inline code`, ~~strikethrough~~
- Bullet lists and ordered lists
- Blockquotes
- Horizontal rules (within slides — `***` or `___`, since `---` splits slides)
- Fenced code blocks with syntax highlighting

### Code Block Modes

**Static** — Just displays with syntax highlighting:
````markdown
```python
print("displayed only")
```
````

**Executable** — Press `Ctrl+R` to run:
````markdown
```python exec
print("I can be executed!")
```
````

**Interactive** — Press `Ctrl+E` to open an editor, edit code, and run:
````markdown
```python interactive
x = 42
print(f"The answer is {x}")
```
````

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `→` / `l` / `Space` | Next slide |
| `←` / `h` | Previous slide |
| `g` | Go to slide number |
| `Home` | First slide |
| `End` | Last slide |
| `Ctrl+R` | Run executable code blocks |
| `Ctrl+E` | Open interactive code editor |
| `t` | Cycle through themes |
| `?` | Show help |
| `q` | Quit |

## Themes

Cycle themes live during a presentation by pressing `t`:

- **default** — Cyan headings, colorful accents
- **dark** — Muted grays and whites
- **ocean** — Cyan and blue tones
- **forest** — Green and earthy tones

## Supported Languages for Code Execution

Python, JavaScript (Node.js), TypeScript (ts-node), Bash, Shell, Ruby, Go, Perl, PHP, Lua, R — and more can be added.

## License

MIT
