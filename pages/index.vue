<template>
  <div class="site">

    <!-- Full-screen Three.js canvas -->
    <canvas ref="canvasEl" class="scene-canvas" />

    <!-- Film grain overlay (CSS layer — GLSL grain added via post-process) -->

    <!-- ── HERO ──────────────────────────────────────────────────────────── -->
    <section class="section hero-section">
      <div class="hero-text">
        <p class="eyebrow" ref="eyebrowEl">Blockchain · Mobile · Web3</p>
        <h1 ref="headlineEl">
          The world's most<br />
          <em>unnecessarily</em><br />
          sophisticated wallet.
        </h1>
        <p class="sub" ref="subEl">
          Ganji isn't just a wallet.<br />
          It's the result of unprecedented blockchain breakthroughs.*
        </p>
        <p class="asterisk">* we just wanted to make something that actually works</p>
        <a class="cta-btn" href="#features">Get Ganji — it's free ↓</a>
      </div>
    </section>

    <!-- ── SECTION 2 ────────────────────────────────────────────────────── -->
    <section class="section feature-section" id="features">
      <div class="feature-block" ref="feat1El">
        <span class="feat-tag">01 / SEND</span>
        <h2>Send money<br />at the speed of<br /><em>thought.</em></h2>
        <p>Peer-to-peer transfers settle in under 3 seconds. No banks. No middlemen. Just you and whoever you're paying.</p>
      </div>
    </section>

    <!-- ── SECTION 3 ────────────────────────────────────────────────────── -->
    <section class="section feature-section feature-section--right">
      <div class="feature-block" ref="feat2El">
        <span class="feat-tag">02 / EARN</span>
        <h2>Your wallet<br />works while<br /><em>you sleep.</em></h2>
        <p>Stake your Ganji coins and earn passive yield. The blockchain keeps running — you keep earning.</p>
      </div>
    </section>

    <!-- ── SECTION 4 ────────────────────────────────────────────────────── -->
    <section class="section feature-section">
      <div class="feature-block" ref="feat3El">
        <span class="feat-tag">03 / SECURE</span>
        <h2>Military-grade.<br />Ridiculously<br /><em>simple.</em></h2>
        <p>256-bit encryption, biometric unlock, and self-custody keys. You own your money — actually own it.</p>
      </div>
    </section>

    <!-- ── FOOTER ────────────────────────────────────────────────────────── -->
    <section ref="footerEl" class="section footer-section">
      <div class="footer-inner">
        <p class="footer-brand">GANJI</p>
        <p class="footer-sub">Built different. &copy; 2026</p>
        <p class="footer-fine">THIS ENTIRE SITE IS A LEARNING PROJECT. NO FINANCIAL PRODUCT EXISTS. YET.</p>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ── Refs ───────────────────────────────────────────────────────────────────
const canvasEl   = ref<HTMLCanvasElement | null>(null)
const eyebrowEl  = ref<HTMLElement | null>(null)
const headlineEl = ref<HTMLElement | null>(null)
const subEl      = ref<HTMLElement | null>(null)
const feat1El    = ref<HTMLElement | null>(null)
const feat2El    = ref<HTMLElement | null>(null)
const feat3El    = ref<HTMLElement | null>(null)
const footerEl   = ref<HTMLElement | null>(null)

// ── Three.js internals ─────────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer
let composer: EffectComposer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let coin: THREE.Group | null = null
let coinWrapper: THREE.Group | null = null
let animId: number
const clock = new THREE.Clock()

// Mouse parallax — target is set instantly, lerp chases it each frame
const mouseLerp   = { x: 0, y: 0 }
const mouseTarget = { x: 0, y: 0 }

// Film grain shader — fragment shader that adds analog noise each frame
const GrainShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime:    { value: 0 },
    uAmount:  { value: 0.018 },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
  `,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform float uTime;
    uniform float uAmount;
    varying vec2 vUv;

    float rand(vec2 co) {
      return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
    }

    void main() {
      vec4 color = texture2D(tDiffuse, vUv);
      // Noise seed changes every frame via uTime
      float noise = rand(vUv + vec2(uTime * 0.001, uTime * 0.0007)) * 2.0 - 1.0;
      color.rgb += noise * uAmount;
      gl_FragColor = color;
    }
  `,
}

// ── Init ───────────────────────────────────────────────────────────────────
onMounted(() => {
  initThree()
  loadCoin()
  animateHeroText()
  // setupScrollAnimations() is called inside loadCoin callback once coin is ready
  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  renderer?.dispose()
  window.removeEventListener('resize', onResize)
  window.removeEventListener('mousemove', onMouseMove)
  ScrollTrigger.getAll().forEach(t => t.kill())
})

