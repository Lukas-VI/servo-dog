const thresholds = [
  ["blue", "#2b73d2", 0.42],
  ["green", "#15965d", 0.58],
  ["purple", "#8f48b8", 0.32],
  ["brown", "#8a5a30", 0.26],
  ["black", "#1a1d1d", 0.72],
];

const root = document.getElementById("thresholds");
thresholds.forEach(([name, color, value]) => {
  const row = document.createElement("div");
  row.className = "threshold-row";
  row.innerHTML = `
    <div class="swatch" style="background:${color}" title="${name}"></div>
    <div>
      <strong>${name}</strong>
      <div class="bar"><span style="width:${Math.round(value * 100)}%"></span></div>
    </div>
  `;
  root.appendChild(row);
});

let running = false;
let frame = 0;
const target = document.querySelector(".target-line");
const err = document.getElementById("err");
const conf = document.getElementById("conf");
const frameEl = document.getElementById("frame");

function tick() {
  if (!running) return;
  frame += 1;
  const error = Math.sin(frame / 18) * 0.34;
  target.style.left = `${50 + error * 42}%`;
  err.textContent = `${error >= 0 ? "+" : ""}${error.toFixed(2)}`;
  conf.textContent = (0.68 + Math.cos(frame / 25) * 0.18).toFixed(2);
  frameEl.textContent = String(frame);
  requestAnimationFrame(tick);
}

document.getElementById("startBtn").addEventListener("click", () => {
  if (!running) {
    running = true;
    tick();
  }
});

document.getElementById("stopBtn").addEventListener("click", () => {
  running = false;
  err.textContent = "+0.00";
  conf.textContent = "0.00";
});

