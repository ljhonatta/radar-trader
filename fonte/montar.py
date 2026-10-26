"""Monta docs/index.html a partir do HTML do painel original (fonte/original.html) com as melhorias da 2.0.
Rode: python3 fonte/montar.py   (só precisa quando mexer no original ou nas trocas abaixo)."""
import os, re

AQUI = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(AQUI, "original.html"), encoding="utf-8").read()
ICONES = open(os.path.join(AQUI, "icones.js"), encoding="utf-8").read()


def troca(velho, novo, n=1):
    global s
    c = s.count(velho)
    assert c == n, f"esperava {n}x, achei {c}x: {velho[:90]!r}"
    s = s.replace(velho, novo)


# ---------- cabeçalho e textos ----------
troca('<!doctype html><html><head><meta charset=utf8>', '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><link rel="icon" type="image/png" sizes="32x32" href="data/img/icone-32.png"><link rel="apple-touch-icon" href="data/img/icone-180.png"><link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#0c1019"><meta name="description" content="Notícias do mercado financeiro coletadas 3 vezes por dia com IA, prontas para virar carrossel."><meta property="og:title" content="Radar Trader"><meta property="og:description" content="Notícias do mercado financeiro com IA, prontas para virar carrossel."><meta property="og:image" content="https://ljhonatta.github.io/radar-trader/data/img/og.jpg"><meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image">')
troca('<title>Radar Trader Fontes</title>', '<title>Radar Trader 2.0</title>')
troca('<span class="eyebrow">Vision Prime · Fábrica de conteúdo financeiro</span>\n      <h1>Radar Trader Fontes</h1>',
      '<span class="eyebrow">Fábrica de conteúdo financeiro · versão 2.0</span>\n      <h1>Radar Trader</h1>')
troca('trazem a fonte de cada notícia.</footer>', 'trazem a fonte de cada notícia. Coleta automática pelo GitHub com IA da OpenAI.</footer>')
troca('<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>',
      '<script src="github.js"></script>\n<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>')
troca('No app do Claude no iPhone ou Android, cada imagem abre a tela de compartilhar ou salvar do celular: escolha <b>Salvar imagem</b> para ir para a galeria.',
      'No celular, abre a tela de compartilhar com todas as imagens juntas: escolha <b>Salvar imagens</b> para ir para a galeria.')

# ---------- capa (imagem gerada com IA) ----------
troca('  <div class="top">', '  <div class="top hero">')
troca('.top{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;justify-content:space-between}',
      '.top{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;justify-content:space-between}\n'
      '.hero{min-height:clamp(150px,22vw,230px);padding:22px clamp(16px,3vw,28px);border-radius:16px;overflow:hidden;color:#fff;'
      'background:linear-gradient(90deg,#05070c 0%,rgba(5,7,12,.85) 32%,rgba(5,7,12,.1) 70%),url(data/img/capa.jpg) right center/cover no-repeat #05070c;'
      'box-shadow:0 18px 40px -24px rgba(0,0,0,.6)}\n'
      '.hero h1{font-size:clamp(28px,4.4vw,44px);color:#fff}\n'
      '.hero .eyebrow{color:#ff8a33}\n'
      '.hero .status{color:#c9cfdc;background:rgba(5,7,12,.55);padding:4px 10px;border-radius:999px}')

# ---------- CSS novo ----------
CSS = r'''
/* ===== 2.0: placar em faixa, busca, ficha completa, antes×depois, passos, faixa de cotações e ícones 3D ===== */
.score{display:flex;overflow-x:auto;scrollbar-width:thin}
.score>div{flex:1 0 auto;min-width:128px}
.filters input[type=text]{width:auto;min-width:200px;flex:1 1 200px}
.nchips{display:flex;flex-wrap:wrap;gap:6px}
.nchip{font-size:12px;border:1px solid var(--line);background:var(--raise);border-radius:7px;padding:3px 8px;color:var(--muted)}
.nchip b{font-family:var(--f-mono);color:var(--ink)}
details.ficha{border-top:1px dashed var(--line);padding-top:8px}
details.ficha summary{cursor:pointer;font-weight:600;font-size:13px;color:var(--accent)}
details.ficha .gch{font-family:var(--f-display);font-weight:700;margin-top:10px}
details.ficha .gch em{font-style:normal;color:var(--accent)}
details.ficha .fb{display:flex;flex-direction:column;gap:3px;margin-top:10px;font-size:13.5px}
details.ficha ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:3px}
details.ficha .cmpt{border-collapse:collapse;font-size:13px}
details.ficha .cmpt td{padding:3px 10px 3px 0;border-bottom:1px solid var(--line)}
.ai-row input{flex:1;min-width:200px;width:auto}
@media (max-width:720px){.nav{width:28px;height:28px;font-size:16px;background:rgba(0,0,0,.35)}.nav.l{left:4px}.nav.r{right:4px}}
.sl .tick{display:flex;gap:calc(30px * var(--k));overflow:hidden;white-space:nowrap;flex:none;margin:calc(-18px * var(--k)) calc(-1 * var(--sx)) 0;padding:calc(12px * var(--k)) var(--sx);background:var(--s-hi);border-top:1px solid var(--s-line2);border-bottom:1px solid var(--s-line2);font-family:"JetBrains Mono",monospace;font-size:calc(22px * var(--k));color:var(--s-txt)}
.sl .tick b{color:var(--s-a);font-weight:600}
.sl .tick i{font-style:normal}.sl .tick i.up{color:#2fcf7a}.sl .tick i.dn{color:#ff5b5b}
.sl .ico3d{margin-left:auto;flex:none;display:block}
.sl .ico3d svg{width:100%;height:100%;display:block}
.sl .cmp{border:1px solid var(--s-line2);border-radius:22px;overflow:hidden;flex:none;background:var(--s-soft)}
.sl .cmp>div{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:16px;padding:calc(20px * var(--k) * var(--t)) calc(28px * var(--k));align-items:center;border-bottom:1px solid var(--s-line)}
.sl .cmp>div:last-child{border-bottom:0}
.sl .cmp .ch{font-family:"JetBrains Mono",monospace;font-size:calc(22px * var(--k));letter-spacing:.12em;text-transform:uppercase;color:var(--s-sub);background:var(--s-hi)}
.sl .cmp .cr span:first-child{font-weight:600;font-size:calc(32px * var(--k) * var(--t));color:var(--s-txt);line-height:1.2}
.sl .cmp .cr span:nth-child(2){font-size:calc(38px * var(--k) * var(--t));color:var(--s-sub)}
.sl .cmp .cr b{font-family:var(--fh);font-weight:var(--fw);font-size:calc(46px * var(--k) * var(--t));color:var(--s-a2);line-height:1.1}
.sl .pss{display:flex;flex-direction:column;gap:calc(22px * var(--k) * var(--t));flex:none}
.sl .ps{display:flex;gap:calc(26px * var(--k));align-items:flex-start;background:var(--s-soft);border:1px solid var(--s-line2);border-radius:22px;padding:calc(22px * var(--k) * var(--t)) calc(26px * var(--k))}
.sl .ps .pn{flex:none;width:calc(72px * var(--k));height:calc(72px * var(--k));border-radius:50%;background:var(--s-a);color:var(--s-on);display:grid;place-items:center;font-family:var(--fh);font-weight:var(--fw);font-size:calc(38px * var(--k))}
.sl .ps>div{display:flex;flex-direction:column;gap:6px;min-width:0}
.sl .ps b{font-size:calc(38px * var(--k) * var(--t));color:var(--s-txt);line-height:1.15}
.sl .ps>div span{font-size:calc(30px * var(--k) * var(--t));color:var(--s-sub);line-height:1.35}
.sl .ps>div span.so{font-size:calc(34px * var(--k) * var(--t));color:var(--s-txt)}
</style>'''
troca('.sl .guide .crop{position:absolute;top:0;bottom:0;border-left:4px solid rgba(255,230,60,.9);border-right:4px solid rgba(255,230,60,.9)}\n</style>',
      '.sl .guide .crop{position:absolute;top:0;bottom:0;border-left:4px solid rgba(255,230,60,.9);border-right:4px solid rgba(255,230,60,.9)}' + CSS)

