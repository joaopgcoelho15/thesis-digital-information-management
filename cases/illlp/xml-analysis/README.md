# XML analysis

Historical structural and Relax NG validation results for the supplied DLP/VOLP corpus. The XML, schema files and correspondence are not included. Rejected entries indicate differences between the collected schema and corpus; rejection does not establish that the lexical information itself is incorrect.

`scripts/analisar_dic_xml.py` profiles compressed XML in streaming mode. `scripts/validar_entradas_rng.py` validates entries against separately supplied schemas. Both use `lxml`; use `--help` to select input and output paths. The original working-folder defaults are not a repository installation layout.

The report retains original workspace-relative paths as provenance. Aggregate structural tables are in `data/`. These materials describe the initial analysis, not a current audit of the deployed application. Full entries and operational editorial data are excluded.
