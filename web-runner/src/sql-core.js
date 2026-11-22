// SQL ученика: разбиение скрипта на операторы, выполнение, таблицы результатов, автопроверка.
// Не зависит от движка: engine(db) даёт prepare(sql) -> { columns(), step() -> массив | null, free() }
// и changes(). В приложении движок — sql.js (SQLite в WebAssembly), в тестах — node:sqlite.

/** Операторы скрипта: [{ text, start, line }]. Учитывает строки, комментарии и тела триггеров. */
export function splitStatements(sql) {
  const out = [];
  let i = 0;
  let firstTok = -1; // позиция первого значимого символа оператора
  const words = []; // первые слова оператора (для CREATE ... TRIGGER)
  let depth = 0; // BEGIN/CASE ... END внутри триггера
  const n = sql.length;
  const isWord = (c) => /[A-Za-z0-9_$]/.test(c);
  while (i < n) {
    const ch = sql[i];
    if (ch === "-" && sql[i + 1] === "-") {
      while (i < n && sql[i] !== "\n") i++;
      continue;
    }
    if (ch === "/" && sql[i + 1] === "*") {
      const end = sql.indexOf("*/", i + 2);
      i = end < 0 ? n : end + 2;
      continue;
    }
    if (/\s/.test(ch)) { i++; continue; }
    if (ch === ";" && depth === 0) {
      if (firstTok >= 0) out.push({ text: sql.slice(firstTok, i), start: firstTok, line: lineAt(sql, firstTok) });
      i++;
      firstTok = -1;
      words.length = 0;
      continue;
    }
    if (firstTok < 0) firstTok = i;
    if (ch === "'" || ch === '"' || ch === "`" || ch === "[") {
      const close = ch === "[" ? "]" : ch;
      i++;
      while (i < n) {
        if (sql[i] === close) {
          if (close !== "]" && sql[i + 1] === close) { i += 2; continue; }
          break;
        }
        i++;
      }
      i++;
      continue;
    }
    if (isWord(ch)) {
      let j = i;
      while (j < n && isWord(sql[j])) j++;
      const w = sql.slice(i, j).toUpperCase();
      if (words.length < 4) words.push(w);
      const trigger = words[0] === "CREATE" && (words[1] === "TRIGGER" || (words[2] === "TRIGGER" && /^TEMP(ORARY)?$/.test(words[1])));
      if (trigger) {
        if (w === "BEGIN" || (w === "CASE" && depth > 0)) depth++;
        else if (w === "END" && depth > 0) depth--;
      }
      i = j;
      continue;
    }
    i++;
  }
  if (firstTok >= 0) out.push({ text: sql.slice(firstTok), start: firstTok, line: lineAt(sql, firstTok) });
  return out;
}

export function lineAt(text, pos) {
  let n = 1;
  for (let i = 0; i < pos; i++) if (text.charCodeAt(i) === 10) n++;
  return n;
}

const RU = [
  [/^no such table: (.+)$/, "нет таблицы «$1» — проверьте имя или создайте её"],
  [/^no such column: (.+)$/, "нет столбца «$1» — проверьте имя столбца"],
  [/^near "(.+)": syntax error$/, "синтаксическая ошибка рядом с «$1»"],
  [/^incomplete input$/, "запрос не закончен — не хватает части команды"],
  [/^unrecognized token: "(.+)"$/, "непонятный символ «$1» — возможно, не закрыта кавычка"],
  [/^table (.+) already exists$/, "таблица «$1» уже существует"],
  [/^UNIQUE constraint failed: (.+)$/, "нарушена уникальность: такое значение $1 уже есть"],
  [/^NOT NULL constraint failed: (.+)$/, "$1 не может быть пустым (NULL)"],
  [/^FOREIGN KEY constraint failed$/, "нарушена связь: внешний ключ указывает на несуществующую строку"],
  [/^CHECK constraint failed: (.+)$/, "не выполнено условие CHECK: $1"],
  [/^ambiguous column name: (.+)$/, "неоднозначный столбец «$1» — укажите таблицу: таблица.$1"],
  [/^table (\S+) has (\d+) columns but (\d+) values were supplied$/, "в таблице «$1» столбцов $2, а значений передано $3"],
  [/^(\d+) values for (\d+) columns$/, "значений $1, а столбцов $2"],
  [/^misuse of aggregate( function)?:? ?(.*)$/, "агрегатную функцию $2 нельзя использовать здесь — условие на группы пишется в HAVING"],
  [/^no such function: (.+)$/, "нет функции «$1»"],
  [/^wrong number of arguments to function (.+)\(\)$/, "неверное число аргументов у функции $1()"],
  [/^datatype mismatch$/, "несовпадение типа данных"],
  [/^(.+) clause is required before (.+)$/, "перед $2 нужен $1"],
  [/^a GROUP BY clause is required before HAVING$/, "HAVING используется только вместе с GROUP BY"],
  [/^SELECTs to the left and right of (.+) do not have the same number of result columns$/, "у запросов слева и справа от $1 разное число столбцов"],
];

