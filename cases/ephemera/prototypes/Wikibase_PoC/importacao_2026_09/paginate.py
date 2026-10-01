#!/usr/bin/env python3
"""Generate the public catalogue: 50 records/page; previews on the first page."""
import json, math, re
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
ROOT=Path(__file__).resolve().parent
BASE='Project:Reportório da oposição — TablePress 77'
def esc(s):
 return re.sub(r'[&<>\[\]{}|]',lambda m:f'&#{ord(m[0])};',str(s))
def generate():
 plan=json.loads((ROOT/'plan.json').read_text())
 ids=json.loads((ROOT/'wikibase_ids.json').read_text())
 rows=[e for e in plan['entities'] if e.get('source_row')]
 pages=[];css=[];count=math.ceil(len(rows)/50)
 for n in range(count):
  nav=' · '.join(('\'\'\''+str(i+1)+'\'\'\'' if i==n else '[['+BASE+('/Página '+str(i+1) if i else '')+'|'+str(i+1)+']]') for i in range(count))
  chunk=rows[n*50:(n+1)*50]
  lines=['= Reportório da oposição =','[[Project:PoC — Importação WordPress e TablePress|← Índice da PoC]] · [[Item:Q18|Metadados do reportório]]',f'Página {n+1} de {count} · Registos {n*50+1}–{n*50+len(chunk)} de {len(rows)}.',nav,'','As colunas Imagem 1 e Imagem 2 correspondem às colunas da fonte. As miniaturas estão ativas apenas nos primeiros 50 registos; nas restantes páginas, as ligações abrem as imagens. «Sem imagem» significa que essa coluna não contém uma imagem no snapshot. A ordenação aplica-se apenas à página atual.','', '<div class="ephemera-catalogue">','{| class="wikitable sortable"','! Entrada na fonte !! Registo !! Data na fonte !! Autor na fonte !! Organização na fonte !! Tipo !! Imagem 1 !! Imagem 2']
  for e in chunk:
   field=lambda p:esc(next((c['value'] for c in e['claims'] if c['p']==p),''))
   cells=[]
   for k in (1,2):
    urls=[c['value'] for c in e['claims'] if c['p']=='P10' and any(q['value']==f'IMAGEM {k}' for q in c.get('qualifiers',[]))]
    links=[]
    for j,u in enumerate(urls):
     parsed=urlparse(u)
     if parsed.scheme!='https' or parsed.hostname not in ('ephemerajpp.com','ephemerajpp.files.wordpress.com'):raise ValueError('Unexpected image host')
     cl=f'ephemera-preview-{e["source_row"]}-{k}-{j}'
     links.append(f'<span class="{cl}">[{u} Abrir imagem {k}]</span>')
     if n==0:
      thumb=urlunparse(parsed._replace(query=urlencode(dict(parse_qsl(parsed.query),w='240'))))
      css.append(f'.ephemera-catalogue .{cl} a::before {{content:"";display:block;width:140px;height:175px;background:center/contain no-repeat url({json.dumps(thumb)});margin-bottom:6px;}}')
    cells.append('<br />'.join(links) if links else 'Sem imagem')
   lines+=['|-','| '+str(e['source_row'])+' || [[Item:'+ids[e['key']]+'|'+esc(e['label'])+']] || '+ ' || '.join([field('date_raw'),field('author_raw'),field('org_raw'),field('type_raw'),*cells])]
  lines+=['|}','</div>',nav]
  pages.append({'title':BASE+('/Página '+str(n+1) if n else ''),'text':'\n'.join(lines)})
 css.insert(0,'.ephemera-catalogue {overflow-x:auto;} .ephemera-catalogue td {vertical-align:top;} .ephemera-catalogue td:nth-last-child(-n+2) {min-width:145px;}')
 payload={'pages':pages,'css':'\n'.join(css),'rows':len(rows),'preview_records':min(50,len(rows))}
 (ROOT/'catalogue-plan.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
 (ROOT/'catalogue.js').write_text((ROOT/'catalogue-source.js').read_text()+'\npublishCatalogue('+json.dumps(payload,ensure_ascii=False)+');')
 assert len(pages)==14 and all(p['text'].count('\n|-\n')==(50 if i<13 else 46) for i,p in enumerate(pages))
 print(f'{len(pages)} pages, {len(rows)} records, {len(css)-1} previews in first 50 records')
if __name__=='__main__':generate()
