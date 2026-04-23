<template>
  <div class="page-wrapper">
    <!-- Three.js canvas -->
    <canvas ref="canvasEl" class="scene-canvas" />

    <!-- Loading screen -->
    <Transition name="fade">
      <div v-if="loading" class="loader">
        <div class="loader-ring" />
        <p>Sculpting gems…</p>
      </div>
    </Transition>

    <!-- Hero overlay -->
    <section class="hero">
      <div class="hero-text">
        <p class="eyebrow" ref="eyebrowEl">Blender · Three.js · GSAP</p>
        <h1 ref="headlineEl">The Gem<br /><em>Collection</em></h1>
        <p class="sub" ref="subEl">
          Procedurally sculpted in Blender. Rendered in Three.js.<br />
          <span class="hint-inline">Drag to orbit · Hover a gem · Click to bid</span>
        </p>
        <button class="scroll-btn" ref="scrollBtnEl" @click="scrollToCards">
          Explore the Collection ↓
        </button>
      </div>

      <!-- Right-side gem legend -->
      <ul class="gem-legend" ref="gemLegendEl">
        <li
          v-for="gem in GEM_DATA"
          :key="gem.name"
          :class="{ active: focusedGem === gem.name }"
          @mouseenter="highlightGem(gem.name)"
          @mouseleave="clearHighlight"
          @click="openPanel(gem)"
        >
          <span class="legend-dot" :style="{ background: gem.hex, boxShadow: `0 0 6px ${gem.hex}` }" />
          {{ gem.name }}
        </li>
      </ul>
    </section>

    <!-- Hover tooltip -->
    <div class="tooltip" v-show="tooltip.visible" :style="tooltip.style">
      <span class="tt-name">{{ tooltip.name }}</span>
      <span class="tt-price">{{ tooltip.price }}</span>
    </div>

    <!-- Gem info panel -->
    <Transition name="panel">
      <aside v-if="panel" class="gem-panel">
        <button class="panel-close" @click="panel = null">&#x2715;</button>
        <div
          class="panel-orb"
          :style="{ background: `radial-gradient(circle at 35% 30%, #fff4, ${panel.hex})`, boxShadow: `0 0 60px ${panel.hex}99` }"
        />
        <h2>{{ panel.name }}</h2>
        <p class="panel-origin">{{ panel.origin }}</p>
        <p class="panel-desc">{{ panel.desc }}</p>
        <div class="panel-price-row">
          <span>Est. Auction Value</span>
          <strong>{{ panel.price }}</strong>
        </div>
        <button class="bid-btn">Register to Bid</button>
      </aside>
    </Transition>

    <!-- Cards section -->
    <section class="collection" id="cards" ref="collectionEl">
      <h2 class="section-title" ref="sectionTitleEl">The Full Collection</h2>
      <div class="cards-grid">
        <div
          v-for="(gem, i) in GEM_DATA"
          :key="gem.name"
          class="card"
          :ref="(el) => (cardRefs[i] = el as HTMLElement)"
          @click="openPanel(gem)"
        >
          <div class="card-orb" :style="{ background: gem.hex, boxShadow: `0 4px 24px ${gem.hex}88` }" />
          <h3>{{ gem.name }}</h3>
          <p class="card-origin">{{ gem.origin }}</p>
          <p class="card-desc">{{ gem.desc }}</p>
          <div class="card-footer">
            <strong class="card-price">{{ gem.price }}</strong>
            <button @click.stop="openPanel(gem)">Bid &#x2192;</button>
          </div>
        </div>
      </div>
    </section>

    <footer class="site-footer">
      PigaBid &mdash; AI-Assisted 3D Showcase &copy; 2026
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ── Types ──────────────────────────────────────────────────────────────────
interface GemEntry { name: string; hex: string; origin: string; desc: string; price: string }

