// BELLAGIO — a walkable digital twin.  Blender 5.2 + Cycles lightmaps, Three.js r186.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { Reflector } from 'three/examples/jsm/objects/Reflector.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import { computeBoundsTree, acceleratedRaycast } from 'three-mesh-bvh';
import { Fountains, SHOWS } from './fountains.js';
import { makePlaces, INFO } from './places.js';
let PLACES = [];

THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;

const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const coarse = matchMedia('(pointer: coarse)').matches || innerWidth < 760;
const A = window.__BELLAGIO_ASSETS || 'assets/';
const BELLAGIO_ROOM_NAMES = [
  'Main lobby','Fiori di Como','Conservatory & Botanical Gardens','Lift foyer','Lake Como salon','Dining room',
  'Rat Pack bar','Glass gallery','Spa & indoor pool','Library','Desert Moon bedroom','Master bath','Dressing room',
  'Rotunda','Roof terrace','Belvedere (lantern)'
];
const PORTABLE_ROOMS = [
  { semanticId:'room:konam:nor3-winter', label:'NOR // 3 · KONA WINTER', role:'Engineering benchmark', href:'kona-rooms/index.html?reviewRoom=nor3-winter' },
  { semanticId:'room:konam:beast-cave', label:'Beast Cave', role:'Athlete experience', href:'kona-rooms/index.html?reviewRoom=beast-cave' },
  { semanticId:'room:konam:breitling-kona', label:'Breitling × KONA · Finish-Line Atelier', role:'Hero product benchmark', href:'kona-rooms/index.html?reviewRoom=breitling-kona' },
];
// Blender Z-up survey metres -> three Y-up
const W = (x, y, z) => new THREE.Vector3(x, z, -y);

// ------------------------------------------------------------------ state
const S = { tod: .72, night: 0, quality: coarse ? 'balanced' : 'high', mode: 'orbit', walkY: 0, busy: false,
  exposure: 1.0, bloom: .55, showInfo: true, sound: false };
try { Object.assign(S, JSON.parse(localStorage.getItem('bellagio.settings') || '{}')); } catch (_) { }
const save = () => { try { localStorage.setItem('bellagio.settings', JSON.stringify({ tod: S.tod, quality: S.quality, exposure: S.exposure, bloom: S.bloom })); } catch (_) { } };

// ------------------------------------------------------------------ renderer
const canvas = $('#c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !coarse, powerPreference: 'high-performance', logarithmicDepthBuffer: false });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.shadowMap.enabled = false;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, 1, .08, 12000);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = .07; controls.zoomToCursor = true;
controls.maxDistance = 9000; controls.minDistance = .5; controls.maxPolarAngle = Math.PI * .495;

const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: coarse ? 0 : 2 }));
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .5, .6, .92);
composer.addPass(bloom);
const grade = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uVig: { value: coarse ? .28 : .42 }, uTime: { value: 0 }, uGrain: { value: coarse ? .06 : .16 }, uRes: { value: new THREE.Vector2(1, 1) } },
  vertexShader: 'varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
  fragmentShader: `uniform sampler2D tDiffuse; uniform float uVig,uTime,uGrain; uniform vec2 uRes; varying vec2 vUv;
    float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
    void main(){ vec2 c=vUv-.5; float r=length(c);
      vec3 col=vec3(texture2D(tDiffuse,vUv+c*.0012*r).r, texture2D(tDiffuse,vUv).g, texture2D(tDiffuse,vUv-c*.0012*r).b);
      col*=mix(1.,smoothstep(.95,.25,r),uVig);
      col+=(h(vUv*uRes+fract(uTime*7.))-.5)*.03*uGrain;
      gl_FragColor=vec4(col,1.);}`,
});
composer.addPass(grade);
composer.addPass(new OutputPass());

function resize() {
  const cap = coarse ? (S.quality === 'ultra' ? 1.35 : S.quality === 'high' ? 1.2 : 1.0) : (S.quality === 'high' ? 1.75 : S.quality === 'ultra' ? 2 : 1.25);
  const pr = Math.min(devicePixelRatio, cap);
  renderer.setPixelRatio(pr); composer.setPixelRatio(pr);
  renderer.setSize(innerWidth, innerHeight, false); composer.setSize(innerWidth, innerHeight);
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  grade.uniforms.uRes.value.set(innerWidth * pr, innerHeight * pr);
}
let resizeRAF = 0;
addEventListener('resize', () => {
  cancelAnimationFrame(resizeRAF);
  resizeRAF = requestAnimationFrame(resize);
}, { passive: true });
if (window.visualViewport) visualViewport.addEventListener('resize', () => {
  cancelAnimationFrame(resizeRAF);
  resizeRAF = requestAnimationFrame(resize);
}, { passive: true });

// ------------------------------------------------------------------ sky + lights (real-time parts)
const sky = new Sky(); sky.scale.setScalar(9000); scene.add(sky);
const su = sky.material.uniforms;
su.turbidity.value = 3.2; su.rayleigh.value = 1.1; su.mieCoefficient.value = .004; su.mieDirectionalG.value = .82;
const sunDir = new THREE.Vector3();
const sunLight = new THREE.DirectionalLight(0xfff1e0, 3.2); scene.add(sunLight, sunLight.target);
const hemi = new THREE.HemisphereLight(0xbfd6ff, 0x6b5a45, .6); scene.add(hemi);
const stars = (() => {
  const n = 2500, p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const u = Math.random(), v = Math.random() * .9 + .1; const th = u * 6.283, ph = Math.acos(v); p.set([Math.sin(ph) * Math.cos(th) * 8000, Math.cos(ph) * 8000, Math.sin(ph) * Math.sin(th) * 8000], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.4, sizeAttenuation: false, transparent: true, opacity: 0, depthWrite: false }));
})();
scene.add(stars);
// distant mountains ring (Spring Mountains to the west, Frenchman to the east) as a soft silhouette
const mountains = (() => {
  const seg = 256, g = new THREE.CylinderGeometry(7000, 7000, 1, seg, 1, true);
  const pos = g.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), z = pos.getZ(i), top = pos.getY(i) > 0;
    const a = Math.atan2(z, x);
    const west = Math.max(0, Math.cos(a - Math.PI)) ** 1.5;           // Spring Mountains (Mt Charleston ~3.6 km)
    const hgt = 90 + 520 * west + 140 * Math.abs(Math.sin(a * 7.3)) * (0.4 + west) + 60 * Math.sin(a * 23.1) ** 2;
    pos.setY(i, top ? hgt : -20);
  }
  g.computeVertexNormals();
  return new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: 0x8a8378, fog: false, side: THREE.BackSide, transparent: true, opacity: .85 }));
})();
scene.add(mountains);
scene.fog = new THREE.FogExp2(0xb9c6d6, .000014);