# ---------- HTML: busca e painel da OpenAI ----------
troca('<option value="7d">Últimos 7 dias</option></select>',
      '<option value="7d">Últimos 7 dias</option></select>\n      <input type="text" id="fBusca" placeholder="Buscar notícia, empresa, tema…" aria-label="Buscar">')
troca('''    <div class="panel">
      <h2>Referências de publicações anteriores''', '''    <div class="panel">
      <h2>Inteligência artificial (OpenAI)</h2>
      <p class="note">Usada para reescrever o carrossel e a legenda, regenerar slides e ler as imagens que você envia. A chave fica guardada só neste navegador, nunca vai para o GitHub. Em outro celular ou computador, coloque de novo. Sem chave, o carrossel é montado com os dados da ficha da notícia.</p>
      <div class="row ai-row"><input type="password" id="aiKey" autocomplete="off" placeholder="sk-..."><button class="btn primary" id="aiSalvar">Salvar chave</button><button class="btn ghost" id="aiRemover">Remover</button></div>
      <div class="row ai-row"><label class="lbl" for="aiModelo">Modelo</label><input type="text" id="aiModelo" placeholder="gpt-4o-mini"><button class="btn sm" id="aiModeloSalvar">Salvar modelo</button></div>
      <span class="status" id="aiStatus"></span>
      <p class="note">Perfis, carrosséis e imagens que você mudar aqui ficam neste navegador. A coleta de notícias usa a chave guardada no GitHub (Settings → Secrets).</p>
    </div>
    <div class="panel">
      <h2>Referências de publicações anteriores''')

# ---------- constantes ----------
troca('''  conclusao:{nome:"Conclusão"''', '''  comparativo:{nome:"Antes × depois",arq:"antes-depois",ia:"tabela antes × depois em 'linhas' [{item, antes, depois}] (2 a 4 linhas, só valores do material; se o material não trouxer valor anterior e novo, deixe 'linhas' vazio e use 'numeros' com 2 a 3 números e titulo 'Em números'); titulo até 6 palavras; texto vazio; natureza fato"},
  detalhes:{nome:"Os detalhes",arq:"detalhes",ia:"3 a 4 detalhes concretos da notícia em 'passos' [{t: vazio, d: até 22 palavras com número, nome ou data}] (quem, quanto, quando, como); titulo até 6 palavras; texto vazio; natureza fato"},
  declaracoes:{nome:"O que disseram",arq:"declaracoes",ia:"até 3 declarações da notícia em 'passos' [{t: nome e cargo de quem falou, d: paráfrase até 25 palavras}], só quem está no material; titulo até 6 palavras; texto vazio; natureza fato"},
  cronologia:{nome:"Linha do tempo",arq:"linha-do-tempo",ia:"2 a 4 marcos em ordem em 'passos' [{t: data ou momento, d: o que aconteceu até 15 palavras}], só do material; titulo até 6 palavras; texto vazio; natureza fato"},
  passos:{nome:"Passo a passo",arq:"passos",ia:"3 passos educativos em 'passos' [{t: até 4 palavras, d: até 14 palavras}] sobre como quem opera ou investe pode acompanhar esse tipo de notícia com método (sem recomendar compra ou venda, sem prometer ganho); titulo até 7 palavras com 1 palavra entre *asteriscos*; texto vazio; natureza contexto"},
  conclusao:{nome:"Conclusão"''')