// ── Gem data ───────────────────────────────────────────────────────────────
const GEM_DATA: GemEntry[] = [
  { name: 'Ruby',       hex: '#ee1111', origin: 'Mogok, Myanmar',      desc: 'Pigeon-blood red corundum — the rarest of all precious stones.',       price: 'KSh 6.2M' },
  { name: 'Emerald',    hex: '#11bb44', origin: 'Muzo, Colombia',      desc: 'The lushest green beryl. Perfection in every facet.',                  price: 'KSh 3.1M' },
  { name: 'Amethyst',   hex: '#9922ee', origin: 'Zambia, Africa',      desc: 'Vivid violet quartz — Africa leads the world in quality.',             price: 'KSh 0.8M' },
  { name: 'Topaz',      hex: '#eebb00', origin: 'Ouro Preto, Brazil',  desc: 'Imperial topaz, the rarest variety — a warm amber fire.',              price: 'KSh 1.4M' },
  { name: 'Aquamarine', hex: '#11ccdd', origin: 'Marambaia, Brazil',   desc: 'Sea-blue beryl with clarity rivalling fine diamonds.',                  price: 'KSh 1.1M' },
  { name: 'Garnet',     hex: '#dd1144', origin: 'Umba Valley, Kenya',  desc: 'Rare Kenyan spessartine — an intense neon-orange flash.',               price: 'KSh 0.6M' },
  { name: 'Citrine',    hex: '#ff9900', origin: 'Rio Grande, Brazil',  desc: 'Golden quartz — sunlight crystallised into gemstone form.',             price: 'KSh 0.5M' },
  { name: 'Tanzanite',  hex: '#4433dd', origin: 'Merelani, Tanzania',  desc: 'Found only near Kilimanjaro — one thousand times rarer than diamonds.', price: 'KSh 2.9M' },
]

// Three.js material override colours (vivid emissive PBR glass)
// Per-gem physical properties — real refractive indices
const GEM_MATERIALS: Record<string, { color: number; ior: number; att: number }> = {
  HeroGem:    { color: 0x1133cc, ior: 2.42, att: 0.6 },  // synthetic diamond-blue
  Ruby:       { color: 0xcc0404, ior: 1.76, att: 0.4 },
  Emerald:    { color: 0x056b1a, ior: 1.58, att: 0.35 },
  Amethyst:   { color: 0x6600aa, ior: 1.54, att: 0.45 },
  Topaz:      { color: 0xcc8800, ior: 1.62, att: 0.45 },
  Aquamarine: { color: 0x007799, ior: 1.58, att: 0.5 },
  Garnet:     { color: 0x990010, ior: 1.73, att: 0.35 },
  Citrine:    { color: 0xdd5500, ior: 1.55, att: 0.4 },
  Tanzanite:  { color: 0x1100aa, ior: 1.69, att: 0.4 },
}

// ── Vue refs / state ───────────────────────────────────────────────────────
const canvasEl       = ref<HTMLCanvasElement | null>(null)
const eyebrowEl      = ref<HTMLElement | null>(null)
const headlineEl     = ref<HTMLElement | null>(null)
const subEl          = ref<HTMLElement | null>(null)
const scrollBtnEl    = ref<HTMLElement | null>(null)
const gemLegendEl    = ref<HTMLElement | null>(null)
const collectionEl   = ref<HTMLElement | null>(null)
const sectionTitleEl = ref<HTMLElement | null>(null)
const cardRefs: HTMLElement[] = new Array(GEM_DATA.length).fill(null)
const loading    = ref(true)
const focusedGem = ref<string | null>(null)
const panel      = ref<GemEntry | null>(null)

const tooltip = reactive({
  visible: false,
  name: '',
  price: '',
  style: { left: '0px', top: '0px' } as { left: string; top: string },
})

// (GEM_DATA and GEM_MATERIALS defined above)

// ── Three.js internals ────────────────────────────────────────────────────
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let composer: EffectComposer
let animId: number
let nebulaMat: THREE.ShaderMaterial | null = null
let floorMat:  THREE.ShaderMaterial | null = null
const clock = new THREE.Clock()

// Animation mixer for Blender-authored crystallize animation
let mixer: THREE.AnimationMixer | null = null
let crystallizeComplete = false

// Gem meshes for raycasting / highlight
const gemMeshes: Array<{ mesh: THREE.Mesh; name: string }> = []

// Camera spherical state
const cam = { theta: 0.5, phi: 0.28, r: 18, tTheta: 0.5, tPhi: 0.28, tR: 8 }
let isDragging = false
let lastPtr = { x: 0, y: 0 }

