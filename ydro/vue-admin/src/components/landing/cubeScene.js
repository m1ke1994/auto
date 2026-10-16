import * as THREE from 'three'
import { sampleStory } from './storyMotion.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'

export function createCube(host, onLost, onProject = null) {
  const mobile = matchMedia('(max-width: 767px)').matches
  const motion = matchMedia('(prefers-reduced-motion: reduce)')
  const renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: !mobile,
    powerPreference: 'low-power',
  })
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, mobile ? 1.25 : 1.7))
  renderer.setClearColor(0, 0)
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.35
  host.appendChild(renderer.domElement)
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50)
  camera.position.set(6.8, 5.1, 8.5)
  camera.lookAt(0, 0, 0)
  scene.add(new THREE.HemisphereLight(0xc5ddff, 0x152139, 3.2))
  const key = new THREE.DirectionalLight(0xf0f4ff, 5)
  key.position.set(-3, 7, 5)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0x467eff, 4)
  rim.position.set(4, 1, -4)
  scene.add(rim)
  const fill = new THREE.DirectionalLight(0xffffff, 1.5)
  fill.position.set(3, -2, 5)
  scene.add(fill)
  const group = new THREE.Group()
  scene.add(group)
  const geometry = new RoundedBoxGeometry(
    0.91,
    0.91,
    0.91,
    mobile ? 2 : 3,
    0.065,
  )
  const metal = new THREE.MeshStandardMaterial({
    color: 0x67717d,
    metalness: 0.55,
    roughness: 0.32,
  })
  const dark = new THREE.MeshStandardMaterial({
    color: 0x273342,
    metalness: 0.62,
    roughness: 0.34,
  })
  const blue = new THREE.MeshStandardMaterial({
    color: 0x2163ed,
    metalness: 0.32,
    roughness: 0.23,
    emissive: 0x0c2977,
    emissiveIntensity: 0.3,
  })
  const glass = new THREE.MeshPhysicalMaterial({
    color: 0x7fafff,
    metalness: 0.12,
    roughness: 0.16,
    transparent: true,
    opacity: 0.78,
    clearcoat: 1,
  })
  const blocks = []
  for (let x = -1; x <= 1; x++)
    for (let y = -1; y <= 1; y++)
      for (let z = -1; z <= 1; z++) {
        const accent =
          (x === 1 && y === 0 && z === 1) || (x === -1 && y === 1 && z === 0)
        const mesh = new THREE.Mesh(
          geometry,
          accent
            ? blue
            : x === 0 && y === 1 && z === 1
              ? glass
              : (x + y + z) % 3 === 0
                ? dark
                : metal,
        )
        const base = new THREE.Vector3(x * 1.02, y * 1.02, z * 1.02)
        const index = blocks.length
        const seed = index * 2.399963
        const background = new THREE.Vector3(Math.sin(seed) * 4.4, Math.cos(seed) * 3.5, -3 - (index % 4) * 0.5)
        mesh.position.copy(base)
        group.add(mesh)
        blocks.push({ mesh, base, background, direction: base.clone().normalize() })
      }
  const selected = [22, 17, 8, 25]
  const destinations = [
    new THREE.Vector3(-2, 1.25, 0.2),
    new THREE.Vector3(2, 1.25, -0.1),
    new THREE.Vector3(-2, -1.35, 0.1),
    new THREE.Vector3(2, -1.35, 0.2),
  ]
  const cameraOffset = new THREE.Vector3()
  const projection = new THREE.Vector3()
  const desiredLook = new THREE.Vector3()
  let portrait = false,
    take = 0
  let cinematic = false,
    requestedProgress = 0,
    cinematicProgress = 0
  const targetPosition = new THREE.Vector3()
  const targetCamera = new THREE.Vector3()
  const lookTarget = new THREE.Vector3()
  let active = -1,
    assemble = false,
    visible = true,
    stopped = false,
    frame = 0,
    progress = 0,
    last = 0,
    start = performance.now()
  const pointer = { x: 0, y: 0 }
  function render(now) {
    frame = 0
    if (stopped || !visible || document.hidden) return
    const dt = Math.min((now - (last || now)) / 1000, 0.05)
    last = now
    const ease = motion.matches ? 1 : 1 - Math.exp(-dt * 6)
    let unsettled = false
    if (cinematic) {
      cinematicProgress += (requestedProgress - cinematicProgress) * ease
      const state = sampleStory(motion.matches ? 1 : cinematicProgress)
      if (Math.abs(requestedProgress - cinematicProgress) > 0.0001)
        unsettled = true
      for (const [index, block] of blocks.entries()) {
        const service = selected.indexOf(index)
        const seed = index * 2.399963
        targetPosition.copy(block.base).multiplyScalar(1 + state.explode * 1.75)
        targetPosition.x += Math.sin(seed) * state.explode * 0.8
        targetPosition.y += Math.cos(seed) * state.explode * 0.65
        targetPosition.z += Math.sin(seed * 0.7) * state.explode
        if (service >= 0) {
          targetPosition.lerp(destinations[service], state.resolve)
          if (active === service) targetPosition.z += state.resolve * 0.7
        } else {
          targetPosition.lerp(block.background, state.resolve)
        }
        if (block.mesh.position.distanceToSquared(targetPosition) > 0.000001)
          unsettled = true
        block.mesh.position.lerp(targetPosition, ease)
        const scale =
          service >= 0
            ? 1 +
              state.resolve *
                (portrait && active >= 0
                  ? active === service
                    ? 1.05
                    : -0.35
                  : active === service
                    ? 0.5
                    : 0.28)
            : 1 - state.resolve * (portrait && active >= 0 ? 0.83 : 0.68)
        if (Math.abs(block.mesh.scale.x - scale) > 0.0001) unsettled = true
        block.mesh.scale.setScalar(
          THREE.MathUtils.lerp(block.mesh.scale.x, scale, ease),
        )
        block.mesh.rotation.set(
          state.explode * Math.sin(seed) * 0.35 * (1 - state.resolve),
          state.explode * Math.cos(seed) * 0.45,
          state.explode * Math.sin(seed * 0.6) * 0.2,
        )
        block.mesh.material =
          service >= 0 && active === service
            ? portrait && active === 1
              ? glass
              : portrait && active === 2
                ? metal
                : blue
            : service >= 0
              ? metal
              : dark
      }
      // A continuous camera arc: close orbit, pull back, then face the service modules.
      const angle = 0.72 - state.orbit * 0.78
      const distance =
        (10.5 - Math.sin(state.orbit * Math.PI) * 1.7 + state.resolve * 2.3) *
        Math.max(1, 1.05 / camera.aspect)
      targetCamera.set(
        Math.sin(angle) * distance,
        4.1 * (1 - state.orbit) + 0.5,
        Math.cos(angle) * distance,
      )
      desiredLook.set(0, 0.15 * (1 - state.resolve), 0)
      if (portrait && active >= 0) {
        desiredLook.copy(destinations[active])
        const orbitAngle = [-0.36, 0.44, -0.24, 0.32][active] + take * 0.3
        const distance = 8.2 * Math.max(1, 1.15 / camera.aspect)
        targetCamera
          .copy(desiredLook)
          .add(
            cameraOffset.set(
              Math.sin(orbitAngle) * distance,
              1.05 + Math.sin(take * Math.PI) * 0.3,
              Math.cos(orbitAngle) * distance,
            ),
          )
      }
      if (
        camera.position.distanceToSquared(targetCamera) > 0.000001 ||
        lookTarget.distanceToSquared(desiredLook) > 0.000001
      )
        unsettled = true
      camera.position.lerp(targetCamera, ease)
      lookTarget.lerp(desiredLook, ease)
      camera.lookAt(lookTarget)
      group.rotation.set(
        pointer.y * 0.025,
        pointer.x * 0.04,
        -0.025 * (1 - state.resolve),
      )
      if (onProject) {
      camera.updateMatrixWorld(true)
      group.updateMatrixWorld(true)
      onProject(
        selected.map((index) => {
          projection.copy(blocks[index].mesh.position)
          group.localToWorld(projection)
          projection.project(camera)
          return {
            x: (projection.x * 0.5 + 0.5) * 100,
            y: (-0.5 * projection.y + 0.5) * 100,
          }
        }),
      )
      }
    } else {
      const opening =
        motion.matches || mobile || assemble
          ? 0
          : Math.max(0, 1 - (now - start) / 1600) * 0.15
      progress += ((assemble ? 0 : 0.035) - progress) * ease
      unsettled = opening > 0
      for (const [index, block] of blocks.entries()) {
        const extension = index === selected[active] ? 0.42 : 0
        targetPosition.copy(block.base).multiplyScalar(1 + opening + progress)
        if (extension)
          targetPosition.addScaledVector(
            block.direction,
            extension,
          )
        if (block.mesh.position.distanceToSquared(targetPosition) > 0.000001)
          unsettled = true
        block.mesh.position.lerp(targetPosition, ease)
      }
      const targetY = -0.16 + pointer.x * 0.09
      const targetX = pointer.y * 0.055
      if (
        Math.abs(group.rotation.y - targetY) > 0.0001 ||
        Math.abs(group.rotation.x - targetX) > 0.0001
      )
        unsettled = true
      group.rotation.y += (targetY - group.rotation.y) * ease
      group.rotation.x += (targetX - group.rotation.x) * ease
    }
    renderer.render(scene, camera)
    if (
      !motion.matches &&
      unsettled &&
      (cinematic || !mobile || now - start < 2200)
    )
      frame = requestAnimationFrame(render)
  }
  function wake() {
    if (!frame && !stopped && visible && !document.hidden)
      frame = requestAnimationFrame(render)
  }
  function resize() {
    const { width, height } = host.getBoundingClientRect()
    if (!width || !height) return
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    wake()
  }
  const resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(host)
  const intersection = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting
    if (!visible) {
      cancelAnimationFrame(frame)
      frame = 0
      last = 0
    } else wake()
  })
  intersection.observe(host)
  function visibility() {
    if (document.hidden) {
      cancelAnimationFrame(frame)
      frame = 0
      last = 0
    } else wake()
  }
  function move(event) {
    if (mobile || motion.matches) return
    const b = host.getBoundingClientRect()
    pointer.x = (event.clientX - b.left) / b.width - 0.5
    pointer.y = (event.clientY - b.top) / b.height - 0.5
    wake()
  }
  function leave() {
    pointer.x = pointer.y = 0
    wake()
  }
  function lost(event) {
    event.preventDefault()
    stopped = true
    cancelAnimationFrame(frame)
    onLost()
  }
  host.addEventListener('pointermove', move)
  host.addEventListener('pointerleave', leave)
  renderer.domElement.setAttribute('aria-hidden', 'true')
  renderer.domElement.addEventListener('webglcontextlost', lost)
  document.addEventListener('visibilitychange', visibility)
  motion.addEventListener('change', wake)
  resize()
  wake()
  return {
    setPortrait(value) {
      portrait = value
      wake()
    },
    setTake(value) {
      take = Math.max(0, Math.min(1, value))
      wake()
    },
    setCinematic(value) {
      cinematic = value
      wake()
    },
    setProgress(value) {
      requestedProgress = Math.min(1, Math.max(0, value))
      wake()
    },
    setActive(value) {
      active = value
      start = performance.now()
      wake()
    },
    setAssemble(value) {
      assemble = value
      start = performance.now()
      wake()
    },
    dispose() {
      stopped = true
      cancelAnimationFrame(frame)
      resizeObserver.disconnect()
      intersection.disconnect()
      host.removeEventListener('pointermove', move)
      host.removeEventListener('pointerleave', leave)
      document.removeEventListener('visibilitychange', visibility)
      motion.removeEventListener('change', wake)
      renderer.domElement.removeEventListener('webglcontextlost', lost)
      geometry.dispose()
      ;[metal, dark, blue, glass].forEach((material) => material.dispose())
      renderer.dispose()
      renderer.forceContextLoss()
      renderer.domElement.remove()
    },
  }
}