// ------------------------------------------------------------------ loading
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
const texLoader = new THREE.TextureLoader();
const hdrLoader = new HDRLoader();
const pmrem = new THREE.PMREMGenerator(renderer);
let manifest, lm = {}, env = {}, fountains, lake, collide = [], floors = [], walls = [], dyn = {}, pick = [];
const bakedMats = [];
const progress = p => { $('#bar').style.width = (p * 100).toFixed(0) + '%'; };

async function loadAll() {
  const steps = [];
  manifest = await (await fetch(A + 'manifest.json')).json();
  const groups = ['tower', 'site', 'village', 'interior', 'penthouse', 'luxor'];
  let done = 0; const total = groups.length * 2 + 3;
  const tick = () => progress(++done / total);
  for (const g of groups) for (const st of ['day', 'night']) {
    steps.push(new Promise(res => texLoader.load(A + `lm_${g}_${st}.webp`, t => {
      t.flipY = false; t.colorSpace = THREE.NoColorSpace; t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter;
      (lm[g] = lm[g] || {})[st] = t; tick(); res();
    }, undefined, () => { tick(); res(); })));
  }
  for (const st of ['day', 'night']) steps.push(new Promise(res => hdrLoader.load(A + `env_${st}.hdr`, t => {
    t.mapping = THREE.EquirectangularReflectionMapping; env[st] = pmrem.fromEquirectangular(t).texture; tick(); res();
  }, undefined, () => { tick(); res(); })));
  const gltf = await new Promise((res, rej) => loader.load(A + 'bellagio.glb', g => { tick(); res(g); }, undefined, rej));
  const cityGltf = await new Promise(res => loader.load(A + 'city.glb?v=20221030d', g => res(g), undefined, () => res(null)));
  await Promise.all(steps);
  PLACES = makePlaces(manifest);
  ui();
  build(gltf.scene, cityGltf && cityGltf.scene);
}

// ------------------------------------------------------------------ materials
function bakedMaterial(group) {
  const m = new THREE.MeshBasicMaterial({ map: lm[group]?.day || null });
  m.userData.u = { uNightMap: { value: lm[group]?.night || lm[group]?.day }, uMix: { value: 0 }, uGain: { value: 1 } };
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, m.userData.u);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D uNightMap; uniform float uMix, uGain;\nvec3 dec(vec3 e){ vec3 e2=e*e; return e2/max(vec3(1e-4),1.-e2); }')
      .replace('#include <map_fragment>', `
        vec3 dayL = dec(texture2D(map, vMapUv).rgb);
        vec3 nightL = dec(texture2D(uNightMap, vMapUv).rgb);
        diffuseColor.rgb = mix(dayL, nightL, uMix) * uGain;`);
  };
  m.name = 'baked_' + group;
  bakedMats.push(m);
  return m;
}

