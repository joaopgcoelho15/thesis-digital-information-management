# Prototype deposit notes

This selection is not a backup of a running installation. Original READMEs describe the experiments and retain references to some files available only in the working environment.

The Tainacan and Wikibase folders remain siblings because preparation scripts use that relationship. Tainacan materials include import scripts, CSV examples, verification outputs and the custom theme. Credentials, Docker volumes, SQL backups, downloaded media and the separately licensed WordPress theme are excluded. Reproduction requires a separately configured local WordPress/Tainacan environment and the media referenced by each manifest.

Wikibase materials preserve batch-import source, public snapshots and generated plans. Review the target instance and original workflow before running write scripts. Local PCP images and the redundant large `published_entities.json` snapshot are excluded; ID mappings and verification summaries are retained.

Batch imports were tested. Continuous synchronization from WordPress to Wikibase was a proposal, not a validated operational workflow. This deposit does not claim that editing a WordPress post automatically updates the deployed Wikibase. The earlier experimental synchronization plugin is not presented as a finished solution here.

FOTOSNERO's CSV is an import example. Its preparation script expects a separately supplied ContentE export in `Downloads/FOTOSNERO`; that export and media are absent. Historical verification outputs are not fresh tests of this repository.
