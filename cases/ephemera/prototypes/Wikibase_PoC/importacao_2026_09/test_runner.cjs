/* Meaningful offline contract tests: idempotency, preservation and uncertain writes. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=__dirname, fullPlan=JSON.parse(fs.readFileSync(root+'/plan.json','utf8'));
const source=fs.readFileSync(root+'/runner.js','utf8');
function harness(){
 const db={},pages={},calls=[];let nextQ=16,nextP=20,rev=100;let failNextCreation=false;
 for(let i=1;i<=15;i++)db['Q'+i]={id:'Q'+i,type:'item',labels:{pt:{language:'pt',value:'Existing '+i}},claims:{},lastrevid:rev++};
 const copy=x=>JSON.parse(JSON.stringify(x));
 const context={URL,URLSearchParams,Set,Map,console:{log(){},warn(){},error(){}},location:{origin:fullPlan.instance},window:{},document:{createElement(){return{style:{},append(){}}},body:{append(){}}},localStorage:{setItem(){}},setTimeout(cb){queueMicrotask(cb)}};
 context.fetch=async(url,opts={})=>{
  const p=Object.fromEntries(opts.body||new URL(url,'https://test.invalid').searchParams);calls.push(copy(p));let result;
  if(p.action==='query'){
   if(p.meta==='userinfo|tokens')result={query:{userinfo:{name:'Test',rights:['editsitecss']},tokens:{csrftoken:'test'}}};
   else if(p.meta==='tokens')result={query:{tokens:{csrftoken:'test'}}};
   else if(p.meta==='siteinfo')result={query:{namespaces:{120:{id:120,canonical:'Item'},122:{id:122,canonical:'Property'}}}};
   else if(p.list==='allpages')result={query:{allpages:Object.values(db).filter(e=>e.type===(p.apnamespace==='120'?'item':'property')).map(e=>({title:(e.type==='item'?'Item:':'Property:')+e.id}))}};
   else if(p.titles){const pg=pages[p.titles];result={query:{pages:{1:pg?{title:p.titles,revisions:[{revid:pg.rev,slots:{main:{'*':pg.text}}}]}:{title:p.titles,missing:''}}}};}
  }else if(p.action==='wbgetentities')result={entities:Object.fromEntries(p.ids.split('|').map(id=>[id,db[id]||{id,missing:''}]))};
  else if(p.action==='wbeditentity'){
   assert.equal(p.clear,undefined,'Never clear an entity');const data=JSON.parse(p.data);const id=p.id||(p.new==='property'?'P'+nextP++:'Q'+nextQ++);
   const e=db[id]||(db[id]={id,type:p.new,labels:{},claims:{}});
   if(p.baserevid)assert.equal(Number(p.baserevid),e.lastrevid);
   if(data.labels)e.labels=copy(data.labels);if(data.descriptions)e.descriptions=copy(data.descriptions);if(data.datatype)e.datatype=data.datatype;
   for(const s of data.claims||[]){s.id=id+'$'+rev++;s.mainsnak.hash='server-generated';if(s.mainsnak.datavalue.type==='quantity'){s.mainsnak.datavalue.value.lowerBound=null;s.mainsnak.datavalue.value.upperBound=null;}for(const qs of Object.values(s.qualifiers||{}))for(const q of qs)q.hash='server-generated';(e.claims[s.mainsnak.property]??=[]).push(s);}
   e.lastrevid=rev++;result={entity:e,success:1};if(p.new&&failNextCreation){failNextCreation=false;throw Error('Simulated response lost after successful creation');}
  }else if(p.action==='edit'){
   if(p.baserevid)assert.equal(Number(p.baserevid),pages[p.title].rev);pages[p.title]={text:p.text,rev:rev++};result={edit:{result:'Success',newrevid:pages[p.title].rev}};
  }
  assert.ok(result,JSON.stringify(p));return{ok:true,json:async()=>copy(result)};
 };
 vm.createContext(context);vm.runInContext(source,context);
 return {db,pages,calls,context,fail(){failNextCreation=true;},run:()=>context.runEphemeraPoC(fullPlan,'unused')};
}
(async()=>{
 const h=harness();let j=await h.run();assert.deepEqual(Array.from(j.errors),[]);assert.equal(j.actions.filter(a=>a.action==='created').length,717);
 const postId=j.map['ephemerajpp.com:post:504130'];h.db[postId].labels.pt.value='Manual correction';h.db[postId].claims.P999=[{type:'statement',rank:'normal',mainsnak:{property:'P999',datavalue:{type:'string',value:'Manual metadata'}}}];
 const before=JSON.stringify(h.db);h.calls.length=0;j=await h.run();assert.deepEqual(Array.from(j.errors),[]);assert.equal(JSON.stringify(h.db),before,'A repeat must preserve ALL existing entity content');assert.equal(h.calls.filter(c=>c.action==='wbeditentity').length,0,'A repeat must issue no entity writes');
 vm.runInContext(fs.readFileSync(root+'/finish-source.js','utf8'),h.context);await h.context.finishEphemera(fullPlan);assert.equal(h.db[j.map.repertory].claims[j.map.has_part].length,696);assert.equal((h.pages['Project:Reportório da oposição — TablePress 77'].text.match(/\n\|-\n/g)||[]).length,696);h.calls.length=0;await h.context.finishEphemera(fullPlan);assert.equal(h.calls.filter(c=>c.action==='wbeditentity').length,0);
 const lost=harness();lost.fail();let interrupted=await lost.run();assert.equal(interrupted.errors.length,1);assert.equal(Object.keys(lost.db).length,16);const recovered=await lost.run();assert.equal(recovered.errors.length,0);assert.equal(Object.keys(lost.db).length,732,'Lost response must not create a duplicate on rescan');
 console.log('PASS: 717 creates; repeat makes zero entity writes; manual labels/claims preserved; uncertain successful POST recovered without duplication.');
})().catch(e=>{console.error(e);process.exitCode=1});
