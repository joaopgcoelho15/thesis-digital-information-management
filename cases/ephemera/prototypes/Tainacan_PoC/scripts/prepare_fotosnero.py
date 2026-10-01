"""Convert ContentE's embedded JSON to a Tainacan CSV import intermediate.

Does not modify the source or contact WordPress. Images must be staged separately.
"""
import csv
import json
from pathlib import Path

source = Path.home() / 'Downloads' / 'FOTOSNERO'
output = Path(__file__).resolve().parents[1] / 'data' / 'fotosnero-import.csv'
html = (source / 'index.html').read_text(encoding='utf-8')
decoder = json.JSONDecoder()
tree = decoder.raw_decode(html.split('const tree = ', 1)[1])[0]
images = decoder.raw_decode(html.split('const imgMap = ', 1)[1])[0]
rows = []

def visit(node):
    if node['id'] in images:
        relative = images[node['id']]
        path = (source / relative).resolve()
        if not path.is_relative_to(source.resolve()) or not path.is_file():
            raise ValueError(f'Invalid or missing image: {relative}')
        m = node.get('metadata', {})
        rows.append([
            m.get('title', ''), m.get('identifier', ''),
            m.get('creator', ''), m.get('date', ''),
            m.get('coverage', ''), m.get('subject', ''),
            m.get('language', ''), 'FOTOSNERO',
            m.get('rights', ''), m.get('rotation', 0),
            node['id'], 'file:' + relative, 'draft',
        ])
    for child in node.get('children', []):
        visit(child)

visit(tree)
assert len(rows) == len(images), 'Some mapped images have no record'
assert len({row[10] for row in rows}) == len(rows), 'Duplicate source IDs'
output.parent.mkdir(parents=True, exist_ok=True)
headers = ['Titulo', 'Identificador', 'Entidade na origem', 'Ano', 'Local',
           'Assunto', 'Idioma', 'Conjunto', 'Notas de direitos na origem',
           'Rotacao na origem', 'ID de origem', 'special_document',
           'special_item_status']
with output.open('w', encoding='utf-8', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(headers)
    writer.writerows(rows)
with output.open(encoding='utf-8', newline='') as handle:
    result = list(csv.reader(handle))
assert result[0] == headers and len(result) == len(rows) + 1
assert all(len(row) == len(headers) for row in result)
print(f'{output}: {len(rows)} records, all images found, status=draft')
