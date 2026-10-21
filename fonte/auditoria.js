/* Auditoria de encaixe: cola no console do painel (ou roda pelo navegador de testes).
   Para cada modelo × formato × slide, renderiza fora da tela e mede se algo passa das margens seguras. */
window.auditar=async function(newsId,n=10){
  const nw=NEWS.find(x=>x.id===newsId)||NEWS.find(x=>x.porQueImporta)||NEWS[0];
  const base=newDeck(nw);base.slides=localSlides(base,n);
  const host=$("offstage"),out=[];
  for(const formato of ["retrato","quadrado"])for(const [kit,K] of Object.entries(KITS)){
    const d={...base,formato,estilo:{...estiloDe(base),...K,el:{...estiloDe(base).el,...(K.el||{})}}};
    d.slides=withMarca(d,base.slides);
    const t=FORMATOS[formato];
    for(let i=0;i<d.slides.length;i++){
      host.innerHTML=slideHTML(d,d.slides[i],i);const el=host.firstElementChild;autofit(el);
      const R=el.getBoundingClientRect(),m=el.querySelector(".main");
      const lim={top:R.top+t.st-2,bottom:R.bottom-t.sb+2,left:R.left+t.sx-2,right:R.right-t.sx+2};
      const prob=[];
      if(m&&m.scrollHeight>m.clientHeight+2)prob.push("corta "+(m.scrollHeight-m.clientHeight)+"px");
      el.querySelectorAll(".frame *").forEach(x=>{if(x.closest(".tick")||!x.offsetParent)return;const r=x.getBoundingClientRect();if(!r.width||!r.height)return;
        const vis=!(m&&m.contains(x))||r.top<m.getBoundingClientRect().bottom;
        if(vis&&(r.bottom>lim.bottom||r.right>lim.right+1)&&x.children.length===0&&x.textContent.trim())prob.push(`${x.className||x.tagName}:${Math.round(Math.max(r.bottom-lim.bottom,r.right-lim.right))}px`);});
      if(prob.length)out.push(`${formato} ${kit} #${i+1} ${d.slides[i].papel} t=${getComputedStyle(el).getPropertyValue("--t")} → ${[...new Set(prob)].slice(0,4).join(", ")}`);
    }
  }
  host.innerHTML="";return out;
};