function onMouseMove(e: MouseEvent) {
  // Normalize to -1..1, Y flipped so up = positive
  mouseTarget.x =  (e.clientX / window.innerWidth)  * 2 - 1
  mouseTarget.y = -((e.clientY / window.innerHeight) * 2 - 1)
}

function initThree() {
  const canvas = canvasEl.value!
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 0.75
  renderer.shadowMap.enabled = true

  scene = new THREE.Scene()
  // No scene.background — CSS handles the warm radial gradient (see body style)
  scene.fog = new THREE.FogExp2(0x000000, 0.018)

  // PMREMGenerator — wraps scene for metallic environment reflections
  const pmrem = new THREE.PMREMGenerator(renderer)
  pmrem.compileEquirectangularShader()
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  pmrem.dispose()

  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200)
  camera.position.set(0, 0.3, 6)

  // ── Lighting ──────────────────────────────────────────────────────────────
  // Key — warm white from upper-right, angled so it doesn't flatten the face
  const key = new THREE.DirectionalLight(0xfff8e8, 2.5)
  key.position.set(5, 4, 3)
  key.castShadow = true
  scene.add(key)

  // Rim — warm gold from back-left, creates the bright silhouette edge
  const rimLight = new THREE.DirectionalLight(0xffcc44, 4)
  rimLight.position.set(-4, 2, -4)
  scene.add(rimLight)

  // Fill — very soft, front-low, lifts the shadow side without flattening
  const fill = new THREE.DirectionalLight(0xffe0aa, 0.6)
  fill.position.set(0, -3, 5)
  scene.add(fill)

  // Under glow — warm point light catches reeded edge from below
  const under = new THREE.PointLight(0xff8800, 2, 7)
  under.position.set(0, -2.5, 1)
  scene.add(under)

  // Ambient — bare minimum so shadowed areas aren't pure black
  scene.add(new THREE.AmbientLight(0x221a0a, 0.8))

  buildStars()

  // ── Post-processing: RenderPass → GrainPass → OutputPass ─────────────────
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  const grainPass = new ShaderPass(GrainShader)
  composer.addPass(grainPass)
  composer.addPass(new OutputPass())

  renderLoop()
}

function buildStars() {
  const N = 7000
  const pos = new Float32Array(N * 3)
  for (let i = 0; i < N; i++) {
    const phi = Math.acos(2 * Math.random() - 1)
    const th  = Math.random() * Math.PI * 2
    const r   = 45 + Math.random() * 25
    pos[i*3]   = Math.sin(phi) * Math.cos(th) * r
    pos[i*3+1] = Math.cos(phi) * r
    pos[i*3+2] = Math.sin(phi) * Math.sin(th) * r
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
    size: 0.07, sizeAttenuation: true, color: 0xffd980, transparent: true, opacity: 0.4,
  })))
}

function overrideMaterials(model: THREE.Group) {
  // Warm polished gold — coin face and edge
  const BODY_MAT = new THREE.MeshPhysicalMaterial({
    color: 0xc8820a,
    metalness: 1.0,
    roughness: 0.30,
    envMapIntensity: 2.2,
    clearcoat: 0.3,
    clearcoatRoughness: 0.25,
  })
  // Burnished darker gold — logo sits recessed/darker against the bright face
  const LOGO_MAT = new THREE.MeshPhysicalMaterial({
    color: 0x7a4800,
    metalness: 1.0,
    roughness: 0.38,
    envMapIntensity: 1.8,
  })
  // Slightly darker mid-gold — hairline rings (subtle groove contrast)
  const RING_MAT = new THREE.MeshPhysicalMaterial({
    color: 0xa06a00,
    metalness: 1.0,
    roughness: 0.45,
    envMapIntensity: 1.5,
  })
  // Bright gold — reeded edge catches the rim light
  const EDGE_MAT = new THREE.MeshPhysicalMaterial({
    color: 0xf0b020,
    metalness: 1.0,
    roughness: 0.18,
    envMapIntensity: 3.0,
    clearcoat: 0.6,
  })
  // Rim text — bright, readable
  const RIM_MAT = new THREE.MeshPhysicalMaterial({
    color: 0xf5c030,
    metalness: 1.0,
    roughness: 0.20,
    envMapIntensity: 2.2,
  })

  model.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return
    const n = child.name
    if (n === 'GanjiEdge') {
      child.material = EDGE_MAT
    } else if (n === 'GanjiLogo') {
      child.material = LOGO_MAT
    } else if (n === 'RingInner' || n === 'RingOuter') {
      child.material = RING_MAT
    } else if (n === 'RimText') {
      child.material = RIM_MAT
    } else {
      child.material = BODY_MAT
    }
    child.castShadow = true
    child.receiveShadow = true
  })
}

