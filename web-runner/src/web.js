// HTML/CSS/JS ученика: сборка страницы для песочницы, запуск и автопроверка (вид тестов "web").
import { protectLoops, JsSyntaxError, parseJs } from "./protect.js";
import { lintHtml, lintCss, lineAt } from "./lint.js";
import { HARNESS } from "./generated/harness-code.js";

export const FRAME_CSP =
  "default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; " +
  "img-src data: blob:; font-src data:; media-src data: blob:; connect-src 'none'; form-action 'none'; base-uri 'none'";

const DEFAULTS = { loopMs: 2000, asyncMs: 3000, settleMs: 30, maxOutput: 16384 };
const JS_TYPES = /^(|text\/javascript|application\/javascript|module)$/i;

function attr(attrs, name) {
  const m = attrs.match(new RegExp(`(?:^|\\s)${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s"'=<>\`]+))`, "i"));
  return m ? (m[1] ?? m[2] ?? m[3]) : null;
}

function escapeScript(code) {
  // Внутри <script> нельзя встретить </script — иначе браузер закончит скрипт раньше.
  return code.replace(/<\/(script)/gi, "<\\/$1");
}

function localPath(src) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(src) || src.startsWith("//")) return null;
  return src.replace(/^\.\//, "").replace(/^\//, "");
}

/** Текст ошибки с номером строки (если строка уже названа в сообщении — не повторяем). */
const withLine = (m) => m.text + (m.line && !/строк[еаи] \d/.test(m.text) ? ` (строка ${m.line})` : "");

/** Ошибка компиляции в формате отчёта: «SyntaxError: … (файл, строка N)». */
function syntaxText(e, file, line) {
  return `SyntaxError: ${e.message}\n  ${file}, строка ${line}, позиция ${e.column}`;
}

/**
 * Готовит страницу для iframe. Возвращает { html, warnings[], compileError }.
 * lang: "html" — code это HTML (files — остальные файлы проекта), "js" — code это скрипт.
 */
