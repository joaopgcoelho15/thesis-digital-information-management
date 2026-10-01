# ACL inventory redactions

The `cases/acl/analysis/Levantamento_ACL.xlsx` deposited on 1 October 2026 is a redacted publication copy, not the original working file. Its filename is retained so the material referenced by the dissertation is easy to find.

58 cells were edited. Contact names and email addresses were replaced with `[CENSURADO]`. IP addresses, contract-cost notes and access-related references to individual staff were also removed or replaced with institutional responsibility labels. Roles, services, software, institutional providers and the recorded analysis remain available. Historical notes were not updated to describe today's implementation status.

Redaction removes cell contents rather than hiding them with formatting. Unreferenced shared strings were removed from the XLSX package, and author/last-editor metadata was stripped. Screening found no original contact names/emails or IP addresses in the resulting XML parts.

All 13 worksheets, 13 charts, 446 original formulas, merges and original cell styles were retained. The spreadsheet exporter altered styles during the first pass, so its authored redacted values were merged back into the original native package. Unrelated cells were compared against the original, and chart/drawing parts remained byte-identical. Formula expressions were preserved; the resulting workbook was not recalculated in native Excel.

The original working file remains untouched outside Git. This redaction does not itself authorize institutional disclosure or make the repository public. João still reviews the deposited copy before approving public release.
