"""Generate data dictionaries (codebooks) from CSV datasets."""
from .core import read_csv, build_codebook, render_markdown, render_html, load_annotations

__version__ = "0.1.0"
__all__ = ["read_csv", "build_codebook", "render_markdown", "render_html", "load_annotations"]
