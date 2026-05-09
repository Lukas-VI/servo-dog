const defaultConfig = {
  camera_index: 0,
  frame_width: 240,
  frame_height: 180,
  loop_hz: 14.0,
  serial_port: "/dev/serial0",
  serial_baud: 9600,
  stand_height: 144,
  runtime_status_path: "/tmp/edog_runtime_status.json",
  vision_status_path: "/tmp/edog_vision_status.json",
  vision_frame_path: "/tmp/edog_vision_frame.jpg",
  pid: {
    kp_side: 0.12,
    kd_side: 0.04,
    kp_yaw: 0.8,
    kd_yaw: 0.18,
    forward_speed: 0.18,
    side_trim: 0.0,
    yaw_trim: 0.0,
    max_side: 0.22,
    max_yaw: 0.9,
    min_track_confidence: 0.18,
    lost_rescue_s: 0.45,
    lost_rescue_decay: 0.72,
  },
  branch: {
    default_turn: "straight",
    fork_confidence: 0.18,
    turn_bias: 0.28,
    branch_error_blend: 0.85,
    fork_speed_factor: 0.88,
    branch_latch_s: 0.75,
  },
  vision: {
    roi_start_ratio: 0.48,
    gate_top_width_ratio: 0.66,
    gate_bottom_width_ratio: 0.96,
    exclude_background: true,
    stripe_min_width_ratio: 0.08,
    stripe_max_width_ratio: 0.82,
    temporal_smoothing: 0.35,
  },
  gamepad: {
    transport: "usb",
    web_command_path: "/tmp/edog_web_gamepad.json",
    axis_forward: 4,
    axis_side: 3,
    axis_yaw: 0,
    axis_height: 1,
    axis_roll: -1,
    axis_pitch: -1,
    axis_left_trigger: -1,
    axis_right_trigger: -1,
    button_emergency_stop: 1,
    button_manual: 4,
    manual_button_required: false,
    max_forward: 0.35,
    max_side: 0.25,
    max_yaw: 0.85,
    max_roll: 0,
    max_pitch: 0,
    min_height: 100,
    max_height: 180,
    height_step: 1.8,
    height_axis_step: 1.8,
    deadzone: 0.10,
    gait: 2,
    mode_buttons: { 0: "track", 2: "stop", 3: "byroad_a", 5: "byroad_b" },
    action_buttons: { 6: "lean_left", 7: "lean_right" },
  },
  colors_hsv: {
    blue: { min: [95, 70, 40], max: [130, 255, 255] },
    green: { min: [40, 60, 40], max: [85, 255, 255] },
    purple: { min: [125, 40, 40], max: [165, 255, 255] },
    brown: { min: [5, 45, 30], max: [25, 230, 220] },
    black: { min: [0, 0, 0], max: [180, 255, 80] },
  },
  task_graph: {
    nodes: [
      { id: "start", label: "集散中心", type: "track", color: "black", action: "", x: 90, y: 285 },
      { id: "speed_bump", label: "减速带", type: "track", color: "black", action: "", x: 190, y: 220 },
      { id: "fork", label: "分岔口", type: "fork", color: "green", action: "", x: 315, y: 170 },
      { id: "purple_gate", label: "紫色住户", type: "resident", color: "purple", action: "lean_right", x: 490, y: 95 },
      { id: "brown_gate", label: "棕色住户", type: "resident", color: "brown", action: "lean_left", x: 490, y: 235 },
      { id: "platform", label: "上下高台", type: "track", color: "blue", action: "updais", x: 315, y: 300 },
      { id: "finish", label: "回到集散中心", type: "stop", color: "black", action: "stop", x: 90, y: 330 },
    ],
    edges: [
      { from: "start", to: "speed_bump", condition: "出发" },
      { from: "speed_bump", to: "fork", condition: "减速带通过" },
      { from: "fork", to: "purple_gate", condition: "左岔/紫色" },
      { from: "fork", to: "brown_gate", condition: "右岔/棕色" },
      { from: "purple_gate", to: "platform", condition: "投递后继续循迹" },
      { from: "brown_gate", to: "platform", condition: "投递后继续循迹" },
      { from: "platform", to: "finish", condition: "返回" },
    ],
  },
  slam_demo: {
    enabled: true,
    mode: "feature_odometry",
    feature_count: 90,
    map_decay: 0.94,
    motion_scale: 1.0,
    loop_threshold: 0.42,
  },
};

const colorOrder = ["blue", "green", "purple", "brown", "black"];
const colorHex = { blue: "#2d6fe8", green: "#1aa568", purple: "#9451c8", brown: "#8b5b34", black: "#151918" };
const nodeTypes = ["track", "fork", "resident", "marker", "color", "action", "stop"];
const pidMeta = {
  kp_side: ["横移 P", 0, 1, 0.01],
  kd_side: ["横移 D", 0, 0.5, 0.01],
  kp_yaw: ["转向 P", 0, 3, 0.01],
  kd_yaw: ["转向 D", 0, 1, 0.01],
  forward_speed: ["前进速度", 0, 0.6, 0.01],
  side_trim: ["机械横移 trim", -0.18, 0.18, 0.005],
  yaw_trim: ["机械偏航 trim", -0.55, 0.55, 0.005],
  max_side: ["横移限幅", 0, 0.6, 0.01],
  max_yaw: ["转向限幅", 0, 2, 0.01],
  min_track_confidence: ["最低追踪置信度", 0.02, 0.6, 0.01],
  lost_rescue_s: ["丢追救弯秒数", 0, 1.5, 0.05],
  lost_rescue_decay: ["救弯衰减", 0, 1, 0.01],
};
const slamMeta = {
  feature_count: ["特征点数量", 20, 180, 1],
  map_decay: ["地图衰减", 0.82, 0.99, 0.01],
  motion_scale: ["运动尺度", 0.2, 2.4, 0.05],
  loop_threshold: ["闭环阈值", 0.1, 0.9, 0.01],
};
const branchMeta = {
  fork_confidence: ["岔路置信度", 0.05, 0.55, 0.01],
  turn_bias: ["岔路转向偏置", 0, 0.8, 0.01],
  branch_error_blend: ["目标通道融合", 0, 1, 0.01],
  fork_speed_factor: ["岔路速度系数", 0.2, 1, 0.01],
  branch_latch_s: ["岔路锁定秒数", 0, 2, 0.05],
};
const visionMeta = {
  roi_start_ratio: ["ROI 起始比例", 0.25, 0.75, 0.01],
  gate_top_width_ratio: ["上方门控宽度", 0.25, 1.0, 0.01],
  gate_bottom_width_ratio: ["底部门控宽度", 0.5, 1.0, 0.01],
  exclude_background: ["排除背景", 0, 1, 1],
  stripe_min_width_ratio: ["条带最小宽度", 0.02, 0.3, 0.01],
  stripe_max_width_ratio: ["条带最大宽度", 0.3, 1, 0.01],
  temporal_smoothing: ["时序平滑", 0, 0.9, 0.01],
};
const gamepadMeta = {
  axis_forward: ["右摇杆前后轴", -1, 15, 1],
  axis_side: ["右摇杆左右轴", -1, 15, 1],
  axis_yaw: ["左摇杆偏航轴", -1, 15, 1],
  axis_height: ["左摇杆高度轴", -1, 15, 1],
  axis_roll: ["滚转轴(禁用-1)", -1, 15, 1],
  axis_pitch: ["俯仰轴(禁用-1)", -1, 15, 1],
  axis_left_trigger: ["左扳机轴(可禁用)", -1, 15, 1],
  axis_right_trigger: ["右扳机轴(可禁用)", -1, 15, 1],
  button_emergency_stop: ["急停按钮", 0, 31, 1],
  button_manual: ["手动保持按钮", 0, 31, 1],
  manual_button_required: ["必须按手动键", 0, 1, 1],
  max_forward: ["最大前后速度", 0, 0.8, 0.01],
  max_side: ["最大左右速度", 0, 0.8, 0.01],
  max_yaw: ["最大偏航", 0, 2, 0.01],
  max_roll: ["最大滚转", 0, 0.8, 0.01],
  max_pitch: ["最大俯仰", 0, 0.8, 0.01],
  min_height: ["最低高度", 60, 180, 1],
  max_height: ["最高高度", 100, 220, 1],
  height_step: ["扳机高度步进", 0, 8, 0.1],
  height_axis_step: ["摇杆高度步进", 0, 8, 0.1],
  deadzone: ["摇杆死区", 0, 0.35, 0.01],
  gait: ["步态编号", 0, 15, 1],
};

