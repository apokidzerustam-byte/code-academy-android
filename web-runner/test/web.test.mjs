// Локальная проверка веб-раннера в настоящем Chromium (Playwright). Запуск: node test/web.test.mjs
import { build } from "esbuild";
import { chromium } from "playwright-core";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "build");
mkdirSync(out, { recursive: true });
await build({ entryPoints: [join(here, "web-entry.js")], bundle: true, format: "iife", target: ["chrome69"], outfile: join(out, "web.js") });
// Та же политика, что и у хост-страницы в приложении.
writeFileSync(join(out, "web.html"), `<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-src 'self' about: data: blob:; form-action 'none'; base-uri 'none'">
</head><body><script src="web.js"></script></body></html>`);

const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", args: ["--no-sandbox"] });
const page = await browser.newPage();
const requests = [];
// Запрос, дошедший до сетевого уровня (CSP блокирует раньше — такие сюда не попадают).
await page.route(/^(https?|wss?):/, (route) => { requests.push(route.request().url()); route.abort(); });
await page.goto("file://" + join(out, "web.html"));

const run = (opts) => page.evaluate(async (o) => (await window.caTest.runWeb(o)).result, opts);
const check = (code, spec, extra = {}) => page.evaluate(([c, s, e]) => window.caTest.checkWeb(c, s, e), [code, spec, extra]);
let n = 0;
async function t(name, fn) {
  try { await fn(); n++; console.log("ok  ", name); } catch (e) { console.log("FAIL", name, "\n", e.message); process.exitCode = 1; }
}

await t("js: console.log форматирует значения", async () => {
  const r = await run({ lang: "js", code: 'console.log("Привет", 5)\nconsole.log([1, "a", [2]], {a: 1, "b c": null})\nconsole.log(new Map([["k", 1]]), new Set([1]), undefined, -0, 10n)' });
  assert.equal(r.status, "OK");
  assert.equal(r.stdout, 'Привет 5\n[1, "a", [2]] {a: 1, "b c": null}\nMap(1) {"k" => 1} Set(1) {1} undefined -0 10n\n');
});
await t("js: бесконечный цикл останавливается с понятной ошибкой", async () => {
  const t0 = Date.now();
  const r = await run({ lang: "js", code: "let i = 0\nwhile (true) {\n  i++\n}\nconsole.log('после')" });
  assert.equal(r.status, "ERROR");
  assert.match(r.stderr, /InfiniteLoopError: цикл в строке 2/);
  assert.ok(Date.now() - t0 < 5000, "долго: " + (Date.now() - t0));
});
await t("js: for(;;); без тела и do-while тоже защищены", async () => {
  const r1 = await run({ lang: "js", code: "for(;;);" });
  assert.match(r1.stderr, /InfiniteLoopError/);
  const r2 = await run({ lang: "js", code: "do x = 1; while (true)" });
  assert.match(r2.stderr, /InfiniteLoopError/);
});
await t("js: циклы с метками и continue работают как без защиты", async () => {
  const code = "let s = 0\nouter: for (let i = 0; i < 5; i++) {\n  for (let j = 0; j < 5; j++) {\n    if (j > i) continue outer\n    if (i === 4) break outer\n    s += j\n  }\n}\nlet k = 0\nif (s) while (k < 3) k++\nelse k = -1\nfor (const x of [1,2]) for (const y in {a:1}) s += x\nconsole.log(s, k)";
  const r = await run({ lang: "js", code });
  assert.equal(r.status, "OK", r.stderr);
  assert.equal(r.stdout, "13 3\n");
});
await t("js: синтаксическая ошибка с номером строки, ничего не выполняется", async () => {
  const r = await run({ lang: "js", code: "console.log('a')\nconsole.log('b'" });
  assert.equal(r.status, "SYNTAX_ERROR");
  assert.match(r.stderr, /SyntaxError: .*\n  main\.js, строка 2/);
  assert.equal(r.stdout, "");
});
await t("js: ошибка выполнения с номером строки", async () => {
  const r = await run({ lang: "js", code: "console.log(1)\n\nfoo()" });
  assert.equal(r.status, "ERROR");
  assert.equal(r.stdout, "1\n");
  assert.match(r.stderr, /ReferenceError: foo is not defined \(строка 3\)/);
});
await t("js: prompt читает ввод, alert выводит", async () => {
  const r = await run({ lang: "js", code: "const name = prompt('Имя?')\nalert('Привет, ' + name)\nconsole.log(prompt())", stdin: "Аня\n" });
  assert.equal(r.stdout, "[alert] Привет, Аня\nnull\n");
});
await t("js: сеть недоступна", async () => {
  const r = await run({ lang: "js", code: "fetch('https://example.com/x').then(() => console.log('сеть есть'), (e) => console.log('нет сети'))", waitMs: 800 });
  assert.equal(r.stdout, "нет сети\n");
});
await t("js: вывод из setTimeout после загрузки", async () => {
  const r = await run({ lang: "js", code: "setTimeout(() => console.log('потом'), 50)\nconsole.log('сразу')" });
  assert.equal(r.stdout, "сразу\nпотом\n");
});
await t("js: огромный вывод обрезается", async () => {
  const r = await run({ lang: "js", code: "for (let i = 0; i < 100000; i++) console.log('строка ' + i)", maxOutput: 2000 });
  assert.equal(r.truncated, true);
  assert.ok(r.stdout.length <= 2000);
});
await t("js: рекурсия без выхода — RangeError", async () => {
  const r = await run({ lang: "js", code: "function f() { return f() }\nf()" });
  assert.match(r.stderr, /RangeError/);
});

