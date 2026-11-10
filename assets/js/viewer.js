/* RobotIC 三维模型查看器 —— three.js + glTF（.glb） */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { MeshoptDecoder } from "../vendor/meshopt/meshopt_decoder.js";

const BG = 0x0b0c0e;

function init() {
  const host = document.querySelector("[data-viewer]");
  if (!host) return;

  const canvas = host.querySelector("canvas");
  const stage = host.querySelector(".viewer__stage");
  const statusEl = host.querySelector("[data-viewer-status]");
  const tabsEl = document.querySelector("[data-model-tabs]");
  const progressEl = host.querySelector("[data-viewer-progress]");
  const progressBar = host.querySelector("[data-viewer-progress] .bar");
  const resetBtn = host.querySelector("[data-viewer-reset]");
  const spinBtn = host.querySelector("[data-viewer-spin]");

  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.92;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = null;

  // 影棚环境光：让铝件、碳板、塑料都有正确的高光与反射
  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  const envRT = pmrem.fromScene(new RoomEnvironment(), 0.045);
  scene.environment = envRT.texture;
  scene.environmentIntensity = 0.42;

  const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
  camera.position.set(1.4, 1.0, 1.6);

  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 0.15;
  controls.maxDistance = 12;
  controls.maxPolarAngle = Math.PI * 0.92;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.8;

  // 灯光：主光 + 补光 + 顶部柔光，让金属/塑料都能看出结构
  const key = new THREE.DirectionalLight(0xffffff, 1.25);
  key.position.set(2.4, 4.2, 2.6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.bias = -0.0012;
  key.shadow.normalBias = 0.01;
  scene.add(key);

  const fill = new THREE.DirectionalLight(0xbcd0ff, 0.35);
  fill.position.set(-2.6, 1.4, -1.8);
  scene.add(fill);

  const rim = new THREE.DirectionalLight(0xff9d80, 0.3);
  rim.position.set(0.6, 1.2, -3);
  scene.add(rim);

  scene.add(new THREE.HemisphereLight(0xdfe8ff, 0x14171b, 0.4));

  // 地面：柔和阴影 + 细网格
  const groundMat = new THREE.ShadowMaterial({ color: 0x000000, opacity: 0.38 });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const grid = new THREE.GridHelper(6, 24, 0x39414d, 0x232830);
  grid.material.transparent = true;
  grid.material.opacity = 0.55;
  grid.position.y = 0.001;
  scene.add(grid);

  const modelGroup = new THREE.Group();
  scene.add(modelGroup);

  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  let current = null;
  let frameBox = null;

  function frameObject(object) {
    const box = new THREE.Box3().setFromObject(object);
    if (box.isEmpty()) return;
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const radius = Math.max(size.x, size.y, size.z) * 0.5;
    const fov = (camera.fov * Math.PI) / 180;
    const dist = (radius / Math.sin(fov / 2)) * 1.02;

    controls.target.copy(center);
    camera.position.set(
      center.x + dist * 0.66,
      center.y + dist * 0.46,
      center.z + dist * 0.70
    );
    camera.near = Math.max(0.002, dist / 100);
    camera.far = dist * 40;
    camera.updateProjectionMatrix();
    controls.minDistance = radius * 0.35;
    controls.maxDistance = dist * 4;
    controls.update();

    // 阴影相机跟着模型走，避免阴影像素糊成一片
    key.shadow.camera.left = -radius * 3.2;
    key.shadow.camera.right = radius * 3.2;
    key.shadow.camera.top = radius * 3.2;
    key.shadow.camera.bottom = -radius * 3.2;
    key.shadow.camera.near = 0.05;
    key.shadow.camera.far = dist * 8;
    key.shadow.camera.updateProjectionMatrix();

    // 网格尺度随模型大小调整，别让线密到发糊
    const gridSize = Math.max(1, Math.round(radius * 8));
    grid.scale.setScalar(gridSize / 6);

    frameBox = { center, dist, radius };
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function showProgress(loaded, total) {
    if (!progressEl) return;
    if (total) {
      progressEl.classList.add("is-active");
      const pct = Math.min(100, Math.round((loaded / total) * 100));
      if (progressBar) progressBar.style.width = pct + "%";
      if (pct >= 100) setTimeout(() => progressEl.classList.remove("is-active"), 260);
    }
  }

  function clearModel() {
    if (current) {
      modelGroup.remove(current);
      current.traverse((o) => {
        if (o.isMesh) {
          o.geometry?.dispose();
          const mats = Array.isArray(o.material) ? o.material : [o.material];
          mats.forEach((m) => m && m.dispose());
        }
      });
      current = null;
    }
  }

  function loadModel(item) {
    clearModel();
    setStatus("加载中…");

    loader.load(
      "assets/models/" + item.file,
      (gltf) => {
        current = gltf.scene;
        current.traverse((o) => {
          if (o.isMesh) {
            o.castShadow = true;
            o.receiveShadow = true;
            if (o.material) {
              o.material.envMapIntensity = 0.9;
            }
          }
        });
        modelGroup.add(current);
        frameObject(current);

        setStatus("就绪");
        if (item.note) {
          const noteEl = document.querySelector("[data-viewer-note]");
          if (noteEl) noteEl.textContent = item.note;
        }
      },
      (evt) => {
        showProgress(evt.loaded, evt.total);
        if (evt.total) setStatus(`加载中 ${Math.round((evt.loaded / evt.total) * 100)}%`);
      },
      (err) => {
        console.error(err);
        setStatus("模型加载失败");
      }
    );
  }

  function resize() {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height;
    camera.updateProjectionMatrix();
  }

  const ro = new ResizeObserver(() => {
    resize();
    if (frameBox && current) {
      // 保持观察目标，重新框一次避免旋转后跑偏
      controls.update();
    }
  });
  ro.observe(stage);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }

  // ---- 交互 ----
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (current) frameObject(current);
    });
  }
  if (spinBtn) {
    spinBtn.addEventListener("click", () => {
      controls.autoRotate = !controls.autoRotate;
      spinBtn.classList.toggle("is-on", controls.autoRotate);
      spinBtn.setAttribute("aria-pressed", controls.autoRotate ? "true" : "false");
    });
    spinBtn.classList.toggle("is-on", controls.autoRotate);
  }

  // ---- 读取清单 ----
  fetch("assets/models/manifest.json")
    .then((r) => r.json())
    .then((data) => {
      const models = (data.models || []).filter((m) => m.file);
      if (!models.length) {
        setStatus("暂无模型");
        return;
      }
      if (tabsEl) {
        tabsEl.innerHTML = models
          .map(
            (m, i) =>
              `<button class="model-tab${i === 0 ? " is-active" : ""}" data-index="${i}" ` +
              `aria-pressed="${i === 0}">` +
              `<span class="model-tab__season">${m.season || ""}</span>` +
              `<span class="model-tab__name">${m.name}</span>` +
              `<span class="model-tab__badge">${m.badge || ""}</span>` +
              `</button>`
          )
          .join("");

        tabsEl.addEventListener("click", (e) => {
          const btn = e.target.closest(".model-tab");
          if (!btn) return;
          const idx = Number(btn.dataset.index);
          tabsEl.querySelectorAll(".model-tab").forEach((b) => {
            b.classList.toggle("is-active", b === btn);
            b.setAttribute("aria-pressed", b === btn ? "true" : "false");
          });
          loadModel(models[idx]);
        });
      }
      const noteEl = document.querySelector("[data-viewer-note]");
      if (noteEl && models[0].note) noteEl.textContent = models[0].note;
      loadModel(models[0]);
    })
    .catch((err) => {
      console.error(err);
      setStatus("清单读取失败");
    });

  resize();
  animate();
  console.log("[viewer] background", BG.toString(16));
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
