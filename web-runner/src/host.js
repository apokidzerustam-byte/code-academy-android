// Хост-страница веб-раннера: HTML/CSS/JS в iframe-песочнице, SQL и Kotlin — в Web Worker.
// Связь с приложением — только через WebMessageListener caHost (разрешён лишь origin приложения).
import { runWeb, checkWeb } from "./web.js";

const stage = document.getElementById("stage");
const preview = new URLSearchParams(location.search).has("preview");
let session = null; // открытая страница ученика (предпросмотр или последний запуск)
let generation = 0; // растёт при «Стоп»: прерывает идущую проверку
const workers = {};
const pending = new Map(); // runId -> язык воркера

function toHost(obj) {
  if (window.caHost) window.caHost.postMessage(JSON.stringify(obj));
}

function worker(kind) {
  if (!workers[kind]) {
    const w = new Worker(kind === "sql" ? "sql-worker.js" : "kotlin-worker.js");
    w.onmessage = (e) => {
      const m = e.data;
      pending.delete(m.runId);
      if (m.check) m.check = JSON.stringify(m.check);
      if (m.result) m.result = JSON.stringify(m.result);
      toHost(m);
    };
    w.onerror = (e) => {
      for (const [id, k] of pending) if (k === kind) { pending.delete(id); toHost({ type: "result", runId: id, error: `Не удалось запустить ${kind}-воркер: ${e.message || "файл не загрузился"}` }); }
      killWorker(kind);
    };
    workers[kind] = w;
  }
  return workers[kind];
}

function killWorker(kind) {
  if (workers[kind]) { workers[kind].terminate(); delete workers[kind]; }
}

function closeSession() {
  if (session) { session.close(); session = null; }
}

window.caRun = async (msg) => {
  const { runId, lang } = msg;
  try {
    if (lang === "sql" || lang === "kotlin") {
      pending.set(runId, lang);
      worker(lang).postMessage(msg);
      return;
    }
    closeSession();
    if (msg.mode === "check") {
      const gen = generation;
      const rep = await checkWeb(msg.code, JSON.parse(msg.tests), {
        container: stage, files: msg.files || {}, entry: msg.entry, aborted: () => gen !== generation,
      });
      if (gen !== generation) return;
      toHost({ type: "result", runId, check: JSON.stringify(rep) });
      return;
    }
    const r = await runWeb({
      lang, code: msg.code, files: msg.files || {}, entry: msg.entry, stdin: msg.stdin || "",
      container: stage, visible: preview, maxOutput: msg.maxOutput,
      // В предпросмотре вывод после загрузки (нажатия кнопок и т. п.) тоже идёт в консоль приложения.
      onEvent: preview ? (m) => { if (m.t === "out" || m.t === "error") toHost({ type: "event", runId, event: m }); } : null,
    });
    if (preview) session = r.session; else if (r.session) r.session.close();
    toHost({ type: "result", runId, result: JSON.stringify(r.result) });
  } catch (err) {
    toHost({ type: "result", runId, error: String((err && err.stack) || err) });
  }
};

// «Стоп»: закрыть страницу ученика и остановить воркеры (это прерывает любой код в них).
window.caStop = () => {
  generation++;
  closeSession();
  stage.replaceChildren();
  for (const k of Object.keys(workers)) killWorker(k);
  for (const id of pending.keys()) toHost({ type: "result", runId: id, stopped: true });
  pending.clear();
};

toHost({ type: "ready", ok: true, preview });