export function sqlErrorText(message) {
  const msg = String(message || "").replace(/^Error:\s*/, "");
  for (const [re, ru] of RU) if (re.test(msg)) return `${msg.replace(re, ru)} (${msg})`;
  return msg;
}

export function isSyntaxMessage(message) {
  return /syntax error|incomplete input|unrecognized token/.test(String(message));
}

function plural(n, one, few, many) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}
export const rowsWord = (n) => `${n} ${plural(n, "строка", "строки", "строк")}`;

function cell(v) {
  if (v === null || v === undefined) return "NULL";
  if (v instanceof Uint8Array) return `<${v.length} байт>`;
  if (typeof v === "number" && !Number.isInteger(v)) return String(Math.round(v * 1e12) / 1e12);
  return String(v);
}

/** Таблица результата текстом: столбцы через « | », строка-разделитель, число строк. */
export function formatTable(columns, rows, more = 0) {
  const data = rows.map((r) => r.map(cell));
  const width = columns.map((c, i) => Math.min(40, Math.max(String(c).length, ...data.map((r) => r[i].length))));
  const pad = (s, w) => (s.length > w ? s.slice(0, w - 1) + "…" : s + " ".repeat(w - s.length));
  const lines = [columns.map((c, i) => pad(String(c), width[i])).join(" | ").trimEnd(), width.map((w) => "-".repeat(w)).join("-+-")];
  for (const r of data) lines.push(r.map((v, i) => pad(v, width[i])).join(" | ").trimEnd());
  const total = rows.length + more;
  lines.push(`(${rowsWord(total)}${more ? `, показаны первые ${rows.length}` : ""})`);
  return lines.join("\n");
}

/**
 * Выполняет скрипт. Возвращает { results: [{ line, columns, rows, more }], changes: [{line, n}],
 * error: { line, message, syntax } | null, stopped }.
 */
export function runScript(engine, script, { showRows = 200, maxRows = 100000 } = {}) {
  const res = { results: [], log: [], error: null };
  let read = 0;
  for (const st of splitStatements(script)) {
    let stmt;
    try {
      stmt = engine.prepare(st.text);
    } catch (e) {
      res.error = { line: st.line, message: String(e.message || e), syntax: isSyntaxMessage(e.message) };
      return res;
    }
    try {
      const columns = stmt.columns();
      const rows = [];
      let more = 0;
      let row;
      while ((row = stmt.step())) {
        if (++read > maxRows) throw new Error(`слишком много строк (больше ${maxRows}) — добавьте условие или LIMIT`);
        if (rows.length < showRows) rows.push(row); else more++;
      }
      if (columns.length) {
        const r = { line: st.line, columns, rows, more };
        res.results.push(r);
        res.log.push({ kind: "table", ...r });
      } else if (/^(INSERT|UPDATE|DELETE|REPLACE)\b/i.test(st.text)) {
        res.log.push({ kind: "changes", line: st.line, n: engine.changes() });
      }
    } catch (e) {
      res.error = { line: st.line, message: String(e.message || e), syntax: isSyntaxMessage(e.message) };
      return res;
    } finally {
      stmt.free();
    }
  }
  return res;
}

/** Текст вывода для консоли приложения. */
export function formatRun(res, total) {
  const parts = [];
  const many = res.log.filter((x) => x.kind === "table").length > 1;
  for (const x of res.log) {
    if (x.kind === "table") parts.push((many ? `-- запрос в строке ${x.line}\n` : "") + formatTable(x.columns, x.rows, x.more));
    else parts.push(`(строка ${x.line}: изменено ${rowsWord(x.n)})`);
  }
  let stdout = parts.join("\n\n");
  if (stdout) stdout += "\n";
  const stderr = res.error ? `SQLError: ${sqlErrorText(res.error.message)}\n  строка ${res.error.line}\n` : "";
  if (!stdout && !stderr && total === 0) stdout = "";
  return { stdout, stderr };
}

// ------------------------------------------------------------------------------
// Автопроверка: { kind: "sql", ordered?, checkColumns?, tolerance?, cases: [{ id, setup, query?, expected: { columns?, rows }, hidden?, hint? }] }
// ------------------------------------------------------------------------------

