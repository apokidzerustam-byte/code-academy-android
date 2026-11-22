// Собирает веб-раннер в assets приложения: хост-страницу, воркеры, sql.js и tree-sitter Kotlin.
import { build } from "esbuild";
import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const out = "../app/src/main/assets/webrunner";
mkdirSync(`${out}/licenses`, { recursive: true });
execFileSync(process.execPath, ["scripts/gen-harness.mjs"], { stdio: "inherit" });

const common = { bundle: true, minify: true, format: "iife", target: ["chrome69"], legalComments: "none" };
await build({ ...common, entryPoints: ["src/host.js"], outfile: `${out}/host.js` });
await build({ ...common, entryPoints: ["src/sql-worker.js"], outfile: `${out}/sql-worker.js` });
await build({ ...common, entryPoints: ["src/kotlin-worker.js"], outfile: `${out}/kotlin-worker.js` });
copyFileSync("src/index.html", `${out}/index.html`);

const copies = [
  ["node_modules/sql.js/dist/sql-wasm.js", "sql-wasm.js"],
  ["node_modules/sql.js/dist/sql-wasm.wasm", "sql-wasm.wasm"],
  ["node_modules/web-tree-sitter/tree-sitter.js", "tree-sitter.js"],
  ["node_modules/web-tree-sitter/tree-sitter.wasm", "tree-sitter.wasm"],
  ["node_modules/tree-sitter-wasms/out/tree-sitter-kotlin.wasm", "tree-sitter-kotlin.wasm"],
];
let total = 0;
for (const [src, dst] of copies) {
  copyFileSync(src, `${out}/${dst}`);
  total += statSync(src).size;
}
// Лицензии сторонних компонентов (все — MIT).
for (const [pkg, name] of [["sql.js", "sql.js"], ["web-tree-sitter", "web-tree-sitter"], ["tree-sitter-wasms", "tree-sitter-wasms"], ["acorn", "acorn"], ["acorn-walk", "acorn-walk"]]) {
  const lic = ["LICENSE", "LICENSE.md", "LICENSE.txt"].map((f) => `node_modules/${pkg}/${f}`).find(existsSync);
  if (lic) copyFileSync(lic, `${out}/licenses/${name}.txt`);
  else writeFileSync(`${out}/licenses/${name}.txt`, `${pkg}: MIT License (см. package.json пакета)\n`);
}
writeFileSync(`${out}/licenses/tree-sitter-kotlin.txt`, "tree-sitter-kotlin (fwcd/tree-sitter-kotlin), MIT License. Грамматика собрана в пакете tree-sitter-wasms.\n");
const versions = Object.fromEntries(["sql.js", "web-tree-sitter", "tree-sitter-wasms", "acorn"].map((p) => [p, JSON.parse(readFileSync(`node_modules/${p}/package.json`, "utf8")).version]));
writeFileSync(`${out}/versions.json`, JSON.stringify(versions));
console.log(`webrunner -> ${out}: ${(total / 1048576).toFixed(1)} MB wasm/js`, versions);
