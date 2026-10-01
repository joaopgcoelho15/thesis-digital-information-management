from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = Path("/private/tmp/ephemera-pcp-1975")
IMAGE_DIR = ROOT / "images"

SOURCE_PAGE = (
    "https://ephemerajpp.com/2014/05/24/"
    "eleicoes-para-assembleia-constituinte-1975-pcp/"
)

RECORDS = [
    {
        "local_key": "PCP1975-001",
        "source_file": "01.jpg",
        "source_filename": "zppaldef30047_rm.jpg",
        "attachment_id": 141267,
        "title": "Junta a tua à nossa voz — Vota PCP",
        "description": "Cartaz eleitoral do PCP com símbolo partidário sobre fundo verde.",
    },
    {
        "local_key": "PCP1975-002",
        "source_file": "02.jpg",
        "source_filename": "zppaldef8901_resize.jpg",
        "attachment_id": 141269,
        "title": "O voto — pela liberdade, pela democracia, pelo socialismo",
        "description": "Cartaz eleitoral do PCP centrado no ato de votar.",
    },
    {
        "local_key": "PCP1975-003",
        "source_file": "03.jpg",
        "source_filename": "zppaldef8889_resize.jpg",
        "attachment_id": 141270,
        "title": "Mulher, nas tuas mãos o futuro dos teus filhos — Vota PCP",
        "description": "Cartaz eleitoral do PCP dirigido às mulheres.",
    },
    {
        "local_key": "PCP1975-004",
        "source_file": "04.jpg",
        "source_filename": "zppaldef8850_resize.jpg",
        "attachment_id": 141268,
        "title": "Dá mais força à liberdade — Vota PCP",
        "description": "Cartaz da Direção da Organização Regional de Lisboa do PCP.",
    },
    {
        "local_key": "PCP1975-005",
        "source_file": "05.jpg",
        "source_filename": "zppaldef0011_brq.jpg",
        "attachment_id": 141266,
        "title": "Por nós e por ti — Vota PCP — Junta a tua à nossa voz",
        "description": "Cartaz eleitoral do PCP com retrato de um homem idoso.",
    },
    {
        "local_key": "PCP1975-006",
        "source_file": "06.jpg",
        "source_filename": "img_0190.jpg",
        "attachment_id": 141279,
        "title": "Por nós e por ti — Vota PCP — Junta a tua à nossa voz",
        "description": "Variante de cartaz eleitoral do PCP com imagem de uma família.",
    },
    {
        "local_key": "PCP1975-007",
        "source_file": "07.jpg",
        "source_filename": "zppaldefart0047_br.jpg",
        "attachment_id": 141277,
        "title": "Para construir a democracia — Junta a tua à nossa voz",
        "description": "Cartaz eleitoral do PCP com três trabalhadores industriais.",
    },
    {
        "local_key": "PCP1975-008",
        "source_file": "08.jpg",
        "source_filename": "zppaldef0058_rm.jpg",
        "attachment_id": 141278,
        "title": "Para construir a democracia — Junta a tua à nossa voz",
        "description": "Variante de cartaz eleitoral do PCP com trabalhadores numa fábrica.",
    },
    {
        "local_key": "PCP1975-009",
        "source_file": "09.jpg",
        "source_filename": "zppaldef8843_resize.jpg",
        "attachment_id": 141386,
        "title": "Vota PCP — Por um Portugal democrático a caminho do socialismo",
        "description": "Cartaz eleitoral programático do PCP para as eleições constituintes de 1975.",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    for record in RECORDS:
        source = SOURCE_DIR / record["source_file"]
        if not source.exists():
            raise FileNotFoundError(f"Ficheiro de origem em falta: {source}")

        destination = IMAGE_DIR / f"{record['local_key']}.jpg"
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.save(destination, "JPEG", quality=95, optimize=True)
            width, height = image.size

        item = {
            **record,
            "source_post_id": 141265,
            "source_page_url": SOURCE_PAGE,
            "source_image_url": (
                "https://ephemerajpp.com/wp-content/uploads/2014/05/"
                + record["source_filename"]
            ),
            "local_file": f"images/{destination.name}",
            "width_px": width,
            "height_px": height,
            "mime_type": "image/jpeg",
            "date": "1975",
            "language": "português",
            "country": "Portugal",
            "object_type": "cartaz político",
            "issuing_body": "Partido Comunista Português",
            "event": "Eleições para a Assembleia Constituinte Portuguesa de 1975",
            "collection": "Cartazes do PCP — Eleições Constituintes de 1975",
            "rights_status": "não determinado no post de origem",
            "source_retrieved": "2026-08-18",
            "sha256": sha256(destination),
        }
        item.pop("source_file")
        manifest.append(item)

    output = {
        "dataset": "PCP — Eleições para a Assembleia Constituinte — 1975",
        "source_page": SOURCE_PAGE,
        "source_post_id": 141265,
        "record_count": len(manifest),
        "rights_note": (
            "O post de origem não apresenta uma licença explícita para as imagens. "
            "As cópias locais destinam-se à prova de conceito; a publicação deve "
            "manter a proveniência e confirmar autorização/licença com o Ephemera."
        ),
        "wikidata": {
            "political_poster": "Q95720408",
            "portuguese_communist_party": "Q769829",
            "constituent_election_1975": "Q3179037",
            "portugal": "Q45",
        },
        "records": manifest,
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
