"""Command-line interface for codebook-generator."""
import argparse
import json
import os
import sys

from .core import build_codebook, load_annotations, read_csv, render_html, render_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="codebook-generator", description="Create a data dictionary from a CSV file.")
    ap.add_argument("csvfile")
    ap.add_argument("-a", "--annotations", help="JSON with labels, descriptions, units and value labels")
    ap.add_argument("-f", "--format", choices=["markdown", "html", "json"], default="markdown")
    ap.add_argument("--max-levels", type=int, default=15, help="max distinct values treated as categorical")
    ap.add_argument("--note", default="", help="dataset description shown under the title")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    with open(args.csvfile, encoding="utf-8-sig", errors="replace", newline="") as fh:
        header, rows = read_csv(fh.read())
    ann = load_annotations(args.annotations) if args.annotations else None
    book = build_codebook(header, rows, ann, args.max_levels)
    title = "Codebook: " + os.path.basename(args.csvfile)
    if args.format == "json":
        out = json.dumps(book, indent=2) + "\n"
    elif args.format == "html":
        out = render_html(book, title)
    else:
        out = render_markdown(book, title, args.note or "%d records, %d variables." % (len(rows), len(header)))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0
