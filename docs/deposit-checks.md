# Deposit checks, 1 October 2026

- Python source files parsed without syntax errors; JSON files parsed successfully.
- Shared WordPress link-classification tests: 3 passed.
- Wikibase extraction tests: 4 passed.
- Wikibase JavaScript runner tests passed using simulated APIs. These tests did not create or update entities on a live service.
- Selected text and Office XML components were scanned for credential literals, private-network addresses, embedded URL authentication and known token formats. No such findings remained in the selected files. This is a bounded screening step, not a full security or privacy certification.
- Working inventories with contacts/access information, emails, credentials and backups were excluded before staging.

Historical prototype verification reports were copied, not rerun against the live services. The Correia source was checked for Python syntax; its deployment was not rebuilt or compared with the current server. Additional privacy edits and replacement of the supporting repository's private history are documented in `publication-redactions.md`.
