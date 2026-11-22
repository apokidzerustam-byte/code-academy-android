// Web Worker: SQLite (sql.js, WebAssembly). Каждый запуск — новая база в памяти.
// Зависание (например, бесконечный рекурсивный запрос) останавливает хост: terminate() воркера.
/* global initSqlJs, importScripts */
import { runScript, formatRun, checkSql } from "./sql-core.js";

importScripts("sql-wasm.js");
let SQL = null;
const ready = initSqlJs({ locateFile: (f) => f }).then((s) => { SQL = s; });

function open() {
  const db = new SQL.Database();
  db.run("PRAGMA foreign_keys = ON");
  const engine = {
    prepare(sql) {
      const st = db.prepare(sql);
      const cols = st.getColumnNames();
      return {
        columns: () => cols,
        step: () => (st.step() ? st.get() : null),
        free: () => st.free(),
      };
    },
    changes: () => db.getRowsModified(),
  };
  return { engine, close: () => db.close() };
}

onmessage = async (e) => {
  const m = e.data;
  try {
    await ready;
    if (m.mode === "check") {
      postMessage({ type: "result", runId: m.runId, check: checkSql(open, m.code, JSON.parse(m.tests)) });
      return;
    }
    const started = Date.now();
    const db = open();
    try {
      if (m.setup) {
        const s = runScript(db.engine, m.setup);
        if (s.error) throw new Error("Ошибка в подготовке базы: " + s.error.message);
      }
      const r = runScript(db.engine, m.code, { showRows: 200, maxRows: 100000 });
      const out = formatRun(r);
      const status = r.error ? (r.error.syntax ? "SYNTAX_ERROR" : "ERROR") : "OK";
      postMessage({ type: "result", runId: m.runId, result: { status, stdout: out.stdout, stderr: out.stderr, truncated: false, durationMs: Date.now() - started } });
    } finally {
      db.close();
    }
  } catch (err) {
    postMessage({ type: "result", runId: m.runId, error: String((err && err.message) || err) });
  }
};