// hotel glass: sky/env reflection + interior-mapped rooms (4 rooms per window, curtains, night lamps)
function roomGlass(village = false) {
  const m = new THREE.MeshStandardMaterial({ color: 0x0a0f10, roughness: .06, metalness: .0, envMapIntensity: 1.0 });
  m.userData.u = { uNight: { value: 0 }, uTime: { value: 0 }, uVillage: { value: village ? 1 : 0 } };
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, m.userData.u);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec2 uv1; varying vec2 vWin; varying vec2 vR; varying vec3 vWP;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWin = uv; vR = uv1; vWP = (modelMatrix*vec4(position,1.)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
      uniform float uNight, uTime, uVillage; varying vec2 vWin; varying vec2 vR; varying vec3 vWP;
      float hh(float x){ return fract(sin(x*127.1)*43758.5453); }
      // bronze mullions drawn from the window's own uv: perimeter, centre bar, floor transom (arcade: lower transom)
      float frameMask(){
        vec2 w = fwidth(vWin) * 1.5;
        float arcade = step(.64, vR.y) * (1. - uVillage);
        float edge = 1. - smoothstep(0., w.x + .018, min(vWin.x, 1. - vWin.x)) * smoothstep(0., w.y + .012, min(vWin.y, 1. - vWin.y));
        float bar = 1. - smoothstep(.012, .012 + w.x, abs(vWin.x - .5));
        float tv = arcade > .5 ? .385 : .5;
        float tr = (1. - uVillage) * (1. - smoothstep(.02, .02 + w.y, abs(vWin.y - tv)));
        return clamp(max(max(edge, bar), tr), 0., 1.);
      }`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
      float fm = frameMask(); roughnessFactor = mix(roughnessFactor, .45, fm); diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.035,.028,.02), fm);`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      {
        // which of the four rooms behind this window
        vec2 q2 = floor(vWin * 2.); float q = q2.x + 2. * q2.y;
        float r = hh(vR.x * 71.3 + q * 3.7);
        vec2 f = fract(vWin * 2.) * 2. - 1.;                      // -1..1 inside the room opening
        vec3 N = normalize(cross(dFdx(vWP), dFdy(vWP)));
        vec3 up = vec3(0.,1.,0.); vec3 T = normalize(cross(up, N)); vec3 B = up;
        vec3 V = normalize(vWP - cameraPosition);
        vec3 d = vec3(dot(V, T), dot(V, B), dot(V, -N));
        d.z = max(d.z, .05);
        float depth = 3.2;                                     // room depth in half-window units
        vec3 o = vec3(f, 0.);
        vec3 tt = (sign(d) - o) / d; tt.z = depth / d.z;
        float t = min(min(tt.x, tt.y), tt.z);
        vec3 hit = o + d * t;
        vec3 wallCol = mix(vec3(.55,.42,.28), vec3(.42,.36,.30), hh(r*9.1));
        vec3 room = t == tt.z ? wallCol * (.8 + .2*sin(hit.x*3.)) : (t == tt.y ? (hit.y > 0. ? vec3(.7,.62,.5) : vec3(.25,.16,.1)) : wallCol*.75);
        float depthFade = 1. - hit.z / depth * .45;
        float lit = step(r, .30) * uNight;
        float curtain = smoothstep(.55 + .35 * hh(r*3.3), .6 + .35 * hh(r*3.3), abs(f.x)) ;
        vec3 lamp = vec3(1.,.72,.42) * (1.1 + .5*hh(r*5.1));
        vec3 inside = room * depthFade * (lit * lamp * 1.6 + .04 + (1.-uNight) * .12);
        inside = mix(inside, vec3(.85,.72,.52) * (lit * 1.2 + .06 + (1.-uNight)*.25), curtain * .8);
        totalEmissiveRadiance += inside * (1. - fm);
      }`);
  };
  return m;
}

function waterMaterialFor(mesh) {
  // Reflector for the lake; small basins get a simple glossy material
  return new THREE.MeshStandardMaterial({ color: 0x0b3a3a, roughness: .05, metalness: .2 });
}

// ------------------------------------------------------------------ scene assembly
let lakeRefl;
function cityMaterial(kind) {
  const glass = kind === 'glass', castle = kind === 'castle', gold = kind === 'gold';
  const steel = kind === 'steel', coaster = kind === 'coaster', neon = kind === 'neon';
  const color = coaster ? 0xd92520 : (steel ? 0xd0d5da : (neon ? 0xffea70 : (gold ? 0xd4af37 : (glass ? 0x14181c : (castle ? 0xc4a07a : 0x8d8880)))));
  const roughness = (coaster || glass) ? .2 : (gold ? .14 : (steel ? .32 : .72));
  const metalness = gold ? .85 : (steel ? .75 : ((glass || coaster) ? .5 : .04));
  const m = new THREE.MeshStandardMaterial({
    color, roughness, metalness,
    emissive: neon ? new THREE.Color(0xffdf55) : new THREE.Color(0x000000),
    emissiveIntensity: neon ? 2.5 : 0,
  });
  if (!coaster && !steel && !neon) {
    m.userData.u = { uNight: { value: 0 } };
    m.onBeforeCompile = sh => {
      Object.assign(sh.uniforms, m.userData.u);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vCity;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvCity = (modelMatrix * vec4(position, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          uniform float uNight; varying vec3 vCity;
          float ch(float x){ return fract(sin(x * 127.1) * 43758.5453); }`)
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          float row = floor(vCity.y / 3.3);
          float col = floor((vCity.x - vCity.z) / 4.4);
          vec2 f = vec2(fract((vCity.x - vCity.z) / 4.4), fract(vCity.y / 3.3));
          float pane = step(.14, f.x) * step(f.x, .86) * step(.2, f.y) * step(f.y, .9);
          float lit = step(.6, ch(row * 13.1 + col * 7.7)) * pane * uNight;
          totalEmissiveRadiance += vec3(1.0, .76, .42) * lit * 1.5;
          diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * .32, pane * (1. - uNight));`);
    };
  }
  return m;
}
function addSolid(o, { floor = false, wall = false } = {}) {
  collide.push(o);
  if (floor) floors.push(o);
  if (wall) walls.push(o);
}
function dressCity(root) {
  const tex = {};
  const file = { wide: 'city_wide.jpg', valley: 'city_valley.jpg', strip: 'city_strip.jpg', luxor: 'luxor_sat.jpg' };
  root.traverse(o => {
    if (!o.isMesh) return;
    const n = o.name, ud = o.userData || {};
    o.frustumCulled = true;
    if (ud.beam) {
      o.material = new THREE.MeshBasicMaterial({ color: new THREE.Color(...(ud.emit || [.9, .95, 1])), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide });
      (dyn.beams = dyn.beams || []).push(o);
    } else if (ud.emit) {
      const c = new THREE.Color(...ud.emit);
      o.material = new THREE.MeshBasicMaterial({ color: c });
      o.userData.baseStrength = ud.strength || 20; o.userData.dynKind = ud.dyn; o.userData.emitColor = c;
      dyn.emit = dyn.emit || []; dyn.emit.push(o);
    } else if (ud.ground === 'plain') {
      o.material = new THREE.MeshStandardMaterial({ color: 0x8d7b64, roughness: .96, metalness: 0 });
      addSolid(o, { floor: true });
    } else if (ud.ground) {
      const key = ud.ground;
      o.material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: .95, metalness: 0 });
      texLoader.load(A + file[key], t => {
        t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.anisotropy = 4;
        o.material.map = t; o.material.needsUpdate = true;
      });
      addSolid(o, { floor: true });
    } else if (n.startsWith('CITY_') || n === 'eiffel') {
      o.material = cityMaterial(ud.city || (n === 'eiffel' ? 'steel' : 'block'));
      addSolid(o, { floor: true, wall: true });
    } else if (ud.mat === 'luxor_glass' || n.includes('pyramid')) {
      o.material = new THREE.MeshPhysicalMaterial({ color: 0x0c0d0f, roughness: .05, metalness: .84, envMapIntensity: 1.2, side: THREE.DoubleSide });
      addSolid(o, { floor: true, wall: true });
    } else if (n.startsWith('LUXOR_')) {
      if (o.material) { o.material.envMapIntensity = 1; o.material.roughness = .7; }
      addSolid(o, { floor: true, wall: true });
    }
  });
  scene.add(root);
}
function build(root, cityRoot) {
  root.traverse(o => {
    if (!o.isMesh) return;
    const n = o.name, ud = o.userData || {};
    o.matrixAutoUpdate = false; o.updateMatrix();
    if (ud.baked) {
      o.material = bakedMaterial(ud.baked);
      addSolid(o, { floor: true, wall: true }); pick.push(o);
    } else if (n.startsWith('GLASS_tower') || n.startsWith('GLASS_spa') || n.startsWith('GLASS_village')) {
      o.material = roomGlass(n.startsWith('GLASS_village')); pick.push(o);
    } else if (n.startsWith('WATER_lake')) {
      lake = o;
    } else if (n.startsWith('WATER')) {
      o.material = new THREE.MeshStandardMaterial({ color: 0x1a6f86, roughness: .04, metalness: .1, transparent: true, opacity: .85 });
    } else if (n.startsWith('GLASS_chihuly')) {
      o.material = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: .12, transmission: 0, emissive: 0xffffff, emissiveIntensity: .0, side: THREE.DoubleSide });
      o.material.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance = vColor.rgb * 1.6;'); };
    } else if (n.startsWith('GLASS')) {
      o.material = new THREE.MeshPhysicalMaterial({ color: 0xe8f2f2, roughness: .02, metalness: 0, transparent: true, opacity: .18, side: THREE.DoubleSide, depthWrite: false });
    } else if (ud.beam) {
      o.material = new THREE.MeshBasicMaterial({ color: new THREE.Color(...ud.emit), transparent: true, opacity: .0, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
      (dyn.beams = dyn.beams || []).push(o);
    } else if (ud.emit) {
      const c = new THREE.Color(...ud.emit);
      o.material = new THREE.MeshBasicMaterial({ color: c });
      o.userData.baseStrength = ud.strength; o.userData.dynKind = ud.dyn;
      o.userData.emitColor = c;
      dyn.emit = dyn.emit || []; dyn.emit.push(o);
    } else if (n.startsWith('DYN_lift')) {
      o.matrixAutoUpdate = true;
      (dyn.lift = dyn.lift || []).push(o);
    } else if (n.startsWith('TREE_')) {
      o.visible = false;
    } else {
      // real-time PBR parts: mullions, steel, props
      if (o.material) { o.material.envMapIntensity = 1.0; }
    }
  });
  scene.add(root);
  // lake: planar reflection with wind ripples
  if (lake) {
    // rebuild the lake as a flat XY shape (Reflector's plane is its local XY, normal +Z)
    const pa = lake.geometry.attributes.position, ix = lake.geometry.index;
    lake.updateMatrixWorld();
    const flat = new THREE.BufferGeometry();
    const fp = new Float32Array(pa.count * 3); let ly = 0;
    const v = new THREE.Vector3();
    for (let i = 0; i < pa.count; i++) { v.fromBufferAttribute(pa, i).applyMatrix4(lake.matrixWorld); fp.set([v.x, -v.z, 0], i * 3); ly = v.y; }
    flat.setAttribute('position', new THREE.BufferAttribute(fp, 3)); if (ix) flat.setIndex(ix);
    const pr = S.quality === 'high' ? .5 : .33;
    lakeRefl = new Reflector(flat, { clipBias: .003, textureWidth: innerWidth * pr, textureHeight: innerHeight * pr, color: 0x9fb8b4, shader: WATER_SHADER });
    lakeRefl.rotation.x = -Math.PI / 2; lakeRefl.position.y = ly;
    lakeRefl.material.uniforms.uDeep = { value: new THREE.Color(0x0a3b38) };
    scene.add(lakeRefl); lake.visible = false;
  }
  // trees: one InstancedMesh per species
  const protos = {}; root.traverse(o => { if (o.isMesh && o.name.startsWith('TREE_')) protos[o.name.slice(5)] = o; });
  const byKind = {};
  for (const t of manifest.trees) (byKind[t.k] = byKind[t.k] || []).push(t);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3();
  for (const [k, list] of Object.entries(byKind)) {
    const p = protos[k]; if (!p) continue;
    const im = new THREE.InstancedMesh(p.geometry, p.material, list.length);
    list.forEach((t, i) => { q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), t.r); sc.setScalar(t.s); m4.compose(W(t.x, t.y, 0), q, sc); im.setMatrixAt(i, m4); });
    im.instanceMatrix.needsUpdate = true;
    scene.add(im);
  }
  if (manifest.chihuly_pieces) scene.add(chihuly(manifest.chihuly_pieces));
  // Luxor + Strip base layer live in city.glb until a full bake folds them into bellagio.glb
  let folded = false;
  root.traverse(o => { if (o.name.startsWith('LUXOR_') || o.name.startsWith('CITY_')) folded = true; });
  if (cityRoot && !folded) dressCity(cityRoot);
  for (const o of collide) if (!o.geometry.boundsTree) o.geometry.computeBoundsTree();
  // fountains
  fountains = new Fountains(scene, manifest.nozzles, manifest.lake_level + .05, W);
  fountains.play('Grand finale');
  // lift parts: remember rest positions
  for (const o of dyn.lift || []) o.userData.rest = o.position.clone();
  applyTime(true);
  $('#loading').classList.add('done');
  window.__survey = () => ({ x: camera.position.x, y: -camera.position.z, z: camera.position.y, tx: controls.target.x, ty: -controls.target.z });
  window.__enterWalk = () => { setMode('walk'); syncWalkFromCamera(); return window.__survey(); };
  window.__goPlace = (name) => {
    const p = PLACES.find(q => q.name && q.name.toLowerCase() === String(name).toLowerCase() && q.pos);
    if (p) go(p, 0.4);
    return !!p;
  };
  const asked = decodeURIComponent((location.hash || '').slice(1));
  const hit = asked && PLACES.find(q => q.name && q.name.toLowerCase() === asked.toLowerCase() && q.pos);
  go(hit || PLACES[0], hit ? 0.05 : 0);
}

// Fiori di Como: the same generator as the Blender build (ruffled Persian saucers + twisted horns)
function chihuly(pieces) {
  const pos = [], col = [], idx = [];
  const n = 18;
  for (const [x, y, z, R, ta, tb, r, g, b, horn] of pieces) {
    const ax = new THREE.Vector3(Math.sin(ta) * Math.cos(tb), Math.sin(ta) * Math.sin(tb), -Math.cos(ta));
    const u = new THREE.Vector3(1, 0, 0); if (Math.abs(ax.x) > .9) u.set(0, 1, 0);
    u.sub(ax.clone().multiplyScalar(u.dot(ax))).normalize();
    const v = ax.clone().cross(u).normalize();
    const base = pos.length / 3, c = new THREE.Vector3(x, y, z);
    const push = p => { const w = W(p.x, p.y, p.z); pos.push(w.x, w.y, w.z); col.push(r, g, b); };
    let rings;
    if (horn) {
      rings = 7; const Lh = R * 3.2;
      for (let k = 0; k < rings; k++) { const t = k / (rings - 1), rr = R * .35 * (1 - t) + .01;
        for (let j = 0; j < n; j++) { const a = j / n * 6.2832 + t * 2.5, s = rr * (1 + .25 * Math.sin(a * 3));
          push(c.clone().addScaledVector(ax, Lh * t).addScaledVector(u, Math.cos(a) * s).addScaledVector(v, Math.sin(a) * s)); } }
    } else {
      rings = 4;
      for (let k = 0; k < rings; k++) { const t = (k + 1) / rings, rr = R * t;
        for (let j = 0; j < n; j++) { const a = j / n * 6.2832, ruf = .18 * R * t * t * Math.sin(a * 7 + x * 3), dep = R * .45 * t * t + ruf;
          push(c.clone().addScaledVector(u, Math.cos(a) * rr).addScaledVector(v, Math.sin(a) * rr).addScaledVector(ax, dep)); } }
      const ci = pos.length / 3; push(c);
      for (let j = 0; j < n; j++) idx.push(ci, base + (j + 1) % n, base + j);
    }
    for (let k = 0; k < rings - 1; k++) for (let j = 0; j < n; j++) {
      const a = base + k * n + j, b2 = base + k * n + (j + 1) % n;
      idx.push(a, b2, b2 + n, a, b2 + n, a + n);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx); g.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .15, metalness: 0, side: THREE.DoubleSide, envMapIntensity: .8 });
  mat.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n totalEmissiveRadiance = vColor.rgb * (1.1 + .5 * (1. - abs(dot(normalize(vNormal), vec3(0.,0.,1.)))));'); };
  const mesh = new THREE.Mesh(g, mat); mesh.name = 'Fiori di Como';
  return mesh;
}

const WATER_SHADER = {
  name: 'LakeWater',
  uniforms: { color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null }, uTime: { value: 0 }, uNight: { value: 0 }, uDeep: { value: new THREE.Color(0x0a3b38) }, uSky: { value: new THREE.Color(0x88aacc) } },
  vertexShader: `uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vW;
    void main(){ vUv = textureMatrix * vec4(position,1.); vW = (modelMatrix*vec4(position,1.)).xyz; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 color, uDeep, uSky; uniform sampler2D tDiffuse; uniform float uTime, uNight; varying vec4 vUv; varying vec3 vW;
    float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
    void main(){
      vec2 p = vW.xz;
      vec2 w = vec2(n(p*.35+uTime*.12)+n(p*1.1-uTime*.2)*.5, n(p*.33-uTime*.1+7.)+n(p*1.3+uTime*.17+3.)*.5) - .75;
      vec4 uv = vUv; uv.xy += w * .035 * uv.w;
      vec3 refl = texture2DProj(tDiffuse, uv).rgb;
      vec3 V = normalize(cameraPosition - vW);
      float fres = .04 + .96 * pow(1. - max(V.y, 0.), 5.);
      vec3 base = mix(uDeep, uDeep * .15, uNight);
      gl_FragColor = vec4(mix(base, refl * color, clamp(fres + .25, 0., 1.)), 1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
};

// ------------------------------------------------------------------ time of day
// tod: 0..1 across a day; 0.25 sunrise, 0.5 noon, 0.75 sunset, <0.2 / >0.82 night
function applyTime(force) {
  const t = S.tod;
  const el = Math.sin((t - .25) * Math.PI * 2) * 72;                  // degrees (Las Vegas summer)
  const az = 90 + (t - .25) * 360;                                    // east at sunrise
  const phi = THREE.MathUtils.degToRad(90 - el), th = THREE.MathUtils.degToRad(az);
  sunDir.setFromSphericalCoords(1, phi, th);
  // survey east is +x, north is -z in three
  sunDir.set(Math.sin(th) * Math.sin(phi), Math.cos(phi), -Math.cos(th) * Math.sin(phi));
  su.sunPosition.value.copy(sunDir);
  const day = clamp((el + 4) / 14);
  S.night = 1 - day;
  sunLight.position.copy(sunDir).multiplyScalar(500); sunLight.intensity = 3.2 * day;
  sunLight.color.setHSL(.09, .6, .6 + .3 * clamp(el / 40));
  hemi.intensity = .15 + .55 * day;
  sky.visible = day > .02;
  stars.material.opacity = clamp((S.night - .5) * 2) * .9;
  scene.background = new THREE.Color().setRGB(.004, .006, .014).lerp(new THREE.Color(.55, .65, .8), day * .0);
  scene.fog.color.setRGB(lerp(.02, .72, day), lerp(.025, .78, day), lerp(.05, .86, day));
  mountains.material.color.setRGB(lerp(.03, .54, day), lerp(.03, .5, day), lerp(.04, .47, day));
  scene.environment = S.night > .5 ? (env.night || null) : (env.day || null);
  renderer.toneMappingExposure = S.exposure * lerp(1.05, .82, day) * (wasIn ? .72 : 1);
  for (const m of bakedMats) { m.userData.u.uMix.value = S.night; }
  for (const o of dyn.emit || []) {
    const k = o.userData.dynKind === 'always' ? 1 : S.night;
    o.material.color.copy(o.userData.emitColor).multiplyScalar(k * Math.min(1.25, .35 + o.userData.baseStrength / 40));
  }
  scene.traverse(o => { if (o.material?.userData?.u?.uNight) o.material.userData.u.uNight.value = S.night; });
  if (lakeRefl) lakeRefl.material.uniforms.uNight.value = S.night;
  for (const o of dyn.beams || []) o.material.opacity = .28 * S.night;
  bloom.strength = S.bloom * (.25 + .45 * S.night); bloom.threshold = .95;
  $('#tod').value = S.tod;
  $('#todLabel').textContent = clockLabel(t);
}
function clockLabel(t) { const m = Math.round(t * 24 * 60) % 1440; return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`; }

// ------------------------------------------------------------------ navigation: fly-to, walk, lift
let tween = null;
function flyTo(pos, target, dur = 2.4, done) {
  const p0 = camera.position.clone(), t0 = controls.target.clone();
  const p1 = pos.clone(), t1 = target.clone();
  const lift = Math.min(250, p0.distanceTo(p1) * .25);
  tween = { t: 0, dur, f: k => {
    const e = ease(k);
    camera.position.lerpVectors(p0, p1, e); camera.position.y += Math.sin(Math.PI * e) * lift;
    controls.target.lerpVectors(t0, t1, e);
    camera.lookAt(controls.target);
  }, done };
}
function go(place, dur = 2.6) {
  if (S.busy) return;
  const p = W(...place.pos), t = W(...place.look);
  setMode(place.walk ? 'walk' : 'orbit', false);
  if (place.walk) S.walkY = place.pos[2] - 1.65;
  flyTo(p, t, dur, () => { if (place.walk) { syncWalkFromCamera(); plantFeet(true); } });
  S.tod = place.tod !== undefined ? place.tod : .5; applyTime();
  if (place.show) fountains.play(place.show);
  showCaption(place);
}
function showCaption(place) {
  const el = $('#caption');
  el.innerHTML = `<b>${place.name}</b><span>${place.note || ''}</span>${place.evidence ? `<em class="ev ev-${place.evidence[0]}">${place.evidence}</em>` : ''}`;
  el.classList.add('on'); clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove('on'), 6500);
}

// walk mode: drag to look, WASD / arrows / on-screen stick to move, gravity onto the floor under you
const walk = { yaw: 0, pitch: 0, vel: new THREE.Vector3(), keys: {}, eye: 1.65, stick: { x: 0, y: 0 } };
function setMode(m, plant = true) {
  S.mode = m; controls.enabled = m === 'orbit';
  $('#modeBtn').textContent = m === 'orbit' ? 'Walk' : 'Orbit';
  document.body.classList.toggle('walking', m === 'walk');
  if (m === 'walk' && plant) plantFeet(true);
}
function groundHit(x, y, z) {
  // From above the feet, so a high camera still finds the street, a roof, or a Bellagio floor.
  ray.set(new THREE.Vector3(x, y + 1.4, z), new THREE.Vector3(0, -1, 0));
  ray.far = 4000;
  const hits = ray.intersectObjects(floors, false);
  return hits.find(h => h.point.y <= y + 0.3) || null;
}
function plantFeet(snap) {
  const hit = groundHit(camera.position.x, camera.position.y, camera.position.z);
  if (!hit) return false;
  const target = hit.point.y + walk.eye;
  if (snap || Math.abs(camera.position.y - target) > 4) camera.position.y = target;
  return true;
}
function wallBlocks(pos, dir, dist) {
  for (const hgt of [-1.05, -0.25]) {
    ray.set(new THREE.Vector3(pos.x, pos.y + hgt, pos.z), dir);
    ray.far = dist;
    const hit = ray.intersectObjects(walls, false)[0];
    if (!hit || hit.distance > dist) continue;
    const n = hit.face?.normal;
    if (n) {
      const up = Math.abs(n.clone().transformDirection(hit.object.matrixWorld).y);
      if (up > 0.65) continue; // floor or ceiling, not a wall
    }
    return true;
  }
  return false;
}
function syncWalkFromCamera() {
  const d = new THREE.Vector3(); camera.getWorldDirection(d);
  walk.yaw = Math.atan2(-d.x, -d.z); walk.pitch = Math.asin(clamp(d.y, -1, 1));
}
addEventListener('keydown', e => { walk.keys[e.code] = true; if (e.code === 'KeyF') fountains.play(Object.keys(SHOWS)[Math.floor(Math.random() * 3)]); });
addEventListener('keyup', e => { walk.keys[e.code] = false; });
let drag = null;
canvas.addEventListener('pointerdown', e => { if (S.mode === 'walk') { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); } });
canvas.addEventListener('pointermove', e => {
  if (S.mode !== 'walk' || !drag) return;
  walk.yaw -= (e.clientX - drag.x) * .0035; walk.pitch = clamp(walk.pitch - (e.clientY - drag.y) * .0035, -1.35, 1.35);
  drag = { x: e.clientX, y: e.clientY };
});
canvas.addEventListener('pointerup', () => { drag = null; });
const ray = new THREE.Raycaster(); ray.firstHitOnly = true;
function stepWalk(dt) {
  const k = walk.keys, f = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0) + walk.stick.y;
  const r = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0) + walk.stick.x;
  const speed = (k.ShiftLeft ? 22 : 4.2) * dt;
  const fwd = new THREE.Vector3(-Math.sin(walk.yaw), 0, -Math.cos(walk.yaw)), right = new THREE.Vector3(-fwd.z, 0, fwd.x);
  const move = fwd.multiplyScalar(f).add(right.multiplyScalar(r));
  if (move.lengthSq() > 0) {
    move.normalize().multiplyScalar(speed);
    const pos = camera.position;
    const dir = move.clone().normalize();
    const dist = speed + .4;
    // Slide along a facade instead of sticking when one axis is blocked.
    const tries = [move, new THREE.Vector3(move.x, 0, 0), new THREE.Vector3(0, 0, move.z)];
    for (const step of tries) {
      if (step.lengthSq() < 1e-6) continue;
      if (!wallBlocks(pos, step.clone().normalize(), dist)) { pos.add(step); break; }
    }
  }
  const hit = groundHit(camera.position.x, camera.position.y, camera.position.z);
  const target = hit ? hit.point.y + walk.eye : camera.position.y;
  const gap = Math.abs(camera.position.y - target);
  camera.position.y = gap > 8 ? target : lerp(camera.position.y, target, 1 - Math.exp(-dt * 12));
  const look = new THREE.Vector3(-Math.sin(walk.yaw) * Math.cos(walk.pitch), Math.sin(walk.pitch), -Math.cos(walk.yaw) * Math.cos(walk.pitch));
  camera.lookAt(camera.position.clone().add(look));
  controls.target.copy(camera.position).add(look.multiplyScalar(4));
}

// the private lift: lobby passage -> level 36 (107 m).  Doors slide, cab rises with you inside.
async function rideLift(up = true) {
  if (S.busy || !dyn.lift) return;
  S.busy = true; setMode('walk');
  const L = manifest.lift; const top = L.top;
  const cab = dyn.lift.find(o => o.name.startsWith('DYN_lift_cab'));
  const doors = dyn.lift.filter(o => o.name.includes('_door_'));
  const lvl = up ? 'g' : 'p', dest = up ? 'p' : 'g';
  const z0 = up ? 0 : top, z1 = up ? top : 0;
  const hall = W(L.x, L.y - 4.2, z0 + 1.65), inside = W(L.x, L.y + .2, z0 + 1.65);
  cab.position.y = cab.userData.rest.y + z0;
  await flyP(hall, W(L.x, L.y + 3, z0 + 1.6), 1.6);
  const ind = $('#lift'); ind.classList.add('on'); ind.querySelector('b').textContent = up ? 'L' : '36';
  await slideDoors(doors, lvl, 1); chime();
  await flyP(inside, W(L.x, L.y - 5, z0 + 1.6), 1.4);                  // step in and turn round
  await slideDoors(doors, lvl, 0);
  const dur = 26;
  await new Promise(res => {
    let t = 0;
    const f = dt => {
      t += dt; const k = clamp(t / dur), e = k < .1 ? (k / .1) ** 2 * .05 : k > .9 ? 1 - ((1 - k) / .1) ** 2 * .05 : .05 + (k - .1) / .8 * .9;
      const z = lerp(z0, z1, e);
      cab.position.y = cab.userData.rest.y + z;
      camera.position.y = z + 1.65 + Math.sin(t * 13) * .002;
      const floor = Math.max(1, Math.round(z / (top / 35)) + (z > 1 ? 1 : 0));
      ind.querySelector('b').textContent = z < 1 ? 'L' : (floor >= 36 ? '36' : String(floor));
      if (k >= 1) { liftTick = null; res(); }
    };
    liftTick = f;
  });
  chime();
  await slideDoors(doors, dest, 1);
  await flyP(W(L.x, L.y - 4.2, z1 + 1.65), W(L.x, L.y - 9, z1 + 1.7), 1.6);
  if (up) await flyP(W(L.x - 3.4, L.y - 3.6, z1 + 1.65), W(L.x - 5.5, L.y + 14, z1 + 2.0), 2.0);
  await slideDoors(doors, dest, 0);
  ind.classList.remove('on');
  S.walkY = z1; syncWalkFromCamera(); S.busy = false;
  showCaption(up ? { name: 'The Penthouse · Level 36', note: 'An invented residence behind the real arcade windows. Walk: drag to look, WASD to move.', evidence: 'X · invented' } :
    { name: 'Lobby level', note: 'Back on the ground floor.' });
}
let liftTick = null;
function flyP(pos, look, dur) { return new Promise(res => flyTo(pos, look, dur, res)); }
function slideDoors(doors, lvl, open) {
  return new Promise(res => {
    const set = doors.filter(o => o.userData.level === lvl);
    let t = 0;
    const f = dt => {
      t += dt; const k = ease(clamp(t / 1.3));
      for (const o of set) o.position.x = o.userData.rest.x + o.userData.side * (open ? k : 1 - k) * .9;
      if (t >= 1.3) { doorTick = null; res(); }
    };
    doorTick = f;
  });
}
let doorTick = null;
let actx;
function chime() {
  try {
    actx = actx || new AudioContext();
    for (const [f, d] of [[1318.5, 0], [1046.5, .18]]) {
      const o = actx.createOscillator(), g = actx.createGain();
      o.type = 'sine'; o.frequency.value = f; g.gain.setValueAtTime(0, actx.currentTime + d);
      g.gain.linearRampToValueAtTime(.08, actx.currentTime + d + .01); g.gain.exponentialRampToValueAtTime(.0001, actx.currentTime + d + 1.2);
      o.connect(g).connect(actx.destination); o.start(actx.currentTime + d); o.stop(actx.currentTime + d + 1.3);
    }
  } catch (_) { }
}

// ------------------------------------------------------------------ governed room index
let portableRoomPoll = 0;
function closePortableRoom() {
  clearInterval(portableRoomPoll); portableRoomPoll = 0;
  const overlay = $('#roomOverlay'), frame = $('#roomFrame');
  overlay?.classList.remove('on'); overlay?.setAttribute('aria-hidden','true');
  if (frame) frame.src = 'about:blank';
  $('#roomStatus') && ($('#roomStatus').textContent = '');
}
function openPortableRoom(room) {
  closePanels();
  const overlay = $('#roomOverlay'), frame = $('#roomFrame'), title = $('#roomTitle'), status = $('#roomStatus');
  if (!overlay || !frame) return;
  overlay.classList.add('on'); overlay.setAttribute('aria-hidden','false');
  if (title) title.textContent = room.label;
  if (status) status.textContent = 'Loading exact room…';
  frame.src = room.href;
  clearInterval(portableRoomPoll);
  let checks = 0;
  portableRoomPoll = setInterval(() => {
    checks++;
    try {
      const got = frame.contentWindow?.__reviewRoomIdentity || frame.contentWindow?.__museum?.reviewRoomIdentity || null;
      if (got === room.semanticId) {
        clearInterval(portableRoomPoll); portableRoomPoll = 0;
        if (status) status.textContent = room.semanticId + ' · verified';
        return;
      }
      if (got && got !== room.semanticId) {
        clearInterval(portableRoomPoll); portableRoomPoll = 0;
        frame.src = 'about:blank';
        if (status) status.textContent = 'Blocked: wrong room identity (' + got + ')';
        return;
      }
    } catch (_) {}
    if (checks >= 150) {
      clearInterval(portableRoomPoll); portableRoomPoll = 0;
      frame.src = 'about:blank';
      if (status) status.textContent = 'Blocked: exact room identity was not verified';
    }
  }, 200);
}

// ------------------------------------------------------------------ UI
function ui() {
  const list = $('#places');
  let lastGroup = '';
  PLACES.forEach((p, i) => {
    if (p.group !== lastGroup) { const h = document.createElement('h4'); h.textContent = p.group; list.appendChild(h); lastGroup = p.group; }
    const b = document.createElement('button'); b.textContent = p.name; b.onclick = () => { if (p.lift) rideLift(p.lift === 'up'); else go(p); closePanels(); };
    list.appendChild(b);
  });
  const roomList = $('#rooms');
  if (roomList) {
    const nativeHead = document.createElement('h4'); nativeHead.textContent = 'Bellagio · native'; roomList.appendChild(nativeHead);
    for (const name of BELLAGIO_ROOM_NAMES) {
      const place = PLACES.find(p => p.name === name);
      const b = document.createElement('button');
      b.innerHTML = '<b>' + name + '</b><span class="room-meta">' + (place?.note || 'Existing Bellagio destination') + '</span>';
      b.disabled = !place;
      b.onclick = () => { if (!place) return; if (place.lift) rideLift(place.lift === 'up'); else go(place); closePanels(); };
      roomList.appendChild(b);
    }
    const konaHead = document.createElement('h4'); konaHead.textContent = 'KONA · final recovered rooms'; roomList.appendChild(konaHead);
    for (const room of PORTABLE_ROOMS) {
      const b = document.createElement('button');
      b.innerHTML = '<span class="room-semantic">' + room.role + '</span><b>' + room.label + '</b><span class="room-meta">' + room.semanticId + '</span>';
      b.onclick = () => openPortableRoom(room);
      roomList.appendChild(b);
    }
  }
  const sh = $('#shows');
  for (const name of Object.keys(SHOWS)) { const b = document.createElement('button'); b.textContent = name; b.onclick = () => fountains.play(name); sh.appendChild(b); }
  $('#tod').oninput = e => { S.tod = +e.target.value; applyTime(); save(); };
  $('#modeBtn').onclick = () => { setMode(S.mode === 'orbit' ? 'walk' : 'orbit'); if (S.mode === 'walk') syncWalkFromCamera(); };
  $('#placesBtn').onclick = () => { closePanels(); $('#placesPanel').classList.toggle('on'); };
  $('#roomsBtn').onclick = () => { closePanels(); $('#roomsPanel').classList.toggle('on'); };
  $('#roomBack').onclick = closePortableRoom;
  $('#infoBtn').onclick = () => { closePanels(); $('#infoPanel').classList.toggle('on'); };
  $('.close').forEach(b => b.onclick = closePanels);
  if (new URLSearchParams(location.search).get('rooms') === '1') $('#roomsPanel')?.classList.add('on');
  $('#quality').value = S.quality; $('#quality').onchange = e => { S.quality = e.target.value; resize(); save(); };
  $('#exposure').value = S.exposure; $('#exposure').oninput = e => { S.exposure = +e.target.value; applyTime(); save(); };
  // on-screen stick for touch walking
  const st = $('#stick'); let sid = null, c0 = null;
  st.addEventListener('pointerdown', e => { sid = e.pointerId; c0 = { x: e.clientX, y: e.clientY }; st.setPointerCapture(sid); });
  st.addEventListener('pointermove', e => { if (e.pointerId !== sid) return; walk.stick.x = clamp((e.clientX - c0.x) / 50, -1, 1); walk.stick.y = clamp(-(e.clientY - c0.y) / 50, -1, 1); });
  st.addEventListener('pointerup', () => { sid = null; walk.stick.x = walk.stick.y = 0; });
  $('#infoBody').innerHTML = INFO;
}
function closePanels() { $$('.panel').forEach(p => p.classList.remove('on')); }

// hover names (evidence class) in orbit mode
const hover = new THREE.Raycaster(); const mouse = new THREE.Vector2(); let hoverT = 0;
canvas.addEventListener('pointermove', e => { mouse.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1); hoverT = .15; });

// ------------------------------------------------------------------ loop
const clock = new THREE.Clock();
function indoors() {
  if (!manifest) return false;
  const p = camera.position, x = p.x, y = -p.z, z = p.y;
  const inBox = b => b && x > b[0] && x < b[2] && y > b[1] && y < b[3] && z < b[4] + 3;
  if (inBox(manifest.lobby) || inBox(manifest.conservatory) || inBox(manifest.passage)) return true;
  const c = manifest.core, fl = manifest.penthouse.fl;
  return z > fl - 1 && z < 124 && Math.hypot(x - c[0], y - c[1]) < 135;
}
let wasIn = null;
function frame() {
  const dt = Math.min(clock.getDelta(), .05);
  if (tween) { tween.t += dt; const k = clamp(tween.t / tween.dur); tween.f(k); if (k >= 1) { const d = tween.done; tween = null; d && d(); } }
  if (doorTick) doorTick(dt);
  if (liftTick) liftTick(dt);
  if (S.mode === 'walk' && !tween && !liftTick) stepWalk(dt);
  if (S.mode === 'orbit' && !tween) controls.update();
  if (fountains) fountains.update(dt, S.night, renderer.getPixelRatio());
  const inn = indoors();
  if (inn !== wasIn) { wasIn = inn; scene.fog.density = inn ? 0 : .000025; applyTime(); }
  if (lakeRefl) lakeRefl.material.uniforms.uTime.value += dt;
  // Animated grain caused visible shimmer on high-density mobile displays.
  // Keep a stable seed on coarse pointers; desktop retains very subtle motion.
  if (!coarse) grade.uniforms.uTime.value += dt * .12;
  composer.render();
  requestAnimationFrame(frame);
}

// review helper: render one frame and POST it to the local server as a JPEG
window.__b = { scene, camera, renderer, bakedMats, S };
window.__snap = async name => { composer.render(); const data = renderer.domElement.toDataURL('image/jpeg', .9);
  await fetch('/snap', { method: 'POST', body: JSON.stringify({ name, data }) }); return data.length; };
window.__go = i => go(PLACES[i], .01);
window.__places = () => PLACES.map(p => p.name);
window.__time = t => { S.tod = t; applyTime(); };
resize();
loadAll().catch(err => { $('#loading').querySelector('p').textContent = 'Could not load the model: ' + err.message; console.error(err); });
frame();