function same(a, b, tol) {
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= tol * Math.max(1, Math.abs(a), Math.abs(b));
  return a === b;
}

function rowKey(r) {
  return JSON.stringify(r.map((v) => (typeof v === "number" ? Math.round(v * 1e9) / 1e9 : v)));
}

export function compareResult(expected, actual, { ordered = false, checkColumns = false, tolerance = 1e-9 } = {}) {
  if (checkColumns && expected.columns) {
    const e = expected.columns.map((c) => String(c).toLowerCase());
    const a = actual.columns.map((c) => String(c).toLowerCase());
    if (e.join("\u0000") !== a.join("\u0000")) return `Столбцы: ожидались ${expected.columns.join(", ")}, получены ${actual.columns.join(", ")}`;
  }
  const width = expected.rows[0] ? expected.rows[0].length : (expected.columns || actual.columns).length;
  if (actual.columns.length !== width) return `Столбцов в ответе ${actual.columns.length}, а нужно ${width}`;
  if (actual.rows.length !== expected.rows.length) return `Строк в ответе ${actual.rows.length}, а нужно ${expected.rows.length}`;
  let e = expected.rows;
  let a = actual.rows;
  if (!ordered) {
    e = [...e].sort((x, y) => (rowKey(x) < rowKey(y) ? -1 : rowKey(x) > rowKey(y) ? 1 : 0));
    a = [...a].sort((x, y) => (rowKey(x) < rowKey(y) ? -1 : rowKey(x) > rowKey(y) ? 1 : 0));
  }
  for (let i = 0; i < e.length; i++) {
    for (let j = 0; j < width; j++) {
      if (!same(e[i][j], a[i][j], tolerance)) {
        if (!ordered) return "Набор строк отличается от ожидаемого";
        const sortedSame = compareResult(expected, actual, { ordered: false, checkColumns: false, tolerance }) === null;
        return sortedSame ? "Строки верные, но порядок другой — проверьте ORDER BY" : `Строка ${i + 1} отличается от ожидаемой`;
      }
    }
  }
  return null;
}

/** open() -> { engine, close() } — новая пустая база для каждого случая. */
export function checkSql(open, code, spec) {
  const started = Date.now();
  const report = { kind: "sql", cases: [] };
  for (const c of spec.cases) {
    const db = open();
    try {
      const base = { id: c.id, hidden: !!c.hidden, passed: false };
      if (c.hint) base.hint = c.hint;
      if (c.setup) {
        const s = runScript(db.engine, c.setup);
        if (s.error) throw new Error(`Ошибка в подготовке теста ${c.id}: ${s.error.message}`);
      }
      const r = runScript(db.engine, code);
      if (r.error) {
        const text = `SQLError: ${sqlErrorText(r.error.message)}\n  строка ${r.error.line}`;
        if (r.error.syntax) {
          report.compileError = text;
          report.cases = [];
          break;
        }
        base.error = text;
        report.cases.push(base);
        continue;
      }
      let actual;
      if (c.query) {
        const q = runScript(db.engine, c.query);
        if (q.error) {
          base.error = `После вашего кода проверочный запрос не выполнился: ${sqlErrorText(q.error.message)}`;
          report.cases.push(base);
          continue;
        }
        actual = q.results[q.results.length - 1];
      } else {
        actual = r.results[r.results.length - 1];
        if (!actual) {
          base.error = "Запрос не вернул таблицу: последней командой должен быть SELECT";
          report.cases.push(base);
          continue;
        }
      }
      const shownExpected = formatTable(c.expected.columns || actual.columns, c.expected.rows);
      const diff = compareResult(c.expected, actual, { ordered: !!spec.ordered, checkColumns: !!spec.checkColumns, tolerance: spec.tolerance ?? 1e-9 });
      base.passed = diff === null;
      if (!base.hidden) {
        base.expected = shownExpected;
        base.actual = formatTable(actual.columns, actual.rows, actual.more);
        if (c.query) base.input = `Проверочный запрос: ${c.query}`;
      }
      if (diff && !base.hint) base.hint = diff;
      else if (diff && !base.hidden) base.hint = `${diff}. ${base.hint}`;
      report.cases.push(base);
    } finally {
      db.close();
    }
  }
  report.passed = report.cases.filter((c) => c.passed).length;
  report.total = spec.cases.length;
  report.allPassed = report.cases.length > 0 && report.passed === report.total;
  report.durationMs = Date.now() - started;
  return report;
}
