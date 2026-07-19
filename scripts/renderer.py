"""
renderer.py

The template engine for the profile. Takes README.template.md (a Jinja2
template containing placeholders like {{ username }}, {{ quote }}, etc.)
plus a context dict of values, and renders it into README.md.

Context is assembled in build.py, mixing static config (username,
tagline, stack, projects) with live/mock data from avatar.py, github.py,
and leetcode.py. This file doesn't know or care where a value came from
- it just needs the context dict to have every key the template uses.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateSyntaxError, UndefinedError

from utils import ROOT_DIR

TEMPLATE_NAME = "README.template.md"
OUTPUT_NAME = "README.md"


def get_environment() -> Environment:
    """
    Build the Jinja2 environment.

    StrictUndefined makes the build fail loudly if the template
    references a placeholder that isn't in the context, instead of
    silently rendering an empty string into the README.
    """
    return Environment(
        loader=FileSystemLoader(str(ROOT_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(context: dict) -> str:
    """
    Render README.template.md with the given context and return the result.

    Raises a clear, actionable error (rather than a raw Jinja traceback)
    if the template has a syntax error or references a context key that
    doesn't exist - the two mistakes most likely when someone edits
    README.template.md by hand.
    """
    env = get_environment()

    try:
        template = env.get_template(TEMPLATE_NAME)
    except TemplateSyntaxError as exc:
        raise RuntimeError(
            f"README.template.md has a syntax error at line {exc.lineno}: {exc.message}"
        ) from exc

    try:
        return template.render(**context)
    except UndefinedError as exc:
        raise RuntimeError(
            "README.template.md references a placeholder that isn't in the "
            f"build context: {exc.message}. Check build_context() in build.py."
        ) from exc


def write_readme(rendered: str, output_path: Path | None = None) -> Path:
    """Write the rendered markdown to README.md (or a custom path)."""
    output_path = output_path or (ROOT_DIR / OUTPUT_NAME)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path
