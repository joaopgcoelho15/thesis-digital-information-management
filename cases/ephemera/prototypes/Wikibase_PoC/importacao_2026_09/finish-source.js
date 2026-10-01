/* Add a navigable native MediaWiki catalogue after the verified import. */
async function finishEphemera(plan) {
 if(location.origin!==plan.instance || window.ephemeraRunning)throw Error('Wrong wiki or import still running');
 const journal=window.ephemeraJournal || JSON.parse(localStorage.getItem('ephemera-poc-journal'));
 const map=journal.map, rows=plan.entities.filter(e=>e.source_row),posts=plan.entities.filter(e=>e.post_id);
 if(rows.length!==696||rows.some(e=>!map[e.key])||posts.some(e=>!map[e.key]))throw Error('Incomplete import map; no catalogue will be published');
 const out=document.createElement('pre');out.id='ephemera-finish';out.style.cssText='position:fixed;top:10px;right:10px;z-index:999999;background:white;padding:15px;color:#202122';document.body.append(out);
 let token;
 const api=async(p,write=false)=>{const a={format:'json',...p};if(write)Object.assign(a,{token,assert:'user',maxlag:5});const r=await fetch('/w/api.php'+(write?'':'?'+new URLSearchParams(a)),write?{method:'POST',body:new URLSearchParams(a)}:{});if(!r.ok)throw Error('HTTP '+r.status);const j=await r.json();if(j.error)throw Error(JSON.stringify(j.error));return j;};
 const page=async(title,text)=>{const q=await api({action:'query',titles:title,prop:'revisions',rvprop:'content|ids',rvslots:'main'});const p=Object.values(q.query.pages)[0];if(p.revisions?.[0]?.slots.main['*']===text)return;const a={action:'edit',title,text,summary:'PoC: catálogo navegável gerado por código a partir dos registos importados'};if(p.missing!==undefined)a.createonly=1;else a.baserevid=p.revisions[0].revid;const r=await api(a,true);if(r.edit?.result!=='Success')throw Error(JSON.stringify(r));};
 const esc=s=>String(s??'').replace(/[&<>\[\]{}|]/g,c=>'&#'+c.charCodeAt(0)+';');
 const field=(e,p)=>e.claims.find(c=>c.p===p)?.value || '';
 try{
  token=(await api({action:'query',meta:'tokens'})).query.tokens.csrftoken;
  out.textContent='A completar as imagens destacadas dos cinco posts…';
  const extraCSS=[];
  for(const r of posts){
   const id=map[r.key],entity=(await api({action:'wbgetentities',ids:id})).entities[id];const add=[];
   for(const c of r.claims.filter(c=>['P10','P13'].includes(c.p))){
    if((entity.claims?.[c.p]||[]).some(s=>s.mainsnak.datavalue?.value===c.value))continue;
    const st={type:'statement',rank:'normal',mainsnak:{snaktype:'value',property:c.p,datavalue:{type:'string',value:c.value}},references:[{snaks:{P9:[{snaktype:'value',property:'P9',datavalue:{type:'string',value:r.source}}]}}]};
    if(c.qualifiers){st.qualifiers={};for(const q of c.qualifiers){const p=map[q.p]||q.p;st.qualifiers[p]=[{snaktype:'value',property:p,datavalue:{type:'string',value:q.value}}];}}
    add.push(st);
   }
   if(add.length)await api({action:'wbeditentity',id,baserevid:entity.lastrevid,data:JSON.stringify({claims:add}),summary:'PoC: incluir a imagem destacada disponibilizada pela API WordPress'},true);
   for(const c of r.claims.filter(c=>c.p==='P10')){const u=new URL(c.value);u.searchParams.set('w','480');extraCSS.push('#P10 .wikibase-snakview-value a[href='+JSON.stringify(c.value)+']::after {background-image:url('+JSON.stringify(u.href)+');}');}
  }
  extraCSS.push('#P10 .wikibase-snakview-value a.external {display:inline-block;width:260px;overflow-wrap:anywhere;}','#P10 .wikibase-snakview-value a::after {width:260px;max-width:none;}');
  for(let i=7;i<=15;i++)extraCSS.push('#'+map.has_part+' .wikibase-snakview-value a[href="/wiki/Item:Q'+i+'"] {display:inline-block;width:240px;}');
  const cssTitle='MediaWiki:Common.css',cssPage=Object.values((await api({action:'query',titles:cssTitle,prop:'revisions',rvprop:'content|ids',rvslots:'main'})).query.pages)[0];
  const original=cssPage.revisions[0].slots.main['*'];const block='/* BEGIN EPHEMERA POC LAYOUT */\n'+extraCSS.join('\n')+'\n/* END EPHEMERA POC LAYOUT */';
  const clean=original.replace(/\/\* BEGIN EPHEMERA POC LAYOUT \*\/[\s\S]*?\/\* END EPHEMERA POC LAYOUT \*\//g,'').trimEnd();
  const updated=clean+'\n'+block;if(updated!==original)await api({action:'edit',title:cssTitle,baserevid:cssPage.revisions[0].revid,text:updated,summary:'PoC: imagens destacadas e largura legível das pré-visualizações'},true);
  out.textContent='A ligar os 696 registos ao reportório…';
  const qid=map.repertory,has=map.has_part;
  const e=(await api({action:'wbgetentities',ids:qid})).entities[qid];const old=new Set((e.claims?.[has]||[]).map(c=>c.mainsnak.datavalue?.value?.id));
  const claims=rows.filter(r=>!old.has(map[r.key])).map(r=>({type:'statement',rank:'normal',mainsnak:{snaktype:'value',property:has,datavalue:{type:'wikibase-entityid',value:{'entity-type':'item',id:map[r.key],'numeric-id':Number(map[r.key].slice(1))}}}}));
  if(claims.length)await api({action:'wbeditentity',id:qid,baserevid:e.lastrevid,data:JSON.stringify({claims}),summary:'PoC: ligar os 696 registos importados através de tem parte'},true);
  out.textContent='A publicar a tabela de consulta…';
  const tableTitle='Project:Reportório da oposição — TablePress 77';
  const lines=['= Reportório da oposição — TablePress 77 =','[[Project:PoC — Importação WordPress e TablePress|← Índice da PoC]] · [[Item:'+qid+'|Entidade do reportório]]','', 'Catálogo gerado por código a partir dos 696 registos preenchidos da tabela pública do Ephemera. Cada ligação abre um item Wikibase com metadados, proveniência e imagens. As datas e os códigos abaixo são transcritos da fonte, incluindo incertezas.','', 'Clique num cabeçalho para ordenar a tabela. A posição identifica a linha no snapshot de origem, não é um identificador permanente.','', '{| class="wikitable sortable"','! Entrada !! Registo !! Data na fonte !! Autor na fonte !! Organização na fonte !! Tipo !! Imagens'];
  for(const r of rows){const id=map[r.key],n=r.claims.filter(c=>c.p==='P10').length;lines.push('|-','| '+r.source_row+' || [[Item:'+id+'|'+esc(r.label)+']] || '+esc(field(r,'date_raw'))+' || '+esc(field(r,'author_raw'))+' || '+esc(field(r,'org_raw'))+' || '+esc(field(r,'type_raw'))+' || '+(n?'[[Item:'+id+'#P10|Ver '+n+' imagem(ns)]]':'—'));}
  lines.push('|}');await page(tableTitle,lines.join('\n'));
  const postsList=posts.map(p=>'* [[Item:'+map[p.key]+'|'+esc(p.label)+']]').join('\n');
  await page('Project:PoC — Importação WordPress e TablePress', '= PoC Ephemera: WordPress e Wikibase =\n\n== Imagens na Wikibase ==\n[[Item:Q1|Coleção dos nove cartazes de 1975]] · [[Item:Q7#P10|Exemplo com imagem]]\n\nAs imagens aparecem junto de P10 através de CSS global gerado pelo importador. Os ficheiros continuam alojados no WordPress do Ephemera; não foram carregados nesta wiki nem no Wikimedia Commons. Os direitos das imagens não são alterados. A vista depende do CSS e dos endereços de origem. Novas URLs precisam de regeneração do CSS.\n\n== TablePress 77: 696 registos ==\n[['+tableTitle+'|Abrir tabela de consulta ordenável]] · [[Item:'+qid+'|Abrir entidade do reportório]]\n\nUm Q por registo preenchido. Quatro linhas vazias foram excluídas. Os registos apontam para o reportório através de P8 e o reportório aponta para os registos através de '+has+'. As duas colunas de imagens são identificadas por qualificadores. Datas ambíguas são conservadas como texto; 123 valores não foram convertidos automaticamente em datas. Os campos AUTOR, ORG, BIO, GEO, TIPO e EVENTO são transcrições, sem desambiguação automática de entidades.\n\n== Cinco posts mais recentes na recolha de 5 de setembro de 2026 ==\n'+postsList+'\n\nSão registos de posts editoriais, não uma catalogação automática de cada objeto físico retratado. Foram importados título, identificador WordPress qualificado pelo domínio, ligação à fonte, data de publicação e URLs de imagens. O corpo integral dos posts está preservado nos snapshots locais. As galerias incorporadas do Google Drive não foram enumeradas; nesses casos usa-se a imagem destacada do WordPress, quando disponível.\n\n== Código e reprodução ==\nFicheiros no projeto local: Wikibase_PoC/importacao_2026_09.\n* collect.py extrai o HTML público TablePress e a API pública WordPress, sem alterar o site de origem.\n* plan.json conserva o plano e a transcrição dos campos.\n* runner.js cria ou completa entidades através da API MediaWiki; a sessão autenticada permanece no browser.\n* verify.py compara os registos publicados com o plano e grava os QIDs.\n* finish-source.js gera esta apresentação e a tabela de consulta.\n\nAs reexecuções verificam os identificadores P12 e não apagam declarações ou rótulos manuais. A fusão é aditiva: não substitui automaticamente valores anteriores que mudem na fonte. Uma atualização editorial contínua exige uma política adicional de reconciliação.\n');
  journal.catalogue=tableTitle;journal.finished=new Date().toISOString();localStorage.setItem('ephemera-poc-journal',JSON.stringify(journal));out.textContent='CONCLUÍDO: catálogo ordenável, cinco posts e imagens publicados.';
 }catch(e){out.textContent='ERRO NA APRESENTAÇÃO: '+e.message;throw e;}
}
