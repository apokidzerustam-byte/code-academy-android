// Web Worker: Pyodide + та же песочница ca_runner.py, что и в Chaquopy.
"use strict";
importScripts("../pyodide/pyodide.js");

let py = null;
let runner = null;

(async () => {
  try {
    py = await loadPyodide({ indexURL: "/assets/pyodide/", stdout: () => {}, stderr: () => {} });
    const src = await (await fetch("/assets/pyrunner/ca_runner.py")).text();
    py.FS.mkdirTree("/home/pyodide/lib");
    py.FS.writeFile("/home/pyodide/lib/ca_runner.py", src);
    py.runPython("import sys; sys.path.insert(0, '/home/pyodide/lib')");
    runner = py.pyimport("ca_runner");
    postMessage({ type: "ready", ok: true, pyInfo: runner.info() });
  } catch (e) {
    postMessage({ type: "ready", ok: false, error: String((e && e.stack) || e) });
  }
})();

async function probe(path) {
  const r = {};
  try {
    const resp = await fetch("https://example.com/");
    r.net = "CONNECTED " + resp.status;
  } catch (e) {
    r.net = "DENIED " + e;
  }
  try {
    const x = new XMLHttpRequest();
    x.open("GET", "file://" + path, false);
    x.send();
    r.file = "READABLE " + x.status + " len=" + x.responseText.length;
  } catch (e) {
    r.file = "DENIED " + e;
  }
  // Python вне run(): хуки неактивны — проверяем, видна ли файловая система устройства.
  r.pyFile = py.runPython(
    "def _p(p):\n" +
    "    try:\n" +
    "        open(p).read(); return 'READABLE'\n" +
    "    except Exception as e:\n" +
    "        return 'DENIED ' + type(e).__name__\n" +
    "_p(" + JSON.stringify(path) + ")"
  );
  return r;
}

onmessage = async (e) => {
  const m = e.data;
  if (m.type === "run" && m.mode === "check") {
    try {
      const rep = runner.check(m.code, m.tests, "/home/pyodide/project/" + (m.project || "check"), 4096);
      postMessage({ type: "result", runId: m.runId, check: rep });
    } catch (err) {
      postMessage({ type: "result", runId: m.runId, error: String(err) });
    }
  } else if (m.type === "run") {
    try {
      const res = runner.run(m.code, "/home/pyodide/project/" + (m.project || "default"), m.stdin || "", m.maxOutput || 16384);
      postMessage({ type: "result", runId: m.runId, result: res });
    } catch (err) {
      postMessage({ type: "result", runId: m.runId, error: String(err) });
    }
  } else if (m.type === "probe") {
    try {
      postMessage({ type: "probe", result: JSON.stringify(await probe(m.path)) });
    } catch (err) {
      postMessage({ type: "probe", result: JSON.stringify({ error: String(err) }) });
    }
  }
};
