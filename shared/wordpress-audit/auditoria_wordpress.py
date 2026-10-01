from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


BASE_URL = "https://ephemerajpp.com"
API_BASE = f"{BASE_URL}/wp-json/wp/v2"
SITE_NAME = "Ephemera"
OUT_DIR = Path("Auditoria_Ephemera")
CACHE_DIR = OUT_DIR / "cache"
EXCEL_PATH = OUT_DIR / "Auditoria_Qualidade_Ephemera.xlsx"
DOCX_PATH = OUT_DIR / "Relatorio_Auditoria_Qualidade_Ephemera.docx"

USER_AGENT = "Mozilla/5.0 Codex Ephemera quality audit"
TODAY = datetime.now().strftime("%Y-%m-%d")


def slugify_filename(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value or "WordPress"


def is_internal_url(url: str) -> bool:
    """Classify HTTP links against the configured site, including subdomains."""
    def host(value: str) -> str:
        name = (urlparse(value).hostname or "").lower().rstrip(".")
        if name.startswith("www."):
            name = name[4:]
        return name.encode("idna").decode("ascii")

    if urlparse(url).scheme.lower() not in {"http", "https"}:
        return False
    site_host = host(BASE_URL)
    target_host = host(url)
    return bool(site_host and target_host) and (
        target_host == site_host or target_host.endswith("." + site_host)
    )


def configure_site(base_url: str, out_dir: str | None = None, site_name: str | None = None) -> None:
    global BASE_URL, API_BASE, SITE_NAME, OUT_DIR, CACHE_DIR, EXCEL_PATH, DOCX_PATH, USER_AGENT
    BASE_URL = base_url.rstrip("/")
    API_BASE = f"{BASE_URL}/wp-json/wp/v2"
    SITE_NAME = site_name or urlparse(BASE_URL).netloc.replace("www.", "") or "WordPress"
    safe_name = slugify_filename(SITE_NAME)
    OUT_DIR = Path(out_dir) if out_dir else Path(f"Auditoria_{safe_name}")
    CACHE_DIR = OUT_DIR / "cache"
    EXCEL_PATH = OUT_DIR / f"Auditoria_Qualidade_{safe_name}.xlsx"
    DOCX_PATH = OUT_DIR / f"Relatorio_Auditoria_Qualidade_{safe_name}.docx"
    USER_AGENT = f"Mozilla/5.0 Codex {SITE_NAME} quality audit"

TYPO_PATTERNS = {
    "liberdadade": "liberdade",
    "portigues": "portugues/portugueses",
    "despois": "depois",
    "docuemtno": "documento",
    "competa": "completa",
    "contéudos": "conteúdos",
    "conteudos": "conteúdos",
    "orgão": "órgão",
}

ORTHOGRAPHY_PAIRS = [
    ("colecção", "coleção"),
    ("colectivo", "coletivo"),
    ("acção", "ação"),
    ("secção", "seção"),
    ("direcção", "direção"),
    ("actualizado", "atualizado"),
    ("actualização", "atualização"),
]

STOPWORDS = {
    "a", "as", "o", "os", "e", "de", "da", "das", "do", "dos", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "para", "por", "com", "sem", "ao", "aos", "à", "às", "que", "se",
    "the", "of", "and", "in",
}

KNOWN_SITE_TERMS = {
    "ephemera", "jpp", "tablepress", "wordpress", "slug", "slugs", "url", "urls",
    "blog", "blogs", "site", "online", "web", "pdf", "jpg", "jpeg", "png",
}


def short_value(value: Any, limit: int = 140) -> str:
    text = strip_html("" if value is None else str(value))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def token_list(value: str) -> list[str]:
    return [t for t in norm_text(value).split() if len(t) >= 4 and not t.isdigit() and t not in STOPWORDS]


def edit_distance(a: str, b: str, max_distance: int = 2) -> int:
    if abs(len(a) - len(b)) > max_distance:
        return max_distance + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        row_min = current[0]
        for j, cb in enumerate(b, 1):
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            current.append(value)
            row_min = min(row_min, value)
        if row_min > max_distance:
            return max_distance + 1
        previous = current
    return previous[-1]


def text_quality_warnings(value: str, slug: str = "") -> list[str]:
    warnings: list[str] = []
    raw = value or ""
    blob = f"{raw} {slug}".strip()
    if not blob:
        return warnings
    if re.search(r"[�]|Ã[\x80-\xbf]", blob):
        warnings.append("possível problema de codificação de caracteres")
    if re.search(r"\s{2,}", raw):
        warnings.append("espaços duplicados")
    if re.search(r"\b([\wÀ-ÿ]{4,})\s+\1\b", raw, flags=re.I):
        warnings.append("palavra repetida consecutivamente")
    if re.search(r"([!?.,;:])\1{1,}", raw):
        warnings.append("pontuação repetida")
    if raw.count("(") != raw.count(")") or raw.count("[") != raw.count("]"):
        warnings.append("parênteses/colchetes possivelmente desequilibrados")
    if re.search(r"\w_[\s/)]|_$|_{2,}", blob):
        warnings.append("underscore ou separador estranho no nome/slug")
    if re.search(r"<[^>]+>|&lt;|&gt;", raw):
        warnings.append("HTML visível no texto")
    if re.search(r"([a-zà-ÿ])\1\1", norm_text(raw)):
        warnings.append("letra repetida três ou mais vezes")
    return warnings


def load_spellcheckers(languages: list[str]) -> dict[str, Any]:
    vendor_candidates = [OUT_DIR / "vendor", Path("Auditoria_Ephemera/vendor")]
    for vendor in vendor_candidates:
        if vendor.exists() and str(vendor) not in sys.path:
            sys.path.insert(0, str(vendor))
    try:
        from spellchecker import SpellChecker  # type: ignore
    except Exception:
        return {}
    checkers: dict[str, Any] = {}
    for language in languages:
        try:
            checker = SpellChecker(language=language)
            checker.word_frequency.load_words(KNOWN_SITE_TERMS)
            checkers[language] = checker
        except Exception:
            continue
    return checkers


def raw_words(value: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]{4,}", value or "")


def is_spellcheck_candidate(raw: str) -> bool:
    if not raw or len(raw) < 5:
        return False
    if raw.lower() in STOPWORDS or raw.lower() in KNOWN_SITE_TERMS:
        return False
    if any(ch.isdigit() for ch in raw):
        return False
    if raw.isupper() and len(raw) <= 4:
        return False
    # Most names of people, places, parties and institutions are capitalized.
    # Skip them unless the word also appears lowercased elsewhere in a slug.
    if raw[0].isupper():
        return False
    return True


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", " ", value, flags=re.I)
    value = re.sub(r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def norm_text(value: str | None) -> str:
    value = strip_html(value or "").lower().strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def slug_tokens(slug: str | None) -> set[str]:
    return {t for t in norm_text(unquote(slug or "")).split() if len(t) > 2 and t not in STOPWORDS}


def compact_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme and url.startswith("//"):
        parsed = urlparse("https:" + url)
    if not parsed.scheme:
        return url
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    query_pairs = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    query = urlencode(query_pairs, doseq=True)
    return urlunparse((scheme, netloc, path, "", query, ""))


def http_safe_url(url: str) -> str:
    parsed = urlparse(url)
    safe_path = quote(unquote(parsed.path), safe="/%")
    safe_query = quote(unquote(parsed.query), safe="=&?/:+,%")
    return urlunparse((parsed.scheme, parsed.netloc, safe_path, "", safe_query, ""))


def request_json(url: str, timeout: int = 60) -> tuple[Any, dict[str, str]]:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
        headers = {k.lower(): v for k, v in response.headers.items()}
        return data, headers


def request_text(url: str, timeout: int = 30) -> tuple[str, int, dict[str, str]]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8", errors="replace")
        headers = {k.lower(): v for k, v in response.headers.items()}
        return text, response.status, headers


def api_url(endpoint: str, **params: Any) -> str:
    query = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{API_BASE}/{endpoint}?{query}"


def fetch_paginated(endpoint: str, fields: str, max_pages: int | None = None, sleep_s: float = 0.03, per_page: int = 100) -> list[dict[str, Any]]:
    first_url = api_url(endpoint, per_page=per_page, page=1, _fields=fields)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            data, headers = request_json(first_url)
            break
        except Exception as exc:
            last_error = exc
            print(f"{endpoint}: retry page 1 attempt {attempt}/3 after {type(exc).__name__}")
            time.sleep(2 * attempt)
    else:
        raise last_error or RuntimeError(f"Failed first page for {endpoint}")
    total_pages = int(headers.get("x-wp-totalpages", "1") or 1)
    if max_pages:
        total_pages = min(total_pages, max_pages)
    items = list(data)
    print(f"{endpoint}: page 1/{total_pages} ({len(items)} items)")
    skipped_pages: list[dict[str, Any]] = []
    for page in range(2, total_pages + 1):
        url = api_url(endpoint, per_page=per_page, page=page, _fields=fields)
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                data, _ = request_json(url)
                break
            except Exception as exc:
                last_error = exc
                print(f"{endpoint}: retry page {page} attempt {attempt}/3 after {type(exc).__name__}")
                time.sleep(2 * attempt)
        else:
            skipped_pages.append({"endpoint": endpoint, "page": page, "error": repr(last_error)})
            print(f"{endpoint}: skipped page {page} after repeated failures")
            continue
        items.extend(data)
        if page % 25 == 0 or page == total_pages:
            print(f"{endpoint}: page {page}/{total_pages} ({len(items)} items)")
        time.sleep(sleep_s)
    if skipped_pages:
        cache_json(f"{endpoint}_skipped_pages.json", skipped_pages)
    return items


def cache_json(name: str, data: Any) -> None:
    (CACHE_DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(name: str) -> Any | None:
    path = CACHE_DIR / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def fetch_wordpress(force: bool = False, max_post_pages: int | None = None, include_post_content: bool = False) -> dict[str, list[dict[str, Any]]]:
    ensure_dirs()
    fields_content = "id,date,modified,slug,link,title,excerpt,content,categories,tags,status,type"
    fields_meta = "id,date,modified,slug,link,title,excerpt,categories,tags,status,type"
    fields_tax = "id,count,description,link,name,slug,parent,taxonomy"
    datasets: dict[str, list[dict[str, Any]]] = {}
    config = [
        ("posts", fields_content if include_post_content else fields_meta, max_post_pages, 100),
        ("pages", fields_content, None, 1),
        ("categories", fields_tax, None, 100),
        ("tags", fields_tax, None, 100),
    ]
    for endpoint, fields, limit, per_page in config:
        cached = load_json(f"{endpoint}.json")
        if cached is not None and not force:
            datasets[endpoint] = cached
            print(f"{endpoint}: cache ({len(cached)} items)")
            continue
        datasets[endpoint] = fetch_paginated(endpoint, fields, max_pages=limit, per_page=per_page)
        cache_json(f"{endpoint}.json", datasets[endpoint])
    return datasets


def fetch_sitemaps(force: bool = False) -> list[str]:
    cached = load_json("sitemaps_urls.json")
    if cached is not None and not force:
        print(f"sitemaps: cache ({len(cached)} urls)")
        return cached
    sitemap_candidates = [f"{BASE_URL}/wp-sitemap.xml", f"{BASE_URL}/sitemap.xml", f"{BASE_URL}/robots.txt"]
    urls: list[str] = []
    discovered: list[str] = []
    for candidate in sitemap_candidates:
        try:
            text, _, _ = request_text(candidate, timeout=20)
        except Exception:
            continue
        if candidate.endswith("robots.txt"):
            for line in text.splitlines():
                if line.lower().startswith("sitemap:"):
                    discovered.append(line.split(":", 1)[1].strip())
            continue
        discovered.append(candidate)
    seen_sitemaps: set[str] = set()
    while discovered:
        sm = discovered.pop(0)
        if sm in seen_sitemaps:
            continue
        seen_sitemaps.add(sm)
        try:
            xml, _, _ = request_text(sm, timeout=30)
            root = ET.fromstring(xml.encode("utf-8"))
        except Exception:
            continue
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in root.findall(".//sm:sitemap/sm:loc", ns):
            if loc.text:
                discovered.append(loc.text.strip())
        for loc in root.findall(".//sm:url/sm:loc", ns):
            if loc.text:
                urls.append(compact_url(loc.text.strip()))
    urls = sorted(set(urls))
    cache_json("sitemaps_urls.json", urls)
    print(f"sitemaps: {len(urls)} urls")
    return urls


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.images: list[tuple[str, str]] = []
        self.headings: list[str] = []
        self._in_heading = False
        self._heading_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "a" and data.get("href"):
            self.links.append((data["href"] or "", data.get("title") or ""))
        if tag == "img":
            self.images.append((data.get("src") or "", data.get("alt") or ""))
        if tag in {"h1", "h2", "h3"}:
            self._in_heading = True
            self._heading_text = []

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._heading_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3"} and self._in_heading:
            heading = re.sub(r"\s+", " ", "".join(self._heading_text)).strip()
            if heading:
                self.headings.append(heading)
            self._in_heading = False


def parse_content(html: str | None) -> dict[str, Any]:
    parser = LinkParser()
    try:
        parser.feed(html or "")
    except Exception:
        pass
    text = strip_html(html)
    return {
        "text": text,
        "links": parser.links,
        "images": parser.images,
        "headings": parser.headings,
        "word_count": len(re.findall(r"\w+", text)),
        "html_length": len(html or ""),
    }


@dataclass
class Issue:
    area: str
    severity: str
    issue_type: str
    url: str
    evidence: str
    recommendation: str


def add_issue(issues: list[Issue], area: str, severity: str, issue_type: str, url: str, evidence: str, recommendation: str) -> None:
    issues.append(Issue(area, severity, issue_type, url, evidence[:500], recommendation))


def read_local_excel(path: str | None = None) -> dict[str, list[dict[str, Any]]]:
    if path:
        candidates = [Path(path)]
    else:
        candidates = sorted(Path(".").glob(f"{SITE_NAME} - Estat*.xlsx")) + sorted(Path(".").glob(f"{SITE_NAME} - Estati*.xlsx"))
        if SITE_NAME.lower() == "ephemera":
            candidates += sorted(Path(".").glob("Ephemera - Estat*.xlsx")) + sorted(Path(".").glob("Ephemera - Estati*.xlsx"))
    candidates = [candidate for candidate in candidates if candidate.exists()]
    if not candidates:
        return {}
    workbook_path = candidates[0]
    wb = load_workbook(workbook_path, data_only=True, read_only=True)
    result: dict[str, list[dict[str, Any]]] = {}
    for sheet_name in ["Páginas", "TablePress", "Tags", "CategoriasPosts"]:
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(h).strip() if h is not None else f"Col{i+1}" for i, h in enumerate(rows[0])]
        result[sheet_name] = [dict(zip(headers, row)) for row in rows[1:] if any(v is not None for v in row)]
    return result


def analyze(datasets: dict[str, list[dict[str, Any]]], sitemap_urls: list[str], excel_data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    issues: list[Issue] = []
    posts = datasets.get("posts", [])
    pages = datasets.get("pages", [])
    categories = datasets.get("categories", [])
    tags = datasets.get("tags", [])

    url_sources: dict[str, set[str]] = defaultdict(set)
    link_rows: list[dict[str, Any]] = []
    image_rows: list[dict[str, Any]] = []
    content_rows: list[dict[str, Any]] = []

    all_content = [("post", item) for item in posts] + [("page", item) for item in pages]
    for content_type, item in all_content:
        title = strip_html((item.get("title") or {}).get("rendered", ""))
        url = item.get("link") or ""
        content_html = (item.get("content") or {}).get("rendered", "")
        parsed = parse_content(content_html)
        content_rows.append({
            "Tipo": content_type,
            "ID": item.get("id"),
            "Título": title,
            "URL": url,
            "Slug": item.get("slug"),
            "Data": item.get("date"),
            "Palavras": parsed["word_count"],
            "Comprimento HTML": parsed["html_length"],
            "Links": len(parsed["links"]),
            "Imagens": len(parsed["images"]),
            "Categorias": len(item.get("categories") or []),
            "Tags": len(item.get("tags") or []),
        })
        if content_type == "page" and parsed["html_length"] > 300_000:
            add_issue(issues, "Técnico", "Alta", "Página muito pesada", url, f"HTML com {parsed['html_length']:,} caracteres e {len(parsed['images'])} imagens.", "Dividir a página, criar paginação ou transformar em listagem carregada por partes.")
        if content_type == "post" and content_html and parsed["word_count"] < 5 and not parsed["images"]:
            add_issue(issues, "Conteúdo", "Baixa", "Post quase vazio", url, f"Título: {title}", "Confirmar se o post deve existir ou se falta conteúdo/imagem.")
        for raw, link_title in parsed["links"]:
            absolute = compact_url(urljoin(url, raw))
            if absolute.startswith("mailto:") or absolute.startswith("tel:") or absolute.startswith("#"):
                continue
            url_sources[absolute].add(url)
            link_rows.append({
                "Origem": url,
                "Tipo origem": content_type,
                "URL destino": absolute,
                "Domínio destino": urlparse(absolute).netloc,
                "Interno": is_internal_url(absolute),
                "Texto/title": link_title,
            })
        for src, alt in parsed["images"]:
            absolute = compact_url(urljoin(url, src))
            image_rows.append({
                "Origem": url,
                "Tipo origem": content_type,
                "Imagem": absolute,
                "Alt": alt,
                "Sem alt": not bool(alt.strip()),
            })

    # Slugs, titles and spelling.
    seen_norm_titles: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_slugs: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    slug_rows: list[dict[str, Any]] = []
    writing_rows: list[dict[str, Any]] = []
    word_counter: Counter[str] = Counter()
    word_examples: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    spellcheckers = load_spellcheckers(["pt", "en", "es", "it", "fr", "de"])
    spellchecker = spellcheckers.get("pt")
    spell_seen: set[tuple[str, str, str]] = set()
    spell_candidates: defaultdict[str, list[tuple[str, str, str]]] = defaultdict(list)

    def add_writing_suspicion(kind: str, value: str, url: str, evidence: str, suggestion: str = "") -> None:
        writing_rows.append({
            "Tipo de suspeita": kind,
            "Texto/termo": value,
            "URL": url,
            "Evidência": evidence,
            "Sugestão possível": suggestion,
        })
        add_issue(issues, "Normalização", "Média", kind, url, evidence, suggestion or "Rever manualmente; trata-se de suspeita automática, não de erro confirmado.")

    def check_portuguese_spelling(source_label: str, value: str, url: str, from_slug: bool = False) -> None:
        if spellchecker is None or not value:
            return
        for raw in raw_words(value.replace("-", " ")):
            word = raw.lower()
            if not is_spellcheck_candidate(raw):
                continue
            if word in spellchecker:
                continue
            if any(word in checker for lang, checker in spellcheckers.items() if lang != "pt"):
                continue
            # Slugs contain many names and foreign terms; require stronger evidence.
            if from_slug and not re.search(r"([a-zà-ÿ])\1\1", word) and len(word) < 8:
                continue
            if len(spell_candidates[word]) < 3:
                spell_candidates[word].append((raw, source_label, url))
            if len(spell_candidates) >= 3000:
                return

    for content_type, item in all_content:
        title = strip_html((item.get("title") or {}).get("rendered", ""))
        slug = item.get("slug") or ""
        url = item.get("link") or ""
        ntitle = norm_text(title)
        seen_norm_titles[ntitle].append(item)
        seen_slugs[norm_text(slug)].append(item)
        title_tokens = {t for t in norm_text(title).split() if len(t) > 2 and t not in STOPWORDS}
        stokens = slug_tokens(slug)
        overlap = len(title_tokens & stokens) / max(1, len(title_tokens))
        reasons = []
        if len(slug) > 130:
            reasons.append("slug muito longo")
        if overlap < 0.35 and len(title_tokens) >= 4:
            reasons.append(f"baixo alinhamento título/slug ({overlap:.0%})")
        text_blob = f"{title} {slug}".lower()
        for bad, good in TYPO_PATTERNS.items():
            if bad in text_blob:
                reasons.append(f"erro provável: {bad} -> {good}")
                add_writing_suspicion("Erro provável por padrão conhecido", title or slug, url, f"{bad} -> {good}", good)
        for warning in text_quality_warnings(title, slug):
            add_writing_suspicion("Suspeita de escrita/formatação", title or slug, url, warning)
        check_portuguese_spelling("título", title, url)
        check_portuguese_spelling("slug", slug, url, from_slug=True)
        if re.search(r"\\s{2,}", title):
            reasons.append("espaços duplicados no título")
        if reasons:
            add_issue(issues, "Normalização", "Média", "Título/slug suspeito", url, "; ".join(reasons), "Rever grafia, slug e consistência do título.")
        slug_rows.append({
            "Tipo": content_type,
            "ID": item.get("id"),
            "Título": title,
            "Slug": slug,
            "URL": url,
            "Alinhamento título/slug": round(overlap, 2),
            "Problemas": "; ".join(reasons),
        })
        for token in token_list(title):
            word_counter[token] += 1
            if len(word_examples[token]) < 3:
                word_examples[token].append((title, url))

    for normalized, items in seen_norm_titles.items():
        if normalized and len(items) > 1:
            urls = [it.get("link") for it in items[:5]]
            add_issue(issues, "Conteúdo", "Média", "Títulos duplicados ou quase iguais", urls[0] or "", f"{len(items)} conteúdos com título normalizado '{normalized}'. Exemplos: {', '.join(filter(None, urls))}", "Verificar se são duplicados reais, séries legítimas ou títulos que precisam de desambiguação.")

    # Taxonomy.
    cat_rows: list[dict[str, Any]] = []
    cat_by_id = {c.get("id"): c for c in categories}
    cat_norms: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for cat in categories:
        name = strip_html(cat.get("name", ""))
        slug = cat.get("slug") or ""
        count = int(cat.get("count") or 0)
        parent = cat.get("parent") or 0
        cat_norms[norm_text(name)].append(cat)
        problems = []
        if count == 0:
            problems.append("categoria sem posts")
        if parent and parent not in cat_by_id:
            problems.append("parent inexistente na API")
        blob = f"{name} {slug}".lower()
        for bad, good in TYPO_PATTERNS.items():
            if bad in blob:
                problems.append(f"erro provável: {bad} -> {good}")
                add_writing_suspicion("Erro provável por padrão conhecido", name or slug, cat.get("link") or "", f"{bad} -> {good}", good)
        for warning in text_quality_warnings(name, slug):
            add_writing_suspicion("Suspeita de escrita/formatação", name or slug, cat.get("link") or "", warning)
        check_portuguese_spelling("nome da categoria", name, cat.get("link") or "")
        check_portuguese_spelling("slug da categoria", slug, cat.get("link") or "", from_slug=True)
        for token in token_list(name):
            word_counter[token] += 1
            if len(word_examples[token]) < 3:
                word_examples[token].append((name, cat.get("link") or ""))
        cat_rows.append({
            "ID": cat.get("id"),
            "Nome": name,
            "Slug": slug,
            "URL": cat.get("link"),
            "Posts": count,
            "Parent": parent,
            "Problemas": "; ".join(problems),
        })
        if problems:
            severity = "Média" if count == 0 or any("erro provável" in p for p in problems) else "Baixa"
            add_issue(issues, "Taxonomia", severity, "Categoria a rever", cat.get("link") or "", f"{name}: {'; '.join(problems)}", "Normalizar, fundir ou remover categorias sem função clara.")

    if spellchecker is not None and spell_candidates:
        # Ask the spellchecker for suggestions only after collecting candidates.
        # This avoids the expensive correction step for every token in the site.
        sorted_candidates = sorted(spell_candidates.items(), key=lambda kv: (len(kv[1]), kv[0]))[:1500]
        for word, examples in sorted_candidates:
            if any(word in checker for lang, checker in spellcheckers.items() if lang != "pt"):
                continue
            correction = spellchecker.correction(word)
            if not correction or correction == word:
                continue
            distance = edit_distance(word, correction, 3)
            if distance > 2:
                continue
            for raw, source_label, url in examples[:1]:
                key = (word, correction, url)
                if key in spell_seen:
                    continue
                spell_seen.add(key)
                add_writing_suspicion(
                    "Erro ortográfico provável (dicionário PT)",
                    raw,
                    url,
                    f"No campo {source_label}, '{raw}' não consta do dicionário português; sugestão automática: '{correction}'.",
                    correction,
                )
            if len(spell_seen) >= 500:
                break

    for normalized, cats in cat_norms.items():
        if normalized and len(cats) > 1:
            pairs = [
                f"{short_value(c.get('name'))} ({int(c.get('count') or 0)} posts) — {c.get('link') or ''}"
                for c in cats[:10]
            ]
            add_issue(
                issues,
                "Taxonomia",
                "Alta",
                "Categorias equivalentes por nome",
                "\n".join(c.get("link") or "" for c in cats[:10]),
                f"{len(cats)} categorias equivalentes a '{normalized}':\n" + "\n".join(pairs),
                "Comparar as categorias lado a lado e confirmar se devem ser fundidas, renomeadas ou mantidas por pertencerem a contextos hierárquicos diferentes.",
            )

    # Orthography variants.
    corpus_names = [strip_html(c.get("name", "")) for c in categories] + [strip_html((p.get("title") or {}).get("rendered", "")) for p in posts[:5000]]
    corpus = " || ".join(corpus_names).lower()
    for old, new in ORTHOGRAPHY_PAIRS:
        if old in corpus and new in corpus:
            evidence = f"Foram encontradas formas '{old}' e '{new}'."
            add_writing_suspicion("Variação ortográfica", f"{old} / {new}", "", evidence, "Definir norma editorial e aplicar em categorias, títulos e páginas.")

    # Corpus-based spelling/normalization suspicion. This finds possible typos
    # only when a very similar term also exists elsewhere in the site.
    words = [
        w for w, count in word_counter.items()
        if 5 <= len(w) <= 24 and count <= 20 and not any(ch.isdigit() for ch in w)
    ]
    by_key: defaultdict[tuple[str, int], list[str]] = defaultdict(list)
    for word in words:
        prefix = word[:2]
        by_key[(prefix, len(word))].append(word)
        by_key[(prefix, len(word) - 1)].append(word)
        by_key[(prefix, len(word) + 1)].append(word)
    seen_pairs: set[tuple[str, str]] = set()
    for word in sorted(words, key=lambda w: (word_counter[w], w)):
        prefix = word[:2]
        candidates = set(by_key.get((prefix, len(word)), []) + by_key.get((prefix, len(word) - 1), []) + by_key.get((prefix, len(word) + 1), []))
        best: tuple[int, int, str] | None = None
        for other in candidates:
            if other == word:
                continue
            pair = tuple(sorted((word, other)))
            if pair in seen_pairs:
                continue
            dist = edit_distance(word, other, 2)
            if dist == 0 or dist > 2:
                continue
            other_count = word_counter[other]
            word_count = word_counter[word]
            if max(other_count, word_count) < 2:
                continue
            if len(word) < 8 and dist > 1:
                continue
            # Prefer cases where one spelling is clearly more established in the corpus,
            # but still keep balanced cases as normalization suspects.
            score = (dist, -abs(other_count - word_count), other)
            if best is None or score < best:
                best = (dist, other_count, other)
        if best is None:
            continue
        dist, other_count, other = best
        pair = tuple(sorted((word, other)))
        seen_pairs.add(pair)
        examples_a = "; ".join(f"{short_value(t, 80)} — {u}" for t, u in word_examples[word][:2])
        examples_b = "; ".join(f"{short_value(t, 80)} — {u}" for t, u in word_examples[other][:2])
        evidence = (
            f"Termos muito próximos no corpus: '{word}' ({word_counter[word]} ocorrências) "
            f"e '{other}' ({other_count} ocorrências), distância {dist}. "
            f"Exemplos '{word}': {examples_a}. Exemplos '{other}': {examples_b}."
        )
        suggestion = f"Confirmar se '{word}' e '{other}' são grafias distintas legítimas ou erro/variante a normalizar."
        add_writing_suspicion("Termos muito semelhantes no corpus", f"{word} / {other}", "", evidence, suggestion)
        if len(writing_rows) > 2500:
            break

    # Tags.
    tag_rows = []
    for tag in tags:
        tag_rows.append({
            "ID": tag.get("id"),
            "Tag": strip_html(tag.get("name", "")),
            "Slug": tag.get("slug"),
            "URL": tag.get("link"),
            "Posts": tag.get("count") or 0,
            "Descrição": strip_html(tag.get("description", "")),
        })
    if len(tags) < 100 and len(categories) > 1000:
        add_issue(issues, "Arquitetura de informação", "Alta", "Uso residual de tags face às categorias", "", f"{len(tags)} tags para {len(categories)} categorias.", "Separar categorias estruturais de descritores temáticos; usar tags para temas transversais controlados.")

    # Sitemap/API coverage.
    api_urls = {compact_url(item.get("link") or "") for _, item in all_content if item.get("link")}
    sitemap_set = set(sitemap_urls)
    not_in_sitemap = sorted(api_urls - sitemap_set)
    if sitemap_urls and not_in_sitemap:
        add_issue(issues, "SEO/Indexação", "Média", "URLs da API não encontradas no sitemap", "", f"{len(not_in_sitemap)} URLs públicas da API não aparecem no conjunto de sitemaps recolhido.", "Confirmar configuração do sitemap WordPress/Jetpack e tipos de conteúdo incluídos.")

    # Excel/TablePress issues already collected.
    tablepress_rows = excel_data.get("TablePress", [])
    tp_out = []
    for row in tablepress_rows:
        notas = str(row.get("Notas") or "")
        title = str(row.get("Título") or "")
        records = row.get("Total_Registos")
        ref = str(row.get("Referência") or "")
        problems = []
        if "Analisar" in notas:
            problems.append("marcada para analisar")
        if "Vazia" in notas or records in (None, 0):
            problems.append("sem registos/vazia")
        if not ref:
            problems.append("sem referência")
        if problems:
            add_issue(issues, "TablePress", "Média", "Tabela a rever", "", f"{title}: {'; '.join(problems)}", "Normalizar metadados, referência e estado da tabela.")
        out = dict(row)
        out["Problemas"] = "; ".join(problems)
        tp_out.append(out)

    # Prioritize and limit rows for readability.
    severity_rank = {"Crítica": 0, "Alta": 1, "Média": 2, "Baixa": 3}
    issue_rows = [
        {
            "Área": i.area,
            "Gravidade": i.severity,
            "Tipo": i.issue_type,
            "URL": i.url,
            "Evidência": i.evidence,
            "Recomendação": i.recommendation,
        }
        for i in sorted(issues, key=lambda x: (severity_rank.get(x.severity, 9), x.area, x.issue_type, x.url))
    ]
    summary = {
        "Data": TODAY,
        "Posts analisados": len(posts),
        "Páginas analisadas": len(pages),
        "Categorias analisadas": len(categories),
        "Tags analisadas": len(tags),
        "URLs sitemap": len(sitemap_urls),
        "Links extraídos": len(link_rows),
        "Imagens extraídas": len(image_rows),
        "Problemas identificados": len(issue_rows),
        "Problemas Alta/Crítica": sum(1 for i in issues if i.severity in {"Alta", "Crítica"}),
    }
    return {
        "summary": summary,
        "issues": issue_rows,
        "slugs": slug_rows,
        "categories": cat_rows,
        "tags": tag_rows,
        "content": content_rows,
        "links": link_rows,
        "images": image_rows,
        "writing": writing_rows,
        "tablepress": tp_out,
        "sitemap_missing": [{"URL API fora do sitemap": u} for u in not_in_sitemap[:5000]],
    }


def check_links(audit: dict[str, Any], max_internal: int = 1200, max_external: int = 250) -> list[dict[str, Any]]:
    candidates: dict[str, set[str]] = defaultdict(set)
    for row in audit["links"]:
        url = row["URL destino"]
        if url.startswith(("http://", "https://")):
            candidates[url].add(row["Origem"])
    internal = [u for u in candidates if is_internal_url(u)]
    external = [u for u in candidates if not is_internal_url(u)]
    selected = internal[:max_internal] + external[:max_external]
    results = []
    for idx, url in enumerate(selected, 1):
        status = None
        final_url = ""
        error = ""
        try:
            req = Request(http_safe_url(url), method="HEAD", headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=12) as response:
                status = response.status
                final_url = response.geturl()
        except HTTPError as exc:
            status = exc.code
            final_url = exc.geturl()
            if exc.code in {403, 405}:
                try:
                    req = Request(http_safe_url(url), headers={"User-Agent": USER_AGENT})
                    with urlopen(req, timeout=12) as response:
                        status = response.status
                        final_url = response.geturl()
                except Exception as exc2:
                    error = repr(exc2)[:200]
        except (URLError, TimeoutError, Exception) as exc:
            error = repr(exc)[:200]
        results.append({
            "URL": url,
            "Interno": is_internal_url(url),
            "Estado": status,
            "URL final": compact_url(final_url) if final_url else "",
            "Erro": error,
            "Nº origens": len(candidates[url]),
            "Exemplo origem": sorted(candidates[url])[0] if candidates[url] else "",
            "Problema": bool(error or (status and status >= 400)),
        })
        if idx % 100 == 0:
            print(f"links: {idx}/{len(selected)}")
        time.sleep(0.02)
    audit["checked_links"] = results
    return results


def write_excel(audit: dict[str, Any]) -> None:
    wb = Workbook()
    default = wb.active
    wb.remove(default)
    navy = "1F4E78"
    light = "EAF2F8"
    border_color = "B7C9D6"
    thin = Side(style="thin", color=border_color)

    def add_sheet(name: str, rows: list[dict[str, Any]]) -> None:
        ws = wb.create_sheet(name[:31])
        ws.sheet_view.showGridLines = False
        if not rows:
            ws["A1"] = "Sem dados"
            return
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor=navy)
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        for row_cells in ws.iter_rows():
            for cell in row_cells:
                cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for col_idx, header in enumerate(headers, 1):
            width = min(max(len(str(header)) + 2, 12), 45)
            sample = [ws.cell(r, col_idx).value for r in range(2, min(ws.max_row, 25) + 1)]
            if sample:
                width = min(max(width, max(len(str(v or "")) for v in sample[:20]) + 2), 60)
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.freeze_panes = "A2"
        if ws.max_row > 1 and ws.max_column > 1:
            table = Table(displayName=re.sub(r"[^A-Za-z0-9_]", "", name)[:25] + "Tbl", ref=f"A1:{get_column_letter(ws.max_column)}{ws.max_row}")
            table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False)
            ws.add_table(table)

    summary_rows = [{"Indicador": k, "Valor": v} for k, v in audit["summary"].items()]
    add_sheet("Resumo", summary_rows)
    add_sheet("Problemas", audit["issues"])
    add_sheet("Links Verificados", audit.get("checked_links", []))
    add_sheet("Suspeitas Escrita", audit.get("writing", []))
    add_sheet("Slugs e Títulos", audit["slugs"])
    add_sheet("Categorias", audit["categories"])
    add_sheet("Tags", audit["tags"])
    add_sheet("Conteúdos", audit["content"])
    add_sheet("Imagens", audit["images"][:10000])
    add_sheet("Links Extraídos", audit["links"][:10000])
    add_sheet("TablePress", audit["tablepress"])
    add_sheet("Sitemap", audit["sitemap_missing"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(EXCEL_PATH)


def write_docx(audit: dict[str, Any]) -> None:
    doc = Document()
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    title = doc.add_heading(f"Auditoria de Qualidade e Consistência do Site {SITE_NAME}", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Data da análise: {TODAY}")
    doc.add_paragraph(
        f"Este relatório sintetiza uma auditoria automática e semi-estruturada ao site público {SITE_NAME}, "
        "com foco em arquitetura de informação, coerência de conteúdos, normalização terminológica, ligações, imagens e tabelas."
    )

    doc.add_heading("Resumo Quantitativo", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Indicador"
    table.rows[0].cells[1].text = "Valor"
    for key, value in audit["summary"].items():
        row = table.add_row().cells
        row[0].text = str(key)
        row[1].text = str(value)

    doc.add_heading("Principais Conclusões", level=1)
    issues = audit["issues"]
    top = issues[:20]
    if not top:
        doc.add_paragraph("Não foram identificados problemas pelo conjunto de testes automáticos aplicados.")
    else:
        for issue in top:
            p = doc.add_paragraph(style=None)
            p.add_run(f"{issue['Gravidade']} - {issue['Área']} - {issue['Tipo']}: ").bold = True
            p.add_run(issue["Evidência"])
            if issue["URL"]:
                doc.add_paragraph(issue["URL"])

    doc.add_heading("Leituras por Área", level=1)
    grouped = Counter(i["Área"] for i in issues)
    for area, count in grouped.most_common():
        doc.add_paragraph(f"{area}: {count} ocorrências sinalizadas.")

    doc.add_heading("Recomendações Prioritárias", level=1)
    recommendations = [
        "Separar categorias estruturais de descritores temáticos, usando uma política controlada para categorias e tags.",
        "Criar uma rotina de revisão de slugs/títulos para detetar erros ortográficos prováveis, títulos duplicados e URLs pouco descritivos.",
        "Tratar páginas muito pesadas com paginação, carregamento progressivo ou divisão por subpáginas temáticas.",
        "Rever tabelas TablePress marcadas como vazias, sem referência ou a analisar.",
        "Manter uma folha de triagem com prioridade, responsável e estado de correção para transformar a auditoria em plano de ação.",
    ]
    for rec in recommendations:
        doc.add_paragraph(rec, style="List Bullet")

    doc.add_heading("Metodologia", level=1)
    doc.add_paragraph(
        "Foram recolhidos dados da API pública WordPress, dos sitemaps públicos quando disponíveis e, se indicado, de ficheiros Excel locais de apoio. "
        "A análise automática sinaliza padrões suspeitos; alguns casos devem ser confirmados manualmente antes de correção, sobretudo quando envolvem interpretação semântica."
    )
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(DOCX_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL, help="URL base do site WordPress, por exemplo https://exemplo.com")
    parser.add_argument("--site-name", default=None, help="Nome curto usado no relatório e nos nomes dos ficheiros.")
    parser.add_argument("--out-dir", default=None, help="Pasta onde serão guardados cache, Excel e Word.")
    parser.add_argument("--local-excel", default=None, help="Excel local opcional para enriquecer a análise com dados auxiliares.")
    parser.add_argument("--force-fetch", action="store_true")
    parser.add_argument("--max-post-pages", type=int, default=None, help="Limit post API pages for a faster exploratory run.")
    parser.add_argument("--include-post-content", action="store_true", help="Fetch full post HTML content. Slower and more likely to timeout on very large sites.")
    parser.add_argument("--skip-link-check", action="store_true")
    parser.add_argument("--max-internal-links", type=int, default=1200)
    parser.add_argument("--max-external-links", type=int, default=250)
    args = parser.parse_args()

    configure_site(args.base_url, out_dir=args.out_dir, site_name=args.site_name)
    ensure_dirs()
    datasets = fetch_wordpress(force=args.force_fetch, max_post_pages=args.max_post_pages, include_post_content=args.include_post_content)
    sitemap_urls = fetch_sitemaps(force=args.force_fetch)
    excel_data = read_local_excel(args.local_excel)
    audit = analyze(datasets, sitemap_urls, excel_data)
    if not args.skip_link_check:
        check_links(audit, max_internal=args.max_internal_links, max_external=args.max_external_links)
    cache_json("audit_results.json", audit)
    write_excel(audit)
    write_docx(audit)
    print(f"Excel: {EXCEL_PATH}")
    print(f"Word: {DOCX_PATH}")


if __name__ == "__main__":
    main()
