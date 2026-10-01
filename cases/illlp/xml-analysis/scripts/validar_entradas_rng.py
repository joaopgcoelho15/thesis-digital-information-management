#!/usr/bin/env python3
"""Valida cada <entry> do consolidado com o academia.rng referenciado."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import re
from collections import Counter
from pathlib import Path

from lxml import etree


TEI = "http://www.tei-c.org/ns/1.0"
XML = "http://www.w3.org/XML/1998/namespace"
XML_ID = f"{{{XML}}}id"


def normalized_error(message: str) -> str:
    message = re.sub(r"'[^']{60,}'", "'…'", message)
    message = re.sub(r"\bDLP-[^\s,;]+", "DLP-…", message)
    return message


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("schema", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    schema_doc = etree.parse(str(args.schema))
    relaxng = etree.RelaxNG(schema_doc)
    counts = Counter()
    errors = Counter()
    samples = []

    with lzma.open(args.source, "rb") as stream:
        context = etree.iterparse(stream, events=("end",), tag=f"{{{TEI}}}entry", huge_tree=True)
        for _, entry in context:
            kind = "VOLP" if entry.get("volp") == "only" else "DLP"
            valid = relaxng.validate(entry)
            counts["total"] += 1
            counts[f"{kind}_total"] += 1
            counts["validas" if valid else "invalidas"] += 1
            counts[f"{kind}_{'validas' if valid else 'invalidas'}"] += 1
            if not valid:
                current_errors = [normalized_error(error.message) for error in relaxng.error_log]
                for message in current_errors:
                    errors[message] += 1
                if len(samples) < 100:
                    orth = entry.find(f"./{{{TEI}}}form/{{{TEI}}}orth")
                    samples.append({
                        "xml_id": entry.get(XML_ID, ""),
                        "lema": " ".join("".join(orth.itertext()).split()) if orth is not None else "",
                        "tipo": kind,
                        "erros": current_errors,
                    })
            parent = entry.getparent()
            entry.clear()
            if parent is not None:
                while entry.getprevious() is not None:
                    del parent[0]
        del context

    result = {
        "fonte": str(args.source),
        "esquema": str(args.schema),
        "sha256_esquema": hashlib.sha256(args.schema.read_bytes()).hexdigest(),
        "contagens": dict(counts),
        "erros": dict(errors),
        "amostras_invalidas": samples,
        "nota_metodologica": (
            "Cada entry foi validada isoladamente, como documento-raiz, porque o elemento "
            "agregador dic não pertence ao esquema academia.rng."
        ),
    }
    (args.output / "validacao_rng.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    with (args.output / "erros_validacao_rng.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["erro", "ocorrencias"])
        writer.writerows(errors.most_common())
    print(json.dumps(result["contagens"], ensure_ascii=False, indent=2))
    print("Tipos de erro distintos:", len(errors))
    for message, count in errors.most_common(20):
        print(count, message)


if __name__ == "__main__":
    main()
