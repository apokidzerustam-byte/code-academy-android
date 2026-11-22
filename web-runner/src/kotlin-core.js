// Kotlin на телефоне: синтаксический разбор (tree-sitter) и проверка структуры решения.
// Скомпилировать и запустить Kotlin внутри приложения нельзя — компилятор работает только на JVM.

/** Синтаксические ошибки дерева tree-sitter: [{ line, column, text }]. */
export function syntaxErrors(tree, code, limit = 5) {
  const out = [];
  const lines = code.split("\n");
  (function walk(node) {
    if (out.length >= limit) return;
    if (node.type === "ERROR" || node.isMissing()) {
      const p = node.startPosition;
      let text;
      if (node.isMissing()) {
        text = `пропущено «${node.type}»`;
      } else {
        const frag = node.text.trim().split("\n")[0].slice(0, 40);
        text = frag ? `непонятный фрагмент «${frag}»` : "непонятная конструкция";
      }
      const src = (lines[p.row] || "").trimEnd();
      out.push({ line: p.row + 1, column: p.column + 1, text, src });
      if (node.type === "ERROR") return; // внутрь ошибки не идём — там шум
    }
    if (!node.hasError() && !node.isMissing()) return;
    for (let i = 0; i < node.childCount; i++) walk(node.child(i));
  })(tree.rootNode);
  return out;
}

export function formatSyntaxErrors(errors, file = "Main.kt") {
  return errors.map((e) => `Синтаксическая ошибка: ${e.text}\n  ${file}, строка ${e.line}, позиция ${e.column}\n  ${e.src}`).join("\n");
}

const COMMENT_OR_STRING = /comment|string_literal|line_string|multi_line_string|character_literal/;

/** Код без комментариев и строк (пробелы на их месте) — для поиска конструкций. */
export function codeOnly(tree, code) {
  const chars = code.split("");
  (function walk(node) {
    if (COMMENT_OR_STRING.test(node.type)) {
      for (let i = node.startIndex; i < node.endIndex; i++) if (chars[i] !== "\n") chars[i] = " ";
      return;
    }
    for (let i = 0; i < node.childCount; i++) walk(node.child(i));
  })(tree.rootNode);
  return chars.join("");
}

function collect(node, type, acc = []) {
  if (node.type === type) acc.push(node);
  for (let i = 0; i < node.namedChildCount; i++) collect(node.namedChild(i), type, acc);
  return acc;
}

const norm = (t) => t.replace(/\s+/g, "");

/** Объявления функций: [{ name, params: [типы], returns, line }]. */
export function functions(tree, cleanCode) {
  return collect(tree.rootNode, "function_declaration").map((n) => {
    const head = cleanCode.slice(n.startIndex, n.endIndex).split(/[{=]/)[0];
    const m = head.match(/fun\s+(?:<[^>]*>\s*)?(?:[\w.]+\.)?([A-Za-z_]\w*)\s*\(([\s\S]*)\)\s*(?::\s*([\s\S]+))?$/);
    if (!m) return null;
    const params = m[2].trim() ? splitTop(m[2]).map((p) => {
      const colon = p.indexOf(":");
      return colon < 0 ? "" : norm(p.slice(colon + 1).split("=")[0]);
    }) : [];
    return { name: m[1], params, returns: m[3] ? norm(m[3]) : "Unit", line: n.startPosition.row + 1 };
  }).filter(Boolean);
}

/** Классы: [{ name, kind: "class" | "data class" | "interface" | "object", line }]. */
export function classes(tree, cleanCode) {
  const out = [];
  for (const type of ["class_declaration", "object_declaration"]) {
    for (const n of collect(tree.rootNode, type)) {
      const head = cleanCode.slice(n.startIndex, n.endIndex).split(/[{(]/)[0];
      const m = head.match(/\b(data\s+class|enum\s+class|class|interface|object)\s+([A-Za-z_]\w*)/);
      if (m) out.push({ name: m[2], kind: m[1].replace(/\s+/, " "), line: n.startPosition.row + 1 });
    }
  }
  return out;
}

function splitTop(s) {
  const parts = [];
  let depth = 0;
  let cur = "";
  for (const ch of s) {
    if ("<([".includes(ch)) depth++;
    if (">)]".includes(ch)) depth--;
    if (ch === "," && depth === 0) { parts.push(cur); cur = ""; } else cur += ch;
  }
  if (cur.trim()) parts.push(cur);
  return parts;
}

/**
 * Проверка: { kind: "kotlin", cases: [ { id, type: "syntax" } | { id, type: "function", name, paramTypes?, returns? }
 *   | { id, type: "class", name, kind? } | { id, type: "contains" | "not_contains", pattern, message, raw? } ] }.
 */
export function checkKotlin(parse, code, spec) {
  const started = Date.now();
  const tree = parse(code);
  const report = { kind: "kotlin", cases: [] };
  try {
    const errors = syntaxErrors(tree, code);
    if (errors.length) {
      report.compileError = formatSyntaxErrors(errors);
    } else {
      const clean = codeOnly(tree, code);
      const fns = functions(tree, clean);
      const cls = classes(tree, clean);
      for (const c of spec.cases) {
        const base = { id: c.id, hidden: !!c.hidden, passed: false };
        if (c.hint) base.hint = c.hint;
        if (c.type === "syntax") {
          base.passed = true;
        } else if (c.type === "function") {
          const types = c.paramTypes;
          const want = `fun ${c.name}(${(types || []).join(", ")})${c.returns ? ": " + c.returns : ""}`;
          base.expected = want;
          const found = fns.filter((f) => f.name === c.name);
          if (!found.length) {
            base.actual = fns.length ? "есть: " + fns.map((f) => f.name + "()").join(", ") : "функций нет";
            base.hint = base.hint || `Объявите функцию ${c.name}: fun ${c.name}(…) { … }`;
          } else {
            const f = found[0];
            base.actual = `fun ${f.name}(${f.params.join(", ")}): ${f.returns}`;
            const okParams = !types || (f.params.length === types.length && f.params.every((p, i) => p === norm(types[i])));
            const okRet = !c.returns || f.returns === norm(c.returns);
            base.passed = okParams && okRet;
            if (!okParams) base.hint = base.hint || `Параметры должны быть такими: (${types.map((p, i) => `p${i + 1}: ${p}`).join(", ")})`;
            else if (!okRet) base.hint = base.hint || `Функция должна возвращать ${c.returns}: после скобок напишите «: ${c.returns}»`;
          }
        } else if (c.type === "class") {
          const found = cls.find((k) => k.name === c.name);
          base.expected = `${c.kind || "class"} ${c.name}`;
          base.actual = found ? `${found.kind} ${found.name}` : cls.length ? "есть: " + cls.map((k) => k.name).join(", ") : "классов нет";
          base.passed = !!found && (!c.kind || found.kind === c.kind);
        } else if (c.type === "contains" || c.type === "not_contains") {
          const text = c.raw ? code : clean;
          const re = new RegExp(c.pattern, c.flags || "m");
          const has = re.test(text);
          base.passed = c.type === "contains" ? has : !has;
          if (!base.passed) base.hint = c.message || base.hint;
        } else {
          throw new Error("Неизвестный вид проверки Kotlin: " + c.type);
        }
        if (base.hidden) { delete base.expected; delete base.actual; }
        report.cases.push(base);
      }
    }
  } finally {
    tree.delete();
  }
  report.passed = report.cases.filter((c) => c.passed).length;
  report.total = spec.cases.length;
  report.allPassed = report.cases.length > 0 && report.passed === report.total;
  report.durationMs = Date.now() - started;
  return report;
}