troca('''  8:["capa","aconteceu","numeros","importa","impacto","contexto","cenarios","conclusao"]
};''', '''  8:["capa","aconteceu","numeros","importa","impacto","contexto","cenarios","conclusao"],
  9:["capa","aconteceu","numeros","comparativo","importa","impacto","contexto","cenarios","conclusao"],
  10:["capa","aconteceu","numeros","comparativo","importa","impacto","contexto","cenarios","passos","conclusao"]
};''')
a = s.index("const FONTES=[")
b = s.index("];\nconst EDU", a)
s = s[:a] + '''const FONTES=[
 ["Money Times","https://www.moneytimes.com.br/mercados/","Feed RSS"],
 ["Bora Investir (B3)","https://borainvestir.b3.com.br/","Feed RSS, fonte oficial da bolsa"],
 ["InfoMoney","https://www.infomoney.com.br/","Feed RSS"],
 ["Exame","https://exame.com/invest/","Feed RSS (mercado e negócios)"],
 ["Bloomberg Línea","https://www.bloomberglinea.com.br/","Feed RSS"],
 ["Agência Brasil Economia","https://agenciabrasil.ebc.com.br/economia","Feed RSS oficial"],
 ["BP Money","https://bpmoney.com.br/","Feed RSS"],
 ["Acionista","https://acionista.com.br/","Feed RSS"],
 ["Seu Dinheiro","https://www.seudinheiro.com/","Feed RSS com filtro de ruído"],
 ["Valor, Folha, G1, Reuters, CNN, Estadão","https://news.google.com/","Pelo Google Notícias (sites que bloqueiam leitura direta)"],
 ["Banco Central · Copom e Focus","https://www.bcb.gov.br/","Buscas do dia + Selic oficial (API do BC)"],
 ["IBGE · IPCA","https://www.ibge.gov.br/","IPCA 12 meses (API do Banco Central)"],
 ["Polymarket","https://polymarket.com/","Sinais de expectativa: juros, inflação, cripto"],
 ["Cotações","https://www.google.com/finance/","Yahoo Finance, Google Finance e AwesomeAPI"]
''' + s[b:]

# ---------- util ----------
troca('const blobSrc=id=>id?"/_blob/"+id:"";', 'const blobSrc=id=>id?window.radarBlob(id):"";\nconst temIA=()=>!!(sample&&window.radarKey?.get());')
troca('let filt={assunto:"",rel:"all",data:"48h"};', 'let filt={assunto:"",rel:"all",data:"48h",q:""};')

# ---------- notícias ----------
troca('coleta automática todo dia às 6h45, 12h45 e 18h45, inclusive fim de semana',
      'coleta automática pelo GitHub todo dia às 6h45, 12h45 e 18h45 (pode atrasar alguns minutos)')
a = s.index("function renderScore(){")
b = s.index("function newsFiltered(){", a)
s = s[:a] + r'''function renderScore(){
  const pl=PLACAR||{};const cls=v=>String(v||"").trim().startsWith("-")?"dn":"up";
  const it=Array.isArray(pl.itens)&&pl.itens.length?pl.itens:[{k:"IBOV",nome:"Ibovespa",v:pl.ibov,var:pl.ibovVar},{k:"USD",nome:"Dólar",v:pl.dolar,var:pl.dolarVar},{k:"BTC",nome:"Bitcoin",v:pl.btc,var:""}];
  $("score").innerHTML=it.map(x=>`<div><div class="k">${esc(x.nome||x.k)}</div><div class="v">${esc(x.v||"—")} ${x.var?`<span class="${cls(x.var)}" style="font-size:13px">${esc(x.var)}</span>`:""}</div></div>`).join("")
    +`<div><div class="k">${esc(pl.obs||"Cotações")}</div><div class="v" style="font-size:14px;font-weight:600">${esc(pl.hora||"")}</div></div>`;
}
function fichaHTML(n){
  const bl=(t,v)=>v?`<div class="fb"><span class="lbl">${t}</span><div>${v}</div></div>`:"";
  const L=a=>Array.isArray(a)&&a.length?`<ul>${a.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`:"";
  const corpo=bl("Fatos",L(n.fatos))
    +bl("Antes × depois",Array.isArray(n.comparativo)&&n.comparativo.length?`<table class="cmpt">${n.comparativo.map(r=>`<tr><td>${esc(r.item)}</td><td>${esc(r.antes)}</td><td>→ <b>${esc(r.depois)}</b></td></tr>`).join("")}</table>`:"")
    +bl("Explicação",(n.explicacao||[]).map(x=>`<p style="margin:0 0 6px">${esc(x)}</p>`).join(""))
    +bl("Detalhes",L(n.detalhes))
    +bl("O que disseram",(n.declaracoes||[]).length?`<ul>${n.declaracoes.map(x=>`<li><b>${esc(x.quem)}:</b> ${esc(x.oque)}</li>`).join("")}</ul>`:"")
    +bl("Linha do tempo",(n.cronologia||[]).length?`<ul>${n.cronologia.map(x=>`<li><b>${esc(x.quando)}:</b> ${esc(x.oque)}</li>`).join("")}</ul>`:"")
    +bl("Glossário",(n.glossario||[]).length?`<ul>${n.glossario.map(x=>`<li><b>${esc(x.termo)}:</b> ${esc(x.significado)}</li>`).join("")}</ul>`:"")
    +bl("Pergunta para os comentários",esc(n.pergunta||""))
    +bl("Por que importa",esc(n.porQueImporta||""))+bl("Impacto no mercado",esc(n.impactoMercado||""))+bl("Entenda",esc(n.entenda||""))
    +bl("O que observar",esc(n.observar||""))+bl("Ângulo para o perfil",esc(n.angulo||""))+bl("Ideias de post",L(n.ideias))
    +bl("Para quem e formato",esc([...(n.publico||[]),...(n.formatos||[])].join(" · ")));
  if(!corpo)return "";
  return `<details class="ficha"><summary>Ficha completa da pauta</summary>${n.gancho?`<div class="gch">Gancho: ${emph(n.gancho)}</div>`:""}${corpo}</details>`;
}
''' + s[b:]
troca('    if(filt.assunto&&n.categoria!==filt.assunto)return false;',
      '    if(filt.assunto&&n.categoria!==filt.assunto)return false;\n    if(filt.q&&!(n.titulo+" "+n.resumo+" "+(n.fatos||[]).join(" ")+" "+n.fonte+" "+n.categoria).toLowerCase().includes(filt.q))return false;')
