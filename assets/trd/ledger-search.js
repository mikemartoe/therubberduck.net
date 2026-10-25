/* The Drop Ledger: search engine (dates first, then drop numbers, then words).
   Pure logic, no DOM. Reads window.QDROPS ([n, unixTs, site, board, url, text]).
   All calendar dates are US Eastern (America/New_York), the same as the /drops/<n>/ pages.
   The raw timestamps are Unix epoch seconds (UTC, zone-free), so Eastern is an exact conversion. */
(function(root){
  'use strict';
  var MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var MONF=['January','February','March','April','May','June','July','August','September','October','November','December'];
  var MONIDX={jan:1,january:1,feb:2,february:2,mar:3,march:3,apr:4,april:4,may:5,jun:6,june:6,jul:7,july:7,aug:8,august:8,sep:9,sept:9,september:9,oct:10,october:10,nov:11,november:11,dec:12,december:12};
  function pad2(v){ return (v<10?'0':'')+v; }

  /* ---------- Eastern time without Intl: US rule since 2007 ---------- */
  function nthSunday(y,m,nth){ /* m 1-12, returns day of month */
    var dow=new Date(Date.UTC(y,m-1,1)).getUTCDay(); var first=1+((7-dow)%7); return first+7*(nth-1);
  }
  function etOffsetHours(ts){ /* ts seconds UTC; returns -4 or -5 */
    var y=new Date(ts*1000).getUTCFullYear();
    var start=Date.UTC(y,2,nthSunday(y,3,2),7)/1000;  /* 2:00 EST = 07:00 UTC */
    var end=Date.UTC(y,10,nthSunday(y,11,1),6)/1000;  /* 2:00 EDT = 06:00 UTC */
    return (ts>=start && ts<end) ? -4 : -5;
  }
  function etParts(ts){
    var off=etOffsetHours(ts), x=new Date((ts+off*3600)*1000);
    return {y:x.getUTCFullYear(), m:x.getUTCMonth()+1, d:x.getUTCDate(), H:x.getUTCHours(), M:x.getUTCMinutes(), S:x.getUTCSeconds(), off:off};
  }
  function fmtTime(p){ var h=p.H%12||12; return h+':'+pad2(p.M)+' '+(p.H<12?'AM':'PM')+' '+(p.off===-4?'EDT':'EST'); }
  function dayKey(y,m,d){ return y*10000+m*100+d; }
  function fmtDay(y,m,d){ return d+' '+MON[m-1]+' '+y; }
  function fmtMD(m,d){ return MON[m-1]+' '+d; }
  function daysIn(y,m){ return new Date(Date.UTC(y,m,0)).getUTCDate(); }
  function validYMD(y,m,d){ return m>=1&&m<=12&&d>=1&&d<=daysIn(y||2020,m); }

  /* ---------- text normalisation ---------- */
  function norm(s){
    s=String(s||'').toLowerCase();
    if(s.normalize) s=s.normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    return s.replace(/[\u2018\u2019\u201B\u2032`´]/g,"'").replace(/[\u201C\u201D\u201E\u2033]/g,'"').replace(/[\u2013\u2014]/g,'-');
  }
  function tokens(s){ return norm(s).replace(/'/g,'').match(/[a-z0-9]+/g)||[]; }

  /* ---------- the index ---------- */
  var R=[], BYN={}, VOCAB=null, DAYCOUNT={}, MDCOUNT={}, FIRST=null, LAST=null;
  function build(raw){
    R=(raw||[]).map(function(r){
      var p=etParts(r[1]), text=r[5]||'';
      var low=norm(text);
      var toks=tokens(text), btok=tokens(r[2]+' '+r[3]);
      var rec={n:r[0], t:r[1], y:p.y, m:p.m, d:p.d, key:dayKey(p.y,p.m,p.d), d_iso:p.y+'-'+pad2(p.m)+'-'+pad2(p.d), time:fmtTime(p),
               b:r[2], bd:r[3], l:r[4], e:text, low:low, flat:low.replace(/'/g,''), tok:toks, btok:btok, tokset:null, len:text.replace(/\s+/g,' ').trim().length};
      return rec;
    }).sort(function(a,b){return a.n-b.n;});
    BYN={}; DAYCOUNT={}; MDCOUNT={};
    R.forEach(function(r){ BYN[r.n]=r; DAYCOUNT[r.key]=(DAYCOUNT[r.key]||0)+1; var md=r.m*100+r.d; MDCOUNT[md]=MDCOUNT[md]||{}; MDCOUNT[md][r.y]=(MDCOUNT[md][r.y]||0)+1; });
    FIRST=R[0]; LAST=R[R.length-1]; VOCAB=null;
    return R;
  }
  function vocab(){
    if(VOCAB) return VOCAB; var s={}; R.forEach(function(r){ r.tok.forEach(function(t){ s[t]=1; }); r.btok.forEach(function(t){ s[t]=1; }); }); VOCAB=Object.keys(s); return VOCAB;
  }
  /* Eastern-dated stats for the heatmap (replaces the UTC-built window.QSTATS.daily/monthly). */
  function etStats(){
    var daily={}, monthly={};
    R.forEach(function(r){ daily[r.d_iso]=(daily[r.d_iso]||0)+1; var mk=r.d_iso.slice(0,7); monthly[mk]=(monthly[mk]||0)+1; });
    return {daily:daily, monthly:monthly, days:Object.keys(daily).length};
  }

  /* ---------- date parsing ---------- */
  function yr(s){ /* '2019' | '19' | "'19" */
    s=String(s).replace(/^'/,''); var v=parseInt(s,10); if(isNaN(v)) return null;
    if(s.length===2) return 2000+v; if(s.length===4) return v; return null;
  }
  /* Parse ONE date-ish phrase. Returns {y,m,d} with any part null, or null when it is not a date. */
  function parseOne(s){
    s=norm(s).trim().replace(/,/g,' ').replace(/\s+/g,' ').replace(/(\d)(st|nd|rd|th)\b/g,'$1').replace(/\bof\b/g,' ').replace(/\s+/g,' ').trim();
    if(!s) return null; var m;
    if((m=s.match(/^(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})$/))){ var a={y:+m[1],m:+m[2],d:+m[3]}; return validYMD(a.y,a.m,a.d)?a:null; }
    if((m=s.match(/^(\d{4})(\d{2})(\d{2})$/)) && +m[1]>=1990 && +m[1]<=2099){ var b={y:+m[1],m:+m[2],d:+m[3]}; return validYMD(b.y,b.m,b.d)?b:null; }
    if((m=s.match(/^(\d{1,2})[-\/.](\d{1,2})[-\/.]('?\d{2}|\d{4})$/))){
      var p1=+m[1], p2=+m[2], y=yr(m[3]); var mm=p1, dd=p2; if(p1>12&&p2<=12){ mm=p2; dd=p1; }
      return validYMD(y,mm,dd)?{y:y,m:mm,d:dd}:null;
    }
    if((m=s.match(/^(\d{4})[-\/.](\d{1,2})$/)) && +m[2]>=1 && +m[2]<=12) return {y:+m[1],m:+m[2],d:null};
    if((m=s.match(/^(\d{1,2})[-\/.](\d{4})$/)) && +m[1]>=1 && +m[1]<=12) return {y:+m[2],m:+m[1],d:null};
    if((m=s.match(/^(\d{1,2})[\/.\-](\d{1,2})$/))){
      var q1=+m[1], q2=+m[2], m3=q1, d3=q2; if(q1>12&&q2<=12){ m3=q2; d3=q1; }
      return validYMD(2020,m3,d3)?{y:null,m:m3,d:d3}:null;
    }
    /* words: month name with optional day and year, in any order */
    var parts=s.split(' '), mon=null, day=null, year=null, bad=false;
    parts.forEach(function(t){
      var t2=t.replace(/\.$/,'');
      if(MONIDX[t2] && mon===null) mon=MONIDX[t2];
      else if(/^'\d{2}$/.test(t2) || /^\d{4}$/.test(t2)){ if(year===null) year=yr(t2); else bad=true; }
      else if(/^\d{1,2}$/.test(t2)){ if(day===null) day=+t2; else if(year===null && mon!==null) year=yr(t2); else bad=true; }
      else bad=true;
    });
    if(bad || mon===null) return null;
    if(day===null && year===null) return null;            /* a lone month word ("may", "march") stays a word */
    if(day!==null && !validYMD(year||2020,mon,day)) return null;
    return {y:year, m:mon, d:day};
  }
  function isYear(s){ return /^(19|20)\d{2}$/.test(s); }
  function startKey(o){ return dayKey(o.y, o.m||1, o.d||1); }
  function endKey(o){ var m=o.m||12; return dayKey(o.y, m, o.d||daysIn(o.y,m)); }

  /* Try to read the whole query as a date filter. Returns a filter object or null. */
  function parseDateQuery(q){
    var s=norm(q).trim();
    if(!s) return null;
    /* spread: "today ±3", "10/24 +-3", "oct 24 +/- 3 days" */
    var spread=0, sm=s.match(/\s*(?:±|\+\/?-|\+-)\s*(\d{1,2})\s*(?:days?)?$/);
    if(sm){ spread=Math.min(15,+sm[1]); s=s.slice(0,sm.index).trim(); }
    /* deltas */
    var dm=s.match(/^(?:(today|yesterday|tomorrow)(?:'?s)?(?:\s+deltas?)?|deltas?|(?:on\s+)?this\s+day)$/);
    if(dm){ return {kind:'delta', which:(dm[1]||'today'), spread:spread}; }
    /* ranges */
    var rm=s.match(/^(?:from\s+)?(.+?)\s*(?:\s-\s|\s?[\u2013\u2014]\s?|\s+to\s+|\s+through\s+|\s+thru\s+|\s+until\s+)\s*(.+)$/);
    if(rm){
      var A=parseOne(rm[1]) || (isYear(rm[1].trim())?{y:+rm[1].trim(),m:null,d:null}:null);
      var B=parseOne(rm[2]) || (isYear(rm[2].trim())?{y:+rm[2].trim(),m:null,d:null}:null);
      if(!A && /^[a-z]+\.?$/.test(rm[1].trim()) && MONIDX[rm[1].trim().replace(/\.$/,'')]) A={y:null,m:MONIDX[rm[1].trim().replace(/\.$/,'')],d:null};
      if(A && B){
        if(A.y==null) A.y=B.y; if(B.y==null) B.y=A.y;
        if(A.y!=null && B.y!=null){
          var k1=startKey(A), k2=endKey(B); if(k2<k1){ var t=k1; k1=startKey(B); k2=endKey(A); }
          return {kind:'range', from:k1, to:k2, A:A, B:B};
        }
      }
    }
    if(isYear(s)) return {kind:'year', y:+s};
    /* tight ranges with a bare hyphen or dash: "10/1/2018-11/30/2018", "2018-10-01-2018-11-30" */
    for(var i=1;i<s.length-1;i++){
      if(s.charAt(i)!=='-') continue;
      var L1=parseOne(s.slice(0,i)), L2=parseOne(s.slice(i+1));
      if(L1 && L2 && L1.y!=null && L2.y!=null && L1.m!=null && L2.m!=null){
        var j1=startKey(L1), j2=endKey(L2); if(j2<j1){ j1=startKey(L2); j2=endKey(L1); }
        return {kind:'range', from:j1, to:j2, A:L1, B:L2};
      }
    }
    var o=parseOne(s);
    if(!o) return null;
    if(o.y!=null && o.m!=null && o.d!=null) return {kind:'day', y:o.y, m:o.m, d:o.d, spread:spread};
    if(o.y==null && o.m!=null && o.d!=null) return {kind:'md', m:o.m, d:o.d, spread:spread};
    if(o.y!=null && o.m!=null) return {kind:'month', y:o.y, m:o.m};
    return null;
  }

  /* ---------- drop numbers ---------- */
  function parseNumber(q){
    var s=norm(q).trim().replace(/\s+/g,' ');
    var m=s.match(/^(?:#|q\s?|>>|drop\s*#?\s*|no\.?\s*|number\s*)?(\d{1,9})$/);
    return m ? parseInt(m[1],10) : null;
  }

  /* ---------- words ---------- */
  var SYN=[
    ['hillary','hrc','clinton','clintons'],
    ['obama','hussein','bho'],
    ['trump','potus','djt'],
    ['nk','north korea','kim jong'],
    ['deep state','[ds]'],
    ['fbi','federal bureau'],
    ['wwg1wga','where we go one'],
    ['msm','fake news','mainstream media'],
    ['doj','department of justice'],
    ['ss','secret service'],
    ['ag','attorney general'],
    ['sc','supreme court']
  ];
  var SYNMAP={}; SYN.forEach(function(g){ g.forEach(function(w){ SYNMAP[w]=g; }); });
  var STOP={the:1,a:1,an:1,of:1,and:1,to:1,in:1,is:1,on:1,for:1,at:1,by:1};

  /* Split a text query into OR-groups of AND-terms. */
  function parseText(q){
    var s=norm(q).replace(/&&/g,' ').replace(/\s+AND\s+/g,' ');
    var groups=[[]], re=/(-?)"([^"]+)"|(\|)|(\S+)/g, m;
    var raw=String(q);
    while((m=re.exec(s))){
      if(m[3]){ groups.push([]); continue; }
      var neg=!!m[1], phrase=m[2];
      var w=m[4];
      if(w!==undefined){
        if(w==='or'){ groups.push([]); continue; }
        if(w==='and') continue;
        if(w.charAt(0)==='-' && w.length>1){ neg=true; w=w.slice(1); }
        groups[groups.length-1].push({w:w, neg:neg, phrase:false});
      } else groups[groups.length-1].push({w:phrase, neg:neg, phrase:true});
    }
    return groups.filter(function(g){ return g.length; });
  }
  function termAlts(t, useSyn){
    var w=t.w.trim(); var alts=[w];
    if(useSyn && !t.neg){
      var g=SYNMAP[w] || SYNMAP[tokens(w).join(' ')];
      if(g) alts=g.slice();
    }
    return alts;
  }
  /* Does one alternative match one record? */
  function altMatch(r, a, exact){
    if(/[^a-z0-9' ]/.test(a)){                           /* punctuation inside ("5:5", "q+", "[ds]") → raw substring */
      return r.low.indexOf(a)>-1;
    }
    var tk=tokens(a);
    if(!tk.length) return true;
    if(tk.length>1){                                     /* phrase: consecutive tokens, last one may be a prefix */
      var t=r.tok;
      for(var i=0;i+tk.length<=t.length;i++){
        var ok=true;
        for(var j=0;j<tk.length;j++){
          var last=(j===tk.length-1);
          if(last ? t[i+j].indexOf(tk[j])!==0 : t[i+j]!==tk[j]){ ok=false; break; }
        }
        if(ok) return true;
      }
      return false;
    }
    var w=tk[0];
    if(r.btok.indexOf(w)>-1) return true;                /* board and site names: "8kun", "qresearch" */
    if(w.length<=2 || exact){ if(!r.tokset){ r.tokset={}; r.tok.forEach(function(x){ r.tokset[x]=1; }); } return !!r.tokset[w]; }
    for(var k=0;k<r.tok.length;k++){ if(r.tok[k].indexOf(w)===0) return true; }
    return false;
  }
  function textFilter(pool, groups, useSyn, used){
    var compiled=groups.map(function(g){
      return g.filter(function(t){ return !(STOP[t.w] && !t.phrase && g.length>1); }).map(function(t){
        var alts=termAlts(t,useSyn); if(alts.length>1 && used) used.push({w:t.w, alts:alts.filter(function(x){return x!==t.w;})});
        return {neg:t.neg, alts:alts, exact:t.phrase};
      });
    });
    return pool.filter(function(r){
      return compiled.some(function(g){
        if(!g.length) return false;
        return g.every(function(t){
          var hit=t.alts.some(function(a){ return altMatch(r,a,t.exact); });
          return t.neg ? !hit : hit;
        });
      });
    });
  }
  /* Optimal-string-alignment distance, capped. */
  function osa(a,b,cap){
    if(Math.abs(a.length-b.length)>cap) return cap+1;
    var d=[],i,j; for(i=0;i<=a.length;i++){ d[i]=[i]; } for(j=0;j<=b.length;j++) d[0][j]=j;
    for(i=1;i<=a.length;i++){ var rowMin=99; for(j=1;j<=b.length;j++){
      var c=a[i-1]===b[j-1]?0:1;
      d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+c);
      if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1]) d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1);
      if(d[i][j]<rowMin) rowMin=d[i][j]; }
      if(rowMin>cap) return cap+1; }
    return d[a.length][b.length];
  }
  function fuzzyGroups(groups){
    var V=vocab(), changed=[];
    var out=groups.map(function(g){ return g.map(function(t){
      if(t.neg || t.phrase || /[^a-z0-9]/.test(t.w) || t.w.length<5) return t;
      var cap=t.w.length>=10?2:1, best=[];
      for(var i=0;i<V.length;i++){ var v=V[i]; if(v===t.w) return t; if(Math.abs(v.length-t.w.length)<=cap && osa(t.w,v,cap)<=cap) best.push(v); }
      if(!best.length) return t;
      best=best.slice(0,6); changed.push({w:t.w, alts:best});
      return {w:t.w, neg:false, phrase:false, fuzzy:best};
    }); });
    return {groups:out, changed:changed};
  }
  function textFilterFuzzy(pool, fg){
    return pool.filter(function(r){
      return fg.some(function(g){ return g.every(function(t){
        var hit = t.fuzzy ? t.fuzzy.some(function(a){ return r.tokset ? !!r.tokset[a] : (r.tok.indexOf(a)>-1); }) : textFilter([r],[[t]],true).length>0;
        return t.neg ? !hit : hit; }); });
    });
  }

  /* ---------- calendar helpers ---------- */
  function addDays(y,m,d,n){ var x=new Date(Date.UTC(y,m-1,d+n)); return {y:x.getUTCFullYear(), m:x.getUTCMonth()+1, d:x.getUTCDate()}; }
  function mdSet(m,d,spread){ var s={}; for(var i=-spread;i<=spread;i++){ var x=addDays(2020,m,d,i); s[x.m*100+x.d]=1; } return s; }
  /* Nearest month-days (any year) that have drops, looking back and forward around the calendar. */
  function nearestMD(m,d){
    var res={before:null, after:null};
    for(var i=1;i<=183&&(!res.before||!res.after);i++){
      if(!res.after){ var a=addDays(2020,m,d,i); if(MDCOUNT[a.m*100+a.d]) res.after={m:a.m,d:a.d,years:MDCOUNT[a.m*100+a.d]}; }
      if(!res.before){ var b=addDays(2020,m,d,-i); if(MDCOUNT[b.m*100+b.d]) res.before={m:b.m,d:b.d,years:MDCOUNT[b.m*100+b.d]}; }
    }
    return res;
  }
  function numberDeltas(m,d){
    var out=[], seen={};
    [m*100+d, d*100+m].forEach(function(n){ if(!seen[n] && BYN[n]){ seen[n]=1; out.push(BYN[n]); } });
    return out;
  }
  var GAPS=[
    {from:20190801, to:20191102, why:'8chan was offline'},
    {from:20201208, to:20220624, why:'Q’s long silence'},
    {from:20220629, to:20221106, why:'a quiet stretch'},
    {from:20181009, to:20181101, why:'a quiet stretch before the 2018 midterms'}
  ];
  function keyToStr(k){ var y=Math.floor(k/10000), m=Math.floor(k/100)%100, d=k%100; return fmtDay(y,m,d); }
  function gapMessage(k1,k2){
    if(!R.length) return '';
    if(k2<FIRST.key) return 'The run begins on '+fmtDay(FIRST.y,FIRST.m,FIRST.d)+' with drop #1 — nothing is earlier.';
    if(k1>LAST.key) return 'The run ends on '+fmtDay(LAST.y,LAST.m,LAST.d)+' with drop #'+LAST.n+' — nothing is later.';
    var before=null, after=null;
    for(var i=0;i<R.length;i++){ if(R[i].key<k1) before=R[i]; else if(R[i].key>k2){ after=R[i]; break; } }
    var why=''; GAPS.forEach(function(g){ if(k1>=g.from && k2<=g.to) why=g.why; });
    var msg='Q posted nothing in that stretch';
    if(before && after) msg='Q posted nothing between '+fmtDay(before.y,before.m,before.d)+' and '+fmtDay(after.y,after.m,after.d)+(why?' ('+why+')':'')+'.';
    return {text:msg, before:before, after:after};
  }

  /* ---------- curated lists ---------- */
  /* One plain line per drop, shown on each Start-here card. Checked against data/drops.js (US Eastern dates). */
  var START=[
    {n:1,    c:'The very first post, Oct 28, 2017'},
    {n:134,  c:'The first time “Dark to light” appears'},
    {n:225,  c:'The first “Future proves past”'},
    {n:513,  c:'The first “Where we go one, we go all” (WWG1WGA)'},
    {n:668,  c:'The first “Trust the plan”'},
    {n:4953, c:'The last post before the 18-month silence'},
    {n:4966, c:'The final drop, Nov 27, 2022'}
  ];

  /* ---------- the main entry ---------- */
  function today(now){ var x=now||new Date(); return {y:x.getFullYear(), m:x.getMonth()+1, d:x.getDate()}; }
  function search(q, opts){
    opts=opts||{}; q=String(q||'');
    var raw=q.trim(), info={q:raw, kind:'all', rows:R, label:'', note:'', nearest:null, numberDeltas:null, alt:null, used:[], fuzzy:null, captions:null, order:null, jump:null, empty:null};
    if(!raw) return info;
    var lowq=norm(raw).trim();

    /* special lists */
    if(lowq==='@start'){
      info.kind='start'; info.order='list'; info.captions={};
      info.rows=START.map(function(s){ info.captions[s.n]=s.c; return BYN[s.n]; }).filter(Boolean);
      info.label='Start here — seven drops that show what the run is like, oldest first.'; return info;
    }
    if(lowq==='@short'){
      info.kind='short'; info.order='list';
      info.rows=R.filter(function(r){ return r.len>=8 && !/^https?:\/\/\S+\s*q?$/i.test(r.e.trim()); }).slice().sort(function(a,b){ return a.len-b.len||a.n-b.n; }).slice(0,50);
      info.label='The 50 shortest drops — quick one-liners, shortest first.'; return info;
    }

    /* 1–2. dates (before numbers) */
    var dq=opts.asText ? null : parseDateQuery(raw);
    if(dq){
      var pool, label, empty=null;
      if(dq.kind==='delta'){
        var t=today(opts.now), shift=dq.which==='yesterday'?-1:dq.which==='tomorrow'?1:0, x=addDays(t.y,t.m,t.d,shift);
        dq={kind:'md', m:x.m, d:x.d, spread:dq.spread, which:dq.which};
      }
      if(dq.kind==='md'){
        var set=mdSet(dq.m,dq.d,dq.spread||0);
        pool=R.filter(function(r){ return set[r.m*100+r.d]; });
        var name=dq.which ? (dq.which.charAt(0).toUpperCase()+dq.which.slice(1)+'’s Deltas — ') : 'Deltas — ';
        var yrs={}; pool.forEach(function(r){ yrs[r.y]=(yrs[r.y]||0)+1; });
        var ys=Object.keys(yrs).map(function(y){ return y+' ('+yrs[y]+')'; }).join(' · ');
        label=name+'drops posted on '+fmtMD(dq.m,dq.d)+(dq.spread?' ± '+dq.spread+' days':'')+', every year'+(ys?': '+ys:'')+'.';
        info.kind='delta'; info.md={m:dq.m,d:dq.d,which:dq.which||null,spread:dq.spread||0};
        info.numberDeltas=numberDeltas(dq.m,dq.d);
        if(!pool.length){ info.nearest=nearestMD(dq.m,dq.d); empty='No drops were posted on '+fmtMD(dq.m,dq.d)+(dq.spread?' ± '+dq.spread+' days':'')+' in any year.'; }
        info.order='date';
      } else if(dq.kind==='day'){
        var sp=dq.spread||0, lo=addDays(dq.y,dq.m,dq.d,-sp), hi=addDays(dq.y,dq.m,dq.d,sp), k1=dayKey(lo.y,lo.m,lo.d), k2=dayKey(hi.y,hi.m,hi.d);
        pool=R.filter(function(r){ return r.key>=k1 && r.key<=k2; });
        label='Drops posted on '+fmtDay(dq.y,dq.m,dq.d)+(sp?' ± '+sp+' days':'')+' (Eastern time).';
        info.kind='date'; info.md={m:dq.m,d:dq.d,y:dq.y};
        if(!pool.length){ var g=gapMessage(k1,k2); empty=g.text||g; info.gap=g; }
      } else if(dq.kind==='month'){
        pool=R.filter(function(r){ return r.y===dq.y && r.m===dq.m; });
        label='Drops posted in '+MONF[dq.m-1]+' '+dq.y+'.';
        info.kind='month';
        if(!pool.length){ var g2=gapMessage(dayKey(dq.y,dq.m,1),dayKey(dq.y,dq.m,daysIn(dq.y,dq.m))); empty=g2.text||g2; info.gap=g2; }
      } else if(dq.kind==='year'){
        pool=R.filter(function(r){ return r.y===dq.y; });
        label='Drops posted in '+dq.y+'.';
        info.kind='year';
        if(BYN[dq.y]) info.alt={label:'Did you mean drop #'+dq.y+'?', q:'#'+dq.y};
        if(!pool.length){ var g3=gapMessage(dayKey(dq.y,1,1),dayKey(dq.y,12,31)); empty=g3.text||g3; info.gap=g3; }
      } else if(dq.kind==='range'){
        pool=R.filter(function(r){ return r.key>=dq.from && r.key<=dq.to; });
        label='Drops posted from '+keyToStr(dq.from)+' to '+keyToStr(dq.to)+'.';
        info.kind='range';
        if(!pool.length){ var g4=gapMessage(dq.from,dq.to); empty=g4.text||g4; info.gap=g4; }
      }
      info.rows=pool; info.label=label; info.empty=empty; info.date=dq;
      return info;
    }

    /* 3. drop numbers */
    var n=opts.asText ? null : parseNumber(raw);
    if(n!==null){
      info.kind='number'; info.jump=n;
      if(BYN[n]){ info.rows=[BYN[n]]; info.label='Drop #'+n+'.'; }
      else { info.rows=[]; info.label='No drop #'+n+'.'; info.empty='The ledger runs from #1 to #'+LAST.n.toLocaleString('en-US')+' — there is no drop #'+n+'.'; info.alt={label:'Show #'+(n>LAST.n?LAST.n:1), q:'#'+(n>LAST.n?LAST.n:1)}; }
      return info;
    }

    /* 4. mixed: a date phrase at the end/start plus words ("HRC Oct 2018", "storm 2018") */
    var pool2=R, prefix='';
    if(!opts.asText){
      var w=raw.split(/\s+/);
      for(var cut=Math.min(4,w.length-1); cut>=1; cut--){
        var tail=w.slice(w.length-cut).join(' '), head=w.slice(0,w.length-cut).join(' ');
        var dt=parseDateQuery(tail);
        if(dt && dt.kind!=='delta'){ var sub=search(tail,opts); pool2=sub.rows; prefix=sub.label.replace(/\.$/,'')+' · '; raw=head; info.date=dt; break; }
        var hd=w.slice(0,cut).join(' '), rest=w.slice(cut).join(' ');
        var dh=parseDateQuery(hd);
        if(dh && dh.kind!=='delta'){ var sub2=search(hd,opts); pool2=sub2.rows; prefix=sub2.label.replace(/\.$/,'')+' · '; raw=rest; info.date=dh; break; }
      }
    }

    /* 5. words */
    var groups=parseText(raw), used=[];
    var rows=textFilter(pool2, groups, !opts.noSyn, used);
    info.kind='text'; info.used=used;
    if(!rows.length){
      var fg=fuzzyGroups(groups);
      if(fg.changed.length){ rows=textFilterFuzzy(pool2, fg.groups); if(rows.length) info.fuzzy=fg.changed; }
    }
    info.rows=rows;
    var shown=groups.map(function(g){ return g.map(function(t){ return (t.neg?'not ':'')+'“'+t.w+'”'; }).join(' + '); }).join(' or ');
    var shownSyn=groups.map(function(g){ return g.map(function(t){
      var a=opts.noSyn?[t.w]:termAlts(t,true), more=a.filter(function(x){return x!==t.w.trim();});
      return (t.neg?'not ':'')+'“'+t.w+'”'+(more.length?' (or '+more.join(', ')+')':''); }).join(' + '); }).join(' or ');
    info.label=prefix+'Drops containing '+shownSyn+'.';
    if(info.fuzzy) info.label=prefix+'No exact match — showing close spellings: '+info.fuzzy.map(function(f){return f.alts.join(', ');}).join('; ')+'.';
    if(!rows.length) info.empty='No drop uses '+shown+(prefix?' in that period':'')+'.';
    return info;
  }

  var API={build:build, search:search, etParts:etParts, etStats:etStats, parseDateQuery:parseDateQuery, parseNumber:parseNumber,
           nearestMD:nearestMD, numberDeltas:numberDeltas, fmtDay:fmtDay, fmtMD:fmtMD, today:today, addDays:addDays,
           START:START, SYN:SYN, records:function(){ return R; }, byN:function(n){ return BYN[n]; }, MON:MON, MONF:MONF};
  root.TRDLedger=API;
  /* Build at once and re-date the heatmap stats to Eastern, so the calendar matches the list and the drop pages. */
  if(root.QDROPS){
    build(root.QDROPS);
    try{ var st=etStats(); if(root.QSTATS){ root.QSTATS.daily=st.daily; root.QSTATS.monthly=st.monthly; root.QSTATS.days=st.days; } }catch(e){}
  }
})(typeof window!=='undefined'?window:globalThis);
