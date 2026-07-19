"""
renderer.py

The template engine for the profile. Takes README.template.md (a Jinja2
template containing placeholders like {{ username }}, {{ quote }}, etc.)
plus a context dict of values, and renders it into README.md.

In Phase 1 the context is built from static/mock data. Later phases
(avatar.py, github.py, leetcode.py) will feed real, live values into
the same context dict without this file needing to change.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

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
    """Render README.template.md with the given context and return the result."""
    env = get_environment()
    template = env.get_template(TEMPLATE_NAME)
    return template.render(**context)


def write_readme(rendered: str, output_path: Path | None = None) -> Path:
    """Write the rendered markdown to README.md (or a custom path)."""
    output_path = output_path or (ROOT_DIR / OUTPUT_NAME)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path
