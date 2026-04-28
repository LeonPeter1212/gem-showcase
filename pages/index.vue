<template>
  <div class="site">

    <!-- Full-screen Three.js canvas -->
    <canvas ref="canvasEl" class="scene-canvas" />

    <!-- Film grain overlay (CSS layer — GLSL grain added via post-process) -->
    <div class="grain-overlay" />

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
    <section class="section footer-section">
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

// ── Three.js internals ─────────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer
let composer: EffectComposer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let coin: THREE.Group | null = null
let animId: number
const clock = new THREE.Clock()

// Film grain shader — fragment shader that adds analog noise each frame
const GrainShader = {
  uniforms: {
    tDiffuse: { value: null },
    uTime:    { value: 0 },
    uAmount:  { value: 0.045 },
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
  setupScrollAnimations()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  renderer?.dispose()
  window.removeEventListener('resize', onResize)
  ScrollTrigger.getAll().forEach(t => t.kill())
})

function initThree() {
  const canvas = canvasEl.value!
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.6
  renderer.shadowMap.enabled = true

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x020510)
  scene.fog = new THREE.FogExp2(0x020510, 0.035)

  // PMREMGenerator — wraps scene for metallic environment reflections
  const pmrem = new THREE.PMREMGenerator(renderer)
  pmrem.compileEquirectangularShader()
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  pmrem.dispose()

  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200)
  camera.position.set(0, 0.3, 6)

  // ── Lighting ──────────────────────────────────────────────────────────────
  // Key — warm-blue area from upper right (like the reference coin photo)
  const key = new THREE.DirectionalLight(0x88bbff, 10)
  key.position.set(4, 5, 3)
  key.castShadow = true
  scene.add(key)

  // Rim — deep blue from back-left (creates silhouette edge like the coins)
  const rim = new THREE.DirectionalLight(0x2244cc, 8)
  rim.position.set(-5, 3, -4)
  scene.add(rim)

  // Fill — soft from front-below (lifts shadows without washing out)
  const fill = new THREE.DirectionalLight(0x6699ff, 3)
  fill.position.set(0, -2, 6)
  scene.add(fill)

  // Under glow — blue point beneath coin
  const under = new THREE.PointLight(0x0044ff, 12, 8)
  under.position.set(0, -2.5, 0.5)
  scene.add(under)

  // Ambient — very low, preserves the dark drama
  scene.add(new THREE.AmbientLight(0x1133aa, 1.5))

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
    size: 0.07, sizeAttenuation: true, color: 0x99bbff, transparent: true, opacity: 0.55,
  })))
}

function overrideMaterials(model: THREE.Group) {
  // Override Blender-exported materials with Three.js PBR equivalents
  // This guarantees consistent rendering regardless of GLTF export quality
  const COIN_MAT = new THREE.MeshPhysicalMaterial({
    color: 0x0a2266,
    metalness: 1.0,
    roughness: 0.05,
    envMapIntensity: 3.0,
    clearcoat: 1.0,
    clearcoatRoughness: 0.02,
  })
  const LOGO_MAT = new THREE.MeshPhysicalMaterial({
    color: 0x4488ff,
    metalness: 1.0,
    roughness: 0.15,
    envMapIntensity: 2.5,
    clearcoat: 0.5,
  })
  const RING_MAT = new THREE.MeshPhysicalMaterial({
    color: 0x2255cc,
    metalness: 0.9,
    roughness: 0.2,
    transparent: true,
    opacity: 0.75,
    envMapIntensity: 2.0,
  })

  model.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return
    const n = child.name
    if (n.includes('Orbit') || n.includes('Ring') || n.includes('Torus')) {
      child.material = RING_MAT
    } else if (n.includes('Logo') || n.includes('Text') || n.includes('GanjiLogo')) {
      child.material = LOGO_MAT
    } else {
      child.material = COIN_MAT
    }
    child.castShadow = true
    child.receiveShadow = true
  })
}

function loadCoin() {
  const loader = new GLTFLoader()
  loader.load('/models/ganji-coin.glb', (gltf) => {
    coin = gltf.scene
    coin.scale.setScalar(1.5)
    coin.rotation.x = Math.PI * 0.08
    overrideMaterials(coin)
    scene.add(coin)
  })
}

