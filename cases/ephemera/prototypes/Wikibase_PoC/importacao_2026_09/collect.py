#!/usr/bin/env python3
"""Reproducible public WordPress/TablePress extraction; standard library only."""
import argparse, collections, datetime as dt, hashlib, html, json, re, subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urljoin
ROOT=Path(__file__).resolve().parent
SOURCE='https://ephemerajpp.com/reportorio-das-publicacoes-clandestinas-semilegais-e-legais-da-oposicao-1926-1974/'
POSTS='https://public-api.wordpress.com/rest/v1.1/sites/ephemerajpp.com/posts/?number=5&order_by=date&order=DESC&type=post&status=publish'
def norm(s): return re.sub(r'\s+', ' ', html.unescape(s)).strip()
def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def imageurl(u):
 u=urljoin(SOURCE,html.unescape(u)); p=urlsplit(u)
 if p.scheme not in ('https','http') or not (p.hostname=='ephemerajpp.com' or p.hostname=='ephemerajpp.files.wordpress.com'): return None
 if not re.search(r'\.(jpe?g|png|gif|webp|tiff?)(?:$)',p.path,re.I):return None
 return urlunsplit(('https',p.netloc,p.path,'',''))
class Parser(HTMLParser):
 def __init__(self,table=False):super().__init__();self.table=table;self.active=not table;self.rows=[];self.row=None;self.cell=None;self.images=[];self.words=[]
 def handle_starttag(self,t,a):
  a=dict(a)
  if self.table and t=='table' and a.get('id')=='tablepress-77':self.active=True
  if not self.active:return
  if t=='tr':self.row=[]
  if t in ('td','th'):self.cell={'text':'','links':[],'images':[]}
  if t in ('br','p','div') and self.cell is not None:self.cell['text']+='\n'
  if t=='a' and self.cell is not None and a.get('href'):self.cell['links'].append(urljoin(SOURCE,a['href']))
  if t=='img':
   u=imageurl(a.get('data-orig-file') or a.get('data-large-file') or a.get('src',''))
   if u:
    self.images.append(u)
    if self.cell is not None:self.cell['images'].append(u)
 def handle_data(self,d):
  if self.active:
   self.words.append(d)
   if self.cell is not None:self.cell['text']+=d
 def handle_endtag(self,t):
  if not self.active:return
  if t in ('td','th') and self.cell is not None:self.cell['text']=norm(self.cell['text']);self.row.append(self.cell);self.cell=None
  if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
  if self.table and t=='table':self.active=False

def timevalue(raw):
 if not re.fullmatch(r'\d{4}(?:/\d{1,2}(?:/\d{1,2})?)?',raw):return None
 parts=list(map(int,raw.split('/')))
 try:dt.date(parts[0],parts[1] if len(parts)>1 else 1,parts[2] if len(parts)>2 else 1)
 except ValueError:return None
 return {'time':f'+{parts[0]:04d}-{parts[1] if len(parts)>1 else 0:02d}-{parts[2] if len(parts)>2 else 0:02d}T00:00:00Z','timezone':0,'before':0,'after':0,'precision':8+len(parts),'calendarmodel':'http://www.wikidata.org/entity/Q1985727'}
def val(p,v,t='string',qualifiers=None):
 r={'p':p,'value':v,'type':t}
 if qualifiers:r['qualifiers']=qualifiers
 return r