function loadCoin() {
  const loader = new GLTFLoader()
  loader.load('/models/ganji-coin.glb', (gltf) => {
    coin = gltf.scene
    coin.scale.setScalar(1.15)

    // rotation.x = +PI/2 → front face toward camera; small back-tilt shows top edge
    coin.rotation.x = Math.PI / 2 - 0.25

    overrideMaterials(coin)

    // coinWrapper carries scroll-driven position/tilt — clean zero-rotation parent
    coinWrapper = new THREE.Group()
    coinWrapper.position.x = 1.8
    scene.add(coinWrapper)
    coinWrapper.add(coin)

    setupScrollAnimations()
  })
}

function renderLoop() {
  animId = requestAnimationFrame(renderLoop)
  const t = clock.getElapsedTime()

  if (coin && coinWrapper) {
    // Lerp mouse influence — ~8% per frame gives ~120ms of lag at 60fps
    mouseLerp.x += (mouseTarget.x - mouseLerp.x) * 0.08
    mouseLerp.y += (mouseTarget.y - mouseLerp.y) * 0.08

    coin.rotation.y = t * 0.35                                         // continuous spin
    coin.rotation.x = (Math.PI / 2 - 0.25) + mouseLerp.y * 0.22      // tilt fwd/back with mouse Y
    coin.rotation.z = -mouseLerp.x * 0.14                             // lean with mouse X
    coinWrapper.position.y = Math.sin(t * 0.6) * 0.07                 // gentle float
  }

  // Update grain shader time uniform every frame (makes noise animate)
  const grainPass = composer.passes.find(
    (p): p is ShaderPass => p instanceof ShaderPass
  )
  if (grainPass) grainPass.uniforms['uTime'].value = t * 1000

  composer.render()
}

// ── GSAP: hero text entrance ───────────────────────────────────────────────
function animateHeroText() {
  const tl = gsap.timeline({ delay: 0.3 })
  tl.from(eyebrowEl.value,   { opacity: 0, y: 14, duration: 0.5, ease: 'power2.out' })
    .from(headlineEl.value,  { opacity: 0, y: 40, duration: 0.9, ease: 'power3.out' }, '-=0.2')
    .from(subEl.value,       { opacity: 0, y: 20, duration: 0.6, ease: 'power2.out' }, '-=0.3')
    .from('.asterisk',       { opacity: 0, duration: 0.5 }, '-=0.1')
    .from('.cta-btn',        { opacity: 0, y: 12, duration: 0.5, ease: 'power2.out' }, '-=0.2')
}

