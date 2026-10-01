/* Ephemera PoC: read-only previews of P10, restricted to Ephemera image hosts. */
(function () {
 'use strict';
 if (!/^Item:Q\d+$/.test(mw.config.get('wgPageName') || '') || mw.config.get('wgAction') !== 'view') return;
 const hostOK = new Set(['ephemerajpp.com', 'ephemerajpp.files.wordpress.com']);
 const safe = value => {
  try { const u = new URL(value); return u.protocol === 'https:' && hostOK.has(u.hostname) && /\.(jpe?g|png|gif|webp|tiff?)$/i.test(u.pathname) ? u : null; } catch (_) { return null; }
 };
 async function render() {
  if (document.getElementById('ephemera-images')) return;
  const qid = mw.config.get('wgPageName').split(':')[1];
  const get = async params => { const r = await fetch('/w/api.php?' + new URLSearchParams({format:'json',...params})); if (!r.ok) throw Error(r.status); const j=await r.json(); if(j.error)throw Error(j.error.info);return j; };
  const first = await get({action:'wbgetentities',ids:qid,props:'claims|labels',languages:'pt|en'});
  const item = first.entities[qid];
  let entities = [item];
  // The collection's links stay in Wikibase, so its gallery follows its current members.
  const parts = Object.values(item.claims || {}).flat().filter(c => c.mainsnak.property === '__HAS_PART__').map(c=>c.mainsnak.datavalue?.value?.id).filter(Boolean).slice(0,50);
  if (parts.length) entities.push(...Object.values((await get({action:'wbgetentities',ids:parts.join('|'),props:'claims|labels',languages:'pt|en'})).entities));
  const images=[];
  for (const e of entities) for (const c of e.claims?.P10 || []) {
   const u=safe(c.mainsnak.datavalue?.value);if(u)images.push({u,e});
  }
  if (!images.length) return;
  const section=document.createElement('section');section.id='ephemera-images';
  section.style.cssText='margin:1.2rem 0;padding:1rem;border:1px solid #c8ccd1;background:#f8f9fa;border-radius:6px';
  const title=document.createElement('h2');title.textContent='Imagens do acervo';section.append(title);
  const note=document.createElement('p');note.textContent='Pré-visualizações das imagens alojadas no WordPress do Ephemera. Os direitos das imagens mantêm-se na fonte; esta apresentação não é um upload para a Wikibase.';section.append(note);
  const grid=document.createElement('div');grid.style.cssText='display:flex;flex-wrap:wrap;gap:16px';section.append(grid);
  for (const {u,e} of images) {
   const fig=document.createElement('figure');fig.style.cssText='margin:0;width:240px;max-width:100%';
   const a=document.createElement('a');a.href=u.href;a.target='_blank';a.rel='noopener noreferrer';
   const img=document.createElement('img');img.alt=e.labels?.pt?.value || e.labels?.en?.value || e.id;img.loading='lazy';img.referrerPolicy='no-referrer';img.style.cssText='width:100%;height:220px;object-fit:contain;background:white';
   const thumb=new URL(u);thumb.searchParams.set('w','480');img.src=thumb.href;
   img.onerror=()=>{img.remove();a.textContent='Imagem indisponível — abrir na fonte';};a.append(img);fig.append(a);
   const caption=document.createElement('figcaption');const link=document.createElement('a');link.href='/wiki/Item:'+e.id+'?uselang=pt';link.textContent=img.alt;caption.append(link);fig.append(caption);grid.append(fig);
  }
  const target=document.querySelector('.wikibase-entityview-main') || document.querySelector('#mw-content-text');
  if(target)target.prepend(section);
 }
 mw.hook('wikipage.content').add(()=>render().catch(error=>console.warn('Ephemera preview:',error.message)));
}());
