// Web Worker: разбор Kotlin через tree-sitter (WebAssembly).
/* global TreeSitter, importScripts */
import { syntaxErrors, formatSyntaxErrors, checkKotlin } from "./kotlin-core.js";

importScripts("tree-sitter.js");
const Parser = self.TreeSitter;
let parser = null;
const ready = Parser.init({ locateFile: (f) => f })
  .then(() => Parser.Language.load("tree-sitter-kotlin.wasm"))
  .then((lang) => { parser = new Parser(); parser.setLanguage(lang); });

const NO_RUN =
  "Синтаксис в порядке.\n" +
  "Запустить Kotlin прямо на телефоне нельзя: компилятору Kotlin нужна Java-машина, которой нет внутри приложения.\n" +
  "Здесь проверяются синтаксис и устройство кода. Запустить программу можно в GitHub Actions:\n" +
  "создайте в «Проектах» проект Kotlin — инструкция в файле README.md.\n";

onmessage = async (e) => {
  const m = e.data;
  try {
    await ready;
    if (m.mode === "check") {
      postMessage({ type: "result", runId: m.runId, check: checkKotlin((c) => parser.parse(c), m.code, JSON.parse(m.tests)) });
      return;
    }
    const started = Date.now();
    const tree = parser.parse(m.code);
    try {
      const errors = syntaxErrors(tree, m.code);
      const result = errors.length
        ? { status: "SYNTAX_ERROR", stdout: "", stderr: formatSyntaxErrors(errors, m.entry || "Main.kt") + "\n" }
        : { status: "OK", stdout: NO_RUN, stderr: "" };
      postMessage({ type: "result", runId: m.runId, result: Object.assign(result, { truncated: false, durationMs: Date.now() - started }) });
    } finally {
      tree.delete();
    }
  } catch (err) {
    postMessage({ type: "result", runId: m.runId, error: String((err && err.stack) || err) });
  }
};
