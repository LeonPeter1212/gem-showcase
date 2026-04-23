<template>
  <div class="page-wrapper">
    <!-- ── Three.js canvas ────────────────────────────────────────── -->
    <canvas ref="canvasEl" class="scene-canvas" />

    <!-- ── Hero text ─────────────────────────────────────────────── -->
    <section class="hero-section" ref="heroSection">
      <div class="hero-content" ref="heroContent">
        <p class="hero-eyebrow" ref="eyebrow">Blender × Three.js × GSAP</p>
        <h1 class="hero-title" ref="heroTitle">
          The Gem<br /><em>Collection</em>
        </h1>
        <p class="hero-sub" ref="heroSub">
          Procedurally sculpted in Blender. Brought to life with Three.js.<br />
          Animated with GSAP.
        </p>
        <button class="cta-btn" ref="ctaBtn" @click="scrollToInfo">
          Explore the Collection
          <span class="cta-arrow">↓</span>
        </button>
      </div>

      <!-- Floating gem labels -->
      <div
        v-for="gem in gemLabels"
        :key="gem.name"
        class="gem-label"
        :ref="el => setLabelRef(el as HTMLElement, gem.name)"
        :style="{ opacity: 0 }"
      >
        {{ gem.name }}
      </div>
    </section>

    <!-- ── Scroll spacer (drives GSAP ScrollTrigger timeline) ──── -->
    <div class="scroll-driver" ref="scrollDriver"></div>

    <!-- ── Info cards ─────────────────────────────────────────────── -->
    <section class="info-section" ref="infoSection" id="info">
      <div class="info-grid">
        <div
          v-for="(gem, i) in gemData"
          :key="gem.name"
          class="gem-card"
          :ref="el => setCardRef(el as HTMLElement, i)"
        >
          <div class="gem-card-dot" :style="{ background: gem.hex }"></div>
          <h3 class="gem-card-name">{{ gem.name }}</h3>
          <p class="gem-card-origin">{{ gem.origin }}</p>
          <p class="gem-card-desc">{{ gem.desc }}</p>
          <div class="gem-card-price">
            <span class="price-label">Est. Value</span>
            <span class="price-val">{{ gem.price }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Footer ─────────────────────────────────────────────────── -->
    <footer class="site-footer">
      <p>PigaBid &mdash; AI-Assisted 3D Showcase &copy; 2026</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ── Refs ───────────────────────────────────────────────────────────────────
const canvasEl     = ref<HTMLCanvasElement | null>(null)
const heroContent  = ref<HTMLElement | null>(null)
const eyebrow      = ref<HTMLElement | null>(null)
const heroTitle    = ref<HTMLElement | null>(null)
const heroSub      = ref<HTMLElement | null>(null)
const ctaBtn       = ref<HTMLElement | null>(null)
const scrollDriver = ref<HTMLElement | null>(null)
const infoSection  = ref<HTMLElement | null>(null)
const labelRefs    = ref<Record<string, HTMLElement>>({})
const cardRefs     = ref<HTMLElement[]>([])

const setLabelRef = (el: HTMLElement | null, name: string) => {
  if (el) labelRefs.value[name] = el
}
const setCardRef = (el: HTMLElement | null, i: number) => {
  if (el) cardRefs.value[i] = el
}

// ── Data ───────────────────────────────────────────────────────────────────
const gemLabels = [
  { name: 'Sapphire' }, { name: 'Ruby' },  { name: 'Emerald' },
  { name: 'Amethyst' }, { name: 'Topaz' },
]

const gemData = [
  { name: 'Sapphire',    hex: '#1040cc', origin: 'Kashmir, India',   desc: 'Royal blue corundum, the stone of wisdom and royalty.',          price: 'KSh 4.8M' },
  { name: 'Ruby',        hex: '#cc1010', origin: 'Mogok, Myanmar',   desc: 'Pigeon-blood red corundum. The rarest of all precious stones.',   price: 'KSh 6.2M' },
  { name: 'Emerald',     hex: '#10a040', origin: 'Muzo, Colombia',   desc: 'The lushest green beryl — perfection in every facet.',            price: 'KSh 3.1M' },
  { name: 'Amethyst',    hex: '#8020cc', origin: 'Zambia, Africa',   desc: 'Vivid violet quartz. African amethysts lead the world market.',    price: 'KSh 0.8M' },
  { name: 'Topaz',       hex: '#ddcc00', origin: 'Ouro Preto, Brazil', desc: 'Imperial topaz, the rarest variety, a warm amber fire.',         price: 'KSh 1.4M' },
  { name: 'Aquamarine',  hex: '#10cccc', origin: 'Marambaia, Brazil', desc: 'Sea-blue beryl, clarity rivalling fine diamonds.',                price: 'KSh 1.1M' },
  { name: 'Garnet',      hex: '#cc1040', origin: 'Umba Valley, Kenya', desc: 'Rare Kenyan spessartine garnets with an intense neon-orange.',   price: 'KSh 0.6M' },
  { name: 'Tanzanite',   hex: '#4020cc', origin: 'Merelani, Tanzania', desc: 'Found only near Kilimanjaro — 1000× rarer than diamonds.',       price: 'KSh 2.9M' },
]

// ── Three.js state ─────────────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let animationId: number
let heroGem: THREE.Object3D | null = null
let orbitGroup: THREE.Group | null = null
let allGems: THREE.Object3D[] = []
const mouse = { x: 0, y: 0 }

// ── Scroll progress (driven by GSAP) ──────────────────────────────────────
const scroll = { progress: 0 }

function initThree() {
  if (!canvasEl.value) return

  // Renderer
  renderer = new THREE.WebGLRenderer({
    canvas: canvasEl.value,
    antialias: true,
    alpha: true,
  })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  renderer.outputColorSpace = THREE.SRGBColorSpace

  // Scene
  scene = new THREE.Scene()

  // Camera
  camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200)
  camera.position.set(0, 0, 18) // start far back for entrance anim

  // Lights (in addition to exported Blender lights)
  const ambient = new THREE.AmbientLight(0x8888cc, 0.4)
  scene.add(ambient)

  const key = new THREE.PointLight(0xffeebb, 3, 30)
  key.position.set(5, 8, 6)
  scene.add(key)

  const fill = new THREE.PointLight(0x4466ff, 2, 20)
  fill.position.set(-5, 2, 4)
  scene.add(fill)

  const rim = new THREE.PointLight(0xcc44ff, 1.5, 20)
  rim.position.set(0, -4, -3)
  scene.add(rim)

  // Load GLB
  const loader = new GLTFLoader()
  loader.load('/gem_scene.glb', (gltf) => {
    const model = gltf.scene
    scene.add(model)

    // Grab hero gem and orbits for independent animation
    heroGem = model.getObjectByName('HeroGem') || null
    orbitGroup = new THREE.Group()
    scene.add(orbitGroup)

    const orbitNames = ['Ruby','Emerald','Amethyst','Topaz','Aquamarine','Garnet','Citrine','Tanzanite']
    orbitNames.forEach(name => {
      const obj = model.getObjectByName(name)
      if (obj) {
        allGems.push(obj)
        // give each a random phase for floating bob
        ;(obj as any).userData.phase = Math.random() * Math.PI * 2
        ;(obj as any).userData.bobSpeed = 0.4 + Math.random() * 0.4
      }
    })

    // Also add shards to allGems list
    model.traverse(child => {
      if (child.name.startsWith('Shard_')) {
        allGems.push(child)
        ;(child as any).userData.phase = Math.random() * Math.PI * 2
        ;(child as any).userData.bobSpeed = 0.6 + Math.random() * 0.8
      }
    })

    playEntranceAnimation()
  })

  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)
  tick()
}

