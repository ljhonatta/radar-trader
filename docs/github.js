/* Radar Trader 2.0 no GitHub Pages: substitui o window.claude do artifact.
   - notícias, cotações e coleta: lidas de data/noticias.json e data/meta.json (gravados pelo GitHub Actions)
   - perfis: data/perfis.json + o que você mudar aqui (fica neste navegador)
   - carrosséis, referências e imagens: guardados neste navegador (localStorage + IndexedDB)
   - IA: OpenAI, com a chave que você coloca na aba Marca (fica só neste navegador) */
(function(){
const LS={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v);}catch(e){return d;}},
 set(k,v){try{localStorage.setItem(k,JSON.stringify(v));return true;}catch(e){return false;}}};
const REPO=(()=>{const h=location.hostname,p=location.pathname.split("/").filter(Boolean);
 return h.endsWith(".github.io")?`${h.split(".")[0]}/${p[0]||"radar-trader"}`:"ljhonatta/radar-trader";})();
window.RADAR_REPO=REPO;

/* ---------- imagens (IndexedDB, com cópia em memória para uso imediato) ---------- */
const IMG={};
const idb=new Promise(res=>{try{const r=indexedDB.open("radar-trader",1);r.onupgradeneeded=()=>r.result.createObjectStore("assets");
 r.onsuccess=()=>res(r.result);r.onerror=()=>res(null);}catch(e){res(null);}});
async function idbAll(){const d=await idb;if(!d)return;await new Promise(res=>{try{const tx=d.transaction("assets"),st=tx.objectStore("assets"),rq=st.openCursor();
 rq.onsuccess=()=>{const c=rq.result;if(c){IMG[c.key]=c.value;c.continue();}else res();};rq.onerror=()=>res();}catch(e){res();}});}
async function idbPut(k,v){const d=await idb;if(!d)throw {code:"quota"};await new Promise((res,rej)=>{const tx=d.transaction("assets","readwrite");tx.objectStore("assets").put(v,k);tx.oncomplete=res;tx.onerror=()=>rej({code:"quota"});});}
async function idbDel(k){const d=await idb;if(!d)return;const tx=d.transaction("assets","readwrite");tx.objectStore("assets").delete(k);}
const toDataURL=b=>new Promise(r=>{const fr=new FileReader();fr.onload=()=>r(fr.result);fr.readAsDataURL(b);});
const assets={
 async upload(blob){if(blob.size>20e6)throw {code:"too_large"};const id="a"+Date.now().toString(36)+Math.random().toString(36).slice(2,8);
  const url=await toDataURL(blob);await idbPut(id,url);IMG[id]=url;return {id};},
 async delete(id){delete IMG[id];await idbDel(id);}};
