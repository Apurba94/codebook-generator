# codebook-generator

**Produce the data dictionary (codebook) that data repositories, journals and collaborators
ask for, directly from a CSV file, merged with your own variable labels, units and value labels.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

FAIR data sharing requires documentation: what each variable means, its unit, how categories are
coded, which codes mean "missing". Codebooks are often written once by hand and then drift out of
date as the dataset changes. Generating them from the data plus a small annotations file keeps them
correct.

## Features

- Variable type detection: categorical (with counts and %), integer, continuous (range, mean, SD), text, empty
- Missing value detection including sentinel codes (`-99`, `-999`, `999`, `NA` ...)
- Annotations JSON for labels, descriptions, units and value labels; warns about undocumented codes
- Markdown, HTML or JSON output, ready for a repository README or supplementary material

## Usage

```bash
pip install .
codebook-generator survey.csv -a annotations.json -o CODEBOOK.md
codebook-generator survey.csv -f html -o codebook.html
```

Annotations example:

```json
{"sex": {"label": "Sex at birth", "values": {"1": "Male", "2": "Female"}},
 "bmi": {"label": "Body mass index", "unit": "kg/m2", "description": "Measured at baseline."}}
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
