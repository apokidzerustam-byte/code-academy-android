// Ядро SQL-раннера на node:sqlite (в приложении тот же код работает поверх sql.js).
import { DatabaseSync } from "node:sqlite";
import assert from "node:assert/strict";
import { splitStatements, runScript, formatRun, checkSql, sqlErrorText, formatTable } from "../src/sql-core.js";

function open() {
  const db = new DatabaseSync(":memory:");
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

let n = 0;
function t(name, fn) {
  try { fn(); n++; console.log("ok  ", name); } catch (e) { console.log("FAIL", name, "\n", e.stack); process.exitCode = 1; }
}

t("разбиение: строки, комментарии, триггер", () => {
  const sql = "-- комментарий; не конец\nSELECT 'a;b', \"x;y\" FROM t; /* ; */\n\nINSERT INTO t VALUES (1);\nCREATE TRIGGER tr AFTER INSERT ON t BEGIN\n  UPDATE t SET a = CASE WHEN a > 0 THEN 1 ELSE 0 END;\n  DELETE FROM t WHERE a = 2;\nEND;\nSELECT 1";
  const st = splitStatements(sql);
  assert.deepEqual(st.map((s) => s.line), [2, 4, 5, 9]);
  assert.equal(st[0].text, "SELECT 'a;b', \"x;y\" FROM t");
  assert.match(st[2].text, /^CREATE TRIGGER[\s\S]*END$/);
  assert.equal(st[3].text, "SELECT 1");
  assert.deepEqual(splitStatements("  ;; -- пусто\n"), []);
});

t("запуск: таблица, изменения, русская форма слова «строка»", () => {
  const db = open();
  const r = runScript(db.engine, "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INT);\nINSERT INTO users (name, age) VALUES ('Анна', 20), ('Борис', 31);\nSELECT name, age FROM users ORDER BY age;");
  const o = formatRun(r);
  assert.equal(o.stderr, "");
  assert.equal(o.stdout, "(строка 2: изменено 2 строки)\n\nname  | age\n------+----\nАнна  | 20\nБорис | 31\n(2 строки)\n");
  assert.equal(formatTable(["x"], [[1]]).split("\n").pop(), "(1 строка)");
  assert.equal(formatTable(["x"], Array(11).fill([1])).split("\n").pop(), "(11 строк)");
  assert.equal(formatTable(["x"], [[null], [1.5], [0.1 + 0.2]]), "x\n----\nNULL\n1.5\n0.3\n(3 строки)");
});

t("ошибки: номер строки и перевод сообщения", () => {
  const db = open();
  const r = runScript(db.engine, "CREATE TABLE t (a INT);\n\nSELEC a FROM t;");
  assert.equal(r.error.line, 3);
  assert.equal(r.error.syntax, true);
  assert.match(formatRun(r).stderr, /SQLError: синтаксическая ошибка рядом с «SELEC»/);
  const r2 = runScript(db.engine, "SELECT nam FROM t");
  assert.match(sqlErrorText(r2.error.message), /^нет столбца «nam»/);
  assert.equal(r2.error.syntax, false);
  const r3 = runScript(db.engine, "SELECT * FROM users");
  assert.match(sqlErrorText(r3.error.message), /^нет таблицы «users»/);
  const r4 = runScript(db.engine, "SELECT a, count(*) FROM t WHERE count(*) > 1 GROUP BY a");
  assert.match(sqlErrorText(r4.error.message), /HAVING/);
});

t("бесконечный рекурсивный запрос прерывается лимитом строк", () => {
  const db = open();
  const r = runScript(db.engine, "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c) SELECT x FROM c;", { maxRows: 5000 });
  assert.match(r.error.message, /слишком много строк/);
});

const SETUP = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INT);\nINSERT INTO users (name, age) VALUES ('Анна', 20), ('Борис', 31), ('Вера', 17);";
const SETUP2 = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INT);\nINSERT INTO users (name, age) VALUES ('Глеб', 40), ('Дина', 18), ('Егор', 12);";
const SPEC = { kind: "sql", ordered: true, cases: [
  { id: "a", setup: SETUP, expected: { columns: ["name"], rows: [["Анна"], ["Борис"]] } },
  { id: "b", setup: SETUP2, hidden: true, expected: { rows: [["Дина"], ["Глеб"]] } },
] };

t("проверка: эталон проходит", () => {
  const r = checkSql(open, "SELECT name FROM users WHERE age >= 18 ORDER BY age;", SPEC);
  assert.equal(r.allPassed, true, JSON.stringify(r, null, 1));
});
t("проверка: подгонка под открытый тест ловится скрытым", () => {
  const r = checkSql(open, "SELECT name FROM users WHERE name IN ('Анна', 'Борис') ORDER BY age;", SPEC);
  assert.equal(r.passed, 1);
  assert.equal(r.cases[1].expected, undefined);
});
t("проверка: порядок без ORDER BY — понятная подсказка", () => {
  const r = checkSql(open, "SELECT name FROM users WHERE age >= 18 ORDER BY age DESC;", SPEC);
  assert.match(r.cases[0].hint, /порядок другой/);
});
t("проверка: синтаксис — compileError; нет SELECT — ошибка случая", () => {
  const r = checkSql(open, "SELECT name FROM users WERE age >= 18", SPEC);
  assert.match(r.compileError, /синтаксическая ошибка/);
  assert.equal(r.allPassed, false);
  const r2 = checkSql(open, "UPDATE users SET age = 1;", SPEC);
  assert.match(r2.cases[0].error, /последней командой должен быть SELECT/);
});
t("проверка: DML с проверочным запросом и неупорядоченное сравнение", () => {
  const spec = { kind: "sql", cases: [{ id: "a", setup: SETUP, query: "SELECT name, age FROM users", expected: { rows: [["Анна", 21], ["Борис", 32], ["Вера", 18]] } }] };
  assert.equal(checkSql(open, "UPDATE users SET age = age + 1;", spec).allPassed, true);
  const r = checkSql(open, "UPDATE users SET age = age + 1 WHERE age > 18;", spec);
  assert.equal(r.allPassed, false);
  assert.match(r.cases[0].hint, /Набор строк отличается/);
});
t("проверка: имена столбцов (AS) при checkColumns", () => {
  const spec = { kind: "sql", checkColumns: true, cases: [{ id: "a", setup: SETUP, expected: { columns: ["total"], rows: [[3]] } }] };
  assert.equal(checkSql(open, "SELECT count(*) AS total FROM users", spec).allPassed, true);
  assert.match(checkSql(open, "SELECT count(*) FROM users", spec).cases[0].hint, /Столбцы/);
});
console.log(`\n${n} тестов прошло`);