// Raycaster
const mouseNDC = new THREE.Vector2(-9, -9)
const raycaster = new THREE.Raycaster()
let hoveredMeshName: string | null = null

// ── Scene builders ─────────────────────────────────────────────────────────
function buildBackground() {
  // Pure black void — spotlights are the only light source
  scene.background = new THREE.Color(0x000000)
}

function buildStars() {
  const N = 9000
  const pos = new Float32Array(N * 3)
  for (let i = 0; i < N; i++) {
    const phi = Math.acos(2 * Math.random() - 1)
    const th  = Math.random() * Math.PI * 2
    const r   = 55 + Math.random() * 16
    pos[i*3]   = Math.sin(phi)*Math.cos(th)*r
    pos[i*3+1] = Math.cos(phi)*r
    pos[i*3+2] = Math.sin(phi)*Math.sin(th)*r
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
    size: 0.09, sizeAttenuation: true, color: 0xffffff, transparent: true, opacity: 0.55,
  })))
}

function buildFloor() {
  floorMat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, side: THREE.DoubleSide,
    uniforms: { uTime: { value: 0 } },
    vertexShader: `
      varying vec2 vUv;
      void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }
    `,
    fragmentShader: `
      varying vec2 vUv; uniform float uTime;
      void main(){
        vec2 g=abs(fract(vUv*14.0)-0.5);
        float line=1.0-smoothstep(0.0,0.045,min(g.x,g.y));
        float dist=length(vUv-0.5)*2.0;
        float fade=1.0-smoothstep(0.35,1.0,dist);
        float pulse=sin(uTime*1.8-dist*5.0)*0.5+0.5;
        vec3 col=mix(vec3(0.18,0.04,0.55),vec3(0.48,0.08,1.0),pulse);
        gl_FragColor=vec4(col,line*fade*0.55);
      }
    `,
  })
  const m = new THREE.Mesh(new THREE.PlaneGeometry(22, 22, 44, 44), floorMat)
  m.rotation.x = -Math.PI / 2
  m.position.y = -2.1
  scene.add(m)
}

function buildLights() {
  // Low ambient — just enough to hint at back-faces through the glass
  scene.add(new THREE.AmbientLight(0xffffff, 0.3))

  // Key — tight warm-white spotlight straight down from upper-right
  const key = new THREE.SpotLight(0xfff8f0, 130, 50, Math.PI / 11, 0.12, 1.4)
  key.position.set(6, 14, 8)
  key.target.position.set(0, 0, 0)
  scene.add(key); scene.add(key.target)

  // Rim — narrow icy blue from upper-back-left, creates silhouette separation
  const rim = new THREE.SpotLight(0x88aaff, 120, 45, Math.PI / 13, 0.2, 1.4)
  rim.position.set(-9, 12, -9)
  rim.target.position.set(0, 0, 0)
  scene.add(rim); scene.add(rim.target)

  // Under — deep violet from below, illuminates gem undersides
  const bot = new THREE.SpotLight(0xcc55ff, 60, 25, Math.PI / 7, 0.45, 2.0)
  bot.position.set(1, -7, 4)
  bot.target.position.set(0, 0.5, 0)
  scene.add(bot); scene.add(bot.target)
}

function overrideMaterials(model: THREE.Object3D) {
  model.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return
    const name = child.name
    if (name.startsWith('Shard_')) {
      const hue = Math.random()
      child.material = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color().setHSL(hue, 1.0, 0.6),
        metalness: 0, roughness: 0,
        transmission: 0.88, thickness: 0.4, ior: 1.5, transparent: true,
        envMapIntensity: 2.0,
      })
      return
    }
    if (name === 'PedestalRing' || name === 'InnerRing') {
      child.material = new THREE.MeshPhysicalMaterial({
        color: 0x444455, emissive: 0x000000, emissiveIntensity: 0,
        metalness: 1.0, roughness: 0.65, envMapIntensity: 0.3,
      })
      return
    }
    const d = GEM_MATERIALS[name as keyof typeof GEM_MATERIALS]
    if (d) {
      child.material = new THREE.MeshPhysicalMaterial({
        color: d.color,
        // Tiny self-color so gems read against the black void
        emissive: new THREE.Color(d.color), emissiveIntensity: 0.07,
        metalness: 0,
        roughness: 0,
        // Physically-based glass
        transmission: 0.82,
        thickness: 1.5,
        ior: d.ior,
        attenuationColor: new THREE.Color(d.color),
        attenuationDistance: d.att,
        transparent: true,
        envMapIntensity: 3.0,
        specularIntensity: 1.0,
      })
      gemMeshes.push({ mesh: child, name })
    }
  })
}