const PAGE = `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Тест</title>
  <style>
    h1 { colr: red; }
    p { color: bluee; margin: 4px }
    .ok { display: flex }
  </style>
</head>
<body>
  <h1 id="t">Счётчик</h1>
  <div class="box">
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
  <button id="b">+1</button>
  <span id="n">0</span>
  <script>
    let count = 0
    document.getElementById('b').addEventListener('click', () => {
      count++
      document.getElementById('n').textContent = count
      console.log('клик', count)
    })
  </script>
</body>
</html>`;
await t("html: предупреждения о CSS и разметке со строками", async () => {
  const r = await run({ lang: "html", code: PAGE });
  assert.equal(r.status, "OK", r.stderr);
  assert.match(r.stderr, /строка 7: Неизвестное свойство «colr»/);
  assert.match(r.stderr, /строка 8: Недопустимое значение «bluee» для свойства «color»/);
  assert.match(r.stderr, /строка 14: Тег <div> не закрыт до <\/body>/);
  assert.match(r.stderr, /строка 15: У <img> нет атрибута alt/);
  assert.doesNotMatch(r.stderr, /display/);
  assert.ok(r.stderr.indexOf("строка 7") < r.stderr.indexOf("строка 14"), "предупреждения по порядку строк");
});
await t("html: ошибка в скрипте — номер строки файла", async () => {
  const r = await run({ lang: "html", code: "<!doctype html>\n<p>x</p>\n<script>\n  let a = 1\n  a.b.c = 2\n</script>" });
  assert.match(r.stderr, /TypeError: .* \(строка 5\)/);
  const r2 = await run({ lang: "html", code: "<!doctype html>\n<p>x</p>\n<script>\n  let a = (1\n</script>" });
  assert.equal(r2.status, "SYNTAX_ERROR");
  assert.match(r2.stderr, /index\.html, строка 5/);
});
await t("html: проект из файлов — script.js и style.css", async () => {
  const files = { "style.css": "h1 { color: red }\nh2 { fontsize: 2px }\nh3 { color: ; margin: 1px\n  padding: 2px }", "script.js": "console.log(document.title)\nnull.x" };
  const r = await run({ lang: "html", code: "<!doctype html><title>Т</title><link rel=\"stylesheet\" href=\"style.css\"><h1>Hi</h1><script src=\"script.js\"></script><script src=\"https://cdn.example.com/x.js\"></script>", files });
  assert.equal(r.stdout, "Т\n");
  assert.match(r.stderr, /style\.css, строка 2: Неизвестное свойство «fontsize»/);
  assert.match(r.stderr, /style\.css, строка 3: У свойства «color» нет значения/);
  assert.match(r.stderr, /style\.css, строка 3: Недопустимое значение «1px\n  padding: 2px» для свойства «margin» — похоже, пропущена «;»/);
  assert.match(r.stderr, /TypeError: .*\(строка 2\)/);
  assert.match(r.stderr, /Внешний скрипт https:\/\/cdn\.example\.com\/x\.js не загрузится/);
});
await t("html: стандартный режим (doctype не сдвинут)", async () => {
  const r = await run({ lang: "html", code: "<!DOCTYPE html>\n<script>console.log(document.compatMode)</script>" });
  assert.equal(r.stdout, "CSS1Compat\n");
});