function renderLoop() {
  animId = requestAnimationFrame(renderLoop)
  const t = clock.getElapsedTime()

  if (coin) {
    coin.rotation.y = t * 0.35
    coin.position.y = Math.sin(t * 0.6) * 0.07
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
  // Section 2 — coin slides right, text enters from left
  ScrollTrigger.create({
    trigger: '#features',
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: 0.25, z: -0.15, duration: 1.3, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 1.8,            duration: 1.2, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 4.8,           duration: 1.5, ease: 'power2.inOut' })
      }
      gsap.from(feat1El.value, { opacity: 0, x: -70, duration: 0.9, ease: 'power3.out' })
    },
    onLeaveBack: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI * 0.08, z: 0, duration: 1.1, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 0,               duration: 1.1, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 6,              duration: 1.3, ease: 'power2.inOut' })
      }
    },
  })

  // Section 3 — coin flips to reveal back, text from right
  ScrollTrigger.create({
    trigger: feat2El.value,
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI + 0.08, duration: 1.5, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: -1.8,            duration: 1.2, ease: 'power2.inOut' })
      }
      gsap.from(feat2El.value, { opacity: 0, x: 70, duration: 0.9, ease: 'power3.out' })
    },
  })

  // Section 4 — coin zooms in close to centre
  ScrollTrigger.create({
    trigger: feat3El.value,
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI * 0.04, z: 0,  duration: 1.4, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 0, y: 0,                duration: 1.2, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 3.0,                  duration: 1.6, ease: 'power2.inOut' })
      }
      gsap.from(feat3El.value, { opacity: 0, y: 60, duration: 0.9, ease: 'power3.out' })
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

/* ── Grain overlay ───────────────────────────────────────────────────────── */
/* Adds a second layer of CSS grain on top of the WebGL grain for extra depth */
.grain-overlay {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: 0.04;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 160px 160px;
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
  color: #3366dd;
  margin-bottom: 1.6rem;
}

h1 {
  font-size: clamp(2.8rem, 6vw, 5.6rem);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -0.03em;
  color: #dde6ff;
  margin-bottom: 1.8rem;
}

h1 em {
  font-style: italic;
  color: #4488ff;
  font-weight: 700;
}

.sub {
  font-size: 1.05rem;
  line-height: 1.75;
  color: #6677aa;
  margin-bottom: 0.5rem;
}

.asterisk {
  font-size: 0.68rem;
  color: #334;
  margin-bottom: 2.4rem;
  letter-spacing: 0.02em;
}

.cta-btn {
  display: inline-block;
  padding: 0.9rem 2.2rem;
  background: #1133ee;
  color: #fff;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-decoration: none;
  border-radius: 2px;
  transition: background 0.2s, transform 0.15s;
}
.cta-btn:hover { background: #2244ff; transform: translateY(-2px); }

/* ── Feature sections ────────────────────────────────────────────────────── */
.feature-section { justify-content: flex-start; }
.feature-section--right { justify-content: flex-end; }

.feature-block { max-width: 500px; }

.feat-tag {
  display: block;
  font-size: 0.65rem;
  letter-spacing: 0.22em;
  color: #1a44bb;
  text-transform: uppercase;
  margin-bottom: 1.1rem;
}

.feature-block h2 {
  font-size: clamp(2rem, 4.5vw, 4rem);
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -0.025em;
  color: #c8d4ff;
  margin-bottom: 1.3rem;
}

.feature-block h2 em {
  font-style: italic;
  color: #4488ff;
}

.feature-block p {
  font-size: 1rem;
  line-height: 1.8;
  color: #556699;
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer-section {
  justify-content: center;
  text-align: center;
  flex-direction: column;
  gap: 0.8rem;
}

.footer-brand {
  font-size: 3.5rem;
  font-weight: 900;
  letter-spacing: 0.35em;
  color: #1133ee;
}

.footer-sub {
  color: #334466;
  font-size: 0.88rem;
  letter-spacing: 0.08em;
}

.footer-fine {
  font-size: 0.62rem;
  color: #1a2233;
  letter-spacing: 0.1em;
  max-width: 480px;
}
</style>
