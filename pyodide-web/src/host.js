// Главная страница: держит Web Worker с Pyodide и пересылает сообщения в Kotlin (caHost).
"use strict";
let worker = null;

function toHost(obj) {
  if (window.caHost) window.caHost.postMessage(JSON.stringify(obj));
}

function start() {
  const t0 = performance.now();
  worker = new Worker("worker.js");
  worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === "ready") {
      m.startMs = Math.round(performance.now() - t0);
      m.crossOriginIsolated = !!self.crossOriginIsolated;
    }
    toHost(m);
  };
  worker.onerror = (e) => toHost({ type: "ready", ok: false, error: "worker: " + (e.message || e) });
}

window.caRun = (msg) => worker.postMessage(Object.assign({ type: "run" }, msg));
window.caProbe = (path) => worker.postMessage({ type: "probe", path });
// terminate() прерывает любой код, включая бесконечный цикл, затем поднимаем новый интерпретатор.
window.caKill = () => { if (worker) worker.terminate(); start(); };

start();
