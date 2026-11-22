// Подсказки по HTML и CSS: браузер молча исправляет такие ошибки, а новичку важно их видеть.

const VOID = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"]);
// Закрывающий тег у этих элементов необязателен по стандарту HTML — не ругаемся.
const OPTIONAL_END = new Set(["html", "head", "body", "p", "li", "dt", "dd", "option", "optgroup", "tr", "td", "th",
  "thead", "tbody", "tfoot", "colgroup", "rp", "rt", "caption"]);
const RAW_TEXT = new Set(["script", "style", "textarea", "title"]);

export function lineAt(text, pos) {
  let n = 1;
  for (let i = 0; i < pos && i < text.length; i++) if (text.charCodeAt(i) === 10) n++;
  return n;
}

/** Предупреждения по разметке: незакрытые и лишние теги, дубли id, img без alt. */
export function lintHtml(html) {
  const warn = [];
  const stack = [];
  const ids = new Map();
  const tagRe = /<!--[\s\S]*?(?:-->|$)|<!(?:doctype|DOCTYPE)[^>]*>|<\/?([A-Za-z][A-Za-z0-9-]*)((?:\s+[^\s"'>\/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?)*)\s*(\/?)>/g;
  let m;
  while ((m = tagRe.exec(html))) {
    const full = m[0];
    if (full.startsWith("<!")) {
      if (full.startsWith("<!--") && !full.endsWith("-->")) warn.push({ line: lineAt(html, m.index), text: "Комментарий <!-- не закрыт -->" });
      continue;
    }
    const name = m[1].toLowerCase();
    const line = lineAt(html, m.index);
    if (full.startsWith("</")) {
      const idx = stack.map((e) => e.name).lastIndexOf(name);
      if (idx < 0) {
        if (!VOID.has(name) && !OPTIONAL_END.has(name)) warn.push({ line, text: `Лишний закрывающий тег </${name}>: открывающего <${name}> нет` });
        continue;
      }
      for (let i = stack.length - 1; i > idx; i--) {
        const e = stack[i];
        if (!OPTIONAL_END.has(e.name)) warn.push({ line: e.line, text: `Тег <${e.name}> не закрыт до </${name}> (строка ${line})` });
      }
      stack.length = idx;
      continue;
    }
    const attrs = m[2] || "";
    const id = attrs.match(/(?:^|\s)id\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))/i);
    if (id) {
      const v = id[1] ?? id[2] ?? id[3];
      if (ids.has(v)) warn.push({ line, text: `id="${v}" уже есть в строке ${ids.get(v)}: id должен быть уникальным` });
      else ids.set(v, line);
    }
    if (name === "img" && !/(?:^|\s)alt\s*=|(?:^|\s)alt(?=\s|$)/i.test(attrs)) {
      warn.push({ line, text: "У <img> нет атрибута alt — для доступности опишите картинку: alt=\"…\"" });
    }
    if (VOID.has(name) || m[3] === "/") continue;
    if (RAW_TEXT.has(name)) {
      const end = html.toLowerCase().indexOf(`</${name}`, tagRe.lastIndex);
      if (end < 0) {
        warn.push({ line, text: `Тег <${name}> не закрыт` });
        break;
      }
      tagRe.lastIndex = end;
    }
    stack.push({ name, line });
  }
  for (const e of stack) if (!OPTIONAL_END.has(e.name)) warn.push({ line: e.line, text: `Тег <${e.name}> не закрыт` });
  return warn.sort((a, b) => a.line - b.line);
}

// At-правила, внутри которых обычные CSS-свойства.
const NESTED_AT = /^@(media|supports|container|layer|document)\b/i;

/**
 * Предупреждения по CSS: неизвестные свойства и недопустимые значения.
 * supports(prop, value) — CSS.supports браузера. lineBase — строка начала CSS в файле.
 */
export function lintCss(css, supports, lineBase = 1) {
  const warn = [];
  if (typeof supports !== "function") return warn;
  const src = css.replace(/\/\*[\s\S]*?(\*\/|$)/g, (c) => c.replace(/[^\n]/g, " "));
  const blocks = []; // стек: что открыто — "rule" (свойства) или "skip"/"group"
  let start = 0;
  for (let i = 0; i <= src.length; i++) {
    const ch = src[i];
    if (ch !== "{" && ch !== "}" && ch !== ";" && i !== src.length) {
      if (ch === '"' || ch === "'") {
        const end = src.indexOf(ch, i + 1);
        i = end < 0 ? src.length - 1 : end;
      }
      continue;
    }
    const seg = src.slice(start, i);
    const top = blocks[blocks.length - 1];
    if (ch === "{") {
      const head = seg.trim();
      if (top === "skip") blocks.push("skip");
      else if (head.startsWith("@")) blocks.push(NESTED_AT.test(head) ? "group" : "skip");
      else blocks.push("rule");
    } else {
      if (top === "rule" && seg.trim()) checkDecl(seg, start);
      if (ch === "}") {
        if (!blocks.length) warn.push({ line: lineBase - 1 + lineAt(src, i), text: "Лишняя закрывающая скобка }" });
        else blocks.pop();
      }
    }
    start = i + 1;
  }
  if (blocks.length) warn.push({ line: lineBase - 1 + lineAt(src, src.length), text: "Не хватает закрывающей скобки } в CSS" });

  function checkDecl(seg, offset) {
    const lead = seg.length - seg.trimStart().length;
    const line = lineBase - 1 + lineAt(src, offset + lead);
    const colon = seg.indexOf(":");
    if (colon < 0) {
      warn.push({ line, text: `«${seg.trim()}» — не свойство: нужно «свойство: значение;»` });
      return;
    }
    const prop = seg.slice(0, colon).trim();
    let value = seg.slice(colon + 1).trim().replace(/\s*!important$/i, "");
    if (!prop || prop.startsWith("--") || /[{}]/.test(prop)) return;
    if (!/^-?[a-zA-Z][a-zA-Z-]*$/.test(prop)) {
      warn.push({ line, text: `«${prop}» — недопустимое имя свойства` });
      return;
    }
    if (prop.startsWith("-webkit-") || prop.startsWith("-moz-") || prop.startsWith("-ms-")) return;
    if (!supports(prop, "inherit")) {
      warn.push({ line, text: `Неизвестное свойство «${prop}» — проверьте написание` });
      return;
    }
    if (!value) {
      warn.push({ line, text: `У свойства «${prop}» нет значения` });
      return;
    }
    if (!/var\(/.test(value) && !supports(prop, value)) {
      const hint = /:/.test(value) ? " — похоже, пропущена «;» перед следующим свойством" : "";
      warn.push({ line, text: `Недопустимое значение «${value}» для свойства «${prop}»${hint}` });
    }
  }
  return warn;
}
