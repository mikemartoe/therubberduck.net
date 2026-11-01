/* ---- index.html lines 1001-1003 (commit fa19b6f62) ---- */
  function paint(st){
    if(deck.classList.contains('is-pl'))return;  /* the playlist tape is in: Spotify drives the deck */
    var live=!!(st&&st.started);
/* ---- index.html lines 1011-1013 (commit fa19b6f62) ---- */
    if(e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;
    if(deck.classList.contains('is-pl'))return;
    e.preventDefault();
/* ---- index.html lines 1116-1116 (commit fa19b6f62) ---- */
    document.querySelectorAll('a.spine, a.deck, .tcase').forEach(function(el){
/* ---- index.html lines 1170-1173 (commit fa19b6f62) ---- */
    closeFace();
    /* the tape in its case spine: load it into the deck */
    if(host.classList.contains('tcase')&&window.__trdSwapTape){window.__trdSwapTape();return;}
    var href=host.getAttribute('href');
/* ---- index.html lines 1190-1194 (commit fa19b6f62) ---- */
    var face=e.target.closest&&(e.target.closest('#trd-face-portal')||e.target.closest('.spine-face'));
    var spine=e.target.closest&&e.target.closest('a.spine');
    var deck=e.target.closest&&e.target.closest('a.deck');
    var shelfT=e.target.closest&&e.target.closest('button.tcase');
    if(deck&&deck.classList.contains('is-pl')&&!face)deck=null;
/* ---- index.html lines 1233-1253 (commit fa19b6f62) ---- */
/* hero: the one primary button plays the album in the pocket player (same as pressing play on the deck);
   without the player it is a plain link to album.html. The Spotify tape case is a normal link now:
   keep it exactly as wide as the room spines on PC. */
(function(){
  var cta=document.querySelector('.hero-cta'),deck=document.querySelector('a.deck[data-trd-pod-door]');
  if(cta)cta.addEventListener('click',function(e){
    if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||e.button)return;
    var cas=deck&&deck.querySelector('.cas');
    if(window.trdPod&&cas&&!window.trdPod.state().started){
      e.preventDefault();
      if(window.trdTrack)window.trdTrack('click/album-play','Homepage: hero Play The Red Pill Album');
      window.trdPod.launchFrom(cas,null,'full');
    }
  });
  var cs=document.querySelector('.hello .tcase');if(!cs)return;
  var pc=window.matchMedia('(min-width:900px) and (min-height:500px)');
  function fitCase(){var sp=document.querySelector('.stack-a .spine');
    if(pc.matches&&sp)cs.style.setProperty('--tcw',sp.offsetWidth+'px');else cs.style.removeProperty('--tcw');}
  fitCase();var ft;window.addEventListener('resize',function(){clearTimeout(ft);ft=setTimeout(fitCase,160);});
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fitCase);
})();
/* ---- index.html lines 1254-1438 (commit fa19b6f62) ---- */
/* two tapes: The Red Pill Album (the site's own player) and The Rubber Duck Personal Playlist (Spotify).
   The tape not in the deck waits in its own case spine on the left; choosing it slides that tape out of its
   case and into the deck while the deck tape ejects and goes back into the case. Only one source ever plays:
   the Spotify player is created only when the playlist is loaded, and is removed when the Red Pill tape goes back in. */
(function(){
  var deck=document.querySelector('a.deck[data-trd-pod-door]'),cs=document.getElementById('tapeCase');
  if(!deck||!cs)return;
  var well=deck.querySelector('.deck-well'),hold=cs.querySelector('.tc-hold'),kpl=deck.querySelector('.kp-pl');
  var deckFace=deck.querySelector('.spine-face img'),csFace=cs.querySelector('.spine-face img');
  var csCat=cs.querySelector('.sp-cat'),csIc=cs.querySelector('.sp-ic'),csN=cs.querySelector('.sp-n'),csS=cs.querySelector('.sp-s');
  var HREF=deck.getAttribute('href'),LABEL=deck.getAttribute('aria-label');
  var PL_URI='spotify:playlist:4lWQJV4n3mnIvp0y4biUqZ',PL_EMBED='https://open.spotify.com/embed/playlist/4lWQJV4n3mnIvp0y4biUqZ?utm_source=generator';
  var FACE={rp:'/assets/trd/img/cassettes/face-redpill.webp?v=cleanblack1',pl:'/assets/trd/img/cassettes/face-playlist.webp?v=1'};
  var TAPE={
    pl:{cls:'tc-pl',cat:'SIDE B',ic:'/assets/trd/img/duck-banner.webp',n:'Personal Playlist',s:'The Rubber Duck\u2122 on Spotify',label:'The Rubber Duck Personal Playlist. Load this tape into the deck'},
    rp:{cls:'tc-rp',cat:'SIDE A',ic:'/assets/trd/img/rpa-pill.webp',n:'The Red Pill Album',s:'22 tracks, plays right here',label:'The Red Pill Album. Load this tape back into the deck'}};
  var mode='rp',busy=false,spot=null,ctl=null,spPlaying=false;
  var pc=window.matchMedia('(min-width:900px) and (min-height:500px)');
  var rm=window.matchMedia('(prefers-reduced-motion: reduce)'),fine=window.matchMedia('(hover:hover) and (pointer:fine)');
  /* PC room: the case is exactly as wide as the room spines below it */
  function fitCase(){var sp=document.querySelector('.stack-a .spine');
    if(pc.matches&&sp){cs.style.setProperty('--tcw',sp.offsetWidth+'px');}else cs.style.removeProperty('--tcw');}
  fitCase();var ft;window.addEventListener('resize',function(){clearTimeout(ft);ft=setTimeout(fitCase,160);});
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fitCase);
  function podPause(){try{var a=window.trdPod&&window.trdPod.audio;if(a&&!a.paused)a.pause();}catch(e){}}
  /* The playlist tape turns into the same Duck Pod as the album: the pod shows this source (cover, track list,
     now playing, progress) and its wheel drives the Spotify player through the iFrame API. Track names come
     from a snapshot of the playlist (/assets/trd/playlist-trd.json); the Spotify player stays the sound source. */
  var POD=!!(window.trdPod&&window.trdPod.useSource),plList=null,queue=false,nearEnd=false,armed=false,wantPlay=false;
  function fmtLen(n){n=Math.max(0,Math.round(n||0));return Math.floor(n/60)+':'+('0'+n%60).slice(-2);}
  var PL={id:'playlist',name:'Personal Playlist',artist:'The Rubber Duck',cover:'/assets/trd/img/playlist-cover-192.jpg',
    intro:'Play the Playlist',sub:'The Rubber Duck on Spotify',tracks:[],i:0,playing:false,started:false,t:0,d:0,
    play:function(){podPause();if(!ctl){wantPlay=true;nudgeSpot();return;}try{ctl.resume();}catch(e){}},
    pause:function(){wantPlay=false;if(ctl){try{ctl.pause();}catch(e){}}},
    toggle:function(){if(PL.playing)PL.pause();else PL.play();},
    playIndex:function(i){var t=PL.tracks[i];if(!t||!t.uri)return PL.play();if(t.off)return;podPause();PL.i=i;PL.started=true;PL.t=0;PL.d=0;
      if(!ctl){wantPlay=true;nudgeSpot();podRefresh();return;}
      queue=true;nearEnd=false;armed=false;try{ctl.loadUri(t.uri);}catch(e){}
      var tries=0;(function kick(){try{ctl.play();}catch(e){}if(++tries<3)setTimeout(function(){if(!PL.playing&&queue)kick();},700);})();podRefresh();},
    next:function(){var n=PL.tracks.length;if(!n)return;for(var k=1;k<=n;k++){var j=(PL.i+k)%n;if(!PL.tracks[j].off)return PL.playIndex(j);}},
    prev:function(){var n=PL.tracks.length;if(!n)return;if(PL.t>3&&ctl){try{ctl.restart();}catch(e){}return;}
      for(var k=1;k<=n;k++){var j=(PL.i-k+n)%n;if(!PL.tracks[j].off)return PL.playIndex(j);}}};
  function podRefresh(){if(POD){try{window.trdPod.refresh();}catch(e){}}}
  function nudgeSpot(){if(spot&&narrow.matches){try{spot.scrollIntoView({behavior:rm.matches?'auto':'smooth',block:'center'});}catch(e){}}}
  function loadList(){
    if(plList){PL.tracks=plList;return;}
    fetch('/assets/trd/playlist-trd.json',{credentials:'same-origin'}).then(function(r){return r.ok?r.json():null;}).then(function(j){
      if(!j||!j.tracks)return;
      plList=j.tracks.map(function(t){return {title:t.t,artist:t.a,uri:'spotify:track:'+t.u,secs:t.s,len:fmtLen(t.s),off:!t.p};});
      if(mode==='pl'){PL.tracks=plList;if(POD)window.trdPod.useSource(PL);}
    }).catch(function(){});
  }
  function plUpdate(d){
    var was=PL.playing&&PL.t>PL.d-2;PL.playing=!d.isPaused;PL.t=(d.position||0)/1000;if(d.duration>0)PL.d=d.duration/1000;
    if(d.playingURI&&PL.tracks.length){for(var k=0;k<PL.tracks.length;k++){if(PL.tracks[k].uri===d.playingURI){PL.i=k;break;}}}
    if(PL.playing||PL.t>0)PL.started=true;
    /* a single track loaded from the pod ends on its own: carry on down the list, like the album does */
    if(PL.d>0&&PL.t>0.5&&PL.t<PL.d-2)armed=true;
    if(queue&&armed&&!nearEnd&&PL.d>0&&(PL.t>=PL.d-0.4||(d.isPaused&&PL.t===0&&was))){nearEnd=true;setTimeout(function(){if(queue&&nearEnd)PL.next();},350);}
    podRefresh();
  }
  function plReset(){PL.i=0;PL.playing=false;PL.started=false;PL.t=0;PL.d=0;queue=false;nearEnd=false;armed=false;wantPlay=false;}
  function setPlaying(on){spPlaying=on;deck.classList.toggle('is-playing',on);if(kpl)kpl.textContent=on?'Pause':'Press play';}
  /* Spotify: the official embed, created on demand; the iFrame API (if it loads) lets the deck keys and the
     site player pause it. Without the API the plain embed is used and is removed on swap. */
  function loadApi(cb){
    if(window.__trdSpApi)return cb(window.__trdSpApi);
    var done=false,t=setTimeout(function(){if(!done){done=true;cb(null);}},4500);
    window.onSpotifyIframeApiReady=function(api){window.__trdSpApi=api;if(!done){done=true;clearTimeout(t);cb(api);}};
    var sc=document.createElement('script');sc.src='https://open.spotify.com/embed/iframe-api/v1';sc.async=true;
    sc.onerror=function(){if(!done){done=true;clearTimeout(t);cb(null);}};document.head.appendChild(sc);
  }
  var narrow=window.matchMedia('(max-width:899px), (max-height:499px)');
  var PL_OPEN='https://open.spotify.com/playlist/4lWQJV4n3mnIvp0y4biUqZ',SL_BAR=30;
  /* in the deck window the player and the playlist link share the tape window: the compact 80px player on small screens */
  function spotH(){if(narrow.matches)return 152;var h=Math.round(well.clientHeight*.4048)-SL_BAR; /* PREVIEW: the Walkman's window, not the whole well */return h>=352?352:(h>=152?152:80);}
  function spotLink(){var a=document.createElement('a');a.className='deck-splink';a.href=PL_OPEN;a.target='_blank';a.rel='noopener';
    a.setAttribute('aria-label','Open the full playlist on Spotify (opens in a new tab)');
    a.innerHTML='<svg class="sl-sp" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>'+
      '<span class="sl-l">Open the full playlist on Spotify</span><span class="sl-s">Full playlist on Spotify</span><svg class="sl-go" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M14 3h7v7h-2.5V7.3l-8.6 8.6-1.8-1.8 8.6-8.6H14zM5 5h6v2.5H7.5v9h9V13H19v6H5z"/></svg>';
    a.addEventListener('click',function(e){e.stopPropagation();if(window.trdTrack)window.trdTrack('click/playlist-spotify','Homepage: open the full playlist on Spotify');});
    return a;}
  /* phones: the deck is too small for the player, so it sits full width right under the deck */
  function spotHome(el){if(narrow.matches){el.classList.add('is-below');deck.parentNode.insertBefore(el,deck.nextSibling);setTimeout(function(){try{el.scrollIntoView({behavior:rm.matches?'auto':'smooth',block:'center'});}catch(e){}},350);}else{el.classList.remove('is-below');well.appendChild(el);}}
  function mountSpot(){
    if(spot)return; spot=document.createElement('div');spot.className='deck-spot';
    plReset();loadList();if(POD)window.trdPod.useSource(PL);
    var h=spotH(); var host=document.createElement('div'); host.style.height=h+'px'; spot.appendChild(host); spot.appendChild(spotLink()); spotHome(spot);
    var mine=spot; setTimeout(function(){mine.classList.add('is-on');},3000);
    loadApi(function(api){
      if(spot!==mine)return;
      function plain(){if(spot!==mine)return;var old=spot.querySelector('iframe')||host;var f=document.createElement('iframe');
        f.src=PL_EMBED;f.width='100%';f.height=String(h);f.loading='lazy';f.title='The Rubber Duck Personal Playlist on Spotify';
        f.allow='autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture';if(old&&old.parentNode===spot)spot.replaceChild(f,old);else spot.insertBefore(f,spot.firstChild);
        f.addEventListener('load',function(){mine.classList.add('is-on');});setTimeout(function(){mine.classList.add('is-on');},1500);}
      if(!api)return plain();
      try{api.createController(host,{uri:PL_URI,width:'100%',height:h},function(c){
        if(spot!==mine){try{c.destroy();}catch(e){}return;}
        ctl=c;var f=spot.querySelector('iframe');if(f)f.title='The Rubber Duck Personal Playlist on Spotify';
        c.addListener('ready',function(){mine.classList.add('is-on');if(wantPlay){wantPlay=false;if(PL.started&&PL.tracks[PL.i])PL.playIndex(PL.i);else PL.play();}});setTimeout(function(){mine.classList.add('is-on');},2500);
        c.addListener('playback_update',function(e){var d=e&&e.data;if(!d)return;var on=!d.isPaused;setPlaying(on);if(on)podPause();plUpdate(d);});
      });}catch(e){plain();}
    });
  }
  function unmountSpot(){if(ctl){try{ctl.pause();}catch(e){}try{ctl.destroy();}catch(e){}}ctl=null;if(spot&&spot.parentNode)spot.parentNode.removeChild(spot);spot=null;setPlaying(false);
    plReset();if(POD)window.trdPod.dropSource(PL);}
  /* the swap itself: two fixed ghosts, one sliding out of the case into the deck, one ejecting from the deck into the case */
  function rect(el){var r=el.getBoundingClientRect(),t='none';try{t=getComputedStyle(el).transform||'none';}catch(e){}
    if(t!=='none'&&el.offsetWidth)return {l:r.left+(r.width-el.offsetWidth)/2,t:r.top+(r.height-el.offsetHeight)/2,w:el.offsetWidth,h:el.offsetHeight,tf:t};
    return {l:r.left,t:r.top,w:r.width,h:r.height};}
  function ghost(el,r){var g=el.cloneNode(true);g.removeAttribute('id');g.classList.add('cas-ghost');g.style.visibility='';
    g.style.left=r.l+'px';g.style.top=r.t+'px';g.style.width=r.w+'px';g.style.height=r.h+'px';document.body.appendChild(g);return g;}
  function paintCase(){var t=TAPE[mode==='rp'?'pl':'rp'];
    cs.classList.remove('tc-pl','tc-rp');cs.classList.add(t.cls);
    csCat.textContent=t.cat;csIc.src=t.ic;csN.textContent=t.n;csS.textContent=t.s;cs.setAttribute('aria-label',t.label);
    if(csFace)csFace.src=mode==='rp'?FACE.pl:FACE.rp;}
  function swap(){
    if(busy)return; busy=true; window.__trdTapeBusy=true; if(fine.matches)cs.setAttribute('data-noface','');
    if(window.__trdClearFace)window.__trdClearFace();
    var toPl=mode==='rp',inDeck=well.querySelector('.cas'),inCase=hold.querySelector('.cas');
    if(toPl)podPause(); else unmountSpot();
    var a0=rect(inDeck),c=rect(cs);
    well.insertBefore(inCase,well.firstChild); hold.appendChild(inDeck);
    mode=toPl?'pl':'rp'; paintMode();
    var b1=rect(inCase);
    /* the Walkman shows only part of the (cassette-sized) tape through its window: the ghosts start / end as that part */
    var wc='';try{wc=getComputedStyle(inCase).clipPath;}catch(e){} if(!wc||wc.indexOf('inset(')!==0)wc='';
    var z='inset(0% 0% 0% 0% round 0px)';
    function clip(list,first,last){if(!wc)return list;list.forEach(function(k,i){k.clipPath=(i===0&&first)||(i===list.length-1&&last)?wc:z;});return list;}
    function finish(){paintCase();cs.classList.remove('is-open');busy=false;window.__trdTapeBusy=false;if(mode==='pl')mountSpot();}
    if(rm.matches||!document.body.animate||!a0.w||!c.w){finish();return;}
    var gOut=ghost(inDeck,a0),gIn=ghost(inCase,c);inCase.style.visibility='hidden';
    cs.classList.add('is-open');
    var lift='0 0 0 2px #e3a82b,0 30px 50px -10px rgba(0,0,0,.85),0 0 30px rgba(255,200,110,.45)',rest='0 6px 16px rgba(0,0,0,.65)';
    function kf(r,o,tr,sh,op){return {left:r.l+'px',top:r.t+'px',width:r.w+'px',height:r.h+'px',offset:o,transform:tr,boxShadow:sh,opacity:op};}
    function mix(p,q,k,dy){return {l:p.l+(q.l-p.l)*k,t:p.t+(q.t-p.t)*k+(dy||0),w:p.w+(q.w-p.w)*k,h:p.h+(q.h-p.h)*k};}
    /* a cassette-shaped box sitting on the case: as tall as the tape would be if it stood just out of its case */
    var th=Math.min(c.h*2.1,a0.h*.62),tw=th*1.5737,at={l:c.l+c.w*.5-tw/2,t:c.t+c.h/2-th/2,w:tw,h:th};
    var up=Math.min(th*.9,90),above={l:at.l,t:at.t-(c.t>a0.t?up:-up*0)-(c.t>a0.t?0:0),w:tw,h:th};
    if(c.t>a0.t)above.t=at.t-up; else above.t=at.t+up*.2;
    var D=1350,E='cubic-bezier(.45,0,.2,1)';
    /* deck tape: eject up, fly over to the case, slide down into it */
    var A=gOut.animate(clip([
      kf(a0,0,a0.tf||'rotate(0)',rest,1),
      kf(mix(a0,a0,0,-a0.h*.24),.2,'rotate(-2deg)',lift,1),
      kf(mix(a0,above,.6,-24),.52,'rotate(3deg)',lift,1),
      kf(above,.72,'rotate(0)',lift,1),
      kf(at,.88,'rotate(0)',rest,1),
      kf(c,1,'rotate(0)',rest,0)],true,false),{duration:D,easing:E,fill:'forwards'});
    /* case tape: slide up out of its case, then over and down into the deck */
    gIn.animate(clip([
      kf(c,0,'rotate(0)',rest,0),
      kf(at,.14,'rotate(0)',rest,1),
      kf(above,.32,'rotate(-3deg)',lift,1),
      kf(mix(above,b1,.6,-28),.7,'rotate(-1.5deg)',lift,1),
      kf(mix(b1,b1,0,-b1.h*.06),.88,'rotate(0)',lift,1),
      kf(b1,1,b1.tf||'rotate(0)',rest,1)],false,true),{duration:D+150,easing:E,fill:'forwards'}).onfinish=function(){
      gOut.remove();gIn.remove();inCase.style.visibility='';finish();
      cs.classList.remove('is-take');void cs.offsetWidth;cs.classList.add('is-take');setTimeout(function(){cs.classList.remove('is-take');},600);};
    window.__trdSwapAnim=A;
  }
  function paintMode(){
    var pl=mode==='pl';
    deck.classList.toggle('is-pl',pl);
    if(pl){deck.removeAttribute('href');deck.classList.remove('is-live','is-playing');
      deck.setAttribute('aria-label','The Rubber Duck Personal Playlist is in the deck. The Spotify player is in the tape window');}
    else{deck.setAttribute('href',HREF);deck.setAttribute('aria-label',LABEL);
      try{document.dispatchEvent(new CustomEvent('trdpod:repaint'));}catch(e){}}
    if(deckFace)deckFace.src=pl?FACE.pl:FACE.rp;
    deck.setAttribute('data-tape',mode);
  }
  cs.addEventListener('click',function(e){if(e.defaultPrevented)return;e.preventDefault();
    if(window.trdTrack)window.trdTrack('click/tape-swap','Homepage: load '+(mode==='rp'?'Personal Playlist':'Red Pill Album'));swap();});
  /* deck keys while the playlist is in: play/pause and stop drive the Spotify player */
  deck.addEventListener('click',function(e){
    if(mode!=='pl')return; e.preventDefault();
    var k=e.target.closest&&e.target.closest('.key'); if(!k)return; if(!ctl&&!k.classList.contains('key-play'))return;
    if(k.classList.contains('key-play')){PL.toggle();}
    else if(k===deck.querySelector('.deck-keys .key:last-child')){PL.pause();}
  });
  /* the site player starts while the playlist is loaded: pause Spotify (or, without the API, put the Red Pill tape back) */
  document.addEventListener('trdpod:state',function(e){var st=e.detail;if(mode!=='pl'||!st||!st.playing||(st.src&&st.src!=='album'))return;
    if(ctl){try{ctl.pause();}catch(x){}setPlaying(false);}else if(spot){swap();}});
  window.__trdSwapTape=swap; window.__trdTapeMode=function(){return mode;};
})();
