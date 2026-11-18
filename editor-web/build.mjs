import { build } from "esbuild";
import { copyFileSync, mkdirSync } from "node:fs";

const out = "../app/src/main/assets/editor";
mkdirSync(out, { recursive: true });
await build({
  entryPoints: ["src/main.js"],
  bundle: true,
  minify: true,
  format: "iife",
  target: ["chrome80"],
  outfile: `${out}/editor.js`,
  legalComments: "external",
});
copyFileSync("src/index.html", `${out}/index.html`);
console.log("editor bundle ->", out);
