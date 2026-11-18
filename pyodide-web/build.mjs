// Копирует ядро Pyodide и страницу-раннер в assets приложения.
import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";

const assets = "../app/src/main/assets";
const py = `${assets}/pyodide`;
const runner = `${assets}/pyrunner`;
mkdirSync(py, { recursive: true });
mkdirSync(runner, { recursive: true });

// Только ядро: интерпретатор + stdlib. Пакеты (numpy и т. п.) — позже, по необходимости.
const CORE = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json", "LICENSE"];
let total = 0;
for (const f of CORE) {
  const src = `node_modules/pyodide/${f}`;
  copyFileSync(src, `${py}/${f}`);
  total += statSync(src).size;
}
for (const f of ["index.html", "host.js", "worker.js"]) copyFileSync(`src/${f}`, `${runner}/${f}`);
// Одна и та же песочница для уровней A (Chaquopy) и W (Pyodide).
copyFileSync("../app/src/main/python/ca_runner.py", `${runner}/ca_runner.py`);

const pkg = JSON.parse(readFileSync("node_modules/pyodide/package.json", "utf8"));
console.log(`pyodide ${pkg.version}: ${(total / 1048576).toFixed(1)} MB -> ${py}`);