export function buildPage({ lang, code, files = {}, entry, stdin = "", nonce, tail = "", options = {} }) {
  const cfg = Object.assign({}, DEFAULTS, options, { nonce, stdin });
  const warnings = [];
  const head = `<meta http-equiv="Content-Security-Policy" content="${FRAME_CSP}"><script>(${HARNESS})(${JSON.stringify(cfg).replace(/</g, "\\u003c")})</script>`;
  const supports = typeof CSS !== "undefined" && CSS.supports ? (p, v) => CSS.supports(p, v) : null;
  let idBase = 0;

  const protect = (src, file, lineBase, module) => {
    try {
      const r = protectLoops(src, { module, idBase });
      idBase += r.count;
      return r.code;
    } catch (e) {
      if (e instanceof JsSyntaxError) {
        const err = new Error(syntaxText(e, file, lineBase + e.line - 1));
        err.compile = true;
        throw err;
      }
      throw e;
    }
  };

  try {
    if (lang === "js") {
      const js = protect(code, entry || "main.js", 1, false);
      const html = `<!doctype html><html><head><meta charset="utf-8">${head}</head><body><script>${escapeScript(js)}\n//# sourceURL=${entry || "main.js"}\n</script>${tail}</body></html>`;
      return { html, warnings };
    }
    const file = entry || "index.html";
    for (const w of lintHtml(code)) warnings.push({ file, ...w });
    // Внешние скрипты с defer/async выполняются после разбора страницы: встраиваем их в конец body.
    const deferred = [];
    let html = code.replace(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi, (all, attrs, body, offset) => {
      const type = (attr(attrs, "type") || "").trim();
      if (!JS_TYPES.test(type)) return all;
      const module = type.toLowerCase() === "module";
      const src = attr(attrs, "src");
      const line = lineAt(code, offset);
      if (src != null) {
        const p = localPath(src);
        if (p == null) {
          warnings.push({ file, line, text: `Внешний скрипт ${src} не загрузится: приложение работает без интернета` });
          return all;
        }
        if (!(p in files)) {
          warnings.push({ file, line, text: `Файл ${src} не найден в проекте` });
          return "<script></script>";
        }
        const js = protect(files[p], p, 1, module);
        const tag = `<script${module ? ' type="module"' : ""}>${escapeScript(js)}\n//# sourceURL=${p}\n</script>`;
        if (!module && /(?:^|\s)(defer|async)(?:\s|=|$)/i.test(attrs)) { deferred.push(tag); return ""; }
        return tag;
      }
      const openLen = all.indexOf(">") + 1;
      const js = protect(body, file, lineAt(code, offset + openLen), module);
      return all.slice(0, openLen) + escapeScript(js) + all.slice(openLen + body.length);
    });
    if (deferred.length) {
      const i = html.search(/<\/body\s*>/i);
      html = i >= 0 ? html.slice(0, i) + deferred.join("") + html.slice(i) : html + deferred.join("");
    }
    // Подключённые CSS-файлы проекта встраиваются; внешние — предупреждение.
    html = html.replace(/<link\b([^>]*)>/gi, (all, attrs, offset) => {
      if (!/stylesheet/i.test(attr(attrs, "rel") || "")) return all;
      const href = attr(attrs, "href");
      if (href == null) return all;
      const p = localPath(href);
      const line = lineAt(code, offset);
      if (p == null) {
        warnings.push({ file, line, text: `Внешний стиль ${href} не загрузится: приложение работает без интернета` });
        return all;
      }
      if (!(p in files)) {
        warnings.push({ file, line, text: `Файл ${href} не найден в проекте` });
        return "";
      }
      for (const w of lintCss(files[p], supports, 1)) warnings.push({ file: p, ...w });
      return `<style>${files[p].replace(/<\/(style)/gi, "<\\/$1")}</style>`;
    });
    code.replace(/<style\b[^>]*>([\s\S]*?)<\/style\s*>/gi, (all, body, offset) => {
      const startLine = lineAt(code, offset + all.indexOf(">") + 1);
      for (const w of lintCss(body, supports, startLine)) warnings.push({ file, ...w });
      return all;
    });
    // Служебный код — сразу после <!doctype>, без переводов строк: номера строк ученика не меняются.
    const dt = html.match(/^\s*<!doctype[^>]*>/i);
    const at = dt ? dt[0].length : 0;
    html = html.slice(0, at) + head + html.slice(at) + tail;
    warnings.sort((a, b) => (a.file === b.file ? a.line - b.line : a.file === file ? -1 : b.file === file ? 1 : a.file < b.file ? -1 : 1));
    return { html, warnings };
  } catch (e) {
    if (e.compile) return { html: null, warnings, compileError: e.message };
    throw e;
  }
}

let frameSeq = 0;

/**
 * Запускает страницу в iframe с sandbox. Возвращает объект сеанса: вывод, ошибки,
 * evaluate(...) для тестов и close(). visible — показать страницу (предпросмотр).
 */
export function startFrame(page, { container, visible = false, timeoutMs = 8000, nonce, onEvent } = {}) {
  const frame = document.createElement("iframe");
  frame.setAttribute("sandbox", "allow-scripts allow-forms");
  frame.setAttribute("referrerpolicy", "no-referrer");
  frame.setAttribute("title", "Страница ученика");
  frame.id = "ca-frame-" + ++frameSeq;
  frame.style.cssText = visible
    ? "border:0;width:100%;height:100%;display:block;background:#fff"
    : "border:0;position:fixed;left:0;top:0;width:360px;height:640px;opacity:0;pointer-events:none";
  const s = {
    frame, stdout: "", stderr: "", errors: [], truncated: false, loaded: false,
    waiting: new Map(), seq: 0, closed: false,
  };
  let loadedResolve;
  s.loadedPromise = new Promise((r) => { loadedResolve = r; });
  const timer = setTimeout(() => loadedResolve(false), timeoutMs);
  s.listener = (ev) => {
    const m = ev.data;
    if (!m || m.__ca !== nonce || ev.source !== frame.contentWindow) return;
    if (m.t === "out") {
      if (m.stream === "stderr") s.stderr += m.text; else s.stdout += m.text;
      if (m.cut) s.truncated = true;
    } else if (m.t === "error") {
      s.errors.push(m);
      s.stderr += withLine(m) + "\n";
    } else if (m.t === "loaded") {
      s.loaded = true;
      clearTimeout(timer);
      loadedResolve(true);
    } else if (m.t === "value") {
      const w = s.waiting.get(m.id);
      if (w) { s.waiting.delete(m.id); w(m); }
    }
    if (onEvent) onEvent(m);
  };
  window.addEventListener("message", s.listener);
  s.evaluate = (msg, ms) => new Promise((resolve) => {
    const id = ++s.seq;
    const t = setTimeout(() => { s.waiting.delete(id); resolve({ ok: false, timeout: true, error: "Проверка не ответила: страница зависла" }); }, ms);
    s.waiting.set(id, (m) => { clearTimeout(t); resolve(m); });
    frame.contentWindow.postMessage(Object.assign({ __ca: nonce, t: "eval", id }, msg), "*");
  });
  s.close = () => {
    if (s.closed) return;
    s.closed = true;
    clearTimeout(timer);
    window.removeEventListener("message", s.listener);
    frame.remove();
  };
  frame.srcdoc = page;
  (container || document.body).appendChild(frame);
  return s;
}

