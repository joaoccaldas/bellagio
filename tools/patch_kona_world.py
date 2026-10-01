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
import { installPlacesPanel } from '../../world-runtime/places.js';

installWorldNav({ href: '../../' });

const KONA_PLACES = [
  ['island','Whole island','Big Island aerial overview'],
  ['pier','Kailua Pier','Race-week waterfront and swim start'],
  ['finish_chute','Finish chute','Aliʻi Drive finish area'],
  ['kona_inn','Kona Inn','Historic oceanfront village'],
  ['huggos',"Huggo's",'Oceanfront dining area'],
  ['bikeworks','Bike Works','Bike service and athlete hub'],
  ['palani_climb','Palani climb','The hot corner and climb'],
  ['kta_kona','KTA Kona','Athlete grocery stop'],
  ['old_airport','Old Airport','Open coastal recreation area'],
  ['airport','KOA airport','Kona International Airport'],
  ['hawi','Hawi','Northern turnaround region'],
  ['energylab','Energy Lab','Iconic Queen K race section'],
  ['waikoloa','Waikoloa','Resort and race corridor'],
  ['kawaihae','Kawaihae','Harbor and north-coast corridor'],
  ['waimea','Waimea','Upland town and green interior'],
  ['hilo','Hilo','Windward Big Island'],
  ['kahaluu','Kahaluʻu','South Kona coastal area'],
  ['southkona','South Kona','Southern Kona district']
].map(([id,label,description])=>({id,label,description}));

import('./src/islandRuntime.js')
  .then(() => {
    const ready = () => {
      if (!window.__kona?.ready) return setTimeout(ready, 80);
      installPlacesPanel({
        title: 'Kona places',
        places: KONA_PLACES,
        initial: 'island',
        onSelect: place => window.__kona.goTo(place.id, { animate: true })
      });
      markWorldReady({ id: 'kona', detail: { kind: 'full-island', places: KONA_PLACES.length } });
    };
    ready();
  })
  .catch(error => {
    console.error('Kona world failed to load', error);
    document.documentElement.dataset.worldError = 'true';
  });
</script>"""
s = s.replace(legacy, shared)
p.write_text(s)