let config = structuredCloneSafe(defaultConfig);
let activeColor = "blue";
let sourceImageData = null;
let selectedNodeId = "start";
let selectedEdgeIndex = 0;
let liveRunning = false;
let visionOverlay = true;
let liveTimer = 0;
let liveFrames = 0;
let slamRunning = false;
let slamTimer = 0;
let slamState = makeSlamState();
let draggingNode = null;
let autoSaveTimer = 0;

const $ = (id) => document.getElementById(id);
const sourceCanvas = $("sourceCanvas");
const maskCanvas = $("maskCanvas");
const sourceCtx = sourceCanvas.getContext("2d", { willReadFrequently: true });
const maskCtx = maskCanvas.getContext("2d", { willReadFrequently: true });

function structuredCloneSafe(value) {
  return JSON.parse(JSON.stringify(value));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, Number(value)));
}

function syncLinkedInputs(target, selector, value) {
  document.querySelectorAll(selector).forEach((input) => {
    if (input !== target) input.value = value;
  });
}

function scheduleConfigSave(label = "参数已更新，正在同步") {
  $("saveState").textContent = label;
  window.clearTimeout(autoSaveTimer);
  autoSaveTimer = window.setTimeout(() => saveConfig({ silent: true }), 250);
}

function rgbToHsv(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const diff = max - min;
  let h = 0;
  if (diff !== 0) {
    if (max === r) h = ((g - b) / diff) % 6;
    else if (max === g) h = (b - r) / diff + 2;
    else h = (r - g) / diff + 4;
    h = Math.round(h * 30);
    if (h < 0) h += 180;
  }
  return [h, Math.round(max === 0 ? 0 : (diff / max) * 255), Math.round(max * 255)];
}

function inRange(hsv, range) {
  const [h, s, v] = hsv;
  const [hMin, sMin, vMin] = range.min;
  const [hMax, sMax, vMax] = range.max;
  const hueHit = hMin <= hMax ? h >= hMin && h <= hMax : h >= hMin || h <= hMax;
  return hueHit && s >= sMin && s <= sMax && v >= vMin && v <= vMax;
}

function renderAll() {
  normalizeTaskGraph();
  renderColorSelector();
  renderColorEditor();
  renderPidEditor();
  renderTaskGraph();
  renderTaskEditor();
  renderGamepadEditor();
  renderYaml();
  renderMask();
  renderSteering();
  renderSlamEditor();
  renderSlam();
}

function normalizeTaskGraph() {
  if (!config.task_graph) config.task_graph = structuredCloneSafe(defaultConfig.task_graph);
  config.task_graph.nodes = Array.isArray(config.task_graph.nodes) ? config.task_graph.nodes : [];
  config.task_graph.edges = Array.isArray(config.task_graph.edges) ? config.task_graph.edges : [];
  config.task_graph.nodes.forEach((node, index) => {
    if (!node.id) node.id = `task_${index + 1}`;
    if (!node.label) node.label = node.id;
    if (!node.type) node.type = "track";
    if (!node.color) node.color = "black";
    if (node.action === undefined) node.action = "";
    if (!Number.isFinite(Number(node.x))) node.x = 90 + (index % 4) * 160;
    if (!Number.isFinite(Number(node.y))) node.y = 90 + Math.floor(index / 4) * 105;
    node.x = clamp(Number(node.x), 45, 635);
    node.y = clamp(Number(node.y), 45, 335);
  });
}

function setAppMode(mode) {
  document.body.classList.toggle("console-mode", mode === "console");
  document.body.classList.toggle("tuning-mode", mode === "tuning");
  $("consoleModeBtn")?.classList.toggle("primary", mode === "console");
  $("tuningModeBtn")?.classList.toggle("primary", mode === "tuning");
}

function renderGamepadEditor() {
  const root = $("gamepadEditor");
  if (!root) return;
  const rows = [`
    <label class="param-row">
      <span>手柄通路</span>
      <select data-gamepad="transport">
        ${["usb", "disabled", "web"].map((value) => `<option value="${value}" ${config.gamepad.transport === value ? "selected" : ""}>${value}</option>`).join("")}
      </select>
    </label>
    <label class="param-row">
      <span>Web命令文件</span>
      <input value="${config.gamepad.web_command_path || defaultConfig.gamepad.web_command_path}" data-gamepad="web_command_path" />
    </label>`].concat(Object.entries(gamepadMeta).map(([key, [label, min, max, step]]) => {
    const value = config.gamepad?.[key] ?? defaultConfig.gamepad[key];
    return `
      <label class="param-row">
      <span>${label}</span>
      <input type="range" min="${min}" max="${max}" step="${step}" value="${Number(value)}" data-gamepad="${key}" />
      <input type="number" min="${min}" max="${max}" step="${step}" value="${Number(value)}" data-gamepad="${key}" />
      </label>`;
  }));
  root.innerHTML = rows.join("") + `
    <div class="mapping-block">
      <h3>模式键位</h3>
      ${renderButtonMap("mode_buttons", ["stop", "track", "byroad_a", "byroad_b", "manual"])}
    </div>
    <div class="mapping-block">
      <h3>动作键位</h3>
      ${renderButtonMap("action_buttons", ["updais", "lean_left", "lean_right", "upstair", "downstair", "leg_left", "leg_right"])}
    </div>`;
}

function renderButtonMap(group, options) {
  const entries = Object.entries(config.gamepad[group] || {});
  return entries.map(([button, value]) => `
    <label class="mapping-row">
      <input type="number" min="0" max="31" step="1" value="${button}" data-gamepad-map-button="${group}" data-old-button="${button}" />
      <select data-gamepad-map-value="${group}" data-button="${button}">
        ${options.map((option) => `<option value="${option}" ${value === option ? "selected" : ""}>${option}</option>`).join("")}
      </select>
      <button data-delete-gamepad-map="${group}" data-button="${button}" class="danger">删除</button>
    </label>`).join("") + `<button data-add-gamepad-map="${group}">新增键位</button>`;
}

