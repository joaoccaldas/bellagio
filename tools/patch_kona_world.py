from pathlib import Path

p = Path("_site/worlds/kona/index.html")
s = p.read_text()

old = (
    "window.__KONA_ASSET_BASE=(location.hostname==='localhost'||"
    "location.hostname==='127.0.0.1')?'../web/public/assets/':"
    "'https://joaoccaldas.github.io/studio-kona/web/public/assets/';"
)
s = s.replace(old, "window.__KONA_ASSET_BASE='./assets/';")

legacy = """<script type="module">
import './src/islandRuntime.js';
</script>"""
shared = """<script type="module">
import { installWorldNav, markWorldReady } from '../../world-runtime/core.js';
installWorldNav({ href: '../../' });
import('./src/islandRuntime.js')
  .then(() => markWorldReady({ id: 'kona', detail: { kind: 'full-island' } }))
  .catch(error => {
    console.error('Kona world failed to load', error);
    document.documentElement.dataset.worldError = 'true';
  });
</script>"""
s = s.replace(legacy, shared)
p.write_text(s)
