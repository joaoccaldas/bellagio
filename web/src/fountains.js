// Fountains of Bellagio — GPU particle show over the surveyed nozzle layout.
// Each nozzle has a schedule (height, tilt, azimuth) sampled 10x/s into a ring-buffer texture;
// every droplet looks up the schedule at its own launch time, so trajectories stay physically consistent.
import * as THREE from 'three';

const G = 9.81, FT = .3048;
const MAXH = { oar: 77 * FT, mini: 100 * FT, super: 240 * FT, extreme: 460 * FT };
const ROWS = 128, RATE = 10;                   // 12.8 s of history (a 140 m jet flies ~10.7 s)
const PER = { oar: 40, mini: 44, super: 72, extreme: 110 };

// ------------------------------------------------------------------ choreography
// Each show is a function (n, t) -> [height 0..1, tilt rad, azimuth rad]; n = nozzle record.
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const pulse = (x, w) => Math.exp(-x * x / (w * w));
export const SHOWS = {
  'Grand finale': { dur: 60, f(n, t) {
    const ph = t / 60;
    if (n.k === 'extreme') return [ph > .78 ? .95 : 0, 0, 0];
    if (n.g === 'arc') { const wv = pulse(((n.u - (t * .09) % 1.4) + 1.4) % 1.4 - .2, .09); return [(.25 + .75 * wv) * smooth(.02, .1, ph) * (n.k === 'super' ? 1 : .6), Math.sin(n.u * 31 + t) * .1, n.u * 20]; }
    if (n.g.startsWith('ring')) { const sw = Math.sin(t * 1.3 + n.u * 12.57); return [.55 + .25 * sw, .35 + .15 * sw, n.u * 6.283]; }
    if (n.g === 'front') return [ph > .55 ? .5 + .5 * Math.sin(n.u * 60 - t * 3) ** 2 : 0, 0, 0];
    return [0, 0, 0];
  } },
  'Oarsmen waltz': { dur: 45, f(n, t) {
    if (n.k === 'oar' || n.g.startsWith('ring')) { const s = Math.sin(t * 2.1 + (n.g === 'ring_out' ? 0 : 1.57)); return [.75, .15 + .45 * Math.abs(s), n.u * 6.283 + (s > 0 ? 0 : 3.14) * (n.g === 'arc' ? 1 : 0)]; }
    if (n.g === 'arc' && n.k === 'super') return [.35 * pulse(((n.u * 4 - t * .5) % 1 + 1) % 1 - .5, .15), 0, 0];
    return [0, 0, 0];
  } },
  'Curtain': { dur: 40, f(n, t) {
    if (n.g === 'front') { const w = smooth(0, .1, ((t * .06 - n.u) + 1) % 1); return [.35 + .5 * w, .08, 3.14]; }
    if (n.g === 'arc') return [n.k === 'super' ? .6 * smooth(.3, .6, t / 40) : .25, 0, 0];
    return [0, 0, 0];
  } },
};