// ── GSAP: scroll-driven coin + camera ─────────────────────────────────────
function setupScrollAnimations() {
  // Single timeline spanning the full page scroll.
  // Total scroll = 4 × 100vh (5 sections). Timeline = 4 units → 1 unit per 100vh.
  // Each transition takes 0.4 units (~40vh), rest is hold time.
  const w = coinWrapper!

  // Scrubbed timeline — each unit = 1 section height (100vh).
  // No camera zoom — just coin tilt and side-to-side movement.
  const tl = gsap.timeline({ defaults: { ease: 'power1.inOut' } })

  // Hero → Features: coin tilts slightly to show depth
  tl.to(w.rotation, { x: 0.15, z: -0.10, duration: 1 })

  // Features → Earn: coin crosses to left, reverses tilt
  tl.to(w.position, { x: -1.8, duration: 1 })
  tl.to(w.rotation, { x: -0.15, z: 0.10, duration: 1 }, '<')

  // Earn → Secure: coin returns to right, levels out
  tl.to(w.position, { x: 1.5, duration: 1 })
  tl.to(w.rotation, { x: 0, z: 0, duration: 1 }, '<')

  // end = 3 × 100vh so each section maps to exactly 1 timeline unit.
  // The SECURE state is fully reached at scroll=300vh (section start),
  // then holds for the remaining footer scroll.
  ScrollTrigger.create({
    animation: tl,
    trigger: document.documentElement,
    start: 'top top',
    end: '+=' + window.innerHeight * 3,
    scrub: 0.8,
  })

  // Text: snapshot-style (not scrubbed — snaps in as section enters)
  ScrollTrigger.create({
    trigger: '#features', start: 'top 60%',
    onEnter:    () => gsap.fromTo(feat1El.value, { opacity: 0, x: -70 }, { opacity: 1, x: 0, duration: 0.9, ease: 'power3.out' }),
    onLeaveBack: () => gsap.to(feat1El.value, { opacity: 0, x: -70, duration: 0.5 }),
  })
  ScrollTrigger.create({
    trigger: feat2El.value, start: 'top 60%',
    onEnter:    () => gsap.fromTo(feat2El.value, { opacity: 0, x: 70 }, { opacity: 1, x: 0, duration: 0.9, ease: 'power3.out' }),
    onLeaveBack: () => gsap.to(feat2El.value, { opacity: 0, x: 70, duration: 0.5 }),
  })
  ScrollTrigger.create({
    trigger: feat3El.value, start: 'top 60%',
    onEnter:    () => gsap.fromTo(feat3El.value, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.9, ease: 'power3.out' }),
    onLeaveBack: () => gsap.to(feat3El.value, { opacity: 0, y: 60, duration: 0.5 }),
  })

  // Footer: fade canvas out as footer sweeps in, restore on scroll back
  ScrollTrigger.create({
    trigger: footerEl.value,
    start: 'top 90%',
    end: 'top 10%',
    scrub: 0.6,
    onUpdate: (self) => {
      if (canvasEl.value) canvasEl.value.style.opacity = String(1 - self.progress)
    },
    onLeaveBack: () => {
      if (canvasEl.value) canvasEl.value.style.opacity = '1'
    },
  })
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
  composer.setSize(window.innerWidth, window.innerHeight)
}
</script>

<style scoped>
.site {
  position: relative;
}

/* ── Canvas ──────────────────────────────────────────────────────────────── */
.scene-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* ── Sections ────────────────────────────────────────────────────────────── */
.section {
  position: relative;
  z-index: 2;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 0 8vw;
}

/* ── Hero ────────────────────────────────────────────────────────────────── */
.hero-section { align-items: center; }

.hero-text { max-width: 600px; }

.eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #8a7a5a;
  margin-bottom: 1.6rem;
}

h1 {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: clamp(2.8rem, 6vw, 5.6rem);
  font-weight: 400;
  line-height: 1.08;
  letter-spacing: -0.01em;
  color: #f2ede4;
  margin-bottom: 1.8rem;
}

h1 em {
  font-style: italic;
  color: #d4920a;
}

.sub {
  font-size: 1.05rem;
  line-height: 1.75;
  color: #7a6e5a;
  margin-bottom: 0.5rem;
}

.asterisk {
  font-size: 0.68rem;
  color: #3d3020;
  margin-bottom: 2.4rem;
  letter-spacing: 0.02em;
}

.cta-btn {
  display: inline-block;
  padding: 0.9rem 2.2rem;
  background: #c48a0a;
  color: #000;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-decoration: none;
  border-radius: 2px;
  transition: background 0.2s, transform 0.15s;
}
.cta-btn:hover { background: #e0a010; transform: translateY(-2px); }

/* ── Feature sections ────────────────────────────────────────────────────── */
.feature-section { justify-content: flex-start; }
.feature-section--right { justify-content: flex-end; }

.feature-block { max-width: 500px; }

.feat-tag {
  display: block;
  font-size: 0.65rem;
  letter-spacing: 0.22em;
  color: #8a7a5a;
  text-transform: uppercase;
  margin-bottom: 1.1rem;
}

.feature-block h2 {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: clamp(2rem, 4.5vw, 4rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: -0.01em;
  color: #f2ede4;
  margin-bottom: 1.3rem;
}

.feature-block h2 em {
  font-style: italic;
  color: #d4920a;
}

.feature-block p {
  font-size: 1rem;
  line-height: 1.8;
  color: #6a5e4a;
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer-section {
  justify-content: center;
  text-align: center;
  flex-direction: column;
  gap: 0.8rem;
  background: #ffffff;
  position: relative;
  isolation: isolate;
}

.footer-brand {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 3.5rem;
  font-weight: 400;
  letter-spacing: 0.25em;
  color: #c48a0a;
}

.footer-sub {
  color: #4a3e2e;
  font-size: 0.88rem;
  letter-spacing: 0.08em;
}

.footer-fine {
  font-size: 0.62rem;
  color: #2a2016;
  letter-spacing: 0.1em;
  max-width: 480px;
}
</style>
