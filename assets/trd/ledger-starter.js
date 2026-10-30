/* The Drop Ledger: the newcomer layer — ten starter buttons and their small panels.
   Every button just runs a normal ledger search, so nothing here can break the list. */
(function(){
  'use strict';
  var LX=window.TRDLedger, UI=window.TRDLedgerUI, box=document.getElementById('lxStart');
  if(!LX || !UI || !box) return;
  var panel=document.getElementById('lxPanel');
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function count(q){ try{ return LX.search(q).rows.length; }catch(e){ return 0; } }
  function nf(v){ return v.toLocaleString('en-US'); }
  function b(label,q,n){ return '<button type="button" class="chip lx-btn" data-lx-q="'+esc(q)+'">'+esc(label)+(n!=null?'<span class="lx-n">'+nf(n)+'</span>':'')+'</button>'; }

  var PHRASES=[['Future proves past','"future proves past"'],['Trust the plan','"trust the plan"'],['WWG1WGA','wwg1wga'],['Dark to light','"dark to light"'],['Nothing can stop what is coming','"nothing can stop what is coming"'],['The Great Awakening','"great awakening"']];
  var TOPICS=[['Hillary / HRC','hillary'],['Obama / Hussein','obama'],['Trump / POTUS','trump'],['FBI & DOJ','fbi | doj'],['Media / Fake news','msm | "media"'],['Elections','elect | vote'],['Russia / Mueller','russia | mueller'],['Patriots','patriot'],
              ['Military','military'],['China','china'],['North Korea','nk'],['Iran','iran'],['Epstein','epstein'],['Soros','soros'],['God','"god"'],['Memes','meme']];
  var YEARS=[2017,2018,2019,2020,2022];

  var BUILD={
    what:function(){
      return '<h3>New words, explained</h3>'+
        '<p><b>Drop:</b> a post made by the Q team on the Q boards. Each numbered post is one drop.</p>'+
        '<p>There are 4,966 of them, from 28 Oct 2017 to 27 Nov 2022 &mdash; first on 4chan, then 8chan, then 8kun (after 8chan went offline in August 2019). Readers called themselves <b>anons</b> and treated each drop as a clue, or <b>crumb</b>.</p>'+
        '<p><b>Delta:</b> a drop anniversary. Each year, anons look at the drops posted on this same date in the past (2017 to 2022) and ask whether they matter today. &ldquo;Future proves past.&rdquo;</p>'+
        '<p><b>Proof:</b> a Delta becomes a proof when a drop from the past comes true in real life on its anniversary date.</p>'+
        '<p><b>Q Proof:</b> a Q drop that Donald Trump (Q+) has confirmed publicly.</p>'+
        '<p class="lx-row">'+b('Show me 7 to start','@start')+b('Today\u2019s Deltas','today')+'<a class="lx-link" href="Qdrops/index.html">More about the drops &rarr;</a></p>';
    },
    phrases:function(){
      return '<h3>Famous phrases</h3><p>The lines people have heard of. Each one finds that exact phrase.</p><div class="lx-chips">'+
        PHRASES.map(function(p){ return b(p[0],p[1],count(p[1])); }).join('')+'</div>';
    },
    years:function(){
      return '<h3>Pick a year</h3><p>There are no drops in 2021 &mdash; Q went quiet from Dec 2020 to Jun 2022.</p><div class="lx-chips">'+
        YEARS.map(function(y){ return b(String(y),String(y),count(String(y))); }).join('')+'</div>';
    },
    topics:function(){
      var h='<h3>Pick a topic</h3><p>Each topic also finds the nicknames Q used (HRC, Hussein, POTUS&hellip;).</p><div class="lx-chips">';
      TOPICS.forEach(function(t,i){ h+=(i===8?'<span class="lx-more" hidden>':'')+b(t[0],t[1],count(t[1])); });
      return h+'</span><button type="button" class="chip lx-btn lx-moreb" data-lx-more="1" aria-expanded="false">More topics</button></div>';
    },
    day:function(){
      var t=LX.today(), v=t.y+'-'+('0'+t.m).slice(-2)+'-'+('0'+t.d).slice(-2);
      return '<h3>On this day</h3><p>Pick any date &mdash; a birthday, an anniversary &mdash; to see what was posted on that day of the year, in every year.</p>'+
        '<p class="lx-row"><label class="lx-date"><span>Date</span><input type="date" id="lxDay" value="'+v+'"></label>'+
        '<button type="button" class="chip lx-btn lx-primary" id="lxDayGo">Show that day</button></p>';
    },
    how:function(){
      return '<h3>How to search</h3><ul class="lx-tips">'+
        '<li>Type a <b>word</b> or two: <code>storm trump</code> finds drops with both.</li>'+
        '<li>Type a <b>date</b> any way you like: <code>10/24</code>, <code>Oct 2018</code>, <code>October 22, 2020</code>, <code>2019</code>, <code>Oct 2019 - Dec 2019</code>, or <code>today</code>.</li>'+
        '<li>Type a <b>number</b> like <code>#1024</code> to open that drop.</li>'+
        '<li>Use <b>&ldquo;quotes&rdquo;</b> for an exact phrase, <code>|</code> or <code>OR</code> for either word, and <code>-word</code> to leave a word out.</li>'+
        '<li>All dates are US Eastern time, the same as the drop pages.</li></ul>';
    }
  };
  var open=null;
  function setOpen(name){
    open=(open===name)?null:name;
    [].slice.call(box.querySelectorAll('[data-lx-panel]')).forEach(function(x){ x.setAttribute('aria-expanded', x.getAttribute('data-lx-panel')===open?'true':'false'); });
    if(!open){ panel.hidden=true; panel.innerHTML=''; return; }
    panel.innerHTML=BUILD[open]()+'<button type="button" class="lx-close" aria-label="Close">&times;</button>';
    panel.hidden=false;
    var go=document.getElementById('lxDayGo');
    if(go) go.addEventListener('click',function(){
      var v=(document.getElementById('lxDay').value||'').split('-');
      if(v.length===3) UI.setQuery(LX.MON[parseInt(v[1],10)-1]+' '+parseInt(v[2],10),{scroll:true});
    });
  }
  box.addEventListener('click',function(e){
    var p=e.target.closest('[data-lx-panel]'); if(p){ setOpen(p.getAttribute('data-lx-panel')); return; }
    if(e.target.closest('.lx-close')){ setOpen(open); return; }
    var m=e.target.closest('[data-lx-more]');
    if(m){ var more=panel.querySelector('.lx-more'); var shown=more.hidden; more.hidden=!shown; m.setAttribute('aria-expanded',shown?'true':'false'); m.textContent=shown?'Fewer topics':'More topics'; return; }
    if(e.target.closest('[data-lx-random]')){
      var R=LX.records().filter(function(r){ return r.len>=40; });
      var r=R[Math.floor(Math.random()*R.length)];
      UI.setQuery('#'+r.n,{scroll:true});
    }
  });
})();