export class Fountains {
  constructor(scene, nozzles, lakeY, toWorld) {
    this.noz = nozzles; this.n = nozzles.length; this.t = 0; this.tick = 0; this.show = null; this.showT = 0;
    this.lakeY = lakeY; this.light = 0; this.idleGlow = 0;
    this.data = new Float32Array(this.n * ROWS * 4);
    this.tex = new THREE.DataTexture(this.data, this.n, ROWS, THREE.RGBAFormat, THREE.FloatType);
    this.tex.minFilter = this.tex.magFilter = THREE.NearestFilter; this.tex.needsUpdate = true;
    // build particle buffers
    let total = 0; for (const z of nozzles) total += PER[z.k];
    const pos = new Float32Array(total * 3), nid = new Float32Array(total), seed = new Float32Array(total * 2);
    let i = 0;
    nozzles.forEach((z, k) => {
      const p = toWorld(z.x, z.y, lakeY);
      for (let j = 0; j < PER[z.k]; j++, i++) {
        pos.set([p.x, p.y, p.z], i * 3); nid[i] = k;
        seed[i * 2] = (j + Math.random()) / PER[z.k]; seed[i * 2 + 1] = Math.random();
      }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('nid', new THREE.BufferAttribute(nid, 1));
    g.setAttribute('seed', new THREE.BufferAttribute(seed, 2));
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(pos[0], 60, pos[2]), 600);
    const maxh = new Float32Array(total); i = 0;
    nozzles.forEach(z => { for (let j = 0; j < PER[z.k]; j++) maxh[i++] = MAXH[z.k]; });
    g.setAttribute('maxh', new THREE.BufferAttribute(maxh, 1));
    this.mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.NormalBlending,
      uniforms: { uSched: { value: this.tex }, uN: { value: this.n }, uTime: { value: 0 }, uHead: { value: 0 }, uRows: { value: ROWS },
        uRate: { value: RATE }, uLight: { value: 0 }, uPx: { value: 1 }, uDay: { value: 1 }, uSun: { value: new THREE.Vector3(.5, .6, .3) } },
      vertexShader: `
        attribute float nid; attribute vec2 seed; attribute float maxh;
        uniform sampler2D uSched; uniform float uN, uTime, uHead, uRows, uRate, uPx;
        varying float vA; varying float vH; varying float vT;
        void main(){
          // flight time budget from the jet's max height; each droplet cycles with its own phase
          float T = 2.0 * sqrt(2.0 * maxh / 9.81) * 1.05;
          float age = fract(seed.x + uTime / T) * T;
          float launch = uTime - age;
          // schedule row at launch time (ring buffer: head row = now)
          float back = floor(age * uRate);
          float row = mod(uHead - back + uRows, uRows);
          vec4 s = texture2D(uSched, vec2((nid + .5) / uN, (row + .5) / uRows));
          float h = s.x * maxh, tilt = s.y, az = s.z;
          float vz = sqrt(2.0 * 9.81 * max(h, 0.0));
          float vh = vz * tan(tilt);
          vec3 v = vec3(cos(az) * vh, vz, -sin(az) * vh);
          // aerodynamic spread grows with time in flight
          float spread = .05 + .018 * age * vz;
          vec3 jit = (vec3(fract(seed.y * 91.7), fract(seed.y * 37.3), fract(seed.y * 13.1)) - .5) * spread;
          vec3 p = position + v * age + vec3(0., -4.905 * age * age, 0.) + jit * age;
          vA = h > .5 ? smoothstep(0., .4, age) * (1. - smoothstep(T * .8, T, age)) : 0.;
          if (p.y < position.y) vA = 0.;
          vH = (p.y - position.y); vT = age / T;
          vec4 mv = modelViewMatrix * vec4(p, 1.);
          gl_Position = projectionMatrix * mv;
          gl_PointSize = clamp(uPx * (0.35 + .012 * h + age * .35) * 300. / -mv.z, 1., 48.);
        }`,
      fragmentShader: `
        uniform float uLight, uDay; varying float vA; varying float vH; varying float vT;
        void main(){
          vec2 c = gl_PointCoord - .5; float r = dot(c, c) * 4.;
          float a = exp(-r * 3.) * vA * .30;
          if (a < .003) discard;
          vec3 day = vec3(.93, .96, 1.) * (.75 + .25 * (1. - vT));
          vec3 lit = vec3(1., .96, .88) * uLight * exp(-vH / 38.) * 2.2 + vec3(.05, .07, .12);
          gl_FragColor = vec4(mix(lit, day, uDay), a);
        }`,
    });
    this.points = new THREE.Points(g, this.mat);
    this.points.frustumCulled = false; this.points.renderOrder = 5;
    scene.add(this.points);
    // underwater lamps (one glow disc per ring/arc cluster) — visible at night
    this.write(0);
  }
  play(name) { this.show = SHOWS[name]; this.showT = 0; this.name = name; }
  stop() { this.show = null; }
  write(time) {
    const row = this.tick % ROWS;
    for (let k = 0; k < this.n; k++) {
      const n = this.noz[k];
      let v = [0, 0, 0];
      if (this.show) v = this.show.f(n, this.showT);
      const o = (row * this.n + k) * 4;
      this.data[o] = v[0]; this.data[o + 1] = v[1]; this.data[o + 2] = v[2]; this.data[o + 3] = 1;
    }
    this.tex.needsUpdate = true;
    this.mat.uniforms.uHead.value = row;
    this.tick++;
  }
  update(dt, night, pxScale) {
    this.t += dt;
    if (this.show) { this.showT += dt; if (this.showT > this.show.dur) this.show = null; }
    this.acc = (this.acc || 0) + dt;
    while (this.acc > 1 / RATE) { this.acc -= 1 / RATE; this.write(this.t); }
    const u = this.mat.uniforms;
    u.uTime.value = this.t; u.uLight.value = night; u.uDay.value = 1 - night; u.uPx.value = pxScale;
  }
  get playing() { return !!this.show; }
}
