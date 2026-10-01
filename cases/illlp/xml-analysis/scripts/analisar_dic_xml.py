#!/usr/bin/env python3
"""Perfil estrutural e controlo de qualidade do dic.xml.xz.

O processamento é feito em streaming para não criar uma cópia descomprimida
de ~187 MB nem carregar o corpus integral em memória.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from lxml import etree


TEI = "http://www.tei-c.org/ns/1.0"
DACL = "http://dacl.zbr.pt/annotations"
XML = "http://www.w3.org/XML/1998/namespace"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS = {"tei": TEI, "dacl": DACL}
XML_ID = f"{{{XML}}}id"
XML_LANG = f"{{{XML}}}lang"
PLACEHOLDER_RE = re.compile(r"^\s*(?:\[\s*\.\.\.\s*\]|\.\.\.|\?{2,})\s*$")
DLP_ID_RE = re.compile(r"^DLP-[^\s]+_\d+-[a-z0-9]+(?:-\d+)*$")
DATE_ATTRS = {"forValidation", "revisto", "revised", "date"}
LOW_CARDINALITY_ATTRS = {
    "type", "status", "volp", "n", "ana", "rend", "digital", "ao",
    "foreign", "subtype", "unit", "level", "mode", "place",
}


def compact_text(el: etree._Element) -> str:
    return " ".join("".join(el.itertext()).split())


def local_name(qname: str) -> str:
    return etree.QName(qname).localname if qname.startswith("{") else qname


def display_name(qname: str) -> str:
    if not qname.startswith("{"):
        return qname
    q = etree.QName(qname)
    prefixes = {TEI: "tei", DACL: "dacl", XML: "xml", XSI: "xsi"}
    return f"{prefixes.get(q.namespace, q.namespace)}:{q.localname}"


def entry_context(entry: etree._Element) -> dict[str, str]:
    entry_id = entry.get(XML_ID, "")
    orths = [compact_text(x) for x in entry.xpath("./tei:form/tei:orth", namespaces=NS)]
    return {"xml_id": entry_id, "lema": " | ".join(x for x in orths if x)[:500]}


def add_sample(samples: dict[str, list[dict]], category: str, item: dict, limit: int = 25) -> None:
    if len(samples[category]) < limit:
        samples[category].append(item)


def parse_date(value: str) -> bool:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def scan_processing_instructions(source: Path) -> tuple[Counter, list[dict[str, str]]]:
    pattern = re.compile(
        rb"<\?xml-model\s+(?P<body>.*?)\?>", re.DOTALL
    )
    attr_pattern = re.compile(rb"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(['\"])(.*?)\2", re.DOTALL)
    counts: Counter = Counter()
    examples: list[dict[str, str]] = []
    with lzma.open(source, "rb") as stream:
        carry = b""
        while chunk := stream.read(1024 * 1024):
            data = carry + chunk
            safe_end = max(0, len(data) - 2048)
            for match in pattern.finditer(data[:safe_end]):
                attrs = {
                    key.decode("utf-8", "replace"): value.decode("utf-8", "replace")
                    for key, _, value in attr_pattern.findall(match.group("body"))
                }
                signature = " | ".join(f"{k}={attrs[k]}" for k in sorted(attrs))
                counts[signature] += 1
                if len(examples) < 20:
                    examples.append(attrs)
            carry = data[safe_end:]
        for match in pattern.finditer(carry):
            attrs = {
                key.decode("utf-8", "replace"): value.decode("utf-8", "replace")
                for key, _, value in attr_pattern.findall(match.group("body"))
            }
            signature = " | ".join(f"{k}={attrs[k]}" for k in sorted(attrs))
            counts[signature] += 1
            if len(examples) < 20:
                examples.append(attrs)
    return counts, examples


def write_counter_csv(path: Path, headers: list[str], rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def analyze(source: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    element_counts: Counter = Counter()
    attribute_counts: Counter = Counter()
    attribute_values: dict[str, Counter] = defaultdict(Counter)
    relation_counts: Counter = Counter()
    depth_counts: Counter = Counter()
    empty_counts: Counter = Counter()
    placeholder_counts: Counter = Counter()
    namespaces: Counter = Counter()
    status_counts: Counter = Counter()
    volp_counts: Counter = Counter()
    gram_counts: Counter = Counter()
    usage_type_counts: Counter = Counter()
    ref_type_counts: Counter = Counter()
    quote_type_counts: Counter = Counter()
    note_type_counts: Counter = Counter()
    sense_ana_counts: Counter = Counter()
    date_attribute_counts: Counter = Counter()
    date_format_counts: Counter = Counter()
    entry_kind_status: Counter = Counter()
    kind_element_counts: Counter = Counter()
    kind_attribute_counts: Counter = Counter()
    anomaly_counts: Counter = Counter()
    samples: dict[str, list[dict]] = defaultdict(list)
    ids: set[str] = set()
    duplicate_ids: Counter = Counter()
    entry_ids: set[str] = set()
    lemma_to_entry_ids: dict[str, list[str]] = defaultdict(list)
    textual_refs: list[tuple[str, str, str]] = []
    entries = senses = definitions = 0
    direct_root_entries = 0
    max_depth = 0
    root_name = ""
    parse_error = None

    def flag(category: str, item: dict) -> None:
        anomaly_counts[category] += 1
        add_sample(samples, category, item)

    compressed_hash = hashlib.sha256()
    with source.open("rb") as raw:
        while block := raw.read(1024 * 1024):
            compressed_hash.update(block)

    try:
        with lzma.open(source, "rb") as stream:
            context = etree.iterparse(
                stream,
                events=("start", "end"),
                recover=False,
                huge_tree=True,
                remove_comments=False,
            )
            depth = 0
            for event, el in context:
                if not isinstance(el.tag, str):
                    continue
                if event == "start":
                    depth += 1
                    max_depth = max(max_depth, depth)
                    if not root_name:
                        root_name = display_name(el.tag)
                    name = display_name(el.tag)
                    element_counts[name] += 1
                    depth_counts[(name, depth)] += 1
                    q = etree.QName(el.tag)
                    namespaces[q.namespace or "(sem namespace)"] += 1
                    parent = el.getparent()
                    if parent is not None and isinstance(parent.tag, str):
                        relation_counts[(display_name(parent.tag), name)] += 1
                    for attr, value in el.attrib.items():
                        attr_name = display_name(attr)
                        key = f"{name}@{attr_name}"
                        attribute_counts[key] += 1
                        if local_name(attr) in LOW_CARDINALITY_ATTRS:
                            attribute_values[key][value] += 1
                        if attr == XML_ID:
                            if value in ids:
                                duplicate_ids[value] += 1
                                flag("xml_id_duplicado", {"xml_id": value, "elemento": name})
                            ids.add(value)
                            if not DLP_ID_RE.match(value):
                                flag("xml_id_fora_do_padrao_proposto", {"xml_id": value, "elemento": name})
                        if local_name(attr) in DATE_ATTRS:
                            date_attribute_counts[f"{name}@{local_name(attr)}"] += 1
                            date_format_counts["válida" if parse_date(value) else "não reconhecida"] += 1
                            if not parse_date(value):
                                flag("data_nao_reconhecida", {"elemento": name, "atributo": local_name(attr), "valor": value})
                    continue

                name = display_name(el.tag)
                text = compact_text(el)
                if not text and len(el) == 0:
                    empty_counts[name] += 1
                if PLACEHOLDER_RE.match(text):
                    placeholder_counts[name] += 1

                if el.tag == f"{{{TEI}}}usg":
                    usage_type_counts[el.get("type", "(sem type)")] += 1
                elif el.tag == f"{{{TEI}}}ref":
                    ref_type_counts[el.get("type", "(sem type)")] += 1
                    if el.get("type") == "entry":
                        ref_text = text
                        raw_ref_text = "".join(el.itertext())
                        ancestor = el.getroottree().getpath(el)
                        entry = next(iter(el.iterancestors(f"{{{TEI}}}entry")), None)
                        textual_refs.append((ref_text, entry.get(XML_ID, "") if entry is not None else "", ancestor))
                        if raw_ref_text != raw_ref_text.strip():
                            flag("referencia_com_espacos", {"valor": raw_ref_text, **(entry_context(entry) if entry is not None else {})})
                elif el.tag == f"{{{TEI}}}quote":
                    quote_type_counts[el.get("type", "(sem type)")] += 1
                elif el.tag == f"{{{TEI}}}note":
                    note_type_counts[el.get("type", "(sem type)")] += 1
                elif el.tag == f"{{{TEI}}}sense":
                    senses += 1
                    sense_ana_counts[el.get("ana", "(sem ana)")] += 1
                elif el.tag == f"{{{TEI}}}def":
                    definitions += 1
                elif el.tag == f"{{{TEI}}}gramGrp":
                    gram_counts[text or "(vazio)"] += 1
                    if text == "???":
                        entry = next(iter(el.iterancestors(f"{{{TEI}}}entry")), None)
                        flag("classe_gramatical_desconhecida", entry_context(entry) if entry is not None else {"valor": text})
                elif local_name(el.tag) == "meta":
                    status_counts[el.get("status", "(sem status)")] += 1
                elif el.tag == f"{{{TEI}}}entry":
                    entries += 1
                    parent = el.getparent()
                    if parent is not None and parent.tag == "dic":
                        direct_root_entries += 1
                    ctx = entry_context(el)
                    entry_id = ctx["xml_id"]
                    if entry_id:
                        entry_ids.add(entry_id)
                    else:
                        flag("entrada_sem_xml_id", ctx)
                    orths = [compact_text(x) for x in el.xpath("./tei:form/tei:orth", namespaces=NS)]
                    if not any(orths):
                        flag("entrada_sem_lema", ctx)
                    for orth in filter(None, orths):
                        lemma_to_entry_ids[orth.casefold()].append(entry_id)
                    status_nodes = el.xpath("./*[local-name()='meta']")
                    status = status_nodes[0].get("status", "(sem status)") if status_nodes else "(sem dacl:meta)"
                    volp = el.get("volp", "(sem volp)")
                    kind = "VOLP" if volp == "only" else "DLP"
                    volp_counts[volp] += 1
                    entry_kind_status[(volp, status)] += 1
                    for descendant in el.iter():
                        if not isinstance(descendant.tag, str):
                            continue
                        descendant_name = display_name(descendant.tag)
                        kind_element_counts[(kind, descendant_name)] += 1
                        for attr in descendant.attrib:
                            kind_attribute_counts[(kind, f"{descendant_name}@{display_name(attr)}")] += 1
                    entry_senses = el.xpath("./tei:sense", namespaces=NS)
                    entry_defs = el.xpath(".//tei:def", namespaces=NS)
                    if volp == "only" and entry_senses:
                        flag("volp_only_com_sentidos", {**ctx, "sentidos": len(entry_senses)})
                    if volp != "only" and not entry_senses:
                        flag("dlp_sem_sentidos", {**ctx, "status": status})
                    if entry_senses and not entry_defs:
                        flag("entrada_com_sentidos_sem_definicao", {**ctx, "sentidos": len(entry_senses)})
                    sense_numbers = [s.get("n") for s in entry_senses if s.get("n")]
                    if sense_numbers:
                        numeric = []
                        for value in sense_numbers:
                            try:
                                numeric.append(int(value))
                            except ValueError:
                                flag("numero_de_sentido_nao_inteiro", {**ctx, "n": value})
                        if numeric and (len(numeric) != len(set(numeric)) or numeric != sorted(numeric)):
                            flag("numeracao_de_sentidos_suspeita", {**ctx, "n": sense_numbers})
                    for s in entry_senses:
                        sid = s.get(XML_ID, "")
                        if not sid:
                            flag("sentido_sem_xml_id", ctx)
                        elif entry_id and not sid.startswith(entry_id + "-"):
                            flag("id_de_sentido_nao_derivado_da_entrada", {**ctx, "sense_id": sid})
                        definition_texts = [compact_text(d) for d in s.xpath("./tei:def", namespaces=NS)]
                        if not definition_texts:
                            flag("sentido_sem_definicao", {**ctx, "sense_id": sid})
                        elif all(PLACEHOLDER_RE.match(x or "") for x in definition_texts):
                            flag("sentido_com_definicao_placeholder", {**ctx, "sense_id": sid, "def": " | ".join(definition_texts)})

                depth -= 1
                if el.tag == f"{{{TEI}}}entry":
                    parent = el.getparent()
                    el.clear()
                    if parent is not None:
                        while el.getprevious() is not None:
                            del parent[0]
            del context
    except (etree.XMLSyntaxError, lzma.LZMAError) as exc:
        parse_error = str(exc)

    duplicate_lemmas = {
        lemma: ids_for_lemma
        for lemma, ids_for_lemma in lemma_to_entry_ids.items()
        if len(ids_for_lemma) > 1
    }
    normalized_lemmas = set(lemma_to_entry_ids)
    dangling_ref_counts: Counter = Counter()
    for ref_text, source_id, path in textual_refs:
        normalized = ref_text.strip().casefold()
        if normalized and normalized not in normalized_lemmas:
            dangling_ref_counts[ref_text] += 1
            flag("referencia_sem_lema_exato", {"referencia": ref_text, "entrada_origem": source_id, "xpath": path})

    pi_counts, pi_examples = scan_processing_instructions(source)
    result = {
        "ficheiro": str(source),
        "tamanho_comprimido_bytes": source.stat().st_size,
        "sha256_comprimido": compressed_hash.hexdigest(),
        "xml_bem_formado": parse_error is None,
        "erro_parse": parse_error,
        "raiz": root_name,
        "profundidade_maxima": max_depth,
        "entradas": entries,
        "entradas_filhas_diretas_da_raiz": direct_root_entries,
        "sentidos": senses,
        "definicoes": definitions,
        "xml_ids_unicos": len(ids),
        "xml_ids_duplicados_distintos": len(duplicate_ids),
        "lemas_normalizados_distintos": len(normalized_lemmas),
        "lemas_com_multiplas_entradas": len(duplicate_lemmas),
        "referencias_textuais_type_entry": len(textual_refs),
        "referencias_sem_lema_exato_ocorrencias": sum(dangling_ref_counts.values()),
        "referencias_sem_lema_exato_distintas": len(dangling_ref_counts),
        "elementos": dict(element_counts),
        "atributos": dict(attribute_counts),
        "namespaces": dict(namespaces),
        "estados": dict(status_counts),
        "volp": dict(volp_counts),
        "tipos_usg": dict(usage_type_counts),
        "tipos_ref": dict(ref_type_counts),
        "tipos_quote": dict(quote_type_counts),
        "tipos_note": dict(note_type_counts),
        "sense_ana": dict(sense_ana_counts),
        "elementos_vazios": dict(empty_counts),
        "placeholders": dict(placeholder_counts),
        "atributos_de_data": dict(date_attribute_counts),
        "formatos_de_data": dict(date_format_counts),
        "estado_por_tipo_de_entrada": {
            f"volp={volp} | status={status}": count
            for (volp, status), count in entry_kind_status.items()
        },
        "elementos_por_tipo_de_entrada": {
            f"{kind} | {element}": count
            for (kind, element), count in kind_element_counts.items()
        },
        "contagens_anomalias": dict(anomaly_counts),
        "xml_model": dict(pi_counts),
        "xml_model_amostras": pi_examples,
        "amostras": dict(samples),
    }

    (output / "perfil_xml.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_counter_csv(
        output / "elementos.csv",
        ["elemento", "ocorrencias"],
        sorted(element_counts.items(), key=lambda x: (-x[1], x[0])),
    )
    write_counter_csv(
        output / "atributos.csv",
        ["elemento_atributo", "ocorrencias"],
        sorted(attribute_counts.items(), key=lambda x: (-x[1], x[0])),
    )
    write_counter_csv(
        output / "relacoes_pai_filho.csv",
        ["pai", "filho", "ocorrencias"],
        ((p, c, n) for (p, c), n in sorted(relation_counts.items(), key=lambda x: (-x[1], x[0]))),
    )
    write_counter_csv(
        output / "elementos_por_tipo_de_entrada.csv",
        ["tipo_entrada", "elemento", "ocorrencias"],
        (
            (kind, element, count)
            for (kind, element), count in sorted(
                kind_element_counts.items(), key=lambda x: (x[0][0], -x[1], x[0][1])
            )
        ),
    )
    write_counter_csv(
        output / "atributos_por_tipo_de_entrada.csv",
        ["tipo_entrada", "elemento_atributo", "ocorrencias"],
        (
            (kind, attribute, count)
            for (kind, attribute), count in sorted(
                kind_attribute_counts.items(), key=lambda x: (x[0][0], -x[1], x[0][1])
            )
        ),
    )
    value_rows = []
    for key, values in attribute_values.items():
        value_rows.extend((key, value, count) for value, count in values.most_common())
    write_counter_csv(
        output / "valores_de_atributos_controlados.csv",
        ["elemento_atributo", "valor", "ocorrencias"],
        sorted(value_rows, key=lambda x: (x[0], -x[2], x[1])),
    )
    write_counter_csv(
        output / "classes_gramaticais.csv",
        ["valor_gramGrp", "ocorrencias"],
        gram_counts.most_common(),
    )
    write_counter_csv(
        output / "referencias_sem_lema_exato.csv",
        ["referencia", "ocorrencias"],
        dangling_ref_counts.most_common(),
    )
    write_counter_csv(
        output / "lemas_com_multiplas_entradas.csv",
        ["lema_normalizado", "numero_entradas", "xml_ids"],
        ((lemma, len(v), " | ".join(v)) for lemma, v in sorted(duplicate_lemmas.items())),
    )
    anomaly_rows = []
    for category, items in sorted(samples.items()):
        for item in items:
            anomaly_rows.append((category, json.dumps(item, ensure_ascii=False, sort_keys=True)))
    write_counter_csv(
        output / "amostras_anomalias.csv",
        ["categoria", "detalhe_json"],
        anomaly_rows,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="dic.xml.xz")
    parser.add_argument("output", type=Path, help="diretório para CSV/JSON")
    args = parser.parse_args()
    result = analyze(args.source, args.output)
    print(json.dumps({
        "xml_bem_formado": result["xml_bem_formado"],
        "entradas": result["entradas"],
        "sentidos": result["sentidos"],
        "definicoes": result["definicoes"],
        "estados": result["estados"],
        "volp": result["volp"],
        "xml_model": result["xml_model"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
