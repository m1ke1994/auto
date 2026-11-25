// Trusted horizontal reading-progress indicator for every generated landing page.
export function installLandingProgress() {
  const id = 'tn-landing-progress';
  if (document.getElementById(id)) return;
  const host = document.createElement('div');
  host.id = id;
  host.setAttribute('aria-hidden', 'true');
  // Isolate the indicator from generated layout and animation styles.
  host.style.cssText = 'all:initial!important;position:fixed!important;top:0!important;left:0!important;right:0!important;width:auto!important;height:3px!important;z-index:2147483647!important;pointer-events:none!important;display:block!important;';
  const shadow = host.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = '.fill{display:block;width:100%;height:100%;background:var(--tn-progress-color,#c4a36b);transform:scaleX(0);transform-origin:left center;will-change:transform;}';
  const fill = document.createElement('div');
  fill.className = 'fill';
  shadow.append(style, fill);
  document.body.append(host);
  let frame = 0;
  function update() {
    frame = 0;
    const root = document.scrollingElement || document.documentElement;
    const max = root.scrollHeight - root.clientHeight;
    const ratio = max > 0 ? Math.min(1, Math.max(0, root.scrollTop / max)) : 0;
    fill.style.transform = 'scaleX(' + ratio + ')';
  }
  function schedule() {
    if (!frame) frame = requestAnimationFrame(update);
  }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  window.addEventListener('pageshow', schedule);
  window.addEventListener('load', schedule, { once: true });
  if (typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(schedule);
    observer.observe(document.documentElement);
    observer.observe(document.body);
  }
  update();
}