troca('''    <div class="meta">${esc(n.fonte)} · ${esc(fmtDT(nTime(n)))}''',
      '''    ${n.tipo!=="sinal"&&Array.isArray(n.numeros)&&n.numeros.length?`<div class="nchips">${n.numeros.slice(0,3).map(x=>`<span class="nchip"><b>${esc(x.valor)}</b> ${esc(x.rotulo)}</span>`).join("")}</div>`:""}
    ${fichaHTML(n)}
    <div class="meta">${esc(n.fonte)} · ${esc(fmtDT(nTime(n)))}''')
troca('setStatus("manualStatus","Coleta iniciada. As notícias aparecem aqui sozinhas em alguns minutos.","ok");',
      'setStatus("manualStatus","Abri o GitHub: toque em Run workflow → Run workflow. Em 3 a 6 minutos as notícias aparecem aqui (recarregue a página).","ok");')
troca('setTimeout(()=>{b.disabled=false},180000);', 'setTimeout(()=>{b.disabled=false},5000);')

# ---------- ícones 3D, antes×depois, passos ----------
troca('const hand=()=>', ICONES + r'''
function shade(h,f){const n=parseInt(h.slice(1),16);const c=[n>>16,(n>>8)&255,n&255].map(v=>Math.max(0,Math.min(255,Math.round(f<0?v*(1+f):v+(255-v)*f))));return "#"+c.map(v=>v.toString(16).padStart(2,"0")).join("");}
function icon3d(name,p){const I=ICONES[name]||ICONES.grafico;const l=p.a2,m=p.a,dk=shade(p.a,-.5);const u=Math.random().toString(36).slice(2,8);
 const tk=(x,c)=>x.replace(/#X#/g,c).replace(/#F#/g,`url(#f${u})`).replace(/#D#/g,dk).replace(/#L#/g,l).replace(/#W#/g,"#ffffff");
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 0 220 210"><defs><linearGradient id="f${u}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${l}"/><stop offset=".55" stop-color="${m}"/><stop offset="1" stop-color="${dk}"/></linearGradient></defs><ellipse cx="104" cy="196" rx="76" ry="9" fill="#000" opacity=".25"/><g transform="translate(7 9)">${tk(I.b,dk)}</g>${tk(I.b,`url(#f${u})`)}${tk(I.t,dk)}</svg>`;}
const ICO_MAP={grafico:"grafico",seta:"grafico",queda:"queda",moeda:"dinheiro",raio:"alerta",escudo:"escudo",alvo:"alvo",foguete:"foguete",globo:"lupa",relogio:"relogio",cadeado:"escudo"};
function icoDe(d,s){const P={numeros:"grafico",importa:"alvo",impacto:/^-|queda|▼/i.test(d.noticia?.destaque||"")?"queda":"grafico",contexto:"lupa",cenarios:"relogio",comparativo:"calendario",passos:"foguete"};return P[s.papel]||ICO_MAP[d.noticia?.icone]||"grafico";}
function cmpHTML(rows){return `<div class="cmp"><div class="ch"><span></span><span>Antes</span><span>Depois</span></div>${rows.slice(0,4).map(r=>`<div class="cr"><span>${esc(r.item)}</span><span>${esc(r.antes)}</span><b>${esc(r.depois)}</b></div>`).join("")}</div>`;}
function passosHTML(list){return `<div class="pss">${list.slice(0,4).map((p,j)=>`<div class="ps"><span class="pn">${j+1}</span><div>${p.t?`<b>${esc(p.t)}</b>`:""}${p.d?`<span${p.t?"":` class="so"`}>${esc(p.d)}</span>`:""}</div></div>`).join("")}</div>`;}
const LISTA=new Set(["passos","detalhes","declaracoes","cronologia"]);
function planoDe(d,n){const nw=d?.noticia||{};
  const tem={detalhes:(nw.detalhes||[]).length>=2,numeros:!nw.numeros||(nw.numeros||[]).length>=2,comparativo:(nw.comparativo||[]).length>0,
    declaracoes:(nw.declaracoes||[]).length>0,cronologia:(nw.cronologia||[]).length>=2};
  const prio=["aconteceu","detalhes","importa","numeros","impacto","declaracoes","comparativo","contexto","cronologia","cenarios","passos"].filter(p=>tem[p]!==false);
  const ORD=["aconteceu","detalhes","numeros","comparativo","cronologia","declaracoes","importa","impacto","contexto","cenarios","passos"];
  const mid=prio.slice(0,Math.max(1,n-2));return ["capa",...ORD.filter(p=>mid.includes(p)),"conclusao"];}
function proximoEstilo(){const ks=Object.keys(KITS);const i=((prefs.kitN??-1)+1)%ks.length;prefs.kitN=i;savePrefs();
  const K=KITS[ks[i]];const e=estiloDe({estilo:prefs.estilo||{}});const o={...e,...K,el:{...e.el,...(K.el||{})}};delete o.nome;delete o.d;return o;}
function tickHTML(d){const it=(d.placar||[]).slice(0,6);if(!it.length)return "";
  return `<div class="tick">${it.map(x=>{const neg=String(x.var||"").trim().startsWith("-");return `<span><b>${esc(x.k)}</b> ${esc(x.v)}${x.var?` <i class="${neg?"dn":"up"}">${neg?"▼":"▲"} ${esc(String(x.var).replace(/^[+-]/,""))}</i>`:""}</span>`}).join("")}</div>`;}
const hand=()=>''')