const SPEC = {
  kind: "web", lang: "html",
  cases: [
    { id: "title", expr: "document.querySelector('h1').textContent", expected: "Счётчик" },
    { id: "click", before: "document.getElementById('b').click(); document.getElementById('b').click()", expr: "document.getElementById('n').textContent", expected: "2" },
    { id: "log", before: "document.getElementById('b').click()", expected_stdout: "клик 1" },
    { id: "hidden", hidden: true, before: "for (let i = 0; i < 3; i++) document.getElementById('b').click()", expr: "+document.getElementById('n').textContent", expected: 3, hint: "Счётчик растёт на 1" },
  ],
};
await t("check html: эталон проходит все случаи", async () => {
  const r = await check(PAGE, SPEC);
  assert.equal(r.allPassed, true, JSON.stringify(r, null, 1));
  assert.equal(r.total, 4);
  assert.ok(r.warnings.length >= 3);
});
await t("check html: неверное решение не проходит, скрытый тест без деталей", async () => {
  const wrong = PAGE.replace("count++", "count += 2");
  const r = await check(wrong, SPEC);
  assert.equal(r.allPassed, false);
  const h = r.cases.find((c) => c.id === "hidden");
  assert.equal(h.passed, false);
  assert.equal(h.expected, undefined);
  assert.equal(h.actual, undefined);
  assert.equal(h.hint, "Счётчик растёт на 1");
  assert.equal(r.cases.find((c) => c.id === "click").actual, "4");
});
await t("check js: функции, const-стрелки, async, ожидаемая ошибка", async () => {
  const spec = { kind: "web", lang: "js", cases: [
    { id: "a", function: "sum", args: [2, 3], expected: 5 },
    { id: "b", function: "half", args: [3], expected: 1.5 },
    { id: "c", function: "later", args: [], expected: { ok: true, list: [1, 2] } },
    { id: "d", function: "boom", args: [], expected_error: "TypeError" },
    { id: "e", expected_stdout: "готово" },
  ] };
  const code = "function sum(a, b) { return a + b }\nconst half = (x) => x / 2\nasync function later() { return { ok: true, list: [1, 2] } }\nfunction boom() { null.x }\nconsole.log('готово')";
  const r = await check(code, spec);
  assert.equal(r.allPassed, true, JSON.stringify(r, null, 1));
  const r2 = await check(code.replace("a + b", "a - b"), spec);
  assert.equal(r2.passed, 4);
  assert.deepEqual(r2.cases[0].actual, -1);
});
await t("check js: функции нет — loadError; синтаксис — compileError; цикл — ошибка случая", async () => {
  const spec = { kind: "web", lang: "js", cases: [{ id: "a", function: "sum", args: [1, 1], expected: 2 }] };
  const r = await check("function summ(a, b) { return a + b }", spec);
  assert.match(r.loadError, /Функция sum\(\) не найдена/);
  const r2 = await check("function sum(a, b) { return a + }", spec);
  assert.match(r2.compileError, /SyntaxError/);
  assert.equal(r2.allPassed, false);
  const r3 = await check("function sum(a, b) { while (a) {} }", spec);
  assert.equal(r3.passed, 0);
  assert.match(r3.cases[0].error, /InfiniteLoopError/);
  const r4 = await check("null.x\nfunction sum(a, b) { return a + b }", { kind: "web", lang: "js", cases: [{ id: "o", expected_stdout: "" }] });
  assert.match(r4.cases[0].error, /TypeError/);
});
await t("check: бесконечный цикл верхнего уровня на странице не вешает проверку", async () => {
  const r = await check("<p id=x>1</p><script>while(1){}</script>", { kind: "web", lang: "html", cases: [{ id: "a", expr: "document.getElementById('x').textContent", expected: "1" }] });
  // Цикл прерван ошибкой, страница загрузилась — DOM доступен, но ошибка показана.
  assert.equal(r.cases.length, 1);
});
const allowed = requests.filter((u) => !u.startsWith("file://") && !u.startsWith("data:") && !u.startsWith("about:"));
await t("никаких сетевых запросов", async () => assert.deepEqual(allowed, []));
await browser.close();
console.log(`\n${n} тестов прошло`);
