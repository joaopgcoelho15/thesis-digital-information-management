/* Execute on the target wiki in an authenticated browser. No credentials leave it. */
async function runEphemeraPoC(plan, previewCode) {
 'use strict';
 if(location.origin!==plan.instance)throw Error('Wrong wiki origin');
 if(window.ephemeraRunning)throw Error('An import is already running in this page');
 window.ephemeraRunning=true;
 const journal=window.ephemeraJournal={started:new Date().toISOString(),map:{},actions:[],errors:[]};
 const panel=document.createElement('pre');panel.id='ephemera-import-status';panel.style.cssText='position:fixed;right:10px;top:10px;z-index:99999;background:white;color:#202122;border:2px solid #36c;padding:14px;max-width:700px;max-height:180px;overflow:auto;white-space:pre-wrap';document.body.append(panel);
 const status=t=>{panel.textContent=t;console.log(t);};
 const canonical=x=>JSON.stringify(sort(x));
 function sort(x){if(Array.isArray(x))return x.map(sort);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])]));return x;}
 const delay=ms=>new Promise(r=>setTimeout(r,ms));
 let token;
 async function api(p,write=false) {
  const params={format:'json',...p};if(write)Object.assign(params,{token,assert:'user',maxlag:'5'});
  for(let attempt=0;attempt<6;attempt++) {
   // An uncertain POST/network response is never blindly retried: re-run to rescan identifiers.
   const r=await fetch('/w/api.php'+(write?'':'?'+new URLSearchParams(params)),write?{method:'POST',body:new URLSearchParams(params)}:{});
   if(!r.ok)throw Error('HTTP '+r.status+'; stop and rescan before retry');
   const j=await r.json();
   if(j.error){if(['maxlag','ratelimited'].includes(j.error.code)&&attempt<5){status('A aguardar limite da API: '+j.error.code);await delay((attempt+1)*10000);continue;}throw Error(JSON.stringify(j.error));}
   return j;
  }
 }
 const all={};
 async function scan(){
  status('A verificar identificadores existentes na Wikibase…');
  const info=await api({action:'query',meta:'siteinfo',siprop:'namespaces'});
  const ns=Object.values(info.query.namespaces).filter(n=>['Item','Property'].includes(n.canonical || n['*']));
  for(const n of ns){let cont={};do{const j=await api({action:'query',list:'allpages',apnamespace:n.id,aplimit:500,...cont});const ids=j.query.allpages.map(p=>p.title.split(':')[1]);for(let i=0;i<ids.length;i+=50)Object.assign(all,(await api({action:'wbgetentities',ids:ids.slice(i,i+50).join('|')})).entities);cont=j.continue||{};}while(Object.keys(cont).length);}
 }
 const index=new Map();
 function addIndex(e){for(const c of e.claims?.P12 || []){const k=c.mainsnak.datavalue?.value;if(typeof k==='string'){if(index.has(k)&&index.get(k)!==e.id)throw Error('Duplicate P12: '+k);index.set(k,e.id);}}}
 function snak(c){
  const p=journal.map[c.p]||c.p;let value=c.value;
  if(c.type==='wikibase-entityid'){const id=value.startsWith('@')?journal.map[value.slice(1)]:value;if(!id)throw Error('Unresolved item '+value);value={'entity-type':'item','numeric-id':Number(id.slice(1)),id};}
  return {snaktype:'value',property:p,datavalue:{value,type:c.type}};
 }
 function statement(c,source){const s={type:'statement',rank:'normal',mainsnak:snak(c)};
  if(c.qualifiers){s.qualifiers={};for(const q of c.qualifiers){const n=snak(q);(s.qualifiers[n.property]??=[]).push(n);}}
  if(source)s.references=[{snaks:{P9:[{snaktype:'value',property:'P9',datavalue:{value:source,type:'string'}}]}}];return s;
 }
 const dv=d=>d.type==='wikibase-entityid'?{type:d.type,value:d.value.id}:d.type==='quantity'?{type:d.type,value:{...d.value,upperBound:d.value.upperBound??null,lowerBound:d.value.lowerBound??null}}:d;
 const signature=s=>canonical({p:s.mainsnak.property,v:dv(s.mainsnak.datavalue),q:Object.fromEntries(Object.entries(s.qualifiers||{}).map(([p,qs])=>[p,qs.map(q=>dv(q.datavalue))]))});
 async function upsert(rec){
  let id=rec.kind==='property'?Object.values(all).find(e=>e.type==='property'&&e.labels?.pt?.value===rec.label)?.id:index.get(rec.claims.find(c=>c.p==='P12')?.value || rec.key);
  if(id && rec.kind==='property' && all[id].datatype!==rec.datatype)throw Error('Property datatype mismatch '+id);
  const claims=rec.claims.map(c=>statement(c,rec.source));
  if(rec.kind!=='property'&&!rec.claims.some(c=>c.p==='P12'))claims.push(statement({p:'P12',type:'string',value:rec.key},null));
  if(!id){const data={labels:{pt:{language:'pt',value:rec.label},en:{language:'en',value:rec.label}},descriptions:{pt:{language:'pt',value:rec.description}},claims};if(rec.datatype)data.datatype=rec.datatype;
   const j=await api({action:'wbeditentity',new:rec.kind,data:JSON.stringify(data),summary:'PoC Ephemera: importação reproduzível WordPress/TablePress'},true);id=j.entity.id;all[id]=j.entity;addIndex(j.entity);journal.actions.push({key:rec.key,id,action:'created',revision:j.entity.lastrevid});
  }else{
   // Additive merge: no clear=1, no removal and no replacement of manual labels/claims.
   const before=(await api({action:'wbgetentities',ids:id})).entities[id];all[id]=before;
   const existing=new Set(Object.values(before.claims||{}).flat().map(signature));const missing=claims.filter(c=>!existing.has(signature(c)));
   if(missing.length){const j=await api({action:'wbeditentity',id,baserevid:before.lastrevid,data:JSON.stringify({claims:missing}),summary:'PoC Ephemera: acrescentar declarações em falta, preservar edições existentes'},true);all[id]=j.entity;journal.actions.push({key:rec.key,id,action:'augmented',revision:j.entity.lastrevid});}
   else journal.actions.push({key:rec.key,id,action:'unchanged'});
  }
  journal.map[rec.key]=id;localStorage.setItem('ephemera-poc-journal',JSON.stringify(journal));return id;
 }
 async function editPage(title,text,append=false){
  const q=await api({action:'query',titles:title,prop:'revisions',rvprop:'content|ids',rvslots:'main'});const pg=Object.values(q.query.pages)[0];const old=pg.revisions?.[0]?.slots.main['*']||'';
  if(append){if(old.includes('/* Ephemera PoC: read-only previews')){journal.actions.push({page:title,action:'unchanged'});return;}text=old+'\n'+text;}
  if(old===text)return;
  const args={action:'edit',title,text,summary:'PoC Ephemera: imagens e importação reproduzível'};
  if(pg.missing!==undefined)args.createonly='1';else args.baserevid=pg.revisions[0].revid;
  const r=await api(args,true);if(r.edit?.result!=='Success')throw Error(JSON.stringify(r));journal.actions.push({page:title,action:'edited',revision:r.edit.newrevid});
 }
 try {
  const auth=await api({action:'query',meta:'userinfo|tokens',uiprop:'rights'});if(auth.query.userinfo.anon!==undefined)throw Error('Login required');token=auth.query.tokens.csrftoken;
  journal.user=auth.query.userinfo.name;await scan();Object.values(all).forEach(addIndex);
  for(const p of plan.properties){status('Propriedade: '+p.label);await upsert(p);}
  const hasPart=journal.map.has_part;
  const imageScript=previewCode.replaceAll('__HAS_PART__',hasPart);
  if(auth.query.userinfo.rights.includes('editsitejs'))await editPage('MediaWiki:Common.js',imageScript,true);
  else {
   // Cloud grants editsitecss but not editsitejs. Generate a reversible site stylesheet.
   const urls=new Set(plan.entities.flatMap(e=>e.claims.filter(c=>c.p==='P10').map(c=>c.value)));
   for(const e of Object.values(all))for(const c of e.claims?.P10 || [])urls.add(c.mainsnak.datavalue.value);
   const quote=v=>JSON.stringify(v);
   const rules=['/* BEGIN EPHEMERA POC PREVIEWS */', '#P10 .wikibase-snakview-value a.external {display:inline-block;width:260px;overflow-wrap:anywhere;}', '#P10 .wikibase-snakview-value a::after {content:"";display:block;width:260px;height:240px;background-repeat:no-repeat;background-position:center;background-size:contain;margin:8px 0;border:1px solid #c8ccd1;background-color:#fff;}'];
   for(const value of urls){const u=new URL(value);if(u.protocol!=='https:'||!['ephemerajpp.com','ephemerajpp.files.wordpress.com'].includes(u.hostname))continue;const thumbnail=new URL(u);thumbnail.searchParams.set('w','480');rules.push('#P10 .wikibase-snakview-value a[href='+quote(value)+']::after {background-image:url('+quote(thumbnail.href)+');}');}
   for(let i=7;i<=15;i++){const u=all['Q'+i]?.claims?.P10?.[0]?.mainsnak.datavalue?.value;if(!u)continue;const thumb=new URL(u);thumb.searchParams.set('w','480');rules.push('#'+hasPart+' .wikibase-snakview-value a[href="/wiki/Item:Q'+i+'"] {display:inline-block;width:240px;}');rules.push('#'+hasPart+' .wikibase-snakview-value a[href="/wiki/Item:Q'+i+'"]::after {content:"";display:block;width:240px;height:220px;background:center/contain no-repeat url('+quote(thumb.href)+');}');}
   rules.push('/* END EPHEMERA POC PREVIEWS */');
   const title='MediaWiki:Common.css';const q=await api({action:'query',titles:title,prop:'revisions',rvprop:'content|ids',rvslots:'main'});const pg=Object.values(q.query.pages)[0];const old=pg.revisions?.[0]?.slots.main['*']||'';
   const stripped=old.replace(/\/\* BEGIN EPHEMERA POC PREVIEWS \*\/[\s\S]*?\/\* END EPHEMERA POC PREVIEWS \*\//g,'').trimEnd();
   const css=stripped+'\n'+rules.join('\n');if(css!==old){const a={action:'edit',title,text:css,summary:'PoC: pré-visualizações das imagens Ephemera em P10; CSS gerado pelo importador'};if(pg.missing!==undefined)a.createonly='1';else a.baserevid=pg.revisions[0].revid;const r=await api(a,true);if(r.edit?.result!=='Success')throw Error(JSON.stringify(r));journal.actions.push({page:title,action:'edited',revision:r.edit.newrevid});}
   journal.preview='CSS global gerado a partir de P10, sem JavaScript global';
  }
  // Link the original poster collection using one reusable property.
  const q1=(await api({action:'wbgetentities',ids:'Q1'})).entities.Q1;
  const parts=Array.from({length:9},(_,i)=>({p:hasPart,type:'wikibase-entityid',value:'Q'+(i+7)}));
  const q1claims=parts.map(c=>statement(c,null));const present=new Set(Object.values(q1.claims||{}).flat().map(signature));const missing=q1claims.filter(c=>!present.has(signature(c)));
  if(missing.length)await api({action:'wbeditentity',id:'Q1',baserevid:q1.lastrevid,data:JSON.stringify({claims:missing}),summary:'PoC: ligar os nove cartazes à coleção'},true);
  for(let i=0;i<plan.entities.length;i++){const rec=plan.entities[i];status(`${i+1}/${plan.entities.length}: ${rec.label}`);await upsert(rec);await delay(150);}
  const rep=journal.map.repertory;
  const postlines=plan.entities.filter(e=>e.post_id).map(e=>'* [[Item:'+journal.map[e.key]+'|'+e.label.replace(/[\[\]{}|]/g,'')+']]').join('\n');
  await editPage('Project:PoC — Importação WordPress e TablePress',`= PoC Ephemera =\nImportação por código a partir das APIs públicas e do HTML público do WordPress.\n\n== Imagens ==\n[[Item:Q1|Galeria dos nove cartazes de 1975]]. As pré-visualizações usam P10 e CSS gerado nesta wiki. Os ficheiros permanecem no WordPress e não passam a ter licença CC0.\n\n== Cinco posts recentes ==\n${postlines}\n\n== TablePress 77 ==\n[[Item:${rep}|Reportório de documentos e publicações da oposição (1926–1974)]]. Foram importados 696 registos preenchidos; quatro linhas vazias foram excluídas. Cada registo aponta para o reportório através de P8.\nAs datas incertas e códigos originais são preservados. AUTOR, ORG, BIO, GEO, TIPO e EVENTO são transcrições, sem ligação automática a pessoas ou organizações.\n\n== Reprodução ==\nCódigo e snapshots: Wikibase_PoC/importacao_2026_09 no projeto local. collect.py extrai os dados; runner.js aplica o plano pela API. Reexecuções verificam P12 antes de criar e preservam declarações e rótulos manuais.\n`);
  journal.completed=new Date().toISOString();localStorage.setItem('ephemera-poc-journal',JSON.stringify(journal));status('CONCLUÍDO: '+plan.entities.length+' entidades processadas. '+journal.actions.filter(a=>a.action==='created').length+' criadas. Página: Project:PoC — Importação WordPress e TablePress');
 }catch(e){journal.errors.push(String(e));localStorage.setItem('ephemera-poc-journal',JSON.stringify(journal));status('PARADO: '+e.message+'\nReexecutar é seguro após resolver a causa; os IDs já criados são pesquisados.');console.error(e);}
 finally{window.ephemeraRunning=false;}
 return journal;
}