# capa manchete sem foto: ícone 3D grande no lugar do gráfico
troca('''  return {bg:(src?`<div class="photo" style="inset:0;${bgStyle(im,s.img,t.w,t.h)}"></div><div class="fade"></div>`:(es.el.deco?deco(p):""))''',
      '''  return {bg:(src?`<div class="photo" style="inset:0;${bgStyle(im,s.img,t.w,t.h)}"></div><div class="fade"></div>`:(es.el.icone?`<div style="position:absolute;right:${t.sx}px;top:${Math.round(t.h*.15)}px;width:${Math.round(420*k)}px;height:${Math.round(400*k)}px">${icon3d(icoDe(d,{papel:"aconteceu"}),p)}</div>`:es.el.deco?deco(p):""))''')

troca('''  const lr=`<div class="lr"><span class="nat ${s.natureza||"fato"}">${NAT[s.natureza||"fato"]||"FATO"}</span><span class="rot">${esc(s.rotulo||PAPEIS[s.papel]?.nome||"")}</span></div>`;''',
      '''  const lr=`<div class="lr"><span class="nat ${s.natureza||"fato"}">${NAT[s.natureza||"fato"]||"FATO"}</span><span class="rot">${esc(s.rotulo||PAPEIS[s.papel]?.nome||"")}</span>${es.el.icone?`<span class="ico3d" style="width:${Math.round(124*k)}px;height:${Math.round(118*k)}px">${icon3d(icoDe(d,s),p)}</span>`:""}</div>`;
  const tick=es.el.ticker&&!last?tickHTML(d):"";''')
troca('    const tx0=s.texto?`<div class="txt">${esc(s.texto)}</div>`:"";\n    const txt=isN?nums+tx0:tx0;',
      '    const tx0=s.texto?`<div class="txt">${esc(s.texto)}</div>`:"";\n    const extra=s.papel==="comparativo"&&s.linhas?.length?cmpHTML(s.linhas):LISTA.has(s.papel)&&s.passos?.length?passosHTML(s.passos):"";\n    const txt=(isN?nums+tx0:tx0)+extra;')
troca('''${s.texto?`<div class="txt qtxt">${esc(s.texto)}</div>`:""}${numsB}''', '''${s.texto?`<div class="txt qtxt">${esc(s.texto)}</div>`:""}${numsB}${extra}''')
troca('<div class="frame">${s.papel==="marca"?"":hd}', '<div class="frame">${s.papel==="marca"?"":tick+hd}')

# ---------- estilos e modelos ----------
troca('el:{linhas:true,deco:true,segs:true,radar:true,selo:true,fonte:true}};',
      'el:{linhas:true,deco:true,segs:true,radar:true,selo:true,fonte:true,ticker:false,icone:false}};')
a = s.index("const KITS={")
b = s.index("\n};", a)
kits = s[a:b]
kits = kits.replace('caixa:"normal"}', 'caixa:"normal",el:{ticker:false,icone:false}}').replace('caixa:"alta"}', 'caixa:"alta",el:{ticker:false,icone:false}}')
kits = kits.replace('const KITS={', '''const KITS={
  terminal:{nome:"Terminal",d:"Faixa de cotações, número gigante, ícones 3D",capa:"numero",conteudo:"card",fecho:"card",marcaLay:"logo",fonte:"tech",alinhar:"esq",caixa:"normal",el:{ticker:true,icone:true}},
  painel:{nome:"Painel 3D",d:"Ícones 3D grandes, títulos fortes",capa:"manchete",conteudo:"titulo",fecho:"minimal",marcaLay:"bloco",fonte:"moderno",alinhar:"esq",caixa:"normal",el:{ticker:false,icone:true}},''')
s = s[:a] + kits + s[b:]
troca('const d2={...deck,estilo:{...e,...v,marcaLay:e.marcaLay==="off"?"off":v.marcaLay}};',
      'const d2={...deck,estilo:{...e,...v,el:{...e.el,...(v.el||{})},marcaLay:e.marcaLay==="off"?"off":v.marcaLay}};')
troca('setEstilo(e=>{const off=e.marcaLay==="off";Object.assign(e,K);',
      'setEstilo(e=>{const off=e.marcaLay==="off";const el={...e.el,...(K.el||{})};Object.assign(e,K);e.el=el;')
troca('const EL={linhas:"Linhas de fundo",', 'const EL={ticker:"Faixa de cotações",icone:"Ícones 3D",linhas:"Linhas de fundo",')
troca('$("segN").innerHTML=[3,4,5,6,7,8].map(', '$("segN").innerHTML=[3,4,5,6,7,8,9,10].map(')

# ---------- planos de slides montados conforme o que a notícia tem ----------
troca('function localSlides(d,n){return withMarca(d,PLANOS[n].map(','function localSlides(d,n){return withMarca(d,planoDe(d,n).map(')
troca('  const plano=PLANOS[n],f=FORMATOS[d.formato];','  const plano=planoDe(d,n),f=FORMATOS[d.formato];')
troca('    const plano=PLANOS[n];if(!r||','    const plano=planoDe(deck,n);if(!r||')
troca('  return withMarca(deck,PLANOS[n].map(','  return withMarca(deck,planoDe(deck,n).map(')
troca('const nConteudo=d=>conteudo(d).length;','const nConteudo=d=>{const c=conteudo(d).length;return c>=3&&c<=10?c:prefs.n;};')
troca('texto até 40 palavras','texto de 35 a 55 palavras com dados concretos da notícia (nomes, números, datas, causas)',4)
troca('texto até 42 palavras','texto de 35 a 55 palavras',1)
# cada carrossel novo usa um modelo diferente
troca('estilo:JSON.parse(JSON.stringify(brandOf(prefs.handle).estilo||prefs.estilo||ESTILO0))','estilo:proximoEstilo()')
troca('  showTab("editor");renderEditor();gerar();','  showTab("editor");renderEditor();gerar().then(()=>{const k=kitDe(estiloDe(deck));if(k&&!$("genStatus").classList.contains("err"))setStatus("genStatus",$("genStatus").textContent+` Modelo: ${KITS[k].nome} (cada carrossel novo vem num modelo diferente; troque acima se quiser).`,"ok");});')

