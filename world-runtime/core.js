export function detectDevice() {
  const coarse = matchMedia('(pointer: coarse)').matches || innerWidth < 760;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  return { coarse, reducedMotion };
}

export function pixelRatioCap({ coarse, quality = 'balanced' } = {}) {
  const dpr = devicePixelRatio || 1;
  if (coarse) {
    const cap = quality === 'ultra' ? 1.35 : quality === 'high' ? 1.2 : 1.0;
    return Math.min(dpr, cap);
  }
  const cap = quality === 'ultra' ? 2 : quality === 'high' ? 1.75 : 1.25;
  return Math.min(dpr, cap);
}

export function installWorldNav({ label = 'World map', href = '../../', side = 'left' } = {}) {
  let nav = document.querySelector('[data-world-nav]');
  if (nav) return nav;
  nav = document.createElement('a');
  nav.dataset.worldNav = '';
  nav.href = href;
  nav.textContent = '← ' + label;
  Object.assign(nav.style, {
    position: 'fixed',
    zIndex: '30',
    top: 'max(10px, env(safe-area-inset-top))',
    [side]: '10px',
    color: '#fff',
    textDecoration: 'none',
    background: 'rgba(6,12,15,.78)',
    border: '1px solid rgba(255,255,255,.16)',
    borderRadius: '999px',
    padding: '9px 12px',
    font: '600 12px/1 system-ui,sans-serif',
    backdropFilter: 'blur(10px)',
    WebkitBackdropFilter: 'blur(10px)',
    touchAction: 'manipulation'
  });
  document.body.appendChild(nav);
  return nav;
}

export function installResize({ renderer, camera, quality = () => 'balanced', onResize } = {}) {
  const device = detectDevice();
  let raf = 0;
  const resize = () => {
    raf = 0;
    const w = Math.max(1, visualViewport?.width || innerWidth);
    const h = Math.max(1, visualViewport?.height || innerHeight);
    if (renderer) {
      renderer.setPixelRatio(pixelRatioCap({ coarse: device.coarse, quality: quality() }));
      renderer.setSize(w, h, false);
    }
    if (camera) {
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    onResize?.({ width: w, height: h, coarse: device.coarse });
  };
  const schedule = () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(resize);
  };
  addEventListener('resize', schedule, { passive: true });
  visualViewport?.addEventListener('resize', schedule, { passive: true });
  resize();
  return { resize, dispose() {
    removeEventListener('resize', schedule);
    visualViewport?.removeEventListener('resize', schedule);
    cancelAnimationFrame(raf);
  }};
}

export function createFrameLoop(update, { pauseWhenHidden = true } = {}) {
  let raf = 0;
  let running = false;
  let last = performance.now();
  const tick = now => {
    if (!running) return;
    const dt = Math.min(.1, Math.max(0, (now - last) / 1000));
    last = now;
    update(dt, now / 1000);
    raf = requestAnimationFrame(tick);
  };
  const start = () => {
    if (running) return;
    running = true;
    last = performance.now();
    raf = requestAnimationFrame(tick);
  };
  const stop = () => {
    running = false;
    cancelAnimationFrame(raf);
  };
  const onVisibility = () => {
    if (!pauseWhenHidden) return;
    document.hidden ? stop() : start();
  };
  document.addEventListener('visibilitychange', onVisibility);
  start();
  return { start, stop, dispose() { stop(); document.removeEventListener('visibilitychange', onVisibility); } };
}

export function markWorldReady({ id, detail = {} } = {}) {
  document.documentElement.dataset.worldReady = 'true';
  window.dispatchEvent(new CustomEvent('caldas-world-ready', { detail: { id, ...detail } }));
}
