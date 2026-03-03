"""Code execution and interactive code block support.

Handles running code blocks in various languages and capturing output.
Supports Python (direct), and other languages via subprocess.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# Language -> (command, file extension)
LANGUAGE_RUNNERS: dict[str, tuple[list[str], str]] = {
    "python": (["python3"], ".py"),
    "python3": (["python3"], ".py"),
    "py": (["python3"], ".py"),
    "javascript": (["node"], ".js"),
    "js": (["node"], ".js"),
    "typescript": (["npx", "ts-node"], ".ts"),
    "ts": (["npx", "ts-node"], ".ts"),
    "bash": (["bash"], ".sh"),
    "sh": (["sh"], ".sh"),
    "zsh": (["zsh"], ".sh"),
    "ruby": (["ruby"], ".rb"),
    "rb": (["ruby"], ".rb"),
    "go": (["go", "run"], ".go"),
    "rust": (["rustc", "-o", "/tmp/deckdown_rust_out", "{file}", "&&", "/tmp/deckdown_rust_out"], ".rs"),
    "perl": (["perl"], ".pl"),
    "php": (["php"], ".php"),
    "lua": (["lua"], ".lua"),
    "r": (["Rscript"], ".R"),
}


def execute_python_inline(code: str) -> str:
    """Execute Python code inline and capture stdout/stderr.

    Runs in the current process for speed, with captured I/O.
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, {"__builtins__": __builtins__}, {})
    except Exception:
        stderr_capture.write(traceback.format_exc())

    output = stdout_capture.getvalue()
    errors = stderr_capture.getvalue()

    if errors:
        if output:
            return output + "\n" + errors
        return errors

    return output if output else "(no output)"


def execute_subprocess(code: str, language: str, timeout: int = 10) -> str:
    """Execute code via subprocess for non-Python languages."""
    runner_info = LANGUAGE_RUNNERS.get(language.lower())
    if not runner_info:
        return f"Error: No runner configured for language '{language}'"

    command_parts, extension = runner_info

    # Write code to a temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=extension,
        prefix="deckdown_",
        delete=False,
    ) as f:
        f.write(code)
        temp_path = f.name

    try:
        # Build the command
        cmd = []
        for part in command_parts:
            if "{file}" in part:
                cmd.append(part.replace("{file}", temp_path))
            else:
                cmd.append(part)
        cmd.append(temp_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/tmp",
        )

        output = result.stdout
        if result.stderr:
            if output:
                output += "\n" + result.stderr
            else:
                output = result.stderr

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout}s"
    except FileNotFoundError:
        return f"Error: '{command_parts[0]}' not found. Is it installed?"
    except Exception as e:
        return f"Error: {e}"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def execute_code(code: str, language: str = "python", timeout: int = 10) -> str:
    """Execute code and return the output string.

    Uses inline execution for Python (faster), subprocess for everything else.
    """
    lang = language.lower().strip()

    if lang in ("python", "python3", "py", ""):
        return execute_python_inline(code)
    else:
        return execute_subprocess(code, lang, timeout)
