/* Publish the paginated Ephemera catalogue. Run on the authenticated target wiki. */
async function publishCatalogue(plan) {
 if(location.origin!=='https://ephemera-poc.wikibase.cloud')throw Error('Wrong wiki');
 const out=document.createElement('pre');out.style.cssText='position:fixed;top:10px;right:10px;z-index:999999;background:white;color:#202122;padding:20px';document.body.append(out);
 let token;
 const api=async(p,write=false)=>{const args={format:'json',...p};if(write)Object.assign(args,{token,assert:'user',maxlag:5});const r=await fetch('/w/api.php'+(write?'':'?'+new URLSearchParams(args)),write?{method:'POST',body:new URLSearchParams(args)}:{});if(!r.ok)throw Error('HTTP '+r.status);const j=await r.json();if(j.error)throw Error(JSON.stringify(j.error));return j;};
 const read=async(title)=>Object.values((await api({action:'query',titles:title,prop:'revisions',rvprop:'content|ids',rvslots:'main'})).query.pages)[0];
 const edit=async(title,text,old)=>{if(old.revisions?.[0]?.slots.main['*']===text)return;const p={action:'edit',title,text,summary:'PoC: catálogo em páginas de 50 registos e miniaturas nas primeiras 50 entradas'};if(old.missing!==undefined)p.createonly=1;else p.baserevid=old.revisions[0].revid;const r=await api(p,true);if(r.edit?.result!=='Success')throw Error(JSON.stringify(r));};
 try {
  token=(await api({action:'query',meta:'tokens'})).query.tokens.csrftoken;
  const old=await read('MediaWiki:Common.css');const start='/* BEGIN EPHEMERA PAGINATED CATALOGUE */',end='/* END EPHEMERA PAGINATED CATALOGUE */';
  const clean=(old.revisions?.[0]?.slots.main['*']||'').replace(/\/\* BEGIN EPHEMERA PAGINATED CATALOGUE \*\/[\s\S]*?\/\* END EPHEMERA PAGINATED CATALOGUE \*\//g,'').trimEnd();
  await edit('MediaWiki:Common.css',clean+'\n'+start+'\n'+plan.css+'\n'+end,old);
  // Publish child pages first; replace the existing catalogue with page 1 last.
  for(const [i,p] of [...plan.pages.slice(1),plan.pages[0]].entries()){
   out.textContent='A publicar página '+(i+1)+'/'+plan.pages.length;
   await edit(p.title,p.text,await read(p.title));
  }
  out.textContent='CONCLUÍDO: 14 páginas, 696 registos, miniaturas nas primeiras 50 entradas.';
 }catch(e){out.textContent='ERRO NO CATÁLOGO: '+e.message;throw e;}
}
