// Запускает задания контента через ТОТ ЖЕ веб-раннер, что и приложение (assets/webrunner),
// в настольном Chromium: адрес страницы, политика CSP и ответы — как в WebView приложения.
// Использование: node tools/run-jobs.mjs jobs.json results.json [assetsDir]
// jobs.json: [{ id, lang: html|js|sql|kotlin, mode: run|check, code, tests?, setup?, stdin?, files? }]
import { chromium } from "playwright-core";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve, extname } from "node:path";

const [jobsPath, outPath, assetsArg] = process.argv.slice(2);
const assets = resolve(assetsArg || new URL("../../app/src/main/assets", import.meta.url).pathname);
const jobs = JSON.parse(readFileSync(jobsPath, "utf8"));
const ORIGIN = "https://appassets.androidplatform.net";
const CSP = "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' blob:; " +
  "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; media-src 'self' data: blob:; " +
  "connect-src 'self'; worker-src 'self'; frame-src 'self' about: data: blob:; form-action 'none'; base-uri 'none'";
const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".wasm": "application/wasm", ".json": "application/json" };
const chrome = process.env.CHROME_PATH || ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium"].find(existsSync);

const browser = await chromium.launch({ executablePath: chrome, args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 360, height: 640 } });
const network = [];
await page.route("**/*", (route) => {
  const url = new URL(route.request().url());
  if (url.origin !== ORIGIN || !url.pathname.startsWith("/assets/")) {
    network.push(url.href);
    return route.abort();
  }
  const file = join(assets, decodeURIComponent(url.pathname.slice("/assets/".length)));
  if (!file.startsWith(assets) || !existsSync(file)) return route.fulfill({ status: 404, body: "" });
  return route.fulfill({
    status: 200, body: readFileSync(file),
    headers: { "Content-Type": MIME[extname(file)] || "application/octet-stream", "Content-Security-Policy": CSP },
  });
});
// Мост как в приложении: страница пишет в caHost.postMessage.
await page.addInitScript(() => {
  window.__caMsgs = [];
  window.caHost = { postMessage: (s) => window.__caMsgs.push(JSON.parse(s)) };
});
await page.goto(`${ORIGIN}/assets/webrunner/index.html`);
await page.waitForFunction(() => window.__caMsgs.some((m) => m.type === "ready"), null, { timeout: 30000 });

const results = {};
let runId = 0;
for (const job of jobs) {
  const id = ++runId;
  const msg = { runId: id, lang: job.lang, mode: job.mode || "run", code: job.code, stdin: job.stdin || "", setup: job.setup || "",
    files: job.files || null, entry: job.entry || null, tests: job.tests ? JSON.stringify(job.tests) : "", maxOutput: 65536 };
  await page.evaluate((m) => window.caRun(m), msg);
  try {
    const handle = await page.waitForFunction((rid) => window.__caMsgs.find((m) => m.type === "result" && m.runId === rid), id,
      { timeout: job.timeoutMs || 30000, polling: 50 });
    const m = await handle.jsonValue();
    results[job.id] = m.check ? { check: JSON.parse(m.check) } : m.result ? { result: JSON.parse(m.result) } : { error: m.error || "нет результата" };
  } catch (e) {
    await page.evaluate(() => window.caStop());
    results[job.id] = { timeout: true };
  }
}
results.__network = network;
writeFileSync(outPath, JSON.stringify(results));
await browser.close();
console.log(`run-jobs: ${jobs.length} заданий, сетевых запросов: ${network.length}`);
