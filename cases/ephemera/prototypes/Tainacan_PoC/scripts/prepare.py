"""Reproducible sample: nine posters and first fifty nonempty TablePress rows."""
import json,hashlib,shutil,subprocess,concurrent.futures,csv
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
media=ROOT/'data/media';media.mkdir(exist_ok=True)
manifest=json.loads((WORK/'Wikibase_PoC/PCP_Constituinte_1975/manifest.json').read_text())
plan=json.loads((WORK/'Wikibase_PoC/importacao_2026_09/plan.json').read_text())
items=[]
for r in manifest['records']:
 dest=media/(r['local_key']+'.jpg');shutil.copyfile(WORK/'Wikibase_PoC/PCP_Constituinte_1975'/r['local_file'],dest)
 items.append(dict(key=r['local_key'],collection='cartazes',title=r['title'],description=r['description'],date=r['date'],author='',organization=r['issuing_body'],type=r['object_type'],source=r['source_page_url'],images=[dict(url=r['source_image_url'],file=dest.name,role='Imagem 1')],notes='',event=r['event'],country=r['country']))
for r in [e for e in plan['entities'] if e.get('source_row')][:50]:
 field=lambda p:next((c['value'] for c in r['claims'] if c['p']==p),'')
 images=[dict(url=c['value'],file=hashlib.sha256(c['value'].encode()).hexdigest()[:20]+'.jpg',role=c.get('qualifiers',[{'value':'Imagem'}])[0]['value']) for c in r['claims'] if c['p']=='P10']
 items.append(dict(key=r['key'],collection='reportorio',title=r['label'],description='Transcrição do reportório do Ephemera; entrada '+str(r['source_row'])+'.',date=field('date_raw'),author=field('author_raw'),organization=field('org_raw'),type=field('type_raw'),source=r['source'],images=images,notes=field('notes_raw'),event=field('event_raw'),country=field('geo_raw')))
def download(im):
 dest=media/im['file']
 if not dest.exists():
  assert urlparse(im['url']).hostname in ('ephemerajpp.com','ephemerajpp.files.wordpress.com')
  subprocess.run(['curl','-fsSL','--retry','2','--max-time','60',im['url']+'?w=1000','-o',str(dest)],check=True)
 if dest.stat().st_size<100:raise ValueError(dest)
 return dest.name
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,[im for r in items for im in r['images']]))
(ROOT/'data/sample.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
with (ROOT/'data/sample.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['key','collection','title','date','author','organization','type','source']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in items)
print(f'{len(items)} items; {sum(len(r["images"]) for r in items)} image associations')