# ---------- carrossel com os dados da ficha ----------
troca('gancho:news.gancho||""},',
      'gancho:news.gancho||"",numeros:news.numeros||[],comparativo:news.comparativo||[],porQueImporta:news.porQueImporta||"",impactoMercado:news.impactoMercado||"",entenda:news.entenda||"",observar:news.observar||"",angulo:news.angulo||"",ideias:news.ideias||[],icone:news.icone||"",explicacao:news.explicacao||[],detalhes:news.detalhes||[],declaracoes:news.declaracoes||[],cronologia:news.cronologia||[],glossario:news.glossario||[],pergunta:news.pergunta||""},')
troca('criadoEm:new Date().toISOString()};\n}\nfunction criar', 'criadoEm:new Date().toISOString(),placar:(PLACAR?.itens||[]).slice(0,8)};\n}\nfunction criar')
troca('  const nums=f.map(x=>{', '  const nums=nw.numeros?.length?nw.numeros.map(x=>({valor:x.valor,rotulo:x.rotulo})):f.map(x=>{')
troca('titulo:"Por que isso importa",texto:"Notícias assim', 'titulo:"Por que isso importa",texto:nw.porQueImporta||"Notícias assim')
troca('titulo:"O que muda para o investidor",texto:"Movimentos', 'titulo:"O que muda para o investidor",texto:nw.impactoMercado||"Movimentos')
troca('texto:EDU[nw.categoria]||EDU._', 'texto:nw.entenda||EDU[nw.categoria]||EDU._')
troca('titulo:"O que observar a seguir",texto:"Os próximos', 'titulo:"O que observar a seguir",texto:nw.observar||"Os próximos')
troca('    default:{const r=String(nw.resumo', '''    case "detalhes":return {...base,titulo:"Os *detalhes*",passos:(nw.detalhes||[]).slice(0,4).map(x=>({t:"",d:x}))};
    case "declaracoes":return {...base,titulo:"O que *disseram*",passos:(nw.declaracoes||[]).slice(0,3).map(x=>({t:x.quem,d:x.oque}))};
    case "cronologia":return {...base,titulo:"Linha do *tempo*",passos:(nw.cronologia||[]).slice(0,4).map(x=>({t:x.quando,d:x.oque}))};
    case "comparativo":return {...base,titulo:nw.comparativo?.length?"Antes *×* depois":"Em números",rotulo:nw.comparativo?.length?"":"Em números",linhas:(nw.comparativo||[]).slice(0,4),numeros:nw.comparativo?.length?[]:nums.slice(0,3)};
    case "passos":return {...base,natureza:"contexto",titulo:"Como acompanhar *com método*",passos:[{t:"Entenda o fato",d:"Leia a notícia na fonte e separe fato de opinião."},{t:"Veja o contexto",d:"Compare com juros, dólar e o humor do mercado no dia."},{t:"Tenha um plano",d:"Defina o risco antes de agir. Impulso não é estratégia."}],fonte:""};
    default:{const r=String(nw.resumo''')
troca('${nw.resumo}\\n\\n${(nw.fatos||[]).slice(0,3)', '${nw.resumo}\\n\\n${nw.porQueImporta?"Por que importa: "+nw.porQueImporta+"\\n\\n":""}${(nw.fatos||[]).slice(0,3)')
troca('categoria:nw.categoria,...(nw.tipo', 'categoria:nw.categoria,explicacao:nw.explicacao,detalhes:nw.detalhes,declaracoes:nw.declaracoes,cronologia:nw.cronologia,glossario:nw.glossario,numeros:nw.numeros,comparativo:nw.comparativo,porQueImporta:nw.porQueImporta,impactoMercado:nw.impactoMercado,entenda:nw.entenda,observar:nw.observar,angulo:nw.angulo,pergunta:nw.pergunta,...(nw.tipo')
troca('"numeros":[{"valor":"...","rotulo":"..."}],"fonte":"..."}],"legenda"', '"numeros":[{"valor":"...","rotulo":"..."}],"linhas":[{"item":"...","antes":"...","depois":"..."}],"passos":[{"t":"...","d":"..."}],"fonte":"..."}],"legenda"')
troca('"numeros":[{"valor":"...","rotulo":"..."}],"fonte":"..."}`,{signal', '"numeros":[{"valor":"...","rotulo":"..."}],"linhas":[{"item":"...","antes":"...","depois":"..."}],"passos":[{"t":"...","d":"..."}],"fonte":"..."}`,{signal')
troca('fonte:String(x?.fonte||"")};', 'fonte:String(x?.fonte||""),linhas:Array.isArray(x?.linhas)?x.linhas.filter(r=>r&&r.antes).slice(0,4).map(r=>({item:String(r.item||""),antes:String(r.antes),depois:String(r.depois||"")})):[],passos:Array.isArray(x?.passos)?x.passos.filter(r=>r&&r.t).slice(0,4).map(r=>({t:String(r.t),d:String(r.d||"")})):[]};')
troca('ESTRUTURA (campo "papel" de cada slide, nesta ordem)', 'Use TODO o material: explicacao, detalhes, declaracoes, cronologia, numeros, porQueImporta, impactoMercado, entenda e observar são a base dos slides correspondentes. Cada slide precisa trazer informação concreta desta notícia (nome, número, data, causa, consequência); é proibido texto genérico que serviria para qualquer notícia. Na legenda, explique a notícia em 2 a 3 parágrafos com os dados reais e termine com a pergunta do material.\nESTRUTURA (campo "papel" de cada slide, nesta ordem)')

