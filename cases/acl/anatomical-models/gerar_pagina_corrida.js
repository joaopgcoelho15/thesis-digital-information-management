const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = __dirname;
const codePath = path.join(root, "js", "code.js");
const outputPath = path.join(root, "modelos-anatomicos-corrido.html");

const code = fs.readFileSync(codePath, "utf8");
const start = code.indexOf("var json =");
const end = code.indexOf("var app =", start);

if (start === -1 || end === -1) {
  throw new Error("Nao foi possivel localizar o bloco var json em js/code.js");
}

const context = {};
vm.createContext(context);
vm.runInContext(code.slice(start, end), context);

const data = context.json;

const sectionConfig = {
  "Locomoção": {
    title: "Locomoção",
    folder: "locomocao",
    overview: "locomocao.jpg",
    intro: "Anatomia da locomoção.",
  },
  "Coração": {
    title: "Coração e Vasos",
    folder: "coracao",
    overview: "coracao.jpg",
    intro: "Anatomia do coração e vasos.",
  },
  "Cabeça": {
    title: "Relação",
    folder: "cabeca",
    overview: "cabeca.jpg",
    intro: "Anatomia do sistema nervoso e órgãos dos sentidos.",
  },
  "Orgãos": {
    title: "Órgãos",
    folder: "orgaos",
    overview: "orgaos.jpg",
    intro: "Anatomia dos órgãos.",
  },
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function slug(value) {
  return String(value)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function jpegSize(filePath) {
  const buffer = fs.readFileSync(filePath);
  let offset = 2;

  if (buffer[0] !== 0xff || buffer[1] !== 0xd8) {
    throw new Error(`Imagem nao parece ser JPEG: ${filePath}`);
  }

  while (offset < buffer.length) {
    if (buffer[offset] !== 0xff) {
      offset += 1;
      continue;
    }

    const marker = buffer[offset + 1];
    const length = buffer.readUInt16BE(offset + 2);

    if (
      marker === 0xc0 ||
      marker === 0xc1 ||
      marker === 0xc2 ||
      marker === 0xc3 ||
      marker === 0xc5 ||
      marker === 0xc6 ||
      marker === 0xc7 ||
      marker === 0xc9 ||
      marker === 0xca ||
      marker === 0xcb ||
      marker === 0xcd ||
      marker === 0xce ||
      marker === 0xcf
    ) {
      return {
        width: buffer.readUInt16BE(offset + 7),
        height: buffer.readUInt16BE(offset + 5),
      };
    }

    offset += 2 + length;
  }

  throw new Error(`Nao foi possivel ler dimensoes da imagem: ${filePath}`);
}

function imageSize(folder, filename) {
  return jpegSize(path.join(root, "img", folder, filename));
}

function pointStyle(point, size, offsets = {}) {
  const left = ((Number(point.x) - (offsets.x || 0)) / size.width) * 100;
  const top = ((Number(point.y) - (offsets.y || 0)) / size.height) * 100;
  return `left:${left.toFixed(4)}%;top:${top.toFixed(4)}%;`;
}

function detailsCount(items) {
  return items.reduce((total, item) => total + (item.detalhe || []).length, 0);
}

function overviewMarkers(items, image) {
  return items
    .map((item, index) => `
      <a class="overview-marker" href="#${slug(item.texto)}" style="${pointStyle({ ...item, y: Number(item.y) + 12 }, image)}" aria-label="${escapeHtml(item.texto)}">
        ${index + 1}
      </a>`)
    .join("");
}

function detailMarkers(details, image, offsets) {
  return (details || [])
    .map((detail) => `
      <span class="detail-marker" style="${pointStyle(detail, image, offsets)}">${escapeHtml(detail.numero)}</span>`)
    .join("");
}

function detailList(details) {
  return (details || [])
    .map((detail) => `
      <li>
        <span class="detail-number">${escapeHtml(detail.numero)}</span>
        <div>
          <h4>${escapeHtml(detail.titulo)}</h4>
          ${detail.texto ? `<p>${escapeHtml(detail.texto)}</p>` : ""}
        </div>
      </li>`)
    .join("");
}

function sectionHtml(key, items) {
  const config = sectionConfig[key];
  const overviewImage = imageSize(config.folder, config.overview);
  return `
    <section class="section" id="${slug(config.title)}">
      <header class="section-header">
        <p class="eyebrow">Galeria</p>
        <h2>${escapeHtml(config.title)}</h2>
        <p>${escapeHtml(config.intro)} Inclui ${items.length} vistas e ${detailsCount(items)} pontos descritos.</p>
      </header>

      <figure class="overview">
        <div class="image-map overview-map">
          <img src="img/${config.folder}/${config.overview}" alt="${escapeHtml(config.title)} - imagem geral">
          ${overviewMarkers(items, overviewImage)}
        </div>
        <figcaption>Imagem geral com a localização das vistas detalhadas.</figcaption>
      </figure>

      <div class="views">
        ${items
          .map((item, index) => {
            const detailImage = imageSize(config.folder, item.img);
            const offsets = {
              x: Math.max(0, (692 - detailImage.width) / 2),
              y: 66,
            };
            return `
            <article class="view" id="${slug(item.texto)}">
              <div class="view-heading">
                <span class="view-index">${index + 1}</span>
                <div>
                  <h3>${escapeHtml(item.texto)}</h3>
                  <p>${(item.detalhe || []).length} pontos identificados</p>
                </div>
              </div>
              <div class="view-grid">
                <figure>
                  <div class="image-map detail-map">
                    <img src="img/${config.folder}/${item.img}" alt="${escapeHtml(item.texto)}">
                    ${detailMarkers(item.detalhe, detailImage, offsets)}
                  </div>
                  <figcaption>${escapeHtml(config.title)} - ${escapeHtml(item.texto)}</figcaption>
                </figure>
                <ol class="detail-list">
                  ${detailList(item.detalhe)}
                </ol>
              </div>
            </article>`;
          })
          .join("")}
      </div>
    </section>`;
}

const toc = Object.entries(data)
  .map(([key, items]) => {
    const config = sectionConfig[key];
    return `
      <a href="#${slug(config.title)}">
        <strong>${escapeHtml(config.title)}</strong>
        <span>${items.length} vistas · ${detailsCount(items)} pontos</span>
      </a>`;
  })
  .join("");

const body = Object.entries(data)
  .map(([key, items]) => sectionHtml(key, items))
  .join("");

const html = `<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Exposição - Modelos Anatómicos</title>
  <style>
    :root {
      --ink: #1f2328;
      --muted: #5c6670;
      --line: #d9dde3;
      --paper: #ffffff;
      --soft: #f5f1e8;
      --accent: #b18a18;
      --accent-dark: #6f5410;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: #e4e4e4;
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.45;
    }

    img {
      display: block;
      max-width: 100%;
      height: auto;
    }

    a {
      color: inherit;
    }

    .page {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      background: var(--paper);
      min-height: 100vh;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.16);
    }

    .hero {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 34px;
      align-items: center;
      padding: 42px 48px 34px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(90deg, #f8f5ee, #fff);
    }

    .hero img {
      width: 150px;
      margin-bottom: 22px;
    }

    .hero h1 {
      margin: 0;
      font-size: 42px;
      text-transform: uppercase;
      line-height: 1.05;
    }

    .hero .subtitle {
      display: inline-block;
      margin-top: 12px;
      padding: 7px 12px;
      background: #f0c43d;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 22px;
      font-style: italic;
      font-weight: 700;
    }

    .hero p {
      margin: 0;
      max-width: 720px;
      color: #30363d;
      font-size: 15px;
    }

    .toc {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      padding: 24px 48px;
      border-bottom: 1px solid var(--line);
    }

    .toc a {
      min-height: 76px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      text-decoration: none;
      background: #fff;
    }

    .toc strong,
    .toc span {
      display: block;
    }

    .toc strong {
      font-size: 17px;
      margin-bottom: 7px;
    }

    .toc span {
      color: var(--muted);
      font-size: 13px;
    }

    .section {
      padding: 42px 48px 12px;
      border-bottom: 1px solid var(--line);
    }

    .section-header {
      max-width: 820px;
      margin-bottom: 24px;
    }

    .eyebrow {
      margin: 0 0 4px;
      color: var(--accent-dark);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h2 {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 34px;
      font-style: italic;
    }

    .section-header p:last-child {
      margin: 10px 0 0;
      color: var(--muted);
    }

    figure {
      margin: 0;
    }

    figcaption {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }

    .overview {
      max-width: 720px;
      margin-bottom: 34px;
    }

    .image-map {
      position: relative;
      display: inline-block;
      max-width: 100%;
      background: #f1f1f1;
      line-height: 0;
      overflow: visible;
    }

    .image-map img {
      width: auto;
      max-height: 780px;
    }

    .overview-marker,
    .detail-marker {
      position: absolute;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 26px;
      padding: 0 5px;
      border: 2px solid var(--accent);
      border-radius: 999px;
      background: #fff;
      color: var(--accent-dark);
      font-size: 11px;
      font-weight: 700;
      line-height: 1;
      text-decoration: none;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
    }

    .overview-marker {
      min-width: 30px;
      width: 36px;
      height: 36px;
      padding: 0;
      background: #f0c43d;
      color: #1f2328;
      font-size: 14px;
    }

    .views {
      display: grid;
      gap: 28px;
    }

    .view {
      break-inside: avoid;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
    }

    .view-heading {
      display: flex;
      gap: 14px;
      align-items: flex-start;
      margin-bottom: 18px;
    }

    .view-index {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 34px;
      height: 34px;
      border-radius: 999px;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      flex: 0 0 auto;
    }

    .view h3 {
      margin: 0;
      font-size: 21px;
      line-height: 1.25;
    }

    .view-heading p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .view-grid {
      display: grid;
      grid-template-columns: minmax(320px, 52%) 1fr;
      gap: 22px;
      align-items: start;
    }

    .detail-list {
      margin: 0;
      padding: 0;
      list-style: none;
      display: grid;
      gap: 10px;
    }

    .detail-list li {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 10px;
      padding: 10px 0;
      border-bottom: 1px solid #eceff3;
    }

    .detail-number {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 28px;
      height: 28px;
      padding: 0 6px;
      border: 2px solid var(--accent);
      border-radius: 999px;
      color: var(--accent-dark);
      font-size: 12px;
      font-weight: 700;
    }

    .detail-list h4 {
      margin: 0;
      font-size: 15px;
      line-height: 1.3;
    }

    .detail-list p {
      margin: 3px 0 0;
      color: #3f464e;
      font-size: 13px;
    }

    .footer {
      padding: 28px 48px 42px;
      color: var(--muted);
      font-size: 12px;
    }

    @media (max-width: 900px) {
      .page {
        width: 100%;
      }

      .hero,
      .toc,
      .view-grid {
        grid-template-columns: 1fr;
      }

      .hero,
      .toc,
      .section,
      .footer {
        padding-left: 22px;
        padding-right: 22px;
      }
    }

    @media print {
      @page {
        size: A4;
        margin: 14mm;
      }

      body {
        background: #fff;
      }

      .page {
        width: auto;
        box-shadow: none;
      }

      .hero,
      .section,
      .footer {
        padding-left: 0;
        padding-right: 0;
      }

      .toc {
        display: none;
      }

      .section {
        break-before: page;
      }

      .view {
        break-inside: avoid;
        page-break-inside: avoid;
      }

      .view-grid {
        grid-template-columns: 48% 1fr;
      }

      .image-map img {
        max-height: 210mm;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div>
        <img src="img/home/logo.png" alt="Academia das Ciências de Lisboa">
        <h1>Exposição</h1>
        <div class="subtitle">Modelos Anatómicos</div>
      </div>
      <p>
        A descrição dos modelos foi elaborada pelo Professor Doutor José António Esperança Pina
        e pela Professora Doutora Maria Alexandre Bettencourt Pires. O registo fotográfico foi
        realizado pelo Senhor Paulo Bastos. Esta versão apresenta, de forma corrida, os conteúdos
        que na versão interativa são abertos através dos pontos de detalhe.
      </p>
    </header>
    <nav class="toc" aria-label="Índice">
      ${toc}
    </nav>
    ${body}
    <footer class="footer">
      Página estática gerada a partir dos ficheiros HTML, CSS, JavaScript e imagens da exposição
      “Modelos Anatómicos”.
    </footer>
  </main>
</body>
</html>
`;

fs.writeFileSync(outputPath, html, "utf8");
console.log(`Criado: ${outputPath}`);