function playEntranceAnimation() {
  // Camera zoom-in
  gsap.to(camera.position, {
    z: 8,
    duration: 2.2,
    ease: 'power3.out',
  })

  // Hero text entrance
  const tl = gsap.timeline({ delay: 0.3 })
  tl.from(eyebrow.value, { opacity: 0, y: 20, duration: 0.6, ease: 'power2.out' })
    .from(heroTitle.value, { opacity: 0, y: 30, duration: 0.8, ease: 'power2.out' }, '-=0.3')
    .from(heroSub.value,   { opacity: 0, y: 20, duration: 0.7, ease: 'power2.out' }, '-=0.4')
    .from(ctaBtn.value,    { opacity: 0, y: 15, duration: 0.6, ease: 'power2.out' }, '-=0.3')

  // Gem labels: fade in with stagger after model loads
  setTimeout(() => {
    const labels = Object.values(labelRefs.value)
    gsap.to(labels, { opacity: 1, duration: 0.5, stagger: 0.12, ease: 'power2.out' })
  }, 800)

  // ScrollTrigger: camera orbits as user scrolls through the spacer
  gsap.to(scroll, {
    progress: 1,
    ease: 'none',
    scrollTrigger: {
      trigger: scrollDriver.value,
      start: 'top bottom',
      end: 'bottom top',
      scrub: 1.5,
    },
    onUpdate: () => {
      // Camera orbits around the scene based on scroll
      const angle = scroll.progress * Math.PI * 2.2
      const radius = 8
      camera.position.x = Math.sin(angle) * radius
      camera.position.z = Math.cos(angle) * radius + 2
      camera.position.y = Math.sin(scroll.progress * Math.PI) * 3 - 0.5
      camera.lookAt(0, 0, 0)
    },
  })

  // Cards stagger in on scroll
  if (cardRefs.value.length) {
    gsap.from(cardRefs.value, {
      opacity: 0,
      y: 50,
      duration: 0.7,
      stagger: 0.1,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: infoSection.value,
        start: 'top 80%',
      },
    })
  }
}