function renderColorSelector() {
  const select = $("activeColor");
  select.innerHTML = colorOrder.map((name) => `<option value="${name}">${name}</option>`).join("");
  select.value = activeColor;
}

function renderColorEditor() {
  const root = $("colorEditor");
  root.innerHTML = colorOrder.map((name) => {
    const item = config.colors_hsv[name] || { min: [0, 0, 0], max: [180, 255, 255] };
    return `
      <article class="color-card ${name === activeColor ? "selected" : ""}" data-color="${name}">
        <button class="color-title" data-select-color="${name}">
          <span class="swatch" style="background:${colorHex[name]}"></span>
          <strong>${name}</strong>
        </button>
        ${["H", "S", "V"].map((label, idx) => rangeRow(name, "min", label, idx, item.min[idx])).join("")}
        ${["H", "S", "V"].map((label, idx) => rangeRow(name, "max", label, idx, item.max[idx])).join("")}
      </article>`;
  }).join("");
}

function rangeRow(color, side, label, index, value) {
  const max = index === 0 ? 180 : 255;
  return `
    <label class="slider-row">
      <span>${side}.${label}</span>
      <input type="range" min="0" max="${max}" value="${value}" data-color="${color}" data-side="${side}" data-index="${index}" />
      <input type="number" min="0" max="${max}" value="${value}" data-color="${color}" data-side="${side}" data-index="${index}" />
    </label>`;
}

function renderPidEditor() {
  $("pidEditor").innerHTML = Object.entries(pidMeta).map(([key, [label, min, max, step]]) => {
    const value = config.pid[key];
    return `
      <label class="param-row">
        <span>${label}</span>
        <input type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-pid="${key}" />
        <input type="number" min="${min}" max="${max}" step="${step}" value="${value}" data-pid="${key}" />
      </label>`;
  }).join("") + `
    <div class="mapping-block"><h3>视觉 ROI / 背景过滤</h3></div>
    ${Object.entries(visionMeta).map(([key, [label, min, max, step]]) => {
      const value = config.vision?.[key] ?? defaultConfig.vision[key];
      return `
        <label class="param-row">
          <span>${label}</span>
          <input type="range" min="${min}" max="${max}" step="${step}" value="${Number(value)}" data-vision="${key}" />
          <input type="number" min="${min}" max="${max}" step="${step}" value="${Number(value)}" data-vision="${key}" />
        </label>`;
    }).join("")}`;
}

function renderSlamEditor() {
  const root = $("slamEditor");
  if (!root) return;
  root.innerHTML = Object.entries(slamMeta).map(([key, [label, min, max, step]]) => {
    const value = config.slam_demo?.[key] ?? defaultConfig.slam_demo[key];
    return `
      <label class="param-row">
        <span>${label}</span>
        <input type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-slam="${key}" />
        <input type="number" min="${min}" max="${max}" step="${step}" value="${value}" data-slam="${key}" />
      </label>`;
  }).join("") + `
    <label class="param-row">
      <span>默认岔路</span>
      <select data-branch="default_turn">
        ${["straight", "left", "right"].map((value) => `<option value="${value}" ${config.branch?.default_turn === value ? "selected" : ""}>${value}</option>`).join("")}
      </select>
    </label>
    ${Object.entries(branchMeta).map(([key, [label, min, max, step]]) => {
      const value = config.branch?.[key] ?? defaultConfig.branch[key];
      return `
        <label class="param-row">
          <span>${label}</span>
          <input type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-branch="${key}" />
          <input type="number" min="${min}" max="${max}" step="${step}" value="${value}" data-branch="${key}" />
        </label>`;
    }).join("")}`;
}

function renderMask() {
  if (!sourceImageData) {
    drawPlaceholder(sourceCtx, sourceCanvas, "打开一张赛道图像后预览阈值");
    drawPlaceholder(maskCtx, maskCanvas, "掩膜预览");
    $("maskRatio").textContent = "0.0%";
    return;
  }
  const range = config.colors_hsv[activeColor];
  const alpha = Number($("overlayAlpha").value) / 100;
  const src = sourceImageData.data;
  const output = maskCtx.createImageData(sourceImageData.width, sourceImageData.height);
  let hits = 0;
  for (let i = 0; i < src.length; i += 4) {
    const hit = inRange(rgbToHsv(src[i], src[i + 1], src[i + 2]), range);
    if (hit) hits += 1;
    const tint = hexToRgb(colorHex[activeColor]);
    output.data[i] = hit ? tint[0] : src[i] * 0.28;
    output.data[i + 1] = hit ? tint[1] : src[i + 1] * 0.28;
    output.data[i + 2] = hit ? tint[2] : src[i + 2] * 0.28;
    output.data[i + 3] = hit ? Math.round(255 * alpha) : 255;
  }
  maskCanvas.width = sourceImageData.width;
  maskCanvas.height = sourceImageData.height;
  maskCtx.putImageData(output, 0, 0);
  $("maskRatio").textContent = `${((hits / (sourceImageData.width * sourceImageData.height)) * 100).toFixed(1)}%`;
}

function taskGraphToMap() {
  return {
    name: $("mapNameInput")?.value?.trim() || "race_track_v1",
    version: 1,
    created_at: new Date().toISOString(),
    mode: "line_topology",
    branch_default: config.branch?.default_turn || "straight",
    nodes: structuredCloneSafe(config.task_graph.nodes || []),
    edges: structuredCloneSafe(config.task_graph.edges || []),
    notes: "纯巡线赛道拓扑图；节点表示岔路、颜色触发点或动作点，边上的 condition 用于自动任务状态机。",
  };
}

function mapToTaskGraph(mapData) {
  if (!mapData || !Array.isArray(mapData.nodes) || !Array.isArray(mapData.edges)) {
    throw new Error("地图 JSON 缺少 nodes/edges");
  }
  config.task_graph = {
    nodes: structuredCloneSafe(mapData.nodes),
    edges: structuredCloneSafe(mapData.edges),
  };
  if (mapData.branch_default) config.branch.default_turn = mapData.branch_default;
  selectedNodeId = config.task_graph.nodes[0]?.id || "";
  selectedEdgeIndex = 0;
  normalizeTaskGraph();
}

function drawImageToSource(image) {
  const scale = Math.min(1, 960 / image.width);
  sourceCanvas.width = Math.max(1, Math.round(image.width * scale));
  sourceCanvas.height = Math.max(1, Math.round(image.height * scale));
  sourceCtx.drawImage(image, 0, 0, sourceCanvas.width, sourceCanvas.height);
  sourceImageData = sourceCtx.getImageData(0, 0, sourceCanvas.width, sourceCanvas.height);
  renderMask();
}

function drawPlaceholder(ctx, canvas, text) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#151b1d";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "rgba(255,255,255,.08)";
  for (let x = 0; x < canvas.width; x += 32) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 32) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
  ctx.fillStyle = "rgba(255,255,255,.72)";
  ctx.font = "15px Arial";
  ctx.fillText(text, 18, 30);
}

function hexToRgb(hex) {
  const intValue = parseInt(hex.slice(1), 16);
  return [(intValue >> 16) & 255, (intValue >> 8) & 255, intValue & 255];
}

