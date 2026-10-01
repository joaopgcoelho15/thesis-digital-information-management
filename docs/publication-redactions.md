# Publication redactions, 1 October 2026

Original working files were not changed.

- `Manual_Procedimentos_Recursos_Eletronicos_publico.docx`: reconstructed without embedded screenshots, comments, revision history or author metadata. Authentication placeholders, administrative URLs and personal contacts were removed; procedure text and dates were retained. Screenshots were excluded rather than visually covered.
- `ACL_Tarefas_a_Discutir_publico.docx`: reconstructed without metadata, generated table of contents, comments or old relationships. Server-access details and personal contacts were replaced with omissions or institutional roles. Historical findings were not silently updated.
- `ACL – Caso Atual.docx`: reconstructed with the same privacy rules, removing its server address.
- `Auditoria_Qualidade_Ephemera.xlsx` and `Ephemera - Estatísticas 20251222.xlsx`: email addresses and IP addresses redacted in XML text and relationship targets. Public bibliographic names were retained.
- `database-202606220726-public.xlsx`: only bibliographic `Sheet1` was retained, with 1,869 records. `Sheet2`, `Sheet3`, `Chat`, `Viewed` and `datas` were excluded. `description`, `carreira`, `notas`, `registo`, `estado` and `editor_name` remain as headers with blank values, removing internal activity, notes and editor identifiers. Identifiers, bibliographic descriptions and public resource links were retained. This historical public copy is not the current validated production database.
- `modelos-anatomicos.pdf`: included unchanged after the author confirmed this version. No email/IP patterns, embedded files or form fields were found in screening.

Code and reachable Git history were screened for common token formats, credential URLs, private keys, credential literals and private filesystem paths. Loopback and local bind addresses in example deployments are not institutional server addresses. Screening reduces disclosure risk but is not a comprehensive security audit.

With the author's authorization, the former private history of this supporting-materials repository was saved in a local Git bundle outside the repository, then replaced with a new root containing the reviewed files. This removes unredacted versions from the branch's reachable public history; it does not guarantee immediate deletion of every unreachable cached object on GitHub. Operational dictionary data remain private.
