"""Preview-only DOM bridge. The exported site never includes editor JavaScript."""
BRIDGE = r"""<script>
(() => {
  if (window.parent === window) return;
  let parentOrigin;
  try { parentOrigin = new URL(document.referrer).origin; } catch { return; }
  if (!['http://localhost:8001','http://127.0.0.1:8001'].includes(parentOrigin)) return;
  const tags = 'h1,h2,h3,h4,h5,h6,p,span,a,button,li,strong,em,small,label,blockquote,figcaption,div';
  const norm = s => (s || '').trim().replace(/\s+/g,' ');
  const originals = new Map();
  let selected = null;
  let selectedOutline = '';
  const send = (type,extra={}) => window.parent.postMessage({type,...extra},parentOrigin);
  const candidates = () => [...document.querySelectorAll(tags)].filter(el =>
    el.childElementCount === 0 && !el.closest('svg,pre,code,[data-tn-film-caption]') &&
    !!el.getClientRects().length && norm(originals.get(el)?.text ?? el.textContent).length >= 2);
  document.addEventListener('click', e => {
    const el = e.target instanceof Element ? e.target.closest(tags) : null;
    if (!el || !candidates().includes(el)) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (selected) selected.style.outline = selectedOutline;
    selected = el;
    selectedOutline = el.style.outline;
    el.style.outline = '2px solid #6f9bff';
    send('tn-visual-select',{text:norm(originals.get(el)?.text ?? el.textContent),tag:el.tagName.toLowerCase()});
  }, true);
  document.addEventListener('submit',e=>{e.preventDefault();e.stopImmediatePropagation()},true);
  window.addEventListener('message', e => {
    if (e.source !== window.parent || e.origin !== parentOrigin || e.data?.type !== 'tn-visual-draft') return;
    const changes=e.data.changes;
    if (!Array.isArray(changes) || changes.length>12) return;
    if(selected)selected.style.outline=selectedOutline;
    for (const [el,original] of originals) if (el.isConnected) {
      el.textContent=original.text;
      if(original.style===null)el.removeAttribute('style');else el.setAttribute('style',original.style);
    }
    originals.clear();
    let applied=0;
    for (const change of changes) {
      if (typeof change?.before!=='string'||typeof change?.after!=='string'||change.after.length>500) continue;
      const matches=candidates().filter(el=>el.tagName.toLowerCase()===change.tag && norm(el.textContent)===change.before);
      if (matches.length!==1) continue;
      const el=matches[0];
      originals.set(el,{text:el.textContent,style:el.getAttribute('style')});
      el.textContent=change.after;
      if(change.styles && typeof change.styles==='object'){
        const allowed=['color','background-color','font-size','font-weight','text-align','letter-spacing','padding-block','padding-inline'];
        for(const key of allowed) if(Object.hasOwn(change.styles,key)&&typeof change.styles[key]==='string'&&change.styles[key].length<=16)el.style.setProperty(key,change.styles[key]);
      }
      if(Array.isArray(change.removedStyles))for(const key of change.removedStyles) if(['color','background-color','font-size','font-weight','text-align','letter-spacing','padding-block','padding-inline'].includes(key))el.style.removeProperty(key);
      applied++;
    }
    if(selected&&selected.isConnected){selectedOutline=selected.style.outline;selected.style.outline='2px solid #6f9bff';}
    send('tn-visual-applied',{applied});
  });
  send('tn-visual-ready');
})();
</script>"""
