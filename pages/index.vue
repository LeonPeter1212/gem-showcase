<template>
  <div class="site">

    <!-- Full-screen Three.js canvas -->
    <canvas ref="canvasEl" class="scene-canvas" />

    <!-- ── HERO ─────────────────────────────────────────────────────────── -->
    <section class="section hero-section">
      <div class="hero-text">
        <p class="eyebrow" ref="eyebrowEl">Blockchain · Mobile · Web3</p>
        <h1 ref="headlineEl">The world's most<br /><em>unnecessarily</em><br />sophisticated wallet.</h1>
        <p class="sub" ref="subEl">
          Ganji isn't just a wallet.<br />
          It's the result of unprecedented blockchain breakthroughs.*
        </p>
        <p class="asterisk">* we just wanted to make something cool</p>
        <a class="cta-btn" href="#features">Get Ganji — it's free ↓</a>
      </div>
    </section>

    <!-- ── SECTION 2: What it does ──────────────────────────────────────── -->
    <section class="section feature-section" id="features">
      <div class="feature-block" ref="feat1El">
        <span class="feat-tag">01 / SEND</span>
        <h2>Send money<br />at the speed of<br /><em>thought.</em></h2>
        <p>Peer-to-peer transfers settle in under 3 seconds. No banks. No middlemen. Just you and whoever you're paying.</p>
      </div>
    </section>

    <section class="section feature-section">
      <div class="feature-block" ref="feat2El">
        <span class="feat-tag">02 / EARN</span>
        <h2>Your wallet<br />works while<br /><em>you sleep.</em></h2>
        <p>Stake your Ganji coins and earn passive yield. The blockchain keeps running — you keep earning.</p>
      </div>
    </section>

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
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ── Refs ───────────────────────────────────────────────────────────────────
const canvasEl  = ref<HTMLCanvasElement | null>(null)
const eyebrowEl = ref<HTMLElement | null>(null)
const headlineEl = ref<HTMLElement | null>(null)
const subEl     = ref<HTMLElement | null>(null)
const feat1El   = ref<HTMLElement | null>(null)
const feat2El   = ref<HTMLElement | null>(null)
const feat3El   = ref<HTMLElement | null>(null)

// ── Three.js internals ─────────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let coin: THREE.Group | null = null
let animId: number
const clock = new THREE.Clock()

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
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.4

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x03060f)

  // Subtle fog for depth
  scene.fog = new THREE.FogExp2(0x03060f, 0.04)

  // Environment map — essential for metallic PBR materials to look good
  const pmrem = new THREE.PMREMGenerator(renderer)
  pmrem.compileEquirectangularShader()
  const envTexture = pmrem.fromScene(new RoomEnvironment(), 0.04).texture
  scene.environment = envTexture
  pmrem.dispose()

  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 200)
  camera.position.set(0, 0.5, 5.5)

  // Lights
  const ambient = new THREE.AmbientLight(0x4488ff, 3.0)
  scene.add(ambient)

  const key = new THREE.DirectionalLight(0x88bbff, 8)
  key.position.set(3, 4, 3)
  scene.add(key)

  const rim = new THREE.DirectionalLight(0x2255ff, 5)
  rim.position.set(-3, 2, -3)
  scene.add(rim)

  const front = new THREE.DirectionalLight(0xaaccff, 4)
  front.position.set(0, 0, 5)
  scene.add(front)

  const under = new THREE.PointLight(0x0066ff, 6, 12)
  under.position.set(0, -3, 1)
  scene.add(under)

  // Stars
  buildStars()

  renderLoop()
}

function buildStars() {
  const N = 6000
  const pos = new Float32Array(N * 3)
  for (let i = 0; i < N; i++) {
    const phi = Math.acos(2 * Math.random() - 1)
    const th  = Math.random() * Math.PI * 2
    const r   = 40 + Math.random() * 30
    pos[i*3]   = Math.sin(phi) * Math.cos(th) * r
    pos[i*3+1] = Math.cos(phi) * r
    pos[i*3+2] = Math.sin(phi) * Math.sin(th) * r
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
    size: 0.06, sizeAttenuation: true, color: 0x88aaff, transparent: true, opacity: 0.6,
  })))
}

function loadCoin() {
  const loader = new GLTFLoader()
  loader.load('/models/ganji-coin.glb', (gltf) => {
    coin = gltf.scene
    coin.scale.setScalar(1.4)
    coin.rotation.x = Math.PI * 0.1
    scene.add(coin)
  })
}

function renderLoop() {
  animId = requestAnimationFrame(renderLoop)
  const t = clock.getElapsedTime()

  if (coin) {
    // Gentle idle float + spin
    coin.rotation.y = t * 0.4
    coin.position.y = Math.sin(t * 0.7) * 0.08
  }

  renderer.render(scene, camera)
}