function assignFloatPhases(model: THREE.Object3D) {
  const orbitSet = new Set(['Ruby','Emerald','Amethyst','Topaz','Aquamarine','Garnet','Citrine','Tanzanite'])
  let i = 0
  model.traverse((o) => {
    if (!(o instanceof THREE.Mesh)) return
    if (orbitSet.has(o.name) || o.name.startsWith('Shard_')) {
      o.userData.phase = (i++ / 8) * Math.PI * 2
      o.userData.bob   = 0.35 + Math.random() * 0.45
      ;(o as any)._baseY = o.position.y
    }
  })
}

function buildComposer() {
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  // Bloom: fire on hot specular highlights only
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.6, 0.45, 0.72))
  composer.addPass(new OutputPass())
}

function applyCameraSpherical() {
  const { r, theta, phi } = cam
  camera.position.x = r * Math.sin(theta) * Math.cos(phi)
  camera.position.y = r * Math.sin(phi)
  camera.position.z = r * Math.cos(theta) * Math.cos(phi)
  camera.lookAt(0, 0.3, 0)
}

function playEntrance() {
  gsap.to(cam, { tR: 8, duration: 2.6, ease: 'power3.out' })
  const tl = gsap.timeline({ delay: 0.3 })
  tl.from(eyebrowEl.value,   { opacity: 0, y: 16, duration: 0.5, ease: 'power2.out' })
    .from(headlineEl.value,  { opacity: 0, y: 30, duration: 0.7, ease: 'power2.out' }, '-=0.2')
    .from(subEl.value,       { opacity: 0, y: 18, duration: 0.6, ease: 'power2.out' }, '-=0.3')
    .from(scrollBtnEl.value, { opacity: 0, y: 12, duration: 0.5, ease: 'power2.out' }, '-=0.3')
    .from(gemLegendEl.value?.querySelectorAll('li') ?? [], {
      opacity: 0, x: 20, stagger: 0.08, duration: 0.4, ease: 'power2.out',
    }, '-=0.3')
  ScrollTrigger.create({
    trigger: collectionEl.value, start: 'top 85%',
    onEnter: () => {
      gsap.from(sectionTitleEl.value, { opacity: 0, y: 32, duration: 0.7, ease: 'power2.out' })
      gsap.from(cardRefs.filter(Boolean), {
        opacity: 0, y: 48, stagger: 0.09, duration: 0.65, ease: 'power3.out', delay: 0.1,
      })
    },
  })
}

function updateHover() {
  if (gemMeshes.length === 0 || !crystallizeComplete) return
  raycaster.setFromCamera(mouseNDC, camera)
  const hits = raycaster.intersectObjects(gemMeshes.map(g => g.mesh))
  if (hits.length > 0) {
    const entry = gemMeshes.find(g => g.mesh === hits[0].object)
    if (!entry) return
    if (entry.name !== hoveredMeshName) {
      if (hoveredMeshName) {
        const prev = gemMeshes.find(g => g.name === hoveredMeshName)
        if (prev) gsap.to(prev.mesh.scale, { x: 1, y: 1, z: 1, duration: 0.25 })
      }
      hoveredMeshName  = entry.name
      focusedGem.value = entry.name
      gsap.to(entry.mesh.scale, { x: 1.35, y: 1.35, z: 1.35, duration: 0.25 })
      const info = GEM_DATA.find(g => g.name === entry.name)
      if (info) { tooltip.name = info.name; tooltip.price = info.price; tooltip.visible = true }
    }
    const he = gemMeshes.find(g => g.name === hoveredMeshName)
    if (he) {
      const wp = new THREE.Vector3()
      he.mesh.getWorldPosition(wp)
      wp.project(camera)
      tooltip.style.left = `${((wp.x+1)/2*window.innerWidth+20).toFixed(0)}px`
      tooltip.style.top  = `${((-wp.y+1)/2*window.innerHeight-48).toFixed(0)}px`
    }
  } else if (hoveredMeshName) {
    const prev = gemMeshes.find(g => g.name === hoveredMeshName)
    if (prev) gsap.to(prev.mesh.scale, { x: 1, y: 1, z: 1, duration: 0.25 })
    hoveredMeshName  = null
    focusedGem.value = null
    tooltip.visible  = false
  }
}

