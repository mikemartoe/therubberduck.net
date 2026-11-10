/* The Drop Ledger: Photos view (Phase 1). Searches captions + original
   filenames + drop number; type chips come from caption words. */
(function(root){
  'use strict';
  var LX=root.TRDLedger, UI=root.TRDLedgerUI;
  if(!LX || !root.TRD_DROP_IMAGES) return;

  var TYPES=[
    {id:'photo', label:'Photo', re:/\bphotos?\b|\bphotograph/i},
    {id:'screenshot', label:'Screenshot', re:/\bscreenshots?\b|\bscreen\s*shots?\b/i},
    {id:'tweet', label:'Tweet', re:/\btweets?\b/i},
    {id:'graphic', label:'Graphic', re:/\bgraphics?\b/i},
    {id:'meme', label:'Meme', re:/\bmemes?\b/i},
    {id:'map', label:'Map', re:/\bmaps?\b/i},
    {id:'document', label:'Document', re:/\bdocuments?\b|\bopen letters?\b|\bletters?\b/i}
  ];

  function capOf(n,i){
    var T=root.TRD_DROP_IMAGE_TEXT||{}, v=T[n+'_'+(i+1)];
    if(v && typeof v==='object') v=v.alt||v.caption||'';
    return String(v||'');
  }
  function fileOf(n,i){
    var F=root.TRD_DROP_IMAGE_FILES||{};
    return String(F[n+'_'+(i+1)]||'');
  }
  function typesOf(cap){
    var out=[], i;
    for(i=0;i<TYPES.length;i++) if(TYPES[i].re.test(cap)) out.push(TYPES[i].id);
    return out;
  }
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function nf(v){ return v.toLocaleString('en-US'); }
  function norm(s){
    s=String(s||'').toLowerCase();
    if(s.normalize) s=s.normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    return s.replace(/[\u2018\u2019\u201B\u2032`´]/g,"'").replace(/[\u201C\u201D\u201E\u2033]/g,'"').replace(/[\u2013\u2014]/g,'-');
  }
  function tokens(s){ return norm(s).replace(/'/g,'').match(/[a-z0-9]+/g)||[]; }

  var DI=root.TRD_DROP_IMAGES;
  var ITEMS=[];
  Object.keys(DI.d).forEach(function(k){
    var n=+k, rec=LX.byN(n), arr=DI.d[k]||[];
    arr.forEach(function(im,i){
      var cap=capOf(n,i), fn=fileOf(n,i);
      ITEMS.push({
        n:n, i:i, src:im.src, sm:im.sm, w:im.w, h:im.h, sw:im.sw, sh:im.sh,
        cap:cap, fn:fn, types:typesOf(cap),
        d:rec?rec.d_iso:'', t:rec?rec.t:0,
        hay:norm(cap+' '+fn+' #'+n+' '+n)
      });
    });
  });
  ITEMS.sort(function(a,b){ return b.n-a.n || a.i-b.i; });

  var main=document.getElementById('main');
  var list=document.getElementById('arcList');
  var info=document.getElementById('arcInfo');
  var empty=document.getElementById('arcEmpty');
  var query=document.getElementById('arcQuery');
  var wrap=document.getElementById('arcSearchWrap');
  var dock=document.getElementById('ldock');
  var PH_LONG='Search photos: caption, filename or #number';
  var PH_SHORT='Search photos';
  var DROP_LONG=query?query.getAttribute('placeholder')||'Search the Q drops: #number, date or phrase':'';
  var state={view:'drops', type:'', filtered:ITEMS.slice(), hl:[]};

  /* ---- chrome: Drops | Photos toggle + type chips + grid ---- */
  var viewBox=document.getElementById('ldockView');
  if(!viewBox && dock){
    viewBox=document.createElement('div');
    viewBox.className='ldock-view';
    viewBox.id='ldockView';
    viewBox.setAttribute('role','tablist');
    viewBox.setAttribute('aria-label','Ledger view');
    viewBox.innerHTML=
      '<button type="button" id="viewDrops" role="tab" aria-selected="true" aria-pressed="true" data-view="drops">Drops</button>'+
      '<button type="button" id="viewPhotos" role="tab" aria-selected="false" aria-pressed="false" data-view="photos">Photos</button>';
    var bar=dock.querySelector('.arc-bar');
    var search=document.getElementById('arcSearchWrap');
    if(bar && search) bar.insertBefore(viewBox, search.nextSibling);
    else if(bar) bar.appendChild(viewBox);
  }

  var typesEl=document.getElementById('phTypes');
  if(!typesEl){
    typesEl=document.createElement('div');
    typesEl.className='ph-types';
    typesEl.id='phTypes';
    typesEl.hidden=true;
    typesEl.setAttribute('role','group');
    typesEl.setAttribute('aria-label','Filter photos by type');
    typesEl.innerHTML=TYPES.map(function(t){
      return '<button type="button" class="chip" data-ph-type="'+t.id+'" aria-pressed="false">'+esc(t.label)+'</button>';
    }).join('');
    if(info && info.parentNode) info.parentNode.insertBefore(typesEl, info.nextSibling);
  }

  var grid=document.getElementById('phGrid');
  if(!grid){
    grid=document.createElement('div');
    grid.className='ph-grid';
    grid.id='phGrid';
    grid.hidden=true;
    grid.setAttribute('role','list');
    grid.setAttribute('aria-label','Drop photos');
    if(list && list.parentNode) list.parentNode.insertBefore(grid, list);
  }

  function isPhone(){ return window.matchMedia && window.matchMedia('(max-width:760px)').matches; }
  function placeholder(){
    if(!query) return;
    if(state.view==='photos') query.setAttribute('placeholder', isPhone()?PH_SHORT:PH_LONG);
    else query.setAttribute('placeholder', isPhone()?'Search the Q drops':DROP_LONG);
  }
  function setViewButtons(){
    if(!viewBox) return;
    [].slice.call(viewBox.querySelectorAll('[data-view]')).forEach(function(b){
      var on=b.getAttribute('data-view')===state.view;
      b.setAttribute('aria-pressed', on?'true':'false');
      b.setAttribute('aria-selected', on?'true':'false');
    });
  }
  function setTypeButtons(){
    [].slice.call(typesEl.querySelectorAll('[data-ph-type]')).forEach(function(b){
      b.setAttribute('aria-pressed', b.getAttribute('data-ph-type')===state.type?'true':'false');
    });
  }

  /* ---- search ---- */
  function parseText(q){
    var s=norm(q).replace(/&&/g,' ').replace(/\s+AND\s+/g,' ');
    var groups=[[]], re=/(-?)"([^"]+)"|(\|)|(\S+)/g, m;
    while((m=re.exec(s))){
      if(m[3] || (m[4]&&m[4]==='or')){ groups.push([]); continue; }
      if(m[4]==='and') continue;
      var neg=!!m[1], w=m[2]!==undefined?m[2]:m[4];
      if(w && w.charAt(0)==='-' && w.length>1 && m[2]===undefined){ neg=true; w=w.slice(1); }
      if(w) groups[groups.length-1].push({w:w, neg:neg, phrase:!!m[2]});
    }
    return groups.filter(function(g){ return g.length; });
  }
  function termHit(hay, tok, term, phrase){
    if(/[^a-z0-9' ]/.test(term) && hay.indexOf(norm(term))>-1) return true;
    if(phrase || tok.length>1){
      var want=tokens(term); if(!want.length) return true;
      for(var i=0;i+want.length<=tok.length;i++){
        var ok=true;
        for(var j=0;j<want.length;j++){
          var last=j===want.length-1;
          if(last ? tok[i+j].indexOf(want[j])!==0 : tok[i+j]!==want[j]){ ok=false; break; }
        }
        if(ok) return true;
      }
      return hay.indexOf(norm(term))>-1;
    }
    var w=tokens(term)[0]; if(!w) return true;
    if(w.length<=2) return tok.indexOf(w)>-1;
    for(var k=0;k<tok.length;k++) if(tok[k].indexOf(w)===0) return true;
    return hay.indexOf(w)>-1;
  }
  function hlTerms(groups){
    var out=[];
    (groups||[]).forEach(function(g){
      g.forEach(function(t){ if(t.neg) return; var w=String(t.w||'').trim(); if(w && out.indexOf(w)<0) out.push(w); });
    });
    return out;
  }
  function markText(s, terms){
    s=String(s||'');
    if(!terms || !terms.length || !s) return esc(s);
    var parts=terms.filter(Boolean).map(function(t){ return t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); });
    if(!parts.length) return esc(s);
    var re=new RegExp('('+parts.join('|')+')','ig');
    var out='', last=0, m;
    while((m=re.exec(s))){
      out+=esc(s.slice(last,m.index))+'<mark class="lx-hl">'+esc(m[0])+'</mark>';
      last=m.index+m[0].length;
    }
    return out+esc(s.slice(last));
  }

  function filterPhotos(q, type, sort){
    var rows=ITEMS.slice(), label='', groups=null, date=null, num=null, raw=(q||'').trim();
    if(type) rows=rows.filter(function(it){ return it.types.indexOf(type)>-1; });
    if(raw){
      date=LX.parseDateQuery(raw);
      num=LX.parseNumber(raw);
      if(num!==null){
        rows=rows.filter(function(it){ return it.n===num; });
        label=rows.length?('Photos from Q drop #'+num+'.'):('No photos in drop #'+num+'.');
      } else if(date){
        var recs=LX.search(raw,{noSyn:true});
        var allow={};
        (recs.rows||[]).forEach(function(r){ allow[r.n]=1; });
        rows=rows.filter(function(it){ return allow[it.n]; });
        label=recs.label?recs.label.replace(/^Drops /,'Photos ').replace(/drops /g,'photos '):('Photos in that period.');
      } else {
        groups=parseText(raw);
        rows=rows.filter(function(it){
          var tok=tokens(it.hay);
          return groups.some(function(g){
            return g.every(function(t){
              var hit=termHit(it.hay, tok, t.w, t.phrase);
              return t.neg?!hit:hit;
            });
          });
        });
        var shown=groups.map(function(g){ return g.map(function(t){ return (t.neg?'not ':'')+'“'+t.w+'”'; }).join(' + '); }).join(' or ');
        label='Photos matching '+shown+'.';
      }
    } else {
      label=type?('Photos tagged as '+TYPES.filter(function(t){return t.id===type;})[0].label+'.'):'Every photo that appeared in a drop.';
    }
    sort=sort||'newest';
    if(sort==='oldest') rows.sort(function(a,b){ return a.t-b.t || a.n-b.n || a.i-b.i; });
    else if(sort==='number') rows.sort(function(a,b){ return a.n-b.n || a.i-b.i; });
    else rows.sort(function(a,b){ return b.n-a.n || a.i-b.i; });
    return {rows:rows, label:label, hl:hlTerms(groups), q:raw};
  }

  /* ---- render ---- */
  var BATCH=80, shown=0, pending=null;
  function tileHTML(it, hl){
    var lab=it.cap || ('Q drop #'+it.n+(it.i?' image '+(it.i+1):''));
    var showCap=!!(hl && hl.length && it.cap);
    var date='';
    if(it.d){ var p=it.d.split('-'); date=parseInt(p[2],10)+' '+LX.MON[parseInt(p[1],10)-1]+' '+p[0]; }
    return '<button type="button" class="ph-tile" role="listitem" data-ph-n="'+it.n+'" data-ph-i="'+it.i+'" aria-label="Enlarge '+esc(lab)+'">'+
      '<span class="ph-thumb"><img src="'+esc(DI.base+it.sm)+'" width="'+it.sw+'" height="'+it.sh+'" loading="lazy" decoding="async" alt="'+esc(lab)+'"></span>'+
      '<span class="ph-meta"><span class="ph-n">#'+nf(it.n)+'</span>'+(date?'<span class="ph-d">'+esc(date)+'</span>':'')+
      (showCap?'<span class="ph-cap">'+markText(it.cap, hl)+'</span>':'')+
      '</span></button>';
  }
  function paintMore(){
    pending=null;
    if(state.view!=='photos') return;
    var rows=state.filtered, next=Math.min(rows.length, shown+BATCH);
    if(next<=shown) return;
    var html='', i, hl=state.hl;
    for(i=shown;i<next;i++) html+=tileHTML(rows[i], hl);
    grid.insertAdjacentHTML('beforeend', html);
    shown=next;
    if(shown<rows.length){
      if('IntersectionObserver' in window){
        if(!paintMore._io){
          var sen=document.createElement('div');
          sen.id='phSentinel'; sen.style.cssText='height:1px;width:100%;grid-column:1/-1';
          grid.appendChild(sen);
          paintMore._io=new IntersectionObserver(function(ents){
            if(ents.some(function(e){return e.isIntersecting;})) paintMore();
          }, {rootMargin:'800px 0px'});
          paintMore._io.observe(sen);
        } else {
          var s=document.getElementById('phSentinel');
          if(s) grid.appendChild(s);
        }
      } else if(!pending){
        pending=requestAnimationFrame(paintMore);
      }
    }
  }
  function renderGrid(res){
    state.filtered=res.rows;
    state.hl=res.hl||[];
    shown=0;
    grid.innerHTML='';
    if(paintMore._io && paintMore._sen){ /* keep observer */ }
    if(!res.rows.length){
      grid.hidden=true;
      if(empty){
        empty.hidden=false;
        var t=document.getElementById('arcEmptyTitle'), b=document.getElementById('arcEmptyBody'), a=document.getElementById('arcActs');
        if(t) t.textContent='No photos match that.';
        if(b) b.textContent='Try a caption word, an original filename, a drop number like #14, or a date like Oct 2018. Type chips narrow by what the caption already says.';
        if(a) a.innerHTML='<button type="button" class="lx-act" data-lx-q="">Clear search</button>';
      }
    } else {
      if(empty) empty.hidden=true;
      grid.hidden=false;
      paintMore();
    }
    if(info){
      var n=res.rows.length, word=n===1?'photo':'photos';
      var total='<span class="lx-total" title="'+nf(n)+' matching '+word+'"><b>'+nf(n)+'</b> '+word+'</span>';
      info.hidden=false;
      info.innerHTML='<span class="lx-lbl">'+esc(res.label||'')+'</span>'+total;
    }
  }

  /* ---- lightbox: captions, links, walk the current photo set from the grid ---- */
  function ensureLinks(el){
    if(el.querySelector('.dlb-links')) return el.querySelector('.dlb-links');
    var nav=document.createElement('nav');
    nav.className='dlb-links';
    nav.innerHTML='<a class="dlb-ledger" href="#">This drop in the Ledger</a><a class="dlb-page" href="#">Open the drop page</a>';
    var fig=el.querySelector('.dlb-fig');
    if(fig) fig.appendChild(nav);
    else el.appendChild(nav);
    return nav;
  }
  function fillLightbox(n,i){
    var el=document.getElementById('dropLightbox'); if(!el) return;
    var img=el.querySelector('.dlb-img'), cap=el.querySelector('.dlb-cap');
    var text=capOf(n,i);
    var lab=text || ('Q drop #'+n);
    if(img) img.alt=lab;
    if(cap) cap.innerHTML=state.view==='photos'?markText(text || lab, state.hl):esc(text || lab);
    var nav=ensureLinks(el);
    var a1=nav.querySelector('.dlb-ledger'), a2=nav.querySelector('.dlb-page');
    if(a1){ a1.href='/ledger.html#drop-'+n; a1.setAttribute('data-ph-ledger', String(n)); a1.textContent='Q drop #'+n+' in the Ledger'; }
    if(a2){ a2.href='/drops/'+n+'/'; a2.textContent='Open drop #'+n; }
  }
  document.addEventListener('click', function(e){
    var a=e.target.closest('a[data-ph-ledger]'); if(!a) return;
    var n=+a.getAttribute('data-ph-ledger'); if(!n) return;
    e.preventDefault();
    var lb=document.getElementById('dropLightbox');
    if(lb && UI && typeof UI.closeLightbox==='function') UI.closeLightbox();
    else if(lb){ var x=lb.querySelector('.dlb-x'); if(x) x.click(); }
    setView('drops', {skipUrl:false});
    if(UI && UI.setQuery) UI.setQuery('#'+n, {scroll:true});
    else location.hash='drop-'+n;
  }, true);

  /* From the grid, prev/next walks the filtered photo list. */
  var walk=null;
  function openFromGrid(it, from){
    var rows=state.filtered, idx=-1, k;
    for(k=0;k<rows.length;k++) if(rows[k].n===it.n && rows[k].i===it.i){ idx=k; break; }
    if(idx<0) idx=0;
    walk={rows:rows, idx:idx};
    if(UI && typeof UI.openLightbox==='function'){
      UI.openLightbox(it.n, it.i, from);
    } else {
      var btn=from;
      if(btn) btn.click();
    }
    /* after the stock lightbox paints, overlay caption/links and hook arrows */
    setTimeout(function(){ fillLightbox(it.n, it.i); hookWalk(); }, 0);
  }
  var hooked=false;
  function hookWalk(){
    var el=document.getElementById('dropLightbox'); if(!el || hooked) return;
    hooked=true;
    el.addEventListener('click', function(e){
      if(!walk || state.view!=='photos') return;
      if(e.target.closest('.dlb-prev')){ e.stopPropagation(); e.preventDefault(); step(-1); }
      else if(e.target.closest('.dlb-next')){ e.stopPropagation(); e.preventDefault(); step(1); }
    }, true);
    document.addEventListener('keydown', function(e){
      if(!walk || state.view!=='photos') return;
      var el2=document.getElementById('dropLightbox'); if(!el2 || el2.hidden) return;
      if(e.key==='ArrowLeft'){ e.preventDefault(); step(-1); }
      else if(e.key==='ArrowRight'){ e.preventDefault(); step(1); }
    }, true);
  }
  function step(dir){
    if(!walk || !walk.rows.length) return;
    walk.idx=(walk.idx+dir+walk.rows.length)%walk.rows.length;
    var it=walk.rows[walk.idx];
    if(UI && typeof UI.showLightbox==='function') UI.showLightbox(it.n, it.i);
    fillLightbox(it.n, it.i);
    var el=document.getElementById('dropLightbox');
    if(el){
      var bp=el.querySelector('.dlb-prev'), bn=el.querySelector('.dlb-next');
      if(bp) bp.hidden=walk.rows.length<2;
      if(bn) bn.hidden=walk.rows.length<2;
    }
  }

  grid.addEventListener('click', function(e){
    var t=e.target.closest('.ph-tile'); if(!t) return;
    var n=+t.getAttribute('data-ph-n'), i=+t.getAttribute('data-ph-i');
    var it=null;
    state.filtered.some(function(x){ if(x.n===n && x.i===i){ it=x; return true; } });
    if(!it) return;
    openFromGrid(it, t);
  });

  /* ---- URL + view ---- */
  function syncURL(){
    try{
      var u=new URL(location.href), q=(UI && UI.state && UI.state.q || '').trim();
      u.searchParams.delete('q'); u.searchParams.delete('delta'); u.searchParams.delete('view');
      if(state.view==='photos') u.searchParams.set('view','photos');
      if(state.type && state.view==='photos') u.searchParams.set('type', state.type);
      else u.searchParams.delete('type');
      if(/^(today|yesterday|tomorrow)$/i.test(q)) u.searchParams.set('delta', q.toLowerCase());
      else if(q) u.searchParams.set('q', q);
      if(q && /^#drop-\d+$/.test(u.hash) && state.view==='photos') u.hash='';
      if(u.href!==location.href) history.replaceState(history.state, '', u.href);
    }catch(e){}
  }

  function applyPhotos(){
    var q=UI && UI.state ? UI.state.q : (query&&query.value||'');
    var sort=UI && UI.state ? UI.state.sort : 'newest';
    renderGrid(filterPhotos(q, state.type, sort));
    typesEl.hidden=false;
    placeholder();
    if(wrap) wrap.classList.toggle('has-value', !!(q&&q.trim()));
  }

  function setView(view, opts){
    opts=opts||{};
    state.view=view==='photos'?'photos':'drops';
    setViewButtons();
    if(main) main.classList.toggle('lx-photos', state.view==='photos');
    document.documentElement.classList.toggle('lx-photos', state.view==='photos');
    typesEl.hidden=state.view!=='photos';
    if(state.view!=='photos'){
      grid.hidden=true;
      grid.innerHTML='';
      shown=0;
      walk=null;
      placeholder();
      if(!opts.skipUrl) syncURL();
      /* let the drop list re-show its own info */
      if(UI && typeof UI.apply==='function' && !opts.skipApply) UI.apply();
      if(isPhone() && UI && UI.phoneFold && UI.state) UI.phoneFold(!!String(UI.state.q||'').trim());
      return;
    }
    if(isPhone() && UI && UI.phoneFold) UI.phoneFold(true);
    applyPhotos();
    if(!opts.skipUrl) syncURL();
    if(opts.scroll!==false){
      var a=document.getElementById('archive');
      if(a && isPhone()) a.scrollIntoView({block:'start', behavior:(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)?'auto':'smooth'});
    }
  }

  if(viewBox){
    viewBox.addEventListener('click', function(e){
      var b=e.target.closest('[data-view]'); if(!b) return;
      setView(b.getAttribute('data-view'), {scroll:true});
    });
  }
  typesEl.addEventListener('click', function(e){
    var b=e.target.closest('[data-ph-type]'); if(!b) return;
    var t=b.getAttribute('data-ph-type');
    state.type=(state.type===t)?'':t;
    setTypeButtons();
    applyPhotos();
    syncURL();
  });

  /* Public caption helper used by the drop-list lightbox as well. */
  root.TRDDropCap=capOf;

  /* Boot from ?view=photos (and optional ?type=). */
  (function boot(){
    var view='drops', type='';
    try{
      var sp=new URLSearchParams(location.search);
      if((sp.get('view')||'').toLowerCase()==='photos') view='photos';
      var t=(sp.get('type')||'').toLowerCase();
      if(TYPES.some(function(x){ return x.id===t; })) type=t;
    }catch(e){}
    state.type=type;
    setTypeButtons();
    setView(view, {skipUrl:false, skipApply:true, scroll:false});
    if(view==='photos' && isPhone()){
      var a=document.getElementById('archive');
      if(a) setTimeout(function(){ a.scrollIntoView({block:'start', behavior:'auto'}); }, 0);
    }
  })();

  placeholder();
  addEventListener('resize', placeholder);
  root.TRDLedgerPhotos={setView:setView, state:state, items:ITEMS, filter:filterPhotos, capOf:capOf, refresh:applyPhotos};
})(typeof window!=='undefined'?window:globalThis);
