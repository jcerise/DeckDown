---
title: "Deckdown Showcase"
author: "CLI Enthusiast"
theme: default
progress: bar
slide_numbers: true
header: "🖥️  Deckdown Showcase"
footer: "Terminal Presentations — 2026"
---

# Deckdown

### Terminal Presentations, Reimagined

*Press → to begin*

---

## What is Deckdown?

A **Markdown-powered** presentation tool that lives
entirely in your terminal.

- No browser needed
- No GUI required
- Just you and your terminal

---

## Rich Text Support

**Bold text** for emphasis

*Italic text* for style

`inline code` for technical content

~~Strikethrough~~ for corrections

Mix them all: **bold and *nested italic***

---

## Lists

### Unordered

- First item
- Second item
- Third item with `code`
- Fourth item in **bold**

### Ordered

1. Step one
2. Step two
3. Step three

---

## Blockquotes

> "Any sufficiently advanced technology
> is indistinguishable from magic."
>
> — Arthur C. Clarke

---

## Code: Syntax Highlighting

```python
from dataclasses import dataclass

@dataclass
class Slide:
    title: str
    content: list[str]
    
    def render(self) -> str:
        return f"# {self.title}\n" + "\n".join(self.content)
```

---

## Code: Live Execution

Press `Ctrl+R` to run this code:

```python exec
import sys
import platform

print(f"Python {sys.version_info.major}.{sys.version_info.minor}")
print(f"Platform: {platform.system()} {platform.machine()}")
print(f"Node: {platform.node()}")
```

---

## Code: Interactive Editing

Press `Ctrl+E` to edit and run:

```python interactive
# Try changing these values!
name = "World"
greeting = f"Hello, {name}!"
print(greeting)
print(f"Length: {len(greeting)} characters")
```

---

## Multi-Language Support

```javascript
// JavaScript (requires Node.js)
const items = ['slides', 'code', 'themes'];
items.forEach(item => console.log(`✓ ${item}`));
```

```bash
# Bash
echo "Running in: $(pwd)"
echo "Date: $(date +%Y-%m-%d)"
```

---

## Themes

Press `t` to cycle through themes:

- **default** — Vibrant & colorful
- **dark** — Subtle & muted
- **ocean** — Cool blues & cyans
- **forest** — Warm greens

---

## Navigation

| Key | Action |
|-----|--------|
| `→` `l` `Space` | Next slide |
| `←` `h` | Previous slide |
| `g` | Jump to slide |
| `Home` / `End` | First / Last |
| `q` | Quit |

---

# Thank You!

### Made with ❤️ in the terminal

*Press `q` to exit*