function onMouseMove(e: MouseEvent) {
  mouse.x = (e.clientX / window.innerWidth - 0.5) * 2
  mouse.y = (e.clientY / window.innerHeight - 0.5) * 2
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
}

function tick() {
  animationId = requestAnimationFrame(tick)
  const t = performance.now() * 0.001

  // Subtle mouse parallax (only when not scroll-driving camera)
  if (scroll.progress === 0 || scroll.progress === 1) {
    camera.position.x += (mouse.x * 0.6 - camera.position.x) * 0.03
    camera.position.y += (-mouse.y * 0.4 - camera.position.y) * 0.03
    camera.lookAt(0, 0, 0)
  }

  // Hero gem: slow continuous rotation
  if (heroGem) {
    heroGem.rotation.y = t * 0.3
    heroGem.rotation.x = Math.sin(t * 0.2) * 0.08
  }

  // Orbit gems: individual float bob + own slow spin
  allGems.forEach((obj) => {
    const d = (obj as any).userData
    if (!d.phase && d.phase !== 0) return
    const bobAmt = obj.name.startsWith('Shard_') ? 0.06 : 0.12
    obj.position.y += Math.sin(t * d.bobSpeed + d.phase) * bobAmt * 0.02
    obj.rotation.y += 0.004
    obj.rotation.x += 0.002
  })

  renderer.render(scene, camera)
}

function scrollToInfo() {
  document.getElementById('info')?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  initThree()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId)
  renderer?.dispose()
  window.removeEventListener('resize', onResize)
  window.removeEventListener('mousemove', onMouseMove)
  ScrollTrigger.getAll().forEach(t => t.kill())
})
</script>

<style scoped>
.page-wrapper {
  position: relative;
  background: #050510;
  min-height: 100vh;
}

/* ── Canvas ────────────────────────────────────────────────────────── */
.scene-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
}

/* ── Hero ──────────────────────────────────────────────────────────── */
.hero-section {
  position: relative;
  z-index: 10;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 0 8vw;
  pointer-events: none;
}

.hero-content {
  max-width: 560px;
  pointer-events: all;
}

.hero-eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #8899ff;
  margin-bottom: 1.2rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.hero-title {
  font-size: clamp(2.8rem, 6vw, 5rem);
  line-height: 1.05;
  color: #f8f6ff;
  margin-bottom: 1.4rem;
}

.hero-title em {
  font-style: italic;
  background: linear-gradient(135deg, #a78bfa, #38bdf8, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  font-size: 1rem;
  line-height: 1.7;
  color: #9999bb;
  margin-bottom: 2.4rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  background: linear-gradient(135deg, #4f35c8, #2563eb);
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 0.85rem 2rem;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(79, 53, 200, 0.5);
}

.cta-arrow {
  font-size: 1.1rem;
  animation: bounce 1.4s ease infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(4px); }
}

/* ── Gem floating labels ──────────────────────────────────────────── */
.gem-label {
  position: absolute;
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(180, 180, 255, 0.7);
  font-family: 'Plus Jakarta Sans', sans-serif;
  pointer-events: none;
  user-select: none;
}

/* Position each label decoratively */
.gem-label:nth-child(1)  { top: 18%; right: 20%; }
.gem-label:nth-child(2)  { top: 38%; right: 14%; }
.gem-label:nth-child(3)  { top: 58%; right: 22%; }
.gem-label:nth-child(4)  { top: 72%; right: 18%; }
.gem-label:nth-child(5)  { top: 30%; right: 35%; }

/* ── Scroll driver (GSAP ScrollTrigger target) ────────────────────── */
.scroll-driver {
  height: 300vh;
  position: relative;
  z-index: 1;
}

/* ── Info cards section ───────────────────────────────────────────── */
.info-section {
  position: relative;
  z-index: 10;
  padding: 8rem 8vw 6rem;
  background: linear-gradient(to bottom, transparent, #0a0818 15%, #0a0818);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.gem-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: border-color 0.25s ease, transform 0.2s ease, box-shadow 0.25s ease;
  cursor: default;
}

.gem-card:hover {
  border-color: rgba(167, 139, 250, 0.4);
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(79, 53, 200, 0.15);
}

.gem-card-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  opacity: 0.9;
  box-shadow: 0 0 16px currentColor;
  margin-bottom: 0.6rem;
}

.gem-card-name {
  font-size: 1.25rem;
  color: #f0eeff;
  font-family: 'Lora', serif;
}

.gem-card-origin {
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6666aa;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.gem-card-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #8888bb;
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin-top: 0.4rem;
}

.gem-card-price {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.price-label {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #6666aa;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.price-val {
  font-size: 1.05rem;
  font-weight: 700;
  color: #a78bfa;
  font-family: 'Plus Jakarta Sans', sans-serif;
  letter-spacing: 0.02em;
}

/* ── Footer ────────────────────────────────────────────────────────── */
.site-footer {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 3rem 2rem;
  font-size: 0.82rem;
  color: #44446a;
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: #0a0818;
}
</style>
