"""Codebook construction: variable types, value labels, ranges, missingness and annotations."""
import csv
import html
import io
import json
import re
import statistics
from collections import Counter

MISSING = {"", "na", "n/a", "nan", "null", "none", "-", ".", "-99", "-999", "999"}


def read_csv(text):
    try:
        delim = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    return rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]


def load_annotations(path):
    """Annotations JSON: {variable: {"label": ..., "description": ..., "unit": ..., "values": {"1": "Male"}}}."""
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _num(v):
    try:
        return float(v)
    except ValueError:
        return None


def build_codebook(header, rows, annotations=None, max_levels=15, missing_codes=MISSING):
    annotations = annotations or {}
    book = []
    for j, name in enumerate(header):
        vals = [(r[j] if j < len(r) else "").strip() for r in rows]
        miss = [v for v in vals if v.lower() in missing_codes]
        present = [v for v in vals if v.lower() not in missing_codes]
        nums = [_num(v) for v in present]
        ann = annotations.get(name, {})
        entry = {"variable": name, "position": j + 1, "label": ann.get("label", re.sub(r"[_.]+", " ", name).strip().capitalize()),
                 "description": ann.get("description", ""), "unit": ann.get("unit", ""), "n": len(present),
                 "missing": len(miss), "missing_codes": sorted(set(miss) - {""}),
                 "distinct": len(set(present))}
        value_labels = {str(k): v for k, v in ann.get("values", {}).items()}
        counts = Counter(present)
        if present and all(x is not None for x in nums) and (len(counts) > max_levels and not value_labels):
            entry["type"] = "integer" if all(x == int(x) for x in nums) else "continuous"
            entry.update({"min": min(nums), "max": max(nums), "mean": round(statistics.fmean(nums), 4),
                          "sd": round(statistics.stdev(nums), 4) if len(nums) > 1 else 0.0})
        elif present and len(counts) <= max_levels or value_labels:
            entry["type"] = "categorical"
            levels = sorted(counts, key=lambda v: (_num(v) is None, _num(v) if _num(v) is not None else 0, v))
            entry["levels"] = [{"value": v, "label": value_labels.get(v, ""), "count": counts[v],
                                "percent": round(100.0 * counts[v] / len(present), 1)} for v in levels]
            undocumented = [l["value"] for l in entry["levels"] if value_labels and not l["label"]]
            if undocumented:
                entry["warning"] = "values without labels: " + ", ".join(undocumented)
        elif not present:
            entry["type"] = "empty"
        else:
            entry["type"] = "text"
            entry["example"] = present[0][:40]
            entry["max_length"] = max(len(v) for v in present)
        book.append(entry)
    return book


def render_markdown(book, title="Codebook", dataset_note=""):
    out = ["# %s" % title, ""]
    if dataset_note:
        out += [dataset_note, ""]
    out += ["| # | Variable | Label | Type | Unit | Valid N | Missing | Details |", "|---|---|---|---|---|---|---|---|"]
    for e in book:
        if e["type"] in ("integer", "continuous"):
            d = "range %g to %g; mean %g (SD %g)" % (e["min"], e["max"], e["mean"], e["sd"])
        elif e["type"] == "categorical":
            d = "; ".join("%s%s: %d" % (l["value"], " = " + l["label"] if l["label"] else "", l["count"]) for l in e["levels"])
        elif e["type"] == "text":
            d = "free text, max length %d" % e["max_length"]
        else:
            d = "no data"
        miss = str(e["missing"]) + (" (codes: %s)" % ", ".join(e["missing_codes"]) if e["missing_codes"] else "")
        out.append("| %d | `%s` | %s | %s | %s | %d | %s | %s |" % (e["position"], e["variable"], e["label"], e["type"],
                                                                 e["unit"], e["n"], miss, d.replace("|", "/")))
    notes = [e for e in book if e.get("description") or e.get("warning")]
    if notes:
        out += ["", "## Variable notes", ""]
        for e in notes:
            out.append("- **%s**: %s%s" % (e["variable"], e.get("description", ""),
                                          (" *Warning: %s*" % e["warning"]) if e.get("warning") else ""))
    return "\n".join(out) + "\n"


def render_html(book, title="Codebook"):
    rows = []
    for e in book:
        if e["type"] == "categorical":
            det = "<ul>" + "".join("<li>%s%s (n=%d, %.1f%%)</li>" % (html.escape(l["value"]),
                                   " = " + html.escape(l["label"]) if l["label"] else "", l["count"], l["percent"])
                                   for l in e["levels"]) + "</ul>"
        elif e["type"] in ("integer", "continuous"):
            det = "range %g&ndash;%g, mean %g (SD %g)" % (e["min"], e["max"], e["mean"], e["sd"])
        else:
            det = html.escape(e.get("example", ""))
        rows.append("<tr><td>%d</td><td><code>%s</code></td><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td>"
                    "<td>%d</td><td>%d</td><td>%s</td></tr>" % (e["position"], html.escape(e["variable"]),
                    html.escape(e["label"]), html.escape(e["description"]), e["type"], html.escape(e["unit"]),
                    e["n"], e["missing"], det))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>%s</title><style>body{font-family:sans-serif;"
            "margin:2em}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 8px;vertical-align:top}"
            "th{background:#eee}</style></head><body><h1>%s</h1><table><tr><th>#</th><th>Variable</th><th>Label</th>"
            "<th>Type</th><th>Unit</th><th>Valid N</th><th>Missing</th><th>Values</th></tr>%s</table></body></html>\n") % (
        html.escape(title), html.escape(title), "".join(rows))