// ------------------------------------------------------------------------------
// Проверка заданий
// ------------------------------------------------------------------------------

const IDENT = /^[A-Za-z_$][\w$]*$/;

function normalize(text, mode) {
  const t = String(text ?? "").replace(/\r\n?/g, "\n");
  if (mode === "exact") return t;
  if (mode === "lines") return t.split("\n").map((l) => l.trimEnd()).join("\n").replace(/\n+$/, "");
  return t.split("\n").map((l) => l.trimEnd()).join("\n").trim();
}

export function valuesEqual(a, b, tol = 1e-9) {
  if (typeof a === "number" && typeof b === "number") return a === b || Math.abs(a - b) <= tol * Math.max(1, Math.abs(a), Math.abs(b));
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object") return a === b;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) return a.length === b.length && a.every((x, i) => valuesEqual(x, b[i], tol));
  const ka = Object.keys(a).sort();
  const kb = Object.keys(b).sort();
  return ka.length === kb.length && ka.every((k, i) => k === kb[i] && valuesEqual(a[k], b[k], tol));
}

/** Хвост страницы: доступ к функциям ученика и функции тестов автора. */
function testTail(spec) {
  const names = new Set();
  const fns = [];
  const index = new Map();
  for (const c of spec.cases) {
    if (c.function) {
      if (!IDENT.test(c.function)) throw new Error("Недопустимое имя функции в тесте: " + c.function);
      names.add(c.function);
    }
    for (const key of ["before", "expr"]) {
      if (c[key] == null) continue;
      const body = key === "expr" ? `return (${c[key]});` : String(c[key]);
      index.set(c, Object.assign(index.get(c) || {}, { [key]: fns.length }));
      fns.push(`function(){${body}\n}`);
    }
  }
  const getters = [...names].map((n) => `${JSON.stringify(n)}:function(){try{return typeof ${n}==="undefined"?undefined:${n}}catch(e){return undefined}}`);
  return {
    tail: `<script>__caExport({${getters.join(",")}});window.__caTests=[${fns.join(",")}];</script>`,
    index,
  };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function describeValue(v) {
  if (v && typeof v === "object" && v.__undefined) return "undefined";
  return v;
}

/**
 * Проверка решения. spec: { kind: "web", lang: "html"|"js", match?, settleMs?, cases: [...] }.
 * Случаи: { expected_stdout, stdin? } — вывод консоли; { function, args, expected | expected_error };
 * { expr, expected, before? } — значение выражения на странице (DOM), before — действия перед ним.
 */
export async function checkWeb(code, spec, { container, files = {}, entry, aborted = () => false } = {}) {
  const started = Date.now();
  const mode = spec.match || "strip";
  const tol = spec.tolerance ?? 1e-9;
  let tailInfo;
  try {
    tailInfo = testTail(spec);
  } catch (e) {
    return { error: String(e.message || e) };
  }
  const report = { kind: "web", cases: [] };
  const lint = [];
  for (const c of spec.cases) {
    if (aborted()) break;
    const nonce = "n" + Math.random().toString(36).slice(2);
    const built = buildPage({ lang: spec.lang || "html", code, files, entry, stdin: c.stdin || "", nonce, tail: tailInfo.tail, options: spec.options || {} });
    if (built.compileError) {
      report.compileError = built.compileError;
      report.cases = [];
      break;
    }
    if (!lint.length) for (const w of built.warnings) lint.push(`${w.file}, строка ${w.line}: ${w.text}`);
    const s = startFrame(built.html, { container, nonce, timeoutMs: spec.loadTimeoutMs || 6000 });
    try {
      const loaded = await s.loadedPromise;
      const base = { id: c.id, hidden: !!c.hidden, passed: false };
      if (c.hint) base.hint = c.hint;
      if (!loaded) {
        report.cases.push(Object.assign(base, { error: "Страница не загрузилась за отведённое время — возможно, бесконечный цикл" }));
        continue;
      }
      const ix = tailInfo.index.get(c) || {};
      if (ix.before != null) {
        const r = await s.evaluate({ kind: "test", index: ix.before }, spec.evalTimeoutMs || 4000);
        if (!r.ok) {
          report.cases.push(Object.assign(base, { error: r.error }));
          continue;
        }
        await sleep(spec.settleMs ?? 60);
      }
      if (c.function) {
        const r = await s.evaluate({ kind: "function", name: c.function, args: c.args || [] }, spec.evalTimeoutMs || 4000);
        if (r.missing) {
          const load = s.errors[0];
          report.loadError = load ? withLine(load) : r.error;
          report.cases = [];
          break;
        }
        base.input = c.args || [];
        if ("expected_error" in c) {
          base.expected = c.expected_error;
          base.passed = !r.ok && r.errorName === c.expected_error;
          if (r.ok) base.actual = describeValue(r.value);
          else if (!base.passed) base.error = r.error;
        } else {
          base.expected = c.expected;
          if (r.ok) {
            base.actual = describeValue(r.value);
            base.passed = valuesEqual(c.expected, r.value, tol);
          } else base.error = r.error;
        }
      } else if (c.expr != null) {
        const r = await s.evaluate({ kind: "test", index: ix.expr }, spec.evalTimeoutMs || 4000);
        base.expected = c.expected;
        if (r.ok) {
          base.actual = describeValue(r.value);
          base.passed = valuesEqual(c.expected, r.value, tol);
        } else base.error = r.error;
        if (!base.passed && s.errors.length && !base.error) base.error = withLine(s.errors[0]);
      } else {
        // Вывод консоли после загрузки (и действий before). Короткие таймеры успевают вывести, как в «Запустить».
        await sleep(spec.outputWaitMs ?? 300);
        const exp = normalize(c.expected_stdout, mode);
        const act = normalize(s.stdout, mode);
        if (c.stdin) base.input = c.stdin;
        base.expected = exp;
        base.actual = act;
        base.passed = exp === act && !s.errors.length;
        if (s.errors.length) base.error = s.errors.map(withLine).join("\n");
      }
      if (base.hidden) {
        delete base.input; delete base.expected; delete base.actual;
        if (base.error) base.error = base.error.split("\n")[0];
      }
      report.cases.push(base);
    } finally {
      s.close();
    }
  }
  report.passed = report.cases.filter((c) => c.passed).length;
  report.total = spec.cases.length;
  report.allPassed = report.cases.length > 0 && report.passed === report.total;
  if (lint.length) report.warnings = lint;
  report.durationMs = Date.now() - started;
  return report;
}

/** Обычный запуск без тестов: вывод консоли, ошибки и предупреждения. */
export async function runWeb({ lang, code, files, entry, stdin, container, visible, timeoutMs = 8000, waitMs = 300, onEvent, maxOutput }) {
  const nonce = "n" + Math.random().toString(36).slice(2);
  const started = Date.now();
  const built = buildPage({ lang, code, files, entry, stdin, nonce, options: maxOutput ? { maxOutput } : {} });
  const warnText = built.warnings.map((w) => `Предупреждение: ${w.file}, строка ${w.line}: ${w.text}\n`).join("");
  if (built.compileError) {
    return { session: null, result: { status: "SYNTAX_ERROR", stdout: "", stderr: built.compileError + "\n" + warnText, truncated: false, durationMs: Date.now() - started } };
  }
  const s = startFrame(built.html, { container, visible, nonce, timeoutMs, onEvent });
  const loaded = await s.loadedPromise;
  if (loaded) await sleep(waitMs); // короткие таймеры после загрузки тоже успевают вывести
  const status = !loaded ? "TIMEOUT" : s.errors.length ? "ERROR" : "OK";
  return {
    session: s,
    result: { status, stdout: s.stdout, stderr: s.stderr + warnText, truncated: s.truncated, durationMs: Date.now() - started },
  };
}

export { parseJs };
