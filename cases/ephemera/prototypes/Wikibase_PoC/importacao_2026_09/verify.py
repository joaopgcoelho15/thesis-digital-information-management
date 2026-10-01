#!/usr/bin/env python3
"""Read-only API audit against the frozen plan; save a complete public-data snapshot."""
import collections, json, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
API='https://ephemera-poc.wikibase.cloud/w/api.php'
def api(**params):
 req=urllib.request.Request(API+'?'+urllib.parse.urlencode(dict(format='json',**params)),headers={'User-Agent':'Ephemera-PoC/1.0 public-data-verification'})
 with urllib.request.urlopen(req,timeout=90) as r:j=json.load(r)
 if 'error'in j:raise RuntimeError(j['error'])
 return j

def main():
 plan=json.loads((ROOT/'plan.json').read_text());entities={}
 for ns in (120,122):
  cont={}
  while True:
   j=api(action='query',list='allpages',apnamespace=ns,aplimit=500,**cont)
   ids=[p['title'].split(':')[1] for p in j['query']['allpages']]
   for i in range(0,len(ids),50):entities.update(api(action='wbgetentities',ids='|'.join(ids[i:i+50]))['entities'])
   cont=j.get('continue',{})
   if not cont:break
 (ROOT/'published_entities.json').write_text(json.dumps(entities,ensure_ascii=False,indent=2))
 props={p['key']:next((e['id'] for e in entities.values() if e.get('type')=='property' and e.get('labels',{}).get('pt',{}).get('value')==p['label']),None) for p in plan['properties']}
 index=collections.defaultdict(list)
 for e in entities.values():
  for c in e.get('claims',{}).get('P12',[]):index[c['mainsnak']['datavalue']['value']].append(e['id'])
 mapping=dict(props);missing=[];duplicates=[]
 for r in plan['entities']:
  identity=next((c['value'] for c in r['claims'] if c['p']=='P12'),r['key']);ids=index[identity]
  if not ids:missing.append(r['key'])
  elif len(set(ids))!=1:duplicates.append({'key':r['key'],'ids':ids})
  else:mapping[r['key']]=ids[0]
 mismatches=[];duplicate_claims=[]
 def value(v,t):
  if t=='wikibase-entityid':return v['id'] if isinstance(v,dict) else mapping.get(v[1:]) if v.startswith('@') else v
  if t=='quantity':return {**v,'upperBound':v.get('upperBound'),'lowerBound':v.get('lowerBound')}
  return v
 def spec_sig(c):return [mapping.get(c['p'],c['p']),value(c['value'],c['type']),{mapping.get(q['p'],q['p']):[value(q['value'],q['type'])] for q in c.get('qualifiers',[])}]
 def live_sig(c):
  s=c['mainsnak'];d=s.get('datavalue')
  if not d:return None
  return [s['property'],value(d['value'],d['type']),{p:[value(q['datavalue']['value'],q['datavalue']['type']) for q in qs] for p,qs in c.get('qualifiers',{}).items()}]
 for r in plan['entities']:
  if r['key'] not in mapping:continue
  qid=mapping[r['key']];live=entities[qid];claims=[c for cs in live.get('claims',{}).values() for c in cs]
  sigs=[live_sig(c) for c in claims]
  counts=collections.Counter(json.dumps(s,sort_keys=True,ensure_ascii=False) for s in sigs)
  duplicate_claims.extend({'id':qid,'signature':k,'count':n} for k,n in counts.items() if n>1)
  for c in r['claims']:
   if spec_sig(c) not in sigs:mismatches.append({'id':qid,'property':c['p'],'value':c['value']})
   if r.get('source'):
    matched=[s for s in claims if live_sig(s)==spec_sig(c)]
    if matched and not any(any(sn.get('datavalue',{}).get('value')==r['source'] for sn in ref.get('snaks',{}).get('P9',[]))for s in matched for ref in s.get('references',[])):mismatches.append({'id':qid,'property':c['p'],'reason':'missing source reference'})
 report={'expected_items':len(plan['entities']),'matched_items':sum(r['key'] in mapping for r in plan['entities']),'matched_properties':sum(bool(x) for x in props.values()),'missing':missing,'duplicate_identifiers':duplicates,'duplicate_claims':duplicate_claims,'mismatched_claims':mismatches,'table_rows':sum('source_row'in r and r['key']in mapping for r in plan['entities']),'posts':{str(r['post_id']):mapping.get(r['key']) for r in plan['entities'] if r.get('post_id')}}
 (ROOT/'wikibase_ids.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2));(ROOT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({**report,'missing':len(missing),'mismatched_claims':len(mismatches)},ensure_ascii=False))
 if missing or duplicates or duplicate_claims or mismatches:raise SystemExit(1)
if __name__=='__main__':main()