window.radarBlob=id=>{if(!id)return "";if(/^img\//.test(id))return "data/"+id;return IMG[id]||"data:image/gif;base64,R0lGODlhAQABAAAAACw=";};

/* ---------- banco ---------- */
const listeners={};
function emit(c){(listeners[c]||[]).forEach(f=>f());}
function on(c,f){(listeners[c]=listeners[c]||[]).push(f);f();}
let NOTICIAS=[],META={},PERFIS0={};
const local=name=>LS.get("rt-db-"+name,{});
function snapCol(name){
 if(name==="noticias")return NOTICIAS.map(n=>[n.id,n]);
 if(name==="perfis"){const m=local("perfis");const ids=new Set([...Object.keys(PERFIS0),...Object.keys(m)]);
  return [...ids].filter(id=>m[id]!==null).map(id=>[id,Object.assign({},PERFIS0[id],m[id])]);}
 return Object.entries(local(name)).filter(([,v])=>v);
}
function snapDoc(path){const [c,id]=path.split("/");
 if(c==="meta")return META[id]||null;
 const r=snapCol(c).find(x=>x[0]===id);return r?r[1]:null;}
function salvar(c,id,data){const all=local(c);all[id]=data;if(!LS.set("rt-db-"+c,all))throw {code:"quota_exceeded"};emit(c);}
function docRef(path){const [c,id]=path.split("/");
 return {id,
  onSnapshot(cb){on(c==="meta"?"meta":c,()=>{const d=snapDoc(path);cb({exists:!!d,data:()=>d});});return ()=>{};},
  async set(data){salvar(c,id,data);},
  async update(data){salvar(c,id,Object.assign({},snapDoc(path)||{},data));},
  async delete(){const all=local(c);if(c==="perfis"&&PERFIS0[id])all[id]=null;else delete all[id];LS.set("rt-db-"+c,all);emit(c);}};}
function query(name){let ord=null,lim=1e9;
 const q={orderBy(f,dir){ord=[f,dir];return q;},limit(n){lim=n;return q;},
  doc(id){return docRef(name+"/"+(id||(Date.now().toString(36)+Math.random().toString(36).slice(2,8))));},
  async add(data){const r=q.doc();await r.set(data);return r;},
  onSnapshot(cb){on(name,()=>{let rows=snapCol(name);
   if(ord)rows=rows.slice().sort((a,b)=>{const x=String(a[1][ord[0]]||""),y=String(b[1][ord[0]]||"");return ord[1]==="desc"?y.localeCompare(x):x.localeCompare(y);});
   cb({docs:rows.slice(0,lim).map(([id,d])=>({id,data:()=>d}))});});return ()=>{};}};
 return q;}
const db={collection:query,doc:docRef};

async function carregar(){
 try{const t="?t="+Date.now();
  const [n,m]=await Promise.all([fetch("data/noticias.json"+t).then(r=>r.json()),fetch("data/meta.json"+t).then(r=>r.json())]);
  NOTICIAS=(Array.isArray(n)?n:[]).filter(x=>x&&x.id);META=m||{};window.RADAR_META=META;emit("noticias");emit("meta");
 }catch(e){const s=document.getElementById("dbstatus");if(s){s.textContent="Não consegui ler as notícias agora. Recarregue a página.";s.className="status err";}}}
const pronto=Promise.all([fetch("data/perfis.json").then(r=>r.json()).then(p=>{PERFIS0=p||{};}).catch(()=>{}),idbAll(),carregar()]);
setInterval(carregar,10*60e3);
document.addEventListener("visibilitychange",()=>{if(!document.hidden)carregar();});

/* ---------- downloads ---------- */
const downloads={async save({filename,data}){const u=URL.createObjectURL(data);const a=document.createElement("a");a.href=u;a.download=filename;
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),60e3);}};

/* ---------- IA (OpenAI) ---------- */
const KEY="rt-openai-key";
window.radarKey={get:()=>{try{return localStorage.getItem(KEY)||"";}catch(e){return "";}},set:v=>{try{v?localStorage.setItem(KEY,v):localStorage.removeItem(KEY);return true;}catch(e){return false;}}};
window.radarModelo={get:()=>LS.get("rt-modelo","")||"gpt-4o-mini",set:v=>LS.set("rt-modelo",v||"")};
const sample={
 async limits(){return {images:{maxCount:4}};},
 async json(prompt,opts={}){
  const key=window.radarKey.get();if(!key)throw {code:"no_key"};
  let content=prompt;
  if(opts.images&&opts.images.length){content=[{type:"text",text:prompt}];for(const f of opts.images)content.push({type:"image_url",image_url:{url:await toDataURL(f)}});}
  let r;
  try{r=await fetch("https://api.openai.com/v1/chat/completions",{method:"POST",signal:opts.signal,
   headers:{"Authorization":"Bearer "+key,"Content-Type":"application/json"},
   body:JSON.stringify({model:window.radarModelo.get(),response_format:{type:"json_object"},messages:[{role:"system",content:"Responda sempre em JSON válido."},{role:"user",content}]})});}
  catch(e){if(e&&e.name==="AbortError")throw {code:"cancelled"};throw {code:"network"};}
  if(r.status===401)throw {code:"bad_key"};
  if(r.status===429)throw {code:"rate_limited"};
  if(!r.ok)throw {code:"http_"+r.status};
  const j=await r.json();try{return JSON.parse(j.choices[0].message.content);}catch(e){throw {code:"invalid_json"};}}};

/* ---------- "Atualizar agora" abre o workflow no GitHub ---------- */
const mcp={async callTool(){window.open(`https://github.com/${REPO}/actions/workflows/coleta.yml`,"_blank","noopener");}};

const caps={db,sample,downloads,assets,mcp};
window.claude={use:async x=>{await pronto;if(!(x in caps))throw {code:"not_declared"};return caps[x];}};
})();