def entity(key,label,description,claims,source=None,kind='item'):
 return dict(key=key,label=label[:250],description=description[:250],claims=claims,source=source,kind=kind)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');args=ap.parse_args()
 snap=ROOT/'snapshots';snap.mkdir(exist_ok=True)
 if args.refresh:
  for name,url in [('tablepress.html',SOURCE),('posts.json',POSTS)]:subprocess.run(['curl','--fail','-L','-sS','--max-time','120',url,'-o',str(snap/name)],check=True)
 table=Parser(True);table.feed((snap/'tablepress.html').read_text())
 expected=['IMAGEM 1','IMAGEM 2','DATA','AUTOR','TÍTULO','ORG','BIO','GEO','TIPO','EVENTO','NOTAS']
 assert [c['text'] for c in table.rows[0]]==expected,'Source schema changed; review mapping'
 definitions=[('date_raw','data na fonte','string','Data tal como transcrita na fonte, incluindo incerteza ou códigos.'),('author_raw','autor na fonte','string','Transcrição de AUTOR; não identifica automaticamente uma pessoa.'),('org_raw','organização na fonte','string','Transcrição de ORG; não pressupõe entidade normalizada.'),('bio_raw','BIO na fonte','string','Valor da coluna BIO, preservado sem inferência.'),('geo_raw','GEO na fonte','string','Valor da coluna GEO, preservado sem inferência.'),('type_raw','tipo na fonte','string','Código da coluna TIPO; vocabulário ainda por validar.'),('event_raw','evento na fonte','string','Transcrição da coluna EVENTO.'),('notes_raw','notas na fonte','string','Transcrição das notas do catálogo.'),('row_number','posição na tabela de origem','quantity','Número da linha de dados no snapshot; não é identificador permanente.'),('image_role','posição da imagem na fonte','string','Coluna ou posição da imagem na fonte; não infere frente ou verso.'),('table_id','identificador TablePress','external-id','Identificador da tabela, qualificado pelo domínio WordPress.'),('published','data de publicação do post','time','Data de publicação editorial; não é data dos objetos retratados.'),('has_part','tem parte','wikibase-item','Entidade ou objeto que integra este conjunto.')]
 props=[entity(k,l,d,[],kind='property')|{'datatype':t} for k,l,t,d in definitions]
 records=[]
 records.append(entity('type_post','post do WordPress','Publicação editorial do blog; pode descrever vários objetos de arquivo.',[]))
 records.append(entity('type_record','registo do reportório da oposição','Entrada do catálogo Ephemera; não pressupõe uma publicação periódica ou exemplar único.',[]))
 records.append(entity('repertory','Reportório de documentos e publicações da oposição (1926–1974)','Catálogo Ephemera: transcrição estruturada da tabela TablePress 77.',[val('table_id','ephemerajpp.com:77'),val('P12','ephemerajpp.com:tablepress:77'),val('P9',SOURCE)],SOURCE))
 # Process posts before the large table so the small pilot is immediately inspectable.
 posts=json.loads((snap/'posts.json').read_text())['posts'];assert len(posts)==5
 for post in posts:
  title=norm(post['title']);key=f"ephemerajpp.com:post:{post['ID']}"
  parser=Parser();parser.feed(post['content'])
  imgs=list(dict.fromkeys(parser.images))
  featured=imageurl(post.get('featured_image',''))
  featured_extra=featured if featured and featured not in imgs else None
  if featured_extra:imgs.append(featured_extra)
  claims=[val('P1','@type_post','wikibase-entityid'),val('P12',key),val('P9',post['URL']),val('P2',{'text':title,'language':'pt'},'monolingualtext'),val('published',timevalue(post['date'][:10].replace('-','/')),'time')]
  claims += [val('P10',u,qualifiers=[val('image_role','imagem destacada' if u==featured_extra else f'imagem {i}')]) for i,u in enumerate(imgs,1)]
  if imgs:claims.append(val('P13','direitos das imagens não determinados; ficheiros mantidos no WordPress'))
  records.append(entity(key,title,'Post publicado no blog Ephemera; metadados importados automaticamente.',claims,post['URL'])|{'post_id':post['ID'],'images':imgs})
 rawrows=[];empty=[];image_keys=collections.Counter()
 for i,row in enumerate(table.rows[1:],1):
  assert len(row)==11,(i,len(row))
  if not any(c['text'] or c['links'] or c['images'] for c in row):empty.append(i);continue
  imgs=[]
  for ci in (0,1):
   urls=[u for a in row[ci]['links'] if (u:=imageurl(a))] or row[ci]['images']
   imgs += [(u,expected[ci]) for u in dict.fromkeys(urls)]
  primary=imgs[0][0] if imgs else None
  if primary:image_keys[primary]+=1
  rawrows.append((i,row,imgs,primary))
 seen=collections.Counter();duplicates=[];rawdates=[]
 mapping={2:'date_raw',3:'author_raw',5:'org_raw',6:'bio_raw',7:'geo_raw',8:'type_raw',9:'event_raw',10:'notes_raw'}
 for i,row,imgs,primary in rawrows:
  base=('image:'+primary) if primary and image_keys[primary]==1 else 'metadata:'+digest(row)
  h=digest(base)[:24];seen[h]+=1
  # Keep indistinguishable repeated source rows separate; report for curation.
  key='ephemerajpp.com:tablepress:77:'+h+(f':duplicate:{seen[h]}' if seen[h]>1 else '')
  if seen[h]>1:duplicates.append(i)
  title=row[4]['text']
  label=title or ('Documento sem título — '+ ' — '.join(c['text'] for c in row[2:4] if c['text'])+f' [{h[:6]}]')
  claims=[val('P1','@type_record','wikibase-entityid'),val('P8','@repertory','wikibase-entityid'),val('P12',key),val('P9',SOURCE+'#tablepress-77'),val('row_number',{'amount':f'+{i}','unit':'1'},'quantity')]
  if title:claims.append(val('P2',{'text':title,'language':'pt'},'monolingualtext'))
  for ci,prop in mapping.items():
   if row[ci]['text']:
    # Wikibase string values have a length limit; preserve exact complete raw data in snapshot.
    if len(row[ci]['text'])>1500: raise ValueError(f'Long cell: row {i}, column {ci}; needs explicit split policy')
    claims.append(val(prop,row[ci]['text']))
  date=timevalue(row[2]['text'])
  if date:claims.append(val('P5',date,'time'))
  elif row[2]['text']:rawdates.append({'row':i,'date':row[2]['text']})
  for u,role in imgs:claims.append(val('P10',u,qualifiers=[val('image_role',role)]))
  if imgs:claims.append(val('P13','direitos das imagens não determinados; ficheiros mantidos no WordPress'))
  records.append(entity(key,label,f'Registo da TablePress 77 do Ephemera; entrada {i} no snapshot de origem.',claims,SOURCE+'#tablepress-77')|{'source_row':i,'raw_cells':row})
 plan={'version':1,'instance':'https://ephemera-poc.wikibase.cloud','properties':props,'entities':records,'source_sha256':{f:hashlib.sha256((snap/f).read_bytes()).hexdigest() for f in ('tablepress.html','posts.json')}}
 (ROOT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
 report={'source_rows':len(table.rows)-1,'nonempty_rows':len(rawrows),'empty_rows':empty,'duplicate_rows':duplicates,'unparsed_dates':rawdates,'posts':[{'id':p['ID'],'title':norm(p['title']),'date':p['date']} for p in posts],'entities':len(records),'properties':len(props)}
 (ROOT/'extraction_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k not in ('unparsed_dates','empty_rows')},ensure_ascii=False));print('empty',len(empty),'unparsed dates',len(rawdates))
if __name__=='__main__':main()
