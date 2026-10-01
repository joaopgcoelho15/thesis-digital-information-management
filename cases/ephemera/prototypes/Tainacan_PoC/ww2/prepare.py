#!/usr/bin/env python3
"""Prepare a bounded, auditable sample from the saved public WordPress API response."""
import json, html, hashlib, re, urllib.request
from pathlib import Path
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent
class Content(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]; self.parts=[]; self.gallery=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='img':
            u=a.get('data-orig-file') or a.get('src','')
            if u and u not in [x['url'] for x in self.images]: self.images.append({'url':u,'alt':a.get('alt','')})
        if 'data-shortcode-data' in a: self.gallery+=1
        if tag in ('p','div','h1','h2','h3','br'): self.parts.append('\n')
    def handle_data(self,d): self.parts.append(d)
    def text(self): return '\n'.join(x.strip() for x in ''.join(self.parts).splitlines() if x.strip())
# Each source stays a single documented unit: no automatic equation of files with objects.
SAMPLE={
416599:('propaganda','Cartaz','A Europa contra o inimigo — propaganda de guerra alemã','Cartaz reproduzido na imagem da fonte, cujo título original é Cartazes de propaganda de guerra alemã. Título descritivo extraído da imagem; sem extrapolar o número de outros cartazes existentes.',''),
226742:('propaganda','Conjunto','Reino Unido — cartazes de propaganda da II Guerra Mundial','Conjunto apresentado num único post. As dez representações são mantidas juntas; a individualização dos cartazes exige revisão documental.',''),
504052:('propaganda','Documento de propaganda','Free French in Libya — propaganda dos Franceses Livres','Documento ilustrado apresentado numa única imagem. Título transcrito da imagem. A publicação em 2026 não constitui uma data de produção do documento.',''),
273556:('periodicos','Série de publicações','Der Adler','Registo ao nível da série, com as capas mostradas na fonte. Não se presume que esta seleção seja completa nem se criam exemplares a partir de cada ficheiro.','1940; 1941; 1942; 1943 — anos indicados nos grupos de imagens da fonte'),
418508:('conjuntos','Álbum','Álbum de fotos de guerra de um soldado alemão','Álbum conservado como unidade, com as suas 18 representações. A atribuição a Johan Hagenberger é apresentada como provável pela fonte. A data da morte referida no texto não é usada como data das fotografias.',''),
164565:('conjuntos','Conjunto','EUA — War Ration Book','As duas imagens compostas são preservadas como representações do conjunto. O título indica EUA, apesar de o endereço original conter reino-unido. A descrição de cada livrete exige revisão.',''),
234166:('fotografias','Fotografia','Loja japonesa atacada em Santiago do Chile','Frente e verso da mesma fotografia, confirmados por inspeção visual, são mantidos no mesmo registo. A data de 25 de março de 1942 identifica o acontecimento referido no título; não comprova a data da impressão fotográfica.',''),
}
EDITORIAL=504362
posts=json.loads((ROOT/'source/posts-1.json').read_text())
assert len(posts['posts'])==posts['found']==93, 'Pagination/snapshot changed: review before importing'
rows=[]; inventory=[]; tasks=[]
for p in posts['posts']:
    c=Content();c.feed(p['content']); pid=p['ID']
    decision='não incluído na amostra'
    if pid in SAMPLE: decision='catálogo: '+SAMPLE[pid][1]
    elif pid==EDITORIAL: decision='publicação editorial de 2026'
    elif c.gallery: decision='adiado: galeria externa; inventário dos ficheiros por validar'
    inventory.append({'source_id':pid,'title':html.unescape(p['title']),'url':p['URL'],'published':p['date'],'html_images':len(c.images),'external_gallery_modules':c.gallery,'decision':decision})
    if pid not in SAMPLE and pid!=EDITORIAL: continue
    r={'source_id':pid,'source':p['URL'],'published':p['date'],'original_title':html.unescape(p['title']),'source_text':c.text(),'external_gallery_modules':c.gallery,'images':c.images}
    if pid in SAMPLE:
        col,level,title,notes,date=SAMPLE[pid]
        r.update(collection=col,level=level,title=title,notes=notes,date=date)
    else: r.update(collection='editorial',title='A Outra Guerra — exposição de propaganda em português na Segunda Guerra Mundial')
    for i,im in enumerate(r['images'],1):
        im['file']=f'{pid}-{i:02d}.jpg';im['role']=('Frente' if i==1 else 'Verso') if pid==234166 else f'Representação {i}';tasks.append(im)
    rows.append(r)
def download(im):
    url=im['url']; assert urllib.parse.urlparse(url).hostname in ('ephemerajpp.com','ephemerajpp.files.wordpress.com')
    target=ROOT/'media'/im['file']
    if not target.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Ephemera-local-research-PoC/1.0'})
        with urllib.request.urlopen(req,timeout=90) as response: data=response.read(40*1024*1024+1)
        if len(data)>40*1024*1024: raise ValueError('Image exceeds 40 MB')
        if not data.startswith(b'\xff\xd8'): raise ValueError('Unexpected image format: '+url)
        target.write_bytes(data)
    im['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(download,tasks))
(ROOT/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(ROOT/'reports/inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print(json.dumps({'inventoried':len(inventory),'catalogue_records':len(SAMPLE),'editorial_posts':1,'images':len(tasks)},ensure_ascii=False))
