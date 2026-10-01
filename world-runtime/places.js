function css(){
  if(document.querySelector('#caldas-places-style')) return;
  const s=document.createElement('style'); s.id='caldas-places-style';
  s.textContent=`
  .cw-places-btn{position:fixed;z-index:29;right:10px;top:max(10px,env(safe-area-inset-top));border:1px solid rgba(255,255,255,.16);background:rgba(6,12,15,.8);color:#fff;border-radius:999px;padding:10px 14px;font:600 12px/1 system-ui,sans-serif;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);touch-action:manipulation}
  .cw-places{position:fixed;z-index:28;right:10px;top:58px;width:min(360px,calc(100vw - 20px));max-height:min(72dvh,680px);overflow:auto;border:1px solid rgba(255,255,255,.13);background:rgba(7,13,16,.92);color:#fff;border-radius:20px;padding:12px;box-shadow:0 24px 70px rgba(0,0,0,.38);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);transform:translateY(-8px);opacity:0;pointer-events:none;transition:.18s ease}
  .cw-places.on{transform:none;opacity:1;pointer-events:auto}
  .cw-places h2{font:650 16px/1.2 system-ui,sans-serif;margin:4px 4px 10px}
  .cw-place{display:block;width:100%;text-align:left;border:1px solid transparent;background:rgba(255,255,255,.045);color:#fff;border-radius:14px;padding:11px 12px;margin:6px 0;min-height:54px}
  .cw-place:hover,.cw-place:focus-visible{border-color:rgba(255,255,255,.2);outline:none}
  .cw-place b{display:block;font:650 13px/1.2 system-ui,sans-serif}.cw-place span{display:block;color:#aebdbb;font:11px/1.35 system-ui,sans-serif;margin-top:4px}
  .cw-place[aria-current="true"]{border-color:rgba(216,180,106,.65);background:rgba(216,180,106,.09)}
  @media(max-width:640px){.cw-places-btn{top:auto;right:10px;bottom:max(12px,env(safe-area-inset-bottom));min-height:44px}.cw-places{top:auto;bottom:calc(64px + env(safe-area-inset-bottom));right:10px;left:10px;width:auto;max-height:58dvh;border-radius:20px}.cw-place{min-height:58px}}
  `;
  document.head.appendChild(s);
}

export function installPlacesPanel({ title='Places', places=[], onSelect, initial=null }={}){
  css();
  const btn=document.createElement('button'); btn.className='cw-places-btn'; btn.type='button'; btn.textContent='Places';
  const panel=document.createElement('section'); panel.className='cw-places'; panel.setAttribute('aria-label',title);
  panel.innerHTML='<h2></h2><div></div>';
  panel.querySelector('h2').textContent=title;
  const list=panel.querySelector('div');
  let current=initial;
  const buttons=new Map();
  for(const p of places){
    const b=document.createElement('button'); b.type='button'; b.className='cw-place'; b.dataset.id=p.id;
    b.innerHTML='<b></b><span></span>'; b.querySelector('b').textContent=p.label; b.querySelector('span').textContent=p.description||'';
    b.setAttribute('aria-current',p.id===current?'true':'false');
    b.addEventListener('click',()=>{
      current=p.id;
      for(const [id,x] of buttons) x.setAttribute('aria-current',id===current?'true':'false');
      onSelect?.(p);
      panel.classList.remove('on');
      btn.setAttribute('aria-expanded','false');
    });
    list.appendChild(b); buttons.set(p.id,b);
  }
  btn.setAttribute('aria-expanded','false');
  btn.addEventListener('click',()=>{
    const on=panel.classList.toggle('on'); btn.setAttribute('aria-expanded',String(on));
  });
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'){panel.classList.remove('on');btn.setAttribute('aria-expanded','false');} });
  document.body.append(panel,btn);
  return {button:btn,panel,setCurrent(id){current=id;for(const [k,x] of buttons)x.setAttribute('aria-current',k===id?'true':'false');}};
}

export function flyCamera({camera,controls,toPosition,toTarget,duration=1.2,onUpdate,onDone}){
  const fromP=camera.position.clone(), fromT=controls.target.clone();
  const start=performance.now(), ms=Math.max(250,duration*1000);
  let raf=0;
  const step=now=>{
    const t=Math.min(1,(now-start)/ms);
    const u=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
    camera.position.lerpVectors(fromP,toPosition,u);
    controls.target.lerpVectors(fromT,toTarget,u);
    controls.update(); onUpdate?.(u);
    if(t<1) raf=requestAnimationFrame(step); else onDone?.();
  };
  raf=requestAnimationFrame(step);
  return ()=>cancelAnimationFrame(raf);
}