function renderSteering() {
  const canvas = $("steeringCanvas");
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#10181a";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(255,255,255,.12)";
  ctx.beginPath();
  ctx.moveTo(20, h / 2);
  ctx.lineTo(w - 20, h / 2);
  ctx.stroke();
  ctx.strokeStyle = "#f4b000";
  ctx.lineWidth = 3;
  ctx.beginPath();
  let lastSide = 0;
  let lastYaw = 0;
  for (let i = 0; i < 80; i += 1) {
    const error = Math.sin(i / 12) * 0.55;
    const deriv = Math.cos(i / 12) * 0.08;
    const side = clamp(-(config.pid.kp_side * error + config.pid.kd_side * deriv), -config.pid.max_side, config.pid.max_side);
    const yaw = clamp(-(config.pid.kp_yaw * error + config.pid.kd_yaw * deriv), -config.pid.max_yaw, config.pid.max_yaw);
    lastSide = side;
    lastYaw = yaw;
    const x = 24 + (i / 79) * (w - 48);
    const y = h / 2 - yaw * 54;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  $("sideOut").textContent = lastSide.toFixed(3);
  $("yawOut").textContent = lastYaw.toFixed(3);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function renderTaskGraph() {
  const svg = $("taskGraph");
  normalizeTaskGraph();
  const nodes = config.task_graph.nodes;
  const edges = config.task_graph.edges;
  const positions = {};
  nodes.forEach((node) => {
    positions[node.id] = { x: Number(node.x), y: Number(node.y) };
  });
  const edgeSvg = edges.map((edge, index) => {
    const a = positions[edge.from] || { x: 40, y: 40 };
    const b = positions[edge.to] || { x: 220, y: 120 };
    return `<g class="edge ${index === selectedEdgeIndex ? "selected" : ""}" data-edge="${index}">
      <line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"></line>
      <text x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 8}">${escapeHtml(edge.condition || "next")}</text>
    </g>`;
  }).join("");
  const nodeSvg = nodes.map((node) => {
    const pos = positions[node.id];
    return `<g class="node ${node.id === selectedNodeId ? "selected" : ""}" data-node="${node.id}">
      <rect x="${pos.x - 66}" y="${pos.y - 30}" width="132" height="60" rx="8"></rect>
      <circle cx="${pos.x - 48}" cy="${pos.y}" r="7" fill="${colorHex[node.color] || "#64748b"}"></circle>
      <text x="${pos.x - 32}" y="${pos.y - 3}">${escapeHtml(node.label)}</text>
      <text class="node-type" x="${pos.x - 32}" y="${pos.y + 16}">${escapeHtml(node.type)}${node.action ? " / " + escapeHtml(node.action) : ""}</text>
    </g>`;
  }).join("");
  svg.innerHTML = `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z"></path></marker></defs>${edgeSvg}${nodeSvg}`;
}

function renderTaskEditor() {
  normalizeTaskGraph();
  const nodes = config.task_graph.nodes;
  const edges = config.task_graph.edges;
  const node = nodes.find((item) => item.id === selectedNodeId) || nodes[0];
  const edge = edges[selectedEdgeIndex] || edges[0] || { from: "", to: "", condition: "" };
  $("taskEditor").innerHTML = `
    <div class="editor-block">
      <h3>节点</h3>
      ${node ? `
        <label>ID<input data-node-field="id" value="${escapeHtml(node.id)}" /></label>
        <label>名称<input data-node-field="label" value="${escapeHtml(node.label)}" /></label>
        <label>类型<select data-node-field="type">${nodeTypes.map((v) => `<option ${node.type === v ? "selected" : ""}>${v}</option>`).join("")}</select></label>
        <label>颜色<select data-node-field="color">${colorOrder.map((v) => `<option ${node.color === v ? "selected" : ""}>${v}</option>`).join("")}</select></label>
        <label>动作<input data-node-field="action" value="${escapeHtml(node.action || "")}" /></label>
        <label>X<input type="number" min="45" max="635" step="1" data-node-field="x" value="${Math.round(Number(node.x))}" /></label>
        <label>Y<input type="number" min="45" max="335" step="1" data-node-field="y" value="${Math.round(Number(node.y))}" /></label>
        <button data-delete-node="${node.id}" class="danger">删除节点</button>
      ` : ""}
    </div>
    <div class="editor-block">
      <h3>连线</h3>
      <label>From<select data-edge-field="from">${nodes.map((n) => `<option ${edge.from === n.id ? "selected" : ""}>${n.id}</option>`).join("")}</select></label>
      <label>To<select data-edge-field="to">${nodes.map((n) => `<option ${edge.to === n.id ? "selected" : ""}>${n.id}</option>`).join("")}</select></label>
      <label>条件<input data-edge-field="condition" value="${escapeHtml(edge.condition || "")}" /></label>
      <button data-delete-edge="${selectedEdgeIndex}" class="danger">删除连线</button>
    </div>`;
}

function makeSlamState() {
  return {
    frame: 0,
    pose: { x: 0, y: 0, theta: -0.15 },
    path: [{ x: 0, y: 0 }],
    landmarks: [],
    forks: [],
    loop: "idle",
  };
}

function resetSlam() {
  slamState = makeSlamState();
  renderSlam();
}

function stepSlam() {
  const cfg = config.slam_demo || defaultConfig.slam_demo;
  const frame = slamState.frame + 1;
  const drift = Math.sin(frame / 19) * 0.035;
  const turn = Math.sin(frame / 37) * 0.055 + drift;
  const speed = 3.2 * Number(cfg.motion_scale || 1);
  slamState.pose.theta += turn;
  slamState.pose.x += Math.cos(slamState.pose.theta) * speed;
  slamState.pose.y += Math.sin(slamState.pose.theta) * speed;
  slamState.frame = frame;
  slamState.path.push({ x: slamState.pose.x, y: slamState.pose.y });
  if (slamState.path.length > 180) slamState.path.shift();

  const desired = Number(cfg.feature_count || 90);
  while (slamState.landmarks.length < desired) {
    const angle = slamState.pose.theta + (Math.random() - 0.5) * 2.3;
    const radius = 42 + Math.random() * 150;
    slamState.landmarks.push({
      x: slamState.pose.x + Math.cos(angle) * radius,
      y: slamState.pose.y + Math.sin(angle) * radius,
      weight: 0.45 + Math.random() * 0.55,
    });
  }
  slamState.landmarks.forEach((point) => {
    point.weight *= Number(cfg.map_decay || 0.94);
    if (Math.random() < 0.08) point.weight = Math.min(1, point.weight + 0.22);
  });
  slamState.landmarks = slamState.landmarks
    .filter((point) => point.weight > 0.08)
    .slice(-desired);

  if (frame % 42 === 0) {
    const choices = ["left", "straight", "right"].filter((_, index) => ((frame / 42) + index) % 2 === 0 || index === 1);
    const selected = choices.includes(config.branch?.default_turn) ? config.branch.default_turn : choices[0];
    slamState.forks.push({
      x: slamState.pose.x,
      y: slamState.pose.y,
      theta: slamState.pose.theta,
      choices,
      selected,
    });
    if (slamState.forks.length > 9) slamState.forks.shift();
  }

  const first = slamState.path[0];
  const distanceToStart = Math.hypot(slamState.pose.x - first.x, slamState.pose.y - first.y);
  slamState.loop = frame > 80 && distanceToStart < 90 * Number(cfg.loop_threshold || 0.42) ? "loop candidate" : "tracking";
  renderSlam();
}

function renderSlam() {
  const canvas = $("slamCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#0f1718";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(255,255,255,.07)";
  ctx.lineWidth = 1;
  for (let x = 20; x < w; x += 32) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
  }
  for (let y = 20; y < h; y += 32) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }

  const center = { x: w / 2, y: h / 2 };
  const pose = slamState.pose;
  const toScreen = (point) => ({
    x: center.x + (point.x - pose.x) * 1.05,
    y: center.y + (point.y - pose.y) * 1.05,
  });

  slamState.landmarks.forEach((point) => {
    const p = toScreen(point);
    if (p.x < -10 || p.x > w + 10 || p.y < -10 || p.y > h + 10) return;
    ctx.fillStyle = `rgba(46, 182, 125, ${Math.max(0.18, point.weight)})`;
    ctx.fillRect(p.x - 2, p.y - 2, 4, 4);
  });

  ctx.strokeStyle = "#f2b13c";
  ctx.lineWidth = 3;
  ctx.beginPath();
  slamState.path.forEach((point, index) => {
    const p = toScreen(point);
    if (index === 0) ctx.moveTo(p.x, p.y);
    else ctx.lineTo(p.x, p.y);
  });
  ctx.stroke();

  slamState.forks.forEach((fork) => {
    const p = toScreen(fork);
    if (p.x < -20 || p.x > w + 20 || p.y < -20 || p.y > h + 20) return;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(fork.theta);
    ctx.strokeStyle = "#64d6a0";
    ctx.lineWidth = 2;
    const rays = { left: -0.75, straight: 0, right: 0.75 };
    fork.choices.forEach((choice) => {
      ctx.save();
      ctx.rotate(rays[choice]);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(28, 0);
      ctx.stroke();
      ctx.restore();
    });
    ctx.fillStyle = fork.selected === "straight" ? "#f2b13c" : "#64d6a0";
    ctx.beginPath();
    ctx.arc(0, 0, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  });

  ctx.save();
  ctx.translate(center.x, center.y);
  ctx.rotate(pose.theta);
  ctx.fillStyle = "#f4f8f6";
  ctx.beginPath();
  ctx.moveTo(18, 0);
  ctx.lineTo(-12, -10);
  ctx.lineTo(-7, 0);
  ctx.lineTo(-12, 10);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  ctx.fillStyle = "rgba(255,255,255,.72)";
  ctx.font = "13px Arial";
  ctx.fillText("line-only topology demo: odometry + fork nodes", 16, 24);

  $("slamFrame").textContent = String(slamState.frame);
  $("slamFeatures").textContent = String(slamState.landmarks.length);
  $("slamLoop").textContent = slamState.loop;
  $("slamForks").textContent = String(slamState.forks.length);
}

function runSlam() {
  if (!slamRunning) return;
  stepSlam();
  slamTimer = window.setTimeout(runSlam, 120);
}

function startSlam() {
  if (slamRunning) {
    slamRunning = false;
    window.clearTimeout(slamTimer);
    $("slamRunBtn").textContent = "运行 demo";
    return;
  }
  slamRunning = true;
  $("slamRunBtn").textContent = "暂停 demo";
  runSlam();
}

function toYaml(data) {
  const lines = [];
  ["camera_index", "frame_width", "frame_height", "loop_hz", "serial_port", "serial_baud", "stand_height", "runtime_status_path", "vision_status_path", "vision_frame_path"].forEach((key) => lines.push(`${key}: ${data[key]}`));
  lines.push("pid:");
  Object.entries(data.pid).forEach(([key, value]) => lines.push(`  ${key}: ${value}`));
  lines.push("branch:");
  Object.entries(data.branch || defaultConfig.branch).forEach(([key, value]) => lines.push(`  ${key}: ${value}`));
  lines.push("vision:");
  Object.entries(data.vision || defaultConfig.vision).forEach(([key, value]) => lines.push(`  ${key}: ${value}`));
  lines.push("gamepad:");
  Object.entries(data.gamepad || defaultConfig.gamepad).forEach(([key, value]) => {
    if (typeof value === "object" && value !== null) {
      lines.push(`  ${key}:`);
      Object.entries(value).forEach(([button, action]) => lines.push(`    ${button}: ${action}`));
    } else {
      lines.push(`  ${key}: ${value}`);
    }
  });
  lines.push("colors_hsv:");
  Object.entries(data.colors_hsv).forEach(([name, spec]) => {
    lines.push(`  ${name}:`);
    lines.push(`    min: [${spec.min.join(", ")}]`);
    lines.push(`    max: [${spec.max.join(", ")}]`);
  });
  lines.push("task_graph:");
  lines.push("  nodes:");
  data.task_graph.nodes.forEach((node) => {
    lines.push(`    - id: ${node.id}`);
    lines.push(`      label: ${node.label}`);
    lines.push(`      type: ${node.type}`);
    lines.push(`      color: ${node.color}`);
    lines.push(`      action: ${node.action || ""}`);
    lines.push(`      x: ${Math.round(Number(node.x || 0))}`);
    lines.push(`      y: ${Math.round(Number(node.y || 0))}`);
  });
  lines.push("  edges:");
  data.task_graph.edges.forEach((edge) => {
    lines.push(`    - from: ${edge.from}`);
    lines.push(`      to: ${edge.to}`);
    lines.push(`      condition: ${edge.condition || ""}`);
  });
  lines.push("slam_demo:");
  Object.entries(data.slam_demo || defaultConfig.slam_demo).forEach(([key, value]) => lines.push(`  ${key}: ${value}`));
  return lines.join("\n") + "\n";
}

function renderYaml() {
  $("yamlOutput").value = toYaml(config);
}

async function loadConfig() {
  try {
    const response = await fetch("/api/config");
    if (!response.ok) throw new Error(response.statusText);
    config = { ...structuredCloneSafe(defaultConfig), ...(await response.json()) };
    config.pid = { ...defaultConfig.pid, ...(config.pid || {}) };
    config.branch = { ...defaultConfig.branch, ...(config.branch || {}) };
    config.vision = { ...defaultConfig.vision, ...(config.vision || {}) };
    config.gamepad = { ...structuredCloneSafe(defaultConfig.gamepad), ...(config.gamepad || {}) };
    config.gamepad.mode_buttons = { ...defaultConfig.gamepad.mode_buttons, ...(config.gamepad.mode_buttons || {}) };
    config.gamepad.action_buttons = { ...defaultConfig.gamepad.action_buttons, ...(config.gamepad.action_buttons || {}) };
    config.colors_hsv = { ...defaultConfig.colors_hsv, ...(config.colors_hsv || {}) };
    config.slam_demo = { ...defaultConfig.slam_demo, ...(config.slam_demo || {}) };
    config.task_graph = config.task_graph || structuredCloneSafe(defaultConfig.task_graph);
    if (!config.task_graph.nodes || config.task_graph.nodes.length === 0) {
      config.task_graph = structuredCloneSafe(defaultConfig.task_graph);
    }
    normalizeTaskGraph();
    $("saveState").textContent = "已读取后端配置";
  } catch {
    $("saveState").textContent = "使用浏览器本地配置";
  }
  renderAll();
}

async function pollLiveFrame() {
  if (!liveRunning) return;
  try {
    const framePath = visionOverlay ? "/api/vision/frame.jpg" : "/api/frame.jpg";
    const response = await fetch(`${framePath}?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(await response.text());
    const blob = await response.blob();
    const image = new Image();
    image.onload = () => {
      liveFrames += 1;
      drawImageToSource(image);
      $("sourceLabel").textContent = `${visionOverlay ? "轨道提取" : "实时摄像头"} · ${sourceCanvas.width}×${sourceCanvas.height} · ${liveFrames}`;
      URL.revokeObjectURL(image.src);
    };
    image.src = URL.createObjectURL(blob);
    if (visionOverlay) refreshVisionStatus();
  } catch (error) {
    $("sourceLabel").textContent = `摄像头未就绪 · ${String(error).slice(0, 80)}`;
  } finally {
    liveTimer = window.setTimeout(pollLiveFrame, 120);
  }
}

async function refreshVisionStatus() {
  try {
    const status = await fetch("/api/vision/status", { cache: "no-store" }).then((response) => response.json());
    const vision = status.vision || {};
    if (!vision.ok) {
      $("visionMetric").textContent = vision.message || "未就绪";
      return;
    }
    const branches = Array.isArray(vision.branches) && vision.branches.length ? vision.branches.join(",") : "-";
    const offsets = vision.branch_offsets ? Object.entries(vision.branch_offsets).map(([k, v]) => `${k}:${Number(v).toFixed(2)}`).join(" ") : "";
    $("visionMetric").textContent = `err ${Number(vision.line_error || 0).toFixed(2)} / conf ${Number(vision.confidence || 0).toFixed(2)} / ${branches}${offsets ? " / " + offsets : ""}`;
  } catch {
    $("visionMetric").textContent = "接口不可用";
  }
}

async function startLive() {
  if (liveRunning) return;
  try {
    const status = await fetch("/api/camera/status", { cache: "no-store" }).then((response) => response.json());
    if (status.message === "camera disabled") {
      $("sourceLabel").textContent = "摄像头未启用，启动 debug_server 时去掉 --no-camera";
      return;
    }
  } catch {
    $("sourceLabel").textContent = "摄像头状态接口不可用";
    return;
  }
  liveRunning = true;
  liveFrames = 0;
  pollLiveFrame();
}

function stopLive() {
  liveRunning = false;
  if (liveTimer) window.clearTimeout(liveTimer);
}

async function saveConfig(options = {}) {
  const silent = Boolean(options.silent);
  try {
    const response = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error(response.statusText);
    $("saveState").textContent = silent ? "参数已实时同步" : "已保存到 config.yaml";
    return true;
  } catch {
    localStorage.setItem("edog-debug-config", JSON.stringify(config));
    $("saveState").textContent = silent ? "后端不可用，参数仅保存到浏览器" : "后端不可用，已保存到浏览器";
    return false;
  }
  finally {
    renderYaml();
  }
}

async function saveMap() {
  const name = $("mapNameInput").value.trim() || "race_track_v1";
  try {
    const response = await fetch(`/api/maps/${encodeURIComponent(name)}.json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskGraphToMap()),
    });
    if (!response.ok) throw new Error(response.statusText);
    $("saveState").textContent = `地图已保存：${name}`;
  } catch {
    localStorage.setItem(`edog-map-${name}`, JSON.stringify(taskGraphToMap()));
    $("saveState").textContent = `后端不可用，地图已保存到浏览器：${name}`;
  }
}