function highlightGem(name: string) {
  focusedGem.value = name
  const e = gemMeshes.find(g => g.name === name)
  if (e) gsap.to(e.mesh.scale, { x: 1.4, y: 1.4, z: 1.4, duration: 0.3 })
}

function clearHighlight() {
  if (focusedGem.value && !hoveredMeshName) {
    const e = gemMeshes.find(g => g.name === focusedGem.value)
    if (e) gsap.to(e.mesh.scale, { x: 1, y: 1, z: 1, duration: 0.25 })
    focusedGem.value = null
  }
}

function openPanel(gem: GemEntry) {
  panel.value = gem
  gsap.to(cam, { tR: 6, duration: 0.8, ease: 'power2.out' })
}

function scrollToCards() {
  document.getElementById('cards')?.scrollIntoView({ behavior: 'smooth' })
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
  composer.setSize(window.innerWidth, window.innerHeight)
}

function tick() {
  animId = requestAnimationFrame(tick)
  // getDelta() advances clock.elapsedTime; grab elapsed immediately after
  const delta = clock.getDelta()
  const t     = clock.elapsedTime
  if (nebulaMat) nebulaMat.uniforms.uTime.value = t
  if (floorMat)  floorMat.uniforms.uTime.value  = t
  // Advance Blender crystallize animation
  if (mixer) mixer.update(delta)
  if (!isDragging) cam.tTheta += 0.0025
  cam.theta += (cam.tTheta - cam.theta) * 0.06
  cam.phi   += (cam.tPhi   - cam.phi)   * 0.06
  cam.r     += (cam.tR     - cam.r)     * 0.05
  applyCameraSpherical()
  // Manual float/rotation — only runs after crystallize finishes
  if (crystallizeComplete) {
    scene.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return
      const ud = o.userData
      if (typeof ud.phase === 'number') {
        const base = (o as any)._baseY ?? 0
        o.position.y = base + Math.sin(t * ud.bob + ud.phase) * 0.1
        o.rotation.y += 0.007
      }
      if (o.name === 'HeroGem') {
        o.rotation.y = t * 0.35
        o.rotation.x = Math.sin(t * 0.22) * 0.07
      }
    })
  }
  updateHover()
  composer.render()
}