# editor: campo de números vira linhas (antes×depois) ou passos conforme o slide
troca('''  $("f-nums").hidden=capa||last;$("e-nums").value=(s.numeros||[]).map(r=>`${r.valor}; ${r.rotulo}`).join("\\n");''',
      '''  $("f-nums").hidden=capa||last;
  const lblN=$("f-nums").querySelector("label");
  if(s.papel==="comparativo"&&(s.linhas||[]).length||LISTA.has(s.papel)){lblN.textContent=LISTA.has(s.papel)?"Passos (título; descrição)":"Antes × depois (item; antes; depois)";$("e-nums").value=LISTA.has(s.papel)?(s.passos||[]).map(r=>`${r.t}; ${r.d}`).join("\\n"):(s.linhas||[]).map(r=>`${r.item}; ${r.antes}; ${r.depois}`).join("\\n");}
  else{lblN.textContent="Números (valor; descrição)";$("e-nums").value=(s.numeros||[]).map(r=>`${r.valor}; ${r.rotulo}`).join("\\n");}''')
troca('''  Object.assign(s,{natureza:$("e-nat").value,rotulo:$("e-rot").value,titulo:$("e-tit").value,texto:$("e-txt").value,fonte:$("e-fonte").value,
    numeros:$("e-nums").value.split("\\n").map(l=>l.split(";")).filter(r=>r[0]&&r[0].trim()).map(r=>({valor:r[0].trim(),rotulo:(r.slice(1).join(";")||"").trim()}))});''',
      '''  const rows=$("e-nums").value.split("\\n").map(l=>l.split(";")).filter(r=>r[0]&&r[0].trim());
  Object.assign(s,{natureza:$("e-nat").value,rotulo:$("e-rot").value,titulo:$("e-tit").value,texto:$("e-txt").value,fonte:$("e-fonte").value});
  if(LISTA.has(s.papel))s.passos=rows.map(r=>({t:r[0].trim(),d:(r.slice(1).join(";")||"").trim()}));
  else if(s.papel==="comparativo"&&(s.linhas||[]).length)s.linhas=rows.map(r=>({item:r[0].trim(),antes:(r[1]||"").trim(),depois:(r.slice(2).join(";")||"").trim()}));
  else s.numeros=rows.map(r=>({valor:r[0].trim(),rotulo:(r.slice(1).join(";")||"").trim()}));''')

troca('case "aconteceu":return {...base,titulo:plain(nw.titulo),texto:nw.resumo,','case "aconteceu":return {...base,titulo:plain(nw.titulo),texto:(nw.explicacao||[])[0]||nw.resumo,')
troca('texto:nw.porQueImporta||"Notícias assim','texto:[nw.porQueImporta,(nw.explicacao||[])[2]].filter(Boolean).join(" ")||"Notícias assim')
troca('${nw.resumo}\\n\\n${nw.porQueImporta?','${(nw.explicacao||[]).length?nw.explicacao.slice(0,3).join("\\n\\n"):nw.resumo}\\n\\n${(nw.detalhes||[]).length?nw.detalhes.slice(0,4).map(x=>"▪️ "+x).join("\\n")+"\\n\\n":""}${nw.pergunta?nw.pergunta+"\\n\\n":""}${nw.porQueImporta?')

# ---------- IA: sem chave usa a ficha ----------
troca('  if(!sample){deck.slides=localSlides(deck,n);deck.legenda=localLegenda(deck);setStatus("genStatus",db?"Gerado pelo modelo padrão (IA indisponível aqui). Edite os textos se quiser.":"Prévia local.");afterGen();return;}',
      '  if(!temIA()){if(reaproveitar)deck.slides=reorgLocal(reaproveitar.slides,n);else{deck.slides=localSlides(deck,n);deck.legenda=localLegenda(deck);}setStatus("genStatus","Montado com os dados da ficha da notícia (sem IA). Para a IA reescrever, coloque a chave da OpenAI na aba Marca.");afterGen();return;}')
troca('  if(sample){await gerar({n,slides:old});}', '  if(temIA()){await gerar({n,slides:old});}')
troca('  if(!sample){setStatus("genStatus","Regenerar precisa da IA, que não está disponível nesta visualização.","err");return;}',
      '  if(!temIA()){setStatus("genStatus","Regenerar precisa da IA: coloque a chave da OpenAI na aba Marca.","err");return;}')
troca('  if(!sample||!canImages){setStatus("imgStatus","Imagens adicionadas. A análise automática não está disponível aqui; escolha o slide de cada uma.");return;}',
      '  if(!temIA()||!canImages){setStatus("imgStatus","Imagens adicionadas. Para a IA ler cada imagem, coloque a chave da OpenAI na aba Marca; por enquanto escolha o slide de cada uma.");return;}')
troca('return c==="cancelled"?"Geração interrompida."', 'return c==="bad_key"?"A chave da OpenAI foi recusada. Confira na aba Marca.":c==="network"?"Sem conexão com a OpenAI. Tente de novo.":/^http_/.test(c||"")?"A OpenAI respondeu com erro ("+c.slice(5)+"). Confira o modelo na aba Marca.":c==="cancelled"?"Geração interrompida."')

# ---------- exportar: celular com tela de compartilhar ----------
troca('    if(reuse)prog(.6,"Usando as imagens já prontas…");', '''    if(reuse)prog(.6,"Usando as imagens já prontas…");
    if(modo==="cel"){const fs=blobs.map((b,i)=>new File([b],fileName(i,deck.slides[i]),{type:b.type}));
      if(navigator.canShare&&navigator.canShare({files:fs})){prog(.8,"Abrindo a tela de compartilhar…");
        try{await navigator.share({files:fs,title:"Carrossel"});prog(1,`${n} imagens enviadas. Escolha "Salvar imagens" para irem para a galeria.`,"ok");}
        catch(e){prog(0,e?.name==="AbortError"?"Compartilhamento cancelado. As imagens continuam prontas.":"Não consegui abrir a tela de compartilhar. Use o ZIP.","err");}
        return;}}''')

# ---------- início ----------
troca('$("dbstatus").textContent=db?"Conectado":"Banco indisponível nesta visualização";',
      '$("dbstatus").textContent=db?"Coleta automática pelo GitHub · 6h45, 12h45 e 18h45":"Não consegui carregar os dados";')
