'use strict';
(async function(){
  const $ = id => document.getElementById(id);
  const id = (new URLSearchParams(location.search).get('id') || location.hash.replace(/^#(id=)?/, '')).replace(/\D/g, '');
  const miss = msg => { $('main').innerHTML = '<div class="msg">' + msg + '</div>'; };
  if(!id){ miss('No post id given. <a href="/x/">Search the archive</a>.'); return; }
  try{ await meta(); }catch(e){ miss('Could not load the archive index.'); return; }
  const i = META.byId.get(id);
  if(i === undefined){ miss('Post ' + esc(id) + ' is not in this archive. <a href="https://x.com/TheRubberDuck79/status/' + esc(id) + '" target="_blank" rel="noopener">Try it on X</a>.'); return; }
  const p = await postAt(i);
  document.title = 'Post ' + p.i + ', ' + p.c.slice(0, 10) + ' | The X Archive | The Rubber Duck\u2122';
  let canon = document.querySelector('link[rel="canonical"]');
  if(!canon){ canon = document.createElement('link'); canon.rel = 'canonical'; document.head.appendChild(canon); }
  canon.href = 'https://therubberduck.net/x/post.html?id=' + id;
  $('main').innerHTML = postHtml(p, {full: true, hi: true});
  const nav = [];
  if(i > 0) nav.push('<a href="/x/post.html?id=' + META.ids[i - 1] + '">Older post</a>'); else nav.push('<span></span>');
  nav.push('<a href="/x/?from=' + p.c.slice(0, 10) + '&to=' + p.c.slice(0, 10) + '&sort=old">All posts this day</a>');
  if(i < META.n - 1) nav.push('<a href="/x/post.html?id=' + META.ids[i + 1] + '">Newer post</a>'); else nav.push('<span></span>');
  $('navp').innerHTML = nav.join('');
  if(p.ri && META.byId.has(p.ri)){
    const pp = await postAt(META.byId.get(p.ri));
    $('parent').innerHTML = '<h3>In reply to (in archive)</h3><div class="posts">' + postHtml(pp) + '</div>';
  }
  if(p.k){
    const ks = await Promise.all(p.k.filter(k => META.byId.has(k)).map(k => postAt(META.byId.get(k))));
    if(ks.length) $('kids').innerHTML = '<h3>Replies in archive</h3><div class="posts">' + ks.map(k => postHtml(k)).join('') + '</div>';
  }
})();