onMounted(() => {
  renderer = new THREE.WebGLRenderer({ canvas: canvasEl.value!, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.3

  scene  = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x000000, 0.01)
  camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 200)
  applyCameraSpherical()

  const pmrem = new THREE.PMREMGenerator(renderer)
  pmrem.compileEquirectangularShader()
  // RoomEnvironment provides soft IBL (ceiling panels + bounce walls) —
  // used ONLY as env map for gem refraction/reflection, not as scene background.
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0).texture
  pmrem.dispose()

  buildBackground()
  buildStars()
  buildFloor()
  buildLights()
  buildComposer()

  const loader = new GLTFLoader()
  loader.load('/gem_scene.glb', (gltf) => {
    scene.add(gltf.scene)
    overrideMaterials(gltf.scene)
    assignFloatPhases(gltf.scene)

    // ── Blender crystallize animation ────────────────────────────────
    // Start all gems + shards at scale 0 so there's no flash before the
    // first crystallize keyframe fires.
    gltf.scene.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return
      if (o.name in GEM_MATERIALS || o.name === 'HeroGem' || o.name.startsWith('Shard_')) {
        o.scale.set(0, 0, 0)
      }
    })

    if (gltf.animations.length > 0) {
      mixer = new THREE.AnimationMixer(gltf.scene)
      // Subclip covers frames 0–160 (6.67 s @24fps).
      // The 9 gems are staggered by 7 frames; last gem starts at ~frame 56 and its
      // crystallise keyframes end at ~frame 143 — still inside our 160-frame window.
      // clampWhenFinished=true keeps gems at scale=1 once each clip finishes.
      gltf.animations.forEach((clip) => {
        const cryClip = THREE.AnimationUtils.subclip(clip, clip.name + '_cry', 0, 160, 24)
        const action  = mixer!.clipAction(cryClip)
        action.setLoop(THREE.LoopOnce, 1)
        action.clampWhenFinished = true
        action.play()
      })
      // Hand off to manual float.  Stop the mixer so it doesn't fight position/rotation,
      // and explicitly reset gem scales to 1 as a safety net.
      setTimeout(() => {
        mixer?.stopAllAction()
        scene.traverse((o) => {
          if (!(o instanceof THREE.Mesh)) return
          if (o.name in GEM_MATERIALS || o.name === 'HeroGem') o.scale.set(1, 1, 1)
        })
        crystallizeComplete = true
      }, 8000)
    } else {
      // No animations — go straight to manual float
      crystallizeComplete = true
    }

    loading.value = false
    playEntrance()
  })

  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', (e) => {
    mouseNDC.set((e.clientX/window.innerWidth)*2-1, -(e.clientY/window.innerHeight)*2+1)
  })

  const cv = canvasEl.value!
  cv.style.cursor = 'grab'
  cv.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch') return
    isDragging = true; lastPtr = { x: e.clientX, y: e.clientY }
    cv.style.cursor = 'grabbing'
  })
  cv.addEventListener('pointermove', (e) => {
    if (!isDragging) return
    cam.tTheta -= (e.clientX - lastPtr.x) * 0.006
    cam.tPhi = Math.max(-0.55, Math.min(0.65, cam.tPhi + (e.clientY - lastPtr.y) * 0.004))
    lastPtr = { x: e.clientX, y: e.clientY }
  })
  cv.addEventListener('pointerup',    () => { isDragging = false; cv.style.cursor = 'grab' })
  cv.addEventListener('pointerleave', () => { isDragging = false })
  cv.addEventListener('click', () => {
    if (!hoveredMeshName) return
    const gem = GEM_DATA.find(g => g.name === hoveredMeshName)
    if (gem) openPanel(gem)
  })
  window.addEventListener('wheel', (e) => {
    if (window.scrollY < window.innerHeight * 0.5)
      cam.tR = Math.max(4, Math.min(18, cam.tR + e.deltaY * 0.018))
  }, { passive: true })

  tick()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  renderer?.dispose()
  composer?.dispose()
  window.removeEventListener('resize', onResize)
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
  pointer-events: auto;
  touch-action: pan-y;
}