troca('$("fData").onchange=e=>{filt.data=e.target.value;renderNews();};',
      '$("fData").onchange=e=>{filt.data=e.target.value;renderNews();};\n$("fBusca").oninput=e=>{filt.q=e.target.value.trim().toLowerCase();renderNews();};')
troca('''</script>

</body></html>''', '''</script>
<script>
(function(){const st=()=>{const k=radarKey.get();setStatus("aiStatus",k?"Chave salva neste navegador (termina em "+k.slice(-4)+") · modelo "+radarModelo.get()+".":"Sem chave: o carrossel é montado com os dados da ficha, sem IA.",k?"ok":"err");};
 $("aiModelo").value=radarModelo.get();
 $("aiSalvar").onclick=()=>{const v=$("aiKey").value.trim();if(!/^sk-/.test(v)){setStatus("aiStatus","A chave da OpenAI começa com sk-.","err");return;}radarKey.set(v);$("aiKey").value="";st();};
 $("aiRemover").onclick=()=>{radarKey.set("");st();};
 $("aiModeloSalvar").onclick=()=>{radarModelo.set($("aiModelo").value.trim());st();};st();})();
</script>
</body></html>''')

# ---------- encaixe: o texto nunca passa das margens seguras (4:5 e 1:1, todos os modelos) ----------
troca("""function autofit(el){
  const m=el.querySelector(".main");if(!m)return;
  let t=1;el.style.setProperty("--t",t);
  while(m.scrollHeight>m.clientHeight+2&&t>0.6){t=+(t-0.05).toFixed(2);el.style.setProperty("--t",t);}
}""", """function autofit(el){
  const m=el.querySelector(".main");if(!m)return;
  const fr=el.querySelector(".frame");
  // passou do quadro: altura (corta embaixo) ou largura (palavra comprida sai pela lateral)
  const over=()=>{if(m.scrollHeight>m.clientHeight+1||m.scrollWidth>m.clientWidth+1)return true;
    const lim=fr.getBoundingClientRect();return [...m.querySelectorAll(".h1,.h2,.qt,.tarja,.brd,.bignum")].some(x=>{const r=x.getBoundingClientRect();return r.right>lim.right+1||r.left<lim.left-1;});};
  let t=1;el.style.setProperty("--t",t);
  while(over()&&t>0.5){t=+(t-0.04).toFixed(2);el.style.setProperty("--t",t);}
  if(!over())return;
  // último recurso: tira frases do fim do texto corrido, depois palavras, até caber
  const txts=[...m.querySelectorAll(".txt,.qx,.sub,.ps>div span")].reverse();
  for(const x of txts){const parts=x.innerHTML.split(/(?<=[.!?])\\s+/);while(over()&&parts.length>1){parts.pop();x.innerHTML=parts.join(" ");}}
  for(const x of txts){let w=x.textContent.split(/\\s+/);let n=0;while(over()&&w.length>6&&n++<120){w.pop();x.textContent=w.join(" ").replace(/[,;:.]$/,"")+"…";}}
}""")
troca('return `<div class="box" style="height:${bh}px">', 'return `<div class="box" style="height:calc(${bh}px * var(--t))">')
s = s.replace('class="ico3d" style="width:${Math.round(124*k)}px;height:${Math.round(118*k)}px"', 'class="ico3d" style="width:calc(${Math.round(124*k)}px * var(--t));height:calc(${Math.round(118*k)}px * var(--t))"')
assert 'calc(${Math.round(124*k)}px' in s
troca('(F.fh.includes("Anton")?.56:.82)', '(F.fh.includes("Anton")?.62:.9)', 2)
troca('function tickHTML(d){const it=(d.placar||[]).slice(0,6);', 'function tickHTML(d){const it=(d.placar||[]).slice(0,4);')
troca("""</style>""", """/* encaixe 2.0: tudo encolhe junto com o texto (--t) e nada atravessa a margem */
.sl .main,.sl .main *{overflow-wrap:break-word;hyphens:manual}
.sl .main>*{max-width:100%}
.sl .tick{margin-top:0;justify-content:space-between;gap:calc(16px * var(--k))}
.sl .tick span{overflow:hidden;text-overflow:ellipsis}
.sl .lr{gap:calc(16px * var(--t))}
.sl .nat{font-size:calc(20px * var(--k) * var(--t))}
.sl .rot{font-size:calc(22px * var(--k) * var(--t));white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.sl .chip{font-size:calc(24px * var(--k) * var(--t))}
.sl .src{font-size:calc(21px * var(--k) * var(--t))}
.sl .uline{height:calc(8px * var(--t))}
.sl .follow{padding:calc(16px * var(--k) * var(--t));gap:calc(20px * var(--k) * var(--t))}
.sl .follow .fa{width:calc(88px * var(--k) * var(--t));height:calc(88px * var(--k) * var(--t))}
.sl .follow .fn b{font-size:calc(32px * var(--k) * var(--t))}
.sl .follow .fn span{font-size:calc(22px * var(--k) * var(--t))}
.sl .follow .fb{font-size:calc(30px * var(--k) * var(--t));padding:calc(14px * var(--k) * var(--t)) calc(32px * var(--k) * var(--t))}
.sl .bio{font-size:calc(28px * var(--k) * var(--t))}
.sl .follow{margin-bottom:calc(58px * var(--k))}
.sl .follow.big{padding-right:calc(46px * var(--k))}
.sl .pill{font-size:calc(34px * var(--k) * var(--t))}
.sl .fa2{max-width:calc(190px * var(--t));max-height:calc(190px * var(--t))}
.sl .cta-btn{font-size:calc(46px * var(--k) * var(--t));padding:calc(28px * var(--k) * var(--t)) 0}
.sl .dados{padding:calc(20px * var(--k) * var(--t)) calc(28px * var(--k))}
.sl .ccard{padding:calc(36px * var(--k) * var(--t)) calc(38px * var(--k))}
</style>""", 2)

open(os.path.join(os.path.dirname(AQUI), "docs", "index.html"), "w", encoding="utf-8").write(s)
print("index.html montado:", len(s), "bytes")
