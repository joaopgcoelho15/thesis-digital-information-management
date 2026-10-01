# Anatomical-model representation

`gerar_pagina_corrida.js` assembles a continuous HTML representation from the recovered presentation. `gerar-pdf.cjs` uses Playwright/Chromium to print it and checks missing images and internal link targets first.

`modelos-anatomicos.pdf` is the continuous, single-page PDF confirmed by the author as the version supplied to the ACL. The recovered website and separate image assets are not bundled. Supply the original inputs in the layout expected by the scripts. The PDF script reads `modelos-anatomicos-corrido.html` alongside itself and writes `../output/pdf/modelos-anatomicos-corrido.pdf`. Install Playwright and Chromium in a separate local Node environment before running it.

These scripts document the representation process. They do not recover files from the former server, deposit material in RCAAP or assign a DOI. Access credentials and correspondence are excluded.