/* ── Loader ────────────────────────────────────────────────────────── */
.loader {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.2rem;
  background: #050510;
  color: #8899ff;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.85rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.loader-ring {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(136, 153, 255, 0.2);
  border-top-color: #8899ff;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.6s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }

/* ── Hero ──────────────────────────────────────────────────────────── */
.hero {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 7vw;
  pointer-events: none;
}

.hero-text {
  max-width: 520px;
  pointer-events: all;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.eyebrow {
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #7788ee;
  margin-bottom: 1rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.hero h1 {
  font-size: clamp(2.6rem, 5.5vw, 4.8rem);
  line-height: 1.06;
  color: #f6f4ff;
  margin: 0 0 1.2rem;
}

.hero h1 em {
  font-style: italic;
  background: linear-gradient(135deg, #a78bfa, #38bdf8, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sub {
  font-size: 0.95rem;
  line-height: 1.75;
  color: #8888bb;
  margin-bottom: 2rem;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.hint-inline {
  font-size: 0.78rem;
  color: #5555aa;
  letter-spacing: 0.05em;
}

.scroll-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  align-self: flex-start;
  background: linear-gradient(135deg, #4f35c8, #2563eb);
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 0.8rem 1.8rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', sans-serif;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}

.scroll-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(79, 53, 200, 0.5);
}

/* ── Gem legend (right-side interactive list) ─────────────────────── */
.gem-legend {
  list-style: none;
  padding: 0;
  margin: 0;
  pointer-events: all;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.gem-legend li {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.8rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(180, 180, 255, 0.55);
  font-family: 'Plus Jakarta Sans', sans-serif;
  cursor: pointer;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  transition: color 0.2s, background 0.2s;
  user-select: none;
}

.gem-legend li:hover,
.gem-legend li.active {
  color: #e0e0ff;
  background: rgba(255, 255, 255, 0.06);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── Tooltip ───────────────────────────────────────────────────────── */
.tooltip {
  position: fixed;
  z-index: 50;
  background: rgba(10, 6, 30, 0.88);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 10px;
  padding: 0.55rem 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  pointer-events: none;
  backdrop-filter: blur(8px);
}

.tt-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #e0deff;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.tt-price {
  font-size: 0.75rem;
  color: #a78bfa;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Gem info panel ────────────────────────────────────────────────── */
.gem-panel {
  position: fixed;
  top: 50%;
  right: 3vw;
  transform: translateY(-50%);
  z-index: 60;
  width: min(360px, 90vw);
  background: rgba(8, 5, 26, 0.92);
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 20px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}

.panel-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(255,255,255,0.07);
  border: none;
  color: #9999cc;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.panel-close:hover { background: rgba(255,255,255,0.15); color: #fff; }

.panel-orb {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  margin: 0.5rem auto 1rem;
}

.gem-panel h2 {
  font-size: 1.7rem;
  color: #f0eeff;
  text-align: center;
  margin: 0;
}

.panel-origin {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6666aa;
  text-align: center;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.panel-desc {
  font-size: 0.88rem;
  line-height: 1.65;
  color: #9999bb;
  font-family: 'Plus Jakarta Sans', sans-serif;
  text-align: center;
}

.panel-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-top: 1px solid rgba(255,255,255,0.07);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.8rem;
  color: #7777aa;
}

.panel-price-row strong { color: #a78bfa; font-size: 1.05rem; }

.bid-btn {
  background: linear-gradient(135deg, #4f35c8, #2563eb);
  color: #fff;
  border: none;
  border-radius: 50px;
  padding: 0.75rem 0;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', sans-serif;
  transition: transform 0.15s, box-shadow 0.2s;
  margin-top: 0.25rem;
}

.bid-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(79, 53, 200, 0.5);
}

.panel-enter-active, .panel-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.panel-enter-from, .panel-leave-to {
  opacity: 0;
  transform: translateY(-50%) translateX(24px);
}

/* ── Collection section ────────────────────────────────────────────── */
.collection {
  position: relative;
  z-index: 10;
  padding: 8rem 6vw 6rem;
  margin-top: 100vh;
  background: linear-gradient(to bottom, transparent, #08060f 8%, #08060f);
}

.section-title {
  font-size: clamp(1.8rem, 4vw, 3rem);
  color: #f0eeff;
  text-align: center;
  margin: 0 0 3.5rem;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.4rem;
  max-width: 1280px;
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 16px;
  padding: 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  cursor: pointer;
  transition: border-color 0.25s, transform 0.2s, box-shadow 0.25s;
}

.card:hover {
  border-color: rgba(167, 139, 250, 0.45);
  transform: translateY(-4px);
  box-shadow: 0 18px 40px rgba(79, 53, 200, 0.18);
}

.card-orb {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.card h3 {
  font-size: 1.2rem;
  color: #f0eeff;
  margin: 0;
}

.card-origin {
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #55558a;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.card-desc {
  font-size: 0.86rem;
  line-height: 1.6;
  color: #8888bb;
  font-family: 'Plus Jakarta Sans', sans-serif;
  margin: 0.25rem 0;
  flex: 1;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.9rem;
  border-top: 1px solid rgba(255,255,255,0.06);
  margin-top: auto;
}

.card-price {
  font-size: 1rem;
  font-weight: 700;
  color: #a78bfa;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.card-footer button {
  background: rgba(79, 53, 200, 0.25);
  border: 1px solid rgba(79, 53, 200, 0.5);
  color: #c4b5fd;
  border-radius: 20px;
  padding: 0.35rem 0.9rem;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', sans-serif;
  transition: background 0.2s;
}

.card-footer button:hover { background: rgba(79, 53, 200, 0.5); }

/* ── Footer ────────────────────────────────────────────────────────── */
.site-footer {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 3rem 2rem;
  font-size: 0.82rem;
  color: #3a3a5a;
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: #08060f;
}
</style>