async function loadMap() {
  const name = $("mapNameInput").value.trim() || "race_track_v1";
  await loadNamedMap(name);
}

async function loadNamedMap(name) {
  try {
    const response = await fetch(`/api/maps/${encodeURIComponent(name)}.json`, { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);
    mapToTaskGraph(await response.json());
    $("saveState").textContent = `地图已读取：${name}`;
  } catch {
    const saved = localStorage.getItem(`edog-map-${name}`);
    if (!saved) {
      $("saveState").textContent = `没有找到地图：${name}`;
      return;
    }
    mapToTaskGraph(JSON.parse(saved));
    $("saveState").textContent = `已读取浏览器地图：${name}`;
  }
  renderAll();
  return true;
}

function exportMap() {
  const text = JSON.stringify(taskGraphToMap(), null, 2);
  navigator.clipboard?.writeText(text);
  $("yamlOutput").value = text;
  $("saveState").textContent = "地图 JSON 已复制";
}

async function sendRuntimeCommand(command) {
  const height = Number(config.stand_height || defaultConfig.stand_height);
  const body = {
    manual_enabled: false,
    emergency_stop: false,
    selected_mode: "",
    selected_action: "",
    motion: { forward: 0, side: 0, yaw: 0, roll: 0, pitch: 0, stand_height: height, gait: Number(config.gamepad?.gait || 2) },
    ...command,
  };
  try {
    const response = await fetch("/api/gamepad", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(response.statusText);
    $("saveState").textContent = `运行命令已发送：${body.selected_mode || body.selected_action || (body.emergency_stop ? "stop" : "init")}`;
  } catch {
    $("saveState").textContent = "运行命令发送失败";
  }
}

async function startAutoRuntime(mode) {
  try {
    await saveConfig();
    const response = await fetch("/api/runtime/auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.message || response.statusText);
    $("saveState").textContent = `自动视觉闭环已启动：${mode}`;
    $("consoleSummary").textContent = `自动视觉闭环运行中 · ${mode}`;
    visionOverlay = true;
    $("visionBtn")?.classList.toggle("primary", true);
    await sendRuntimeCommand({ selected_mode: mode });
  } catch (error) {
    $("consoleSummary").textContent = `自动启动失败：${String(error).slice(0, 90)}`;
    $("saveState").textContent = "自动启动失败";
  }
}

async function startMissionMap(mapName, mode) {
  const loaded = await loadNamedMap(mapName);
  if (!loaded) return;
  $("mapNameInput").value = mapName;
  await startAutoRuntime(mode);
}

async function stopAutoRuntime() {
  try {
    await sendRuntimeCommand({ emergency_stop: true, selected_mode: "stop" });
    const response = await fetch("/api/runtime/stop", { method: "POST" });
    if (!response.ok) throw new Error(response.statusText);
    $("consoleSummary").textContent = "自动视觉闭环已停止";
    $("saveState").textContent = "自动视觉闭环已停止";
  } catch (error) {
    $("consoleSummary").textContent = `停止失败：${String(error).slice(0, 90)}`;
  }
}

async function pollRuntimeProcess() {
  try {
    const status = await fetch("/api/runtime/process", { cache: "no-store" }).then((response) => response.json());
    $("consoleProcess").textContent = status.running ? `running #${status.pid}` : "stopped";
  } catch {
    $("consoleProcess").textContent = "-";
  } finally {
    window.setTimeout(pollRuntimeProcess, 800);
  }
}

async function pollRuntimeStatus() {
  try {
    const response = await fetch("/api/runtime/status", { cache: "no-store" });
    const status = await response.json();
    $("runtimeMode").textContent = status.mode || "-";
    $("runtimeSource").textContent = status.gamepad?.source || (status.gamepad?.connected ? "unknown" : "none");
    $("runtimeWrites").textContent = String(status.write_count || 0);
    $("runtimeFrame").textContent = status.last_frame_hex || "-";
    if (status.map_pose?.ok) {
      $("runtimePose").textContent = `${status.map_pose.from || "?"}->${status.map_pose.to || "?"} ${(Number(status.map_pose.progress || 0) * 100).toFixed(0)}%`;
    } else {
      $("runtimePose").textContent = status.map_pose?.message || "-";
    }
    $("runtimeRaw").textContent = JSON.stringify(status, null, 2);
    $("consoleMode").textContent = status.mode || "-";
    $("consolePose").textContent = $("runtimePose").textContent;
    $("consoleFrame").textContent = status.last_frame_hex || "-";
  } catch (error) {
    $("runtimeRaw").textContent = `runtime 状态不可用: ${String(error)}`;
  } finally {
    window.setTimeout(pollRuntimeStatus, 250);
  }
}

async function pollConsoleVision() {
  try {
    const status = await fetch("/api/vision/status", { cache: "no-store" }).then((response) => response.json());
    const vision = status.vision || {};
    if (vision.ok) {
      const branches = Array.isArray(vision.branches) && vision.branches.length ? vision.branches.join(",") : "-";
      const offsets = vision.branch_offsets ? Object.entries(vision.branch_offsets).map(([k, v]) => `${k}:${Number(v).toFixed(2)}`).join(" ") : "";
      $("consoleVisionError").textContent = `${Number(vision.line_error || 0).toFixed(2)} / ${Number(vision.confidence || 0).toFixed(2)}`;
      $("consoleBranches").textContent = offsets ? `${branches} · ${offsets}` : branches;
      $("consoleSummary").textContent = `${status.source || "vision"} · ${new Date().toLocaleTimeString()}`;
    }
  } catch {
    $("consoleVisionError").textContent = "-";
  } finally {
    const img = $("consoleVisionFrame");
    const framePath = visionOverlay ? "/api/vision/frame.jpg" : "/api/frame.jpg";
    if (img) img.src = `${framePath}?t=${Date.now()}`;
    window.setTimeout(pollConsoleVision, 300);
  }
}

function bindEvents() {
  $("consoleModeBtn").addEventListener("click", () => setAppMode("console"));
  $("tuningModeBtn").addEventListener("click", () => setAppMode("tuning"));
  $("missionLeftBtn").addEventListener("click", () => startMissionMap("left_resident", "byroad_a"));
  $("missionRightBtn").addEventListener("click", () => startMissionMap("right_resident", "byroad_b"));
  $("missionStraightBtn").addEventListener("click", () => startMissionMap("race_track_v1", "track"));
  $("consoleStopBtn").addEventListener("click", stopAutoRuntime);
  $("consoleVisionToggleBtn").addEventListener("click", () => {
    visionOverlay = !visionOverlay;
    $("consoleVisionToggleBtn").classList.toggle("primary", visionOverlay);
  });
  $("activeColor").addEventListener("change", (event) => {
    activeColor = event.target.value;
    renderAll();
  });
  $("overlayAlpha").addEventListener("input", renderMask);
  $("imageInput").addEventListener("change", loadImage);
  $("liveBtn").addEventListener("click", startLive);
  $("visionBtn").addEventListener("click", () => {
    visionOverlay = !visionOverlay;
    $("visionBtn").classList.toggle("primary", visionOverlay);
    if (!liveRunning) startLive();
  });
  $("pauseLiveBtn").addEventListener("click", stopLive);
  $("loadConfigBtn").addEventListener("click", loadConfig);
  $("saveConfigBtn").addEventListener("click", saveConfig);
  $("exportBtn").addEventListener("click", () => {
    navigator.clipboard?.writeText(toYaml(config));
    $("saveState").textContent = "YAML 已复制";
  });
  $("slamRunBtn").addEventListener("click", startSlam);
  $("slamStepBtn").addEventListener("click", stepSlam);
  $("slamResetBtn").addEventListener("click", resetSlam);
  $("runtimeInitBtn").addEventListener("click", () => sendRuntimeCommand({ selected_mode: "stop" }));
  $("runtimeStartBtn").addEventListener("click", () => sendRuntimeCommand({ selected_mode: "track" }));
  $("runtimeStopBtn").addEventListener("click", () => sendRuntimeCommand({ emergency_stop: true, selected_mode: "stop" }));
  $("runtimeLeftBtn").addEventListener("click", () => startMissionMap("left_resident", "byroad_a"));
  $("runtimeStraightBtn").addEventListener("click", () => startMissionMap("race_track_v1", "track"));
  $("runtimeRightBtn").addEventListener("click", () => startMissionMap("right_resident", "byroad_b"));
  $("saveMapBtn").addEventListener("click", saveMap);
  $("loadMapBtn").addEventListener("click", loadMap);
  $("exportMapBtn").addEventListener("click", exportMap);
  $("taskGraph").addEventListener("pointerdown", handleGraphPointerDown);
  $("taskGraph").addEventListener("pointermove", handleGraphPointerMove);
  $("taskGraph").addEventListener("pointerup", handleGraphPointerUp);
  $("taskGraph").addEventListener("pointerleave", handleGraphPointerUp);
  document.body.addEventListener("input", handleInput);
  document.body.addEventListener("click", handleClick);
}

function handleInput(event) {
  const target = event.target;
  if (target.dataset.color) {
    const color = target.dataset.color;
    const side = target.dataset.side;
    const index = Number(target.dataset.index);
    const value = clamp(target.value, 0, index === 0 ? 180 : 255);
    config.colors_hsv[color][side][index] = value;
    syncLinkedInputs(target, `[data-color="${color}"][data-side="${side}"][data-index="${index}"]`, value);
    renderMask();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.pid) {
    const key = target.dataset.pid;
    config.pid[key] = Number(target.value);
    syncLinkedInputs(target, `[data-pid="${key}"]`, config.pid[key]);
    renderSteering();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.slam) {
    const key = target.dataset.slam;
    config.slam_demo[key] = Number(target.value);
    syncLinkedInputs(target, `[data-slam="${key}"]`, config.slam_demo[key]);
    renderSlam();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.branch) {
    const key = target.dataset.branch;
    config.branch[key] = key === "default_turn" ? target.value : Number(target.value);
    syncLinkedInputs(target, `[data-branch="${key}"]`, config.branch[key]);
    renderSlam();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.vision) {
    const key = target.dataset.vision;
    config.vision[key] = key === "exclude_background" ? Number(target.value) >= 0.5 : Number(target.value);
    syncLinkedInputs(target, `[data-vision="${key}"]`, key === "exclude_background" ? Number(target.value) : config.vision[key]);
    renderMask();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.gamepad) {
    const key = target.dataset.gamepad;
    if (key === "transport" || key === "web_command_path") {
      config.gamepad[key] = target.value;
      renderYaml();
      scheduleConfigSave();
      return;
    }
    const integerKeys = new Set(["axis_forward", "axis_side", "axis_yaw", "axis_height", "axis_roll", "axis_pitch", "axis_left_trigger", "axis_right_trigger", "button_emergency_stop", "button_manual", "min_height", "max_height", "gait"]);
    if (key === "manual_button_required") {
      config.gamepad[key] = Number(target.value) >= 0.5;
    } else {
      config.gamepad[key] = integerKeys.has(key) ? Math.round(Number(target.value)) : Number(target.value);
    }
    syncLinkedInputs(target, `[data-gamepad="${key}"]`, Number(config.gamepad[key]));
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.gamepadMapButton) {
    const group = target.dataset.gamepadMapButton;
    const oldButton = target.dataset.oldButton;
    const newButton = String(Math.round(clamp(target.value, 0, 31)));
    const current = config.gamepad[group][oldButton];
    delete config.gamepad[group][oldButton];
    config.gamepad[group][newButton] = current;
    renderGamepadEditor();
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.gamepadMapValue) {
    config.gamepad[target.dataset.gamepadMapValue][target.dataset.button] = target.value;
    renderYaml();
    scheduleConfigSave();
  }
  if (target.dataset.nodeField) {
    updateNode(target.dataset.nodeField, target.value);
  }
  if (target.dataset.edgeField) {
    updateEdge(target.dataset.edgeField, target.value);
  }
}

function handleClick(event) {
  const selectColor = event.target.closest("[data-select-color]");
  if (selectColor) {
    activeColor = selectColor.dataset.selectColor;
    renderAll();
  }
  const nodeTarget = event.target.closest("[data-node]");
  if (nodeTarget) {
    selectedNodeId = nodeTarget.dataset.node;
    renderTaskGraph();
    renderTaskEditor();
  }
  const edgeTarget = event.target.closest("[data-edge]");
  if (edgeTarget) {
    selectedEdgeIndex = Number(edgeTarget.dataset.edge);
    renderTaskGraph();
    renderTaskEditor();
  }
  if (event.target.id === "addTaskBtn") addNode();
  if (event.target.id === "addEdgeBtn") addEdge();
  if (event.target.dataset.deleteNode) deleteNode(event.target.dataset.deleteNode);
  if (event.target.dataset.deleteEdge) deleteEdge(Number(event.target.dataset.deleteEdge));
  if (event.target.dataset.addGamepadMap) addGamepadMap(event.target.dataset.addGamepadMap);
  if (event.target.dataset.deleteGamepadMap) deleteGamepadMap(event.target.dataset.deleteGamepadMap, event.target.dataset.button);
}

function svgPointFromEvent(svg, event) {
  const rect = svg.getBoundingClientRect();
  const viewBox = svg.viewBox.baseVal;
  const x = viewBox.x + ((event.clientX - rect.left) / Math.max(1, rect.width)) * viewBox.width;
  const y = viewBox.y + ((event.clientY - rect.top) / Math.max(1, rect.height)) * viewBox.height;
  return { x: clamp(x, 45, 635), y: clamp(y, 45, 335) };
}

function handleGraphPointerDown(event) {
  const nodeTarget = event.target.closest("[data-node]");
  if (!nodeTarget) return;
  selectedNodeId = nodeTarget.dataset.node;
  draggingNode = selectedNodeId;
  $("taskGraph").setPointerCapture?.(event.pointerId);
  event.preventDefault();
  renderTaskEditor();
}

function handleGraphPointerMove(event) {
  if (!draggingNode) return;
  const node = config.task_graph.nodes.find((item) => item.id === draggingNode);
  if (!node) return;
  const point = svgPointFromEvent($("taskGraph"), event);
  node.x = Math.round(point.x);
  node.y = Math.round(point.y);
  renderTaskGraph();
}

function handleGraphPointerUp() {
  if (!draggingNode) return;
  draggingNode = null;
  renderTaskEditor();
  renderYaml();
  scheduleConfigSave("任务图坐标已更新，正在同步");
}

function loadImage(event) {
  stopLive();
  const file = event.target.files?.[0];
  if (!file) return;
  const image = new Image();
  image.onload = () => {
    drawImageToSource(image);
    $("sourceLabel").textContent = `${file.name} · ${sourceCanvas.width}×${sourceCanvas.height}`;
  };
  image.src = URL.createObjectURL(file);
}

function updateNode(field, value) {
  const node = config.task_graph.nodes.find((item) => item.id === selectedNodeId);
  if (!node) return;
  const oldId = node.id;
  node[field] = field === "x" || field === "y" ? Math.round(Number(value)) : String(value).trim();
  if (field === "x") node.x = clamp(Number(node.x), 45, 635);
  if (field === "y") node.y = clamp(Number(node.y), 45, 335);
  if (field === "id") {
    selectedNodeId = node.id;
    config.task_graph.edges.forEach((edge) => {
      if (edge.from === oldId) edge.from = node.id;
      if (edge.to === oldId) edge.to = node.id;
    });
  }
  renderTaskGraph();
  renderYaml();
  scheduleConfigSave("任务图节点已更新，正在同步");
}

function updateEdge(field, value) {
  const edge = config.task_graph.edges[selectedEdgeIndex];
  if (!edge) return;
  edge[field] = value.trim();
  renderTaskGraph();
  renderYaml();
  scheduleConfigSave("任务图连线已更新，正在同步");
}

function addNode() {
  const id = `task_${config.task_graph.nodes.length + 1}`;
  config.task_graph.nodes.push({ id, label: id, type: "track", color: activeColor, action: "", x: 120, y: 120 });
  selectedNodeId = id;
  renderAll();
  scheduleConfigSave("任务图已更新，正在同步");
}

function addEdge() {
  const nodes = config.task_graph.nodes;
  if (nodes.length < 2) return;
  config.task_graph.edges.push({ from: nodes[0].id, to: nodes[nodes.length - 1].id, condition: "next" });
  selectedEdgeIndex = config.task_graph.edges.length - 1;
  renderAll();
  scheduleConfigSave("任务图已更新，正在同步");
}

function deleteNode(id) {
  config.task_graph.nodes = config.task_graph.nodes.filter((node) => node.id !== id);
  config.task_graph.edges = config.task_graph.edges.filter((edge) => edge.from !== id && edge.to !== id);
  selectedNodeId = config.task_graph.nodes[0]?.id || "";
  renderAll();
  scheduleConfigSave("任务图已更新，正在同步");
}

function deleteEdge(index) {
  config.task_graph.edges.splice(index, 1);
  selectedEdgeIndex = Math.max(0, config.task_graph.edges.length - 1);
  renderAll();
  scheduleConfigSave("任务图已更新，正在同步");
}

function addGamepadMap(group) {
  let button = 0;
  while (config.gamepad[group][String(button)] !== undefined && button < 32) button += 1;
  config.gamepad[group][String(button)] = group === "mode_buttons" ? "track" : "updais";
  renderAll();
  scheduleConfigSave("手柄映射已更新，正在同步");
}

function deleteGamepadMap(group, button) {
  delete config.gamepad[group][button];
  renderAll();
  scheduleConfigSave("手柄映射已更新，正在同步");
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
    $(`${button.dataset.tab}Tab`).classList.add("active");
  });
});

bindEvents();
const saved = localStorage.getItem("edog-debug-config");
if (saved) config = JSON.parse(saved);
loadConfig();
pollRuntimeStatus();
pollRuntimeProcess();
pollConsoleVision();
