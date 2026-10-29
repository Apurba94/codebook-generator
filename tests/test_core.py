import json
import os
import tempfile
import unittest

from codebook_generator.cli import main
from codebook_generator.core import build_codebook, read_csv, render_html, render_markdown

CSV = "participant_id,sex,age,score,comment\n" + "\n".join(
    "P%02d,%s,%d,%s,%s" % (i, "1" if i % 2 else "2", 20 + i, "-99" if i == 3 else str(i * 1.5), "note %d" % i)
    for i in range(1, 21)) + "\n"
ANN = {"sex": {"label": "Sex", "values": {"1": "Male"}}, "score": {"unit": "points", "description": "Total score."}}


class CodebookTests(unittest.TestCase):
    def setUp(self):
        self.book = {e["variable"]: e for e in build_codebook(*read_csv(CSV), annotations=ANN)}

    def test_types(self):
        self.assertEqual(self.book["sex"]["type"], "categorical")
        self.assertEqual(self.book["age"]["type"], "integer")
        self.assertEqual(self.book["score"]["type"], "continuous")
        self.assertEqual(self.book["comment"]["type"], "text")

    def test_missing_codes(self):
        s = self.book["score"]
        self.assertEqual((s["n"], s["missing"], s["missing_codes"]), (19, 1, ["-99"]))

    def test_value_labels_and_warning(self):
        levels = self.book["sex"]["levels"]
        self.assertEqual([(l["value"], l["label"], l["count"]) for l in levels], [("1", "Male", 10), ("2", "", 10)])
        self.assertIn("values without labels: 2", self.book["sex"]["warning"])

    def test_default_label(self):
        self.assertEqual(self.book["participant_id"]["label"], "Participant id")

    def test_renderers(self):
        book = build_codebook(*read_csv(CSV), annotations=ANN)
        md = render_markdown(book)
        self.assertIn("| 3 | `age` | Age | integer |  | 20 | 0 | range 21 to 40", md)
        self.assertIn("- **score**: Total score.", md)
        self.assertIn("<code>sex</code>", render_html(book))

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as d:
            p, a, out = (os.path.join(d, n) for n in ("d.csv", "a.json", "cb.json"))
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(CSV)
            with open(a, "w", encoding="utf-8") as fh:
                json.dump(ANN, fh)
            main([p, "-a", a, "-f", "json", "-o", out])
            with open(out, encoding="utf-8") as fh:
                self.assertEqual(len(json.load(fh)), 5)


if __name__ == "__main__":
    unittest.main()
