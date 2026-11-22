// Превращает harness.js в однострочную строку для вставки в страницу ученика.
import { transformSync } from "esbuild";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { caHarness } from "../src/harness.js";

const here = dirname(fileURLToPath(import.meta.url));
// Присваивание не даёт минификатору выбросить «неиспользуемое» выражение.
const out = transformSync(`__caH=${caHarness.toString()}`, { minify: true, target: "chrome69", loader: "js", supported: { "template-literal": false } }).code.trim();
if (!out.startsWith("__caH=")) throw new Error("harness: неожиданный вывод esbuild");
const code = "(" + out.slice("__caH=".length).replace(/;$/, "") + ")";
if (code.includes("\n")) throw new Error("harness: в минифицированном коде остался перевод строки");
mkdirSync(join(here, "../src/generated"), { recursive: true });
writeFileSync(join(here, "../src/generated/harness-code.js"),
  `// Сгенерировано scripts/gen-harness.mjs — не редактировать.\nexport const HARNESS = ${JSON.stringify(code)};\n`);
console.log(`harness: ${code.length} символов`);
