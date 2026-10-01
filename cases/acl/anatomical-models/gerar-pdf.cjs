const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

const sourcePath = path.join(__dirname, "modelos-anatomicos-corrido.html");
const outputPath = path.resolve(__dirname, "..", "output", "pdf", "modelos-anatomicos-corrido.pdf");

async function generatePdf() {
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    executablePath: chromium.executablePath(),
  });

  try {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 720 },
      deviceScaleFactor: 1,
    });

    await page.goto(pathToFileURL(sourcePath).href, { waitUntil: "load" });
    await page.evaluate(async () => {
      await Promise.all(
        Array.from(document.images, (image) => {
          if (image.complete) return Promise.resolve();
          return new Promise((resolve) => {
            image.addEventListener("load", resolve, { once: true });
            image.addEventListener("error", resolve, { once: true });
          });
        })
      );
    });

    await page.emulateMedia({ media: "screen" });

    const dimensions = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a[href^="#"]'));

      return {
        width: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
        brokenImages: Array.from(document.images).filter(
          (image) => !image.complete || image.naturalWidth === 0
        ).length,
        internalLinks: links.length,
        brokenInternalLinks: links.filter((link) => {
          const targetId = decodeURIComponent(link.hash.slice(1));
          return !targetId || !document.getElementById(targetId);
        }).length,
        overviewLinks: document.querySelectorAll("a.overview-marker").length,
        detailLinks: document.querySelectorAll("a.detail-marker").length,
        returnLinks: document.querySelectorAll("a.detail-number").length,
      };
    });

    if (dimensions.brokenImages > 0) {
      throw new Error(`${dimensions.brokenImages} imagem(ns) não foram carregadas.`);
    }

    if (dimensions.brokenInternalLinks > 0) {
      throw new Error(`${dimensions.brokenInternalLinks} ligação(ões) interna(s) sem destino.`);
    }

    await page.pdf({
      path: outputPath,
      width: `${dimensions.width}px`,
      height: `${dimensions.height}px`,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
      printBackground: true,
      preferCSSPageSize: false,
      displayHeaderFooter: false,
    });

    console.log(`PDF criado: ${outputPath}`);
    console.log(`Dimensões: ${dimensions.width} x ${dimensions.height} px`);
    console.log(`Ligações internas: ${dimensions.internalLinks}`);
    console.log(
      `Marcadores: ${dimensions.overviewLinks} gerais, ` +
        `${dimensions.detailLinks} detalhados e ${dimensions.returnLinks} regressos`
    );
  } finally {
    await browser.close();
  }
}

generatePdf().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