// ── GSAP hero text entrance ────────────────────────────────────────────────
function animateHeroText() {
  const tl = gsap.timeline({ delay: 0.2 })
  tl.from(eyebrowEl.value,  { opacity: 0, y: 14, duration: 0.5, ease: 'power2.out' })
    .from(headlineEl.value, { opacity: 0, y: 40, duration: 0.8, ease: 'power3.out' }, '-=0.2')
    .from(subEl.value,      { opacity: 0, y: 20, duration: 0.6, ease: 'power2.out' }, '-=0.3')
    .from('.asterisk',      { opacity: 0, duration: 0.4 }, '-=0.1')
    .from('.cta-btn',       { opacity: 0, y: 12, duration: 0.5, ease: 'power2.out' }, '-=0.2')
}

// ── GSAP scroll-driven camera + coin ──────────────────────────────────────
function setupScrollAnimations() {
  // Section 2 — coin tilts & moves right, text comes in left
  ScrollTrigger.create({
    trigger: '#features',
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: 0.3, z: -0.2, duration: 1.2, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 1.6, duration: 1.2, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 4.5, duration: 1.5, ease: 'power2.inOut' })
      }
      gsap.from(feat1El.value, { opacity: 0, x: -60, duration: 0.8, ease: 'power3.out' })
    },
    onLeaveBack: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI * 0.1, z: 0, duration: 1.0, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 0, duration: 1.0, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 5.5, duration: 1.2, ease: 'power2.inOut' })
      }
    },
  })

  // Section 3 — coin flips to show back face
  ScrollTrigger.create({
    trigger: feat2El.value,
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI + 0.1, duration: 1.4, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: -1.6, duration: 1.2, ease: 'power2.inOut' })
      }
      gsap.from(feat2El.value, { opacity: 0, x: 60, duration: 0.8, ease: 'power3.out' })
    },
  })

  // Section 4 — coin comes back to center, zooms in close
  ScrollTrigger.create({
    trigger: feat3El.value,
    start: 'top 80%',
    onEnter: () => {
      if (coin) {
        gsap.to(coin.rotation, { x: Math.PI * 0.05, z: 0, duration: 1.4, ease: 'power2.inOut' })
        gsap.to(coin.position, { x: 0, y: 0, duration: 1.2, ease: 'power2.inOut' })
        gsap.to(camera.position, { z: 3.2, duration: 1.6, ease: 'power2.inOut' })
      }
      gsap.from(feat3El.value, { opacity: 0, y: 50, duration: 0.8, ease: 'power3.out' })
    },
  })
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}
</script>

<style scoped>
.site {
  position: relative;
}

.scene-canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* ── Sections ─────────────────────────────────────────────────────── */
.section {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 0 8vw;
}

/* ── Hero ─────────────────────────────────────────────────────────── */
.hero-section { align-items: center; }

.hero-text {
  max-width: 580px;
}

.eyebrow {
  font-size: 0.75rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #4488ff;
  margin-bottom: 1.4rem;
}

h1 {
  font-size: clamp(2.8rem, 6vw, 5.2rem);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  color: #e8eeff;
  margin-bottom: 1.6rem;
}

h1 em {
  font-style: italic;
  color: #4488ff;
}

.sub {
  font-size: 1.05rem;
  line-height: 1.7;
  color: #8899cc;
  margin-bottom: 0.6rem;
}

.asterisk {
  font-size: 0.72rem;
  color: #445577;
  margin-bottom: 2.2rem;
}

.cta-btn {
  display: inline-block;
  padding: 0.85rem 2rem;
  background: #1a3aff;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-decoration: none;
  border-radius: 2px;
  transition: background 0.2s, transform 0.2s;
}
.cta-btn:hover { background: #3355ff; transform: translateY(-2px); }

/* ── Features ─────────────────────────────────────────────────────── */
.feature-section:nth-of-type(even) { justify-content: flex-end; }

.feature-block {
  max-width: 520px;
}

.feat-tag {
  display: block;
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  color: #2255cc;
  text-transform: uppercase;
  margin-bottom: 1rem;
}

.feature-block h2 {
  font-size: clamp(2rem, 4.5vw, 3.8rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #d0d8ff;
  margin-bottom: 1.2rem;
}

.feature-block h2 em {
  font-style: italic;
  color: #4488ff;
}

.feature-block p {
  font-size: 1rem;
  line-height: 1.75;
  color: #6677aa;
}

/* ── Footer ───────────────────────────────────────────────────────── */
.footer-section { justify-content: center; text-align: center; flex-direction: column; gap: 0.6rem; }

.footer-brand {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: 0.3em;
  color: #1a3aff;
}

.footer-sub {
  color: #445577;
  font-size: 0.9rem;
  letter-spacing: 0.06em;
}

.footer-fine {
  font-size: 0.65rem;
  color: #223;
  letter-spacing: 0.08em;
  max-width: 500px;
}
</style>
