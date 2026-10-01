"""Read-only checks against the real local WordPress and Tainacan API."""
import json,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base='http://localhost:8087'
def get(path):
 with urllib.request.urlopen(base+path,timeout=30) as r:return json.load(r)
ids=json.loads((ROOT/'reports/ids.json').read_text());sample=json.loads((ROOT/'data/sample.json').read_text());live={};counts={}
for key,cid in ids['collections'].items():
 data=get(f'/wp-json/tainacan/v2/collection/{cid}/items/?perpage=96');counts[key]=len(data['items']);live.update({r['id']:r for r in data['items']})
 (ROOT/f'reports/{key}-api.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
assert counts=={'cartazes':9,'reportorio':50},counts
for row in sample:
 r=live[ids['items'][row['key']]];assert r['title']==row['title']
 values={int(m['id']):m['value'] for m in r['metadata'].values()}
 for field in ('key','date','author','organization','type','source','notes','event','country'):
  assert values.get(ids['metadata'][row['collection']][field],'')==row[field],(row['key'],field)
 assert r['url'].startswith(base+'/')
 if row['images']:assert r['document_type']=='attachment' and r['_thumbnail_id']
filtered=get('/wp-json/tainacan/v2/collection/42/items/?'+urllib.parse.urlencode({'perpage':96,'metaquery[0][key]':54,'metaquery[0][value]':'PCP'}))
assert len(filtered['items'])==6
media=get('/wp-json/wp/v2/media?per_page=100');assert len(media)==71,len(media)
for image in media:
 assert image['source_url'].startswith(base+'/wp-content/uploads/')
 assert image['media_details'].get('sizes'),image['id']
 with urllib.request.urlopen(urllib.request.Request(image['source_url'],method='HEAD'),timeout=30) as r:assert r.status==200
with urllib.request.urlopen(base+'/cartazes-num-post/') as r:post=r.read().decode()
assert 'TESTE LOCAL — atualização' not in post
assert 'PCP1975-001' in post and '1975' in post and '/uploads/' in post
report={'collections':counts,'items':len(live),'media':len(media),'pcp_filter_results':len(filtered['items']),'metadata_match':True,'local_images_http_200':True,'wordpress_thumbnails_generated':True,'temporary_note_removed':True,'editorial_contains_catalogue_metadata':True}
(ROOT/'reports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
