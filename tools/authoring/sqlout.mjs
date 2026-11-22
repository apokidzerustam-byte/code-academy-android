// Вывод SQL-скрипта в формате приложения (ядро sql-core.js поверх node:sqlite) — для сценариев уроков.
// node --experimental-sqlite --no-warnings tools/authoring/sqlout.mjs < {"setup": "...", "code": "...", "check"?: spec}
import { DatabaseSync } from "node:sqlite";
import { runScript, formatRun, checkSql } from "../../web-runner/src/sql-core.js";

function open() {
  const db = new DatabaseSync(":memory:");
  db.exec("PRAGMA foreign_keys = ON");
  let last = 0;
  const engine = {
    prepare(sql) {
      const st = db.prepare(sql);
      st.setReturnArrays(true);
      const cols = st.columns().map((c) => c.name);
      let it = null;
      return {
        columns: () => cols,
        step() {
          if (!it) {
            if (!cols.length) { last = Number(st.run().changes); return null; }
            it = st.iterate();
          }
          const r = it.next();
          return r.done ? null : r.value.map((v) => (typeof v === "bigint" ? Number(v) : v));
        },
        free() { if (it && it.return) it.return(); },
      };
    },
    changes: () => last,
  };
  return { engine, close: () => db.close() };
}

let input = "";
for await (const chunk of process.stdin) input += chunk;
const req = JSON.parse(input);
if (req.check) {
  process.stdout.write(JSON.stringify(checkSql(open, req.code, req.check)));
} else {
  const db = open();
  if (req.setup) { const s = runScript(db.engine, req.setup); if (s.error) throw new Error(s.error.message); }
  const r = runScript(db.engine, req.code);
  process.stdout.write(JSON.stringify(Object.assign(formatRun(r), { error: r.error })));
}
