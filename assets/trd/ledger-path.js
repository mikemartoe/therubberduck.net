/* The Drop Ledger: the path choice at the top of the ledger.
   "New here" shows the guided Start-here layer; "I know the drops" goes straight to the full ledger and search.
   The choice is remembered in localStorage (trd.ledgerPath) and can be switched any time from the bar.
   Nothing here touches search, Deltas or dates: the cards just run a normal "#n" ledger search. */
(function(){
  'use strict';
  var KEY='trd.ledgerPath', arc=document.getElementById('archive'), box=document.getElementById('lxPath');
  if(!arc || !box) return;
  var LX=window.TRDLedger;

  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function get(){ try{ var v=localStorage.getItem(KEY); return (v==='new'||v==='know')?v:null; }catch(e){ return null; } }
  function save(v){ try{ localStorage.setItem(KEY,v); }catch(e){} }
  function show(v){
    if(v) arc.setAttribute('data-lx-path',v); else arc.removeAttribute('data-lx-path');
    [].slice.call(box.querySelectorAll('.lx-path-seg [data-lx-path]')).forEach(function(b){
      b.setAttribute('aria-pressed', b.getAttribute('data-lx-path')===v?'true':'false');
    });
  }
  function scrollTo(el,off){
    var calm=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var y=el.getBoundingClientRect().top+window.pageYOffset-(off||90);
    window.scrollTo({top:Math.max(0,y),behavior:calm?'auto':'smooth'});
  }

  /* The seven Start-here cards: number, one plain line, and the date (US Eastern, from the data). */
  function cards(){
    var ol=document.getElementById('lxCards'), wrap=document.getElementById('lxSeven');
    if(!ol || !wrap || !LX || !LX.START) return;
    ol.innerHTML=LX.START.map(function(s){
      var r=LX.byN(s.n); if(!r) return '';
      var date=LX.MON[r.m-1]+' '+r.d+', '+r.y;
      var line=s.c.replace(/,\s*[A-Z][a-z]{2} \d{1,2}, \d{4}$/,'');
      return '<li><button type="button" class="lx-card" data-lx-q="#'+s.n+'" aria-label="Drop '+s.n+': '+esc(line)+', '+esc(date)+'">'+
        '<span class="lx-card-n">#'+s.n+'</span><span class="lx-card-c">'+esc(line)+'</span><span class="lx-card-d">'+esc(date)+'</span></button></li>';
    }).join('');
    wrap.hidden=false;
  }

  box.addEventListener('click',function(e){
    var b=e.target.closest('[data-lx-path]'); if(!b) return;
    var v=b.getAttribute('data-lx-path'), fromAsk=!!e.target.closest('.lx-path-ask');
    save(v); show(v);
    if(v==='know'){
      var bar=document.querySelector('.arc-bar'), q=document.getElementById('arcQuery');
      if(bar) scrollTo(bar,90);
      if(q && fromAsk){ try{ q.focus({preventScroll:true}); }catch(err){ q.focus(); } }
    } else if(fromAsk){
      scrollTo(box,90);
    }
  });

  show(get());
  cards();
  window.TRDLedgerPath={get:get, set:function(v){ save(v); show(v); }, reset:function(){ try{ localStorage.removeItem(KEY); }catch(e){} show(null); }};
})();
