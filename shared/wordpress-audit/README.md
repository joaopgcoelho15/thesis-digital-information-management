# WordPress API audit

These Python scripts collect public WordPress data and generate an Excel workbook and a Word report. They were used for EPHEMERA and the ACL. The complementary script inspects the HTML body of posts and pages for textual inconsistencies and adds review sheets to the workbook.

## Run

Use Python 3.10 or later, from this directory.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 auditoria_wordpress.py --base-url https://example.org --site-name Example --out-dir output/example --max-post-pages 5 --skip-link-check
```

Remove `--max-post-pages 5` for the full post collection. Add `--include-post-content` to collect the HTML needed for the complementary analysis, then run:

```sh
python3 auditoria_texto_wordpress.py --base-url https://example.org --site-name Example --out-dir output/example
```

Use a separate output directory for each site. Both scripts accept `--help`.

## Scope

The scripts use the public API without administrator credentials. Available data depend on the site's API configuration. Internal links are classified using the domain passed in `--base-url`. Link checks are limited by configurable counts, and failed API requests or timeouts may leave incomplete results. Review the reports and collection errors before interpreting totals.

Generated files and API caches are ignored by Git. Review any report separately before deciding to publish it.

## Tests

```sh
python3 -m unittest discover -s . -p 'test_*.py'
```
