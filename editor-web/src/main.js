import { EditorState, Compartment } from "@codemirror/state";
import {
  EditorView, keymap, lineNumbers, highlightActiveLine, highlightActiveLineGutter,
  drawSelection, highlightSpecialChars,
} from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab, undo, redo } from "@codemirror/commands";
import {
  indentOnInput, bracketMatching, syntaxHighlighting, defaultHighlightStyle, indentUnit,
} from "@codemirror/language";
import { closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap } from "@codemirror/autocomplete";
import { searchKeymap, highlightSelectionMatches } from "@codemirror/search";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { html } from "@codemirror/lang-html";
import { css } from "@codemirror/lang-css";
import { sql } from "@codemirror/lang-sql";
import { oneDark } from "@codemirror/theme-one-dark";

const LANGS = { python, javascript, html, css, sql };
const language = new Compartment();
const theme = new Compartment();
const fontSize = new Compartment();
const readOnly = new Compartment();
const dark = window.matchMedia("(prefers-color-scheme: dark)");
let explicitTheme = null; // приложение задаёт тему явно; иначе — по системе

// Канал к приложению: WebMessageListener (caEditorHost) в IDE, JavascriptInterface — в прототипе.
function toHost(obj) {
  if (window.caEditorHost) window.caEditorHost.postMessage(JSON.stringify(obj));
}
let changeTimer = null;
// Небольшой текст отправляется приложению сразу после каждого изменения — тогда «Запустить»/«Проверить»
// всегда видят последнюю правку. Только очень большие файлы отправляются с короткой задержкой.
const IMMEDIATE_LIMIT = 32 * 1024;
function notify(doc, external) {
  const text = doc.toString();
  if (window.AndroidBridge) window.AndroidBridge.onChange(text);
  if (window.caEditorHost && !external) {
    clearTimeout(changeTimer);
    if (text.length <= IMMEDIATE_LIMIT) toHost({ type: "change", text });
    else changeTimer = setTimeout(() => toHost({ type: "change", text }), 120);
  }
}
// Изменения, пришедшие из приложения (setText), обратно в приложение (caEditorHost) не отправляются.
let applyingExternal = false;
function fontTheme(px) {
  return EditorView.theme({ "&": { fontSize: px + "px" }, ".cm-gutters": { fontSize: px + "px" } });
}

const view = new EditorView({
  parent: document.getElementById("editor"),
  state: EditorState.create({
    doc: "", // настоящий текст приходит из приложения через setText
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightSpecialChars(),
      history(),
      drawSelection(),
      indentUnit.of("    "),
      indentOnInput(),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      keymap.of([...closeBracketsKeymap, ...defaultKeymap, ...searchKeymap, ...historyKeymap, ...completionKeymap, indentWithTab]),
      language.of(python()),
      theme.of(dark.matches ? oneDark : []),
      fontSize.of(fontTheme(15)),
      readOnly.of(EditorState.readOnly.of(false)),
      EditorView.lineWrapping,
      EditorView.updateListener.of((u) => { if (u.docChanged) notify(u.state.doc, applyingExternal); }),
    ],
  }),
});

dark.addEventListener("change", (e) => {
  if (explicitTheme === null) view.dispatch({ effects: theme.reconfigure(e.matches ? oneDark : []) });
});

// API для Kotlin (EditorActivity).
window.caEditor = {
  insert(text) {
    const sel = view.state.selection.main;
    const insertText = text === "\t" ? "    " : text;
    view.dispatch({
      changes: { from: sel.from, to: sel.to, insert: insertText },
      selection: { anchor: sel.from + insertText.length },
      userEvent: "input.type",
    });
    view.focus();
  },
  setText(text) {
    if (text === view.state.doc.toString()) return;
    // Новый текст целиком (загрузка файла, сброс к заготовке): курсор — в конец.
    applyingExternal = true;
    try {
      view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text }, selection: { anchor: text.length } });
    } finally {
      applyingExternal = false;
    }
  },
  setTheme(isDark) {
    explicitTheme = !!isDark;
    view.dispatch({ effects: theme.reconfigure(isDark ? oneDark : []) });
    document.documentElement.style.background = isDark ? "#282c34" : "#ffffff";
    document.body.style.background = isDark ? "#282c34" : "#ffffff";
  },
  setFontSize(px) { view.dispatch({ effects: fontSize.reconfigure(fontTheme(px)) }); },
  setReadOnly(ro) { view.dispatch({ effects: readOnly.reconfigure(EditorState.readOnly.of(!!ro)) }); },
  focus() { view.focus(); },
  flush() { clearTimeout(changeTimer); toHost({ type: "change", text: view.state.doc.toString() }); },
  getText() {
    return view.state.doc.toString();
  },
  setLanguage(name) {
    const lang = LANGS[name];
    if (lang) view.dispatch({ effects: language.reconfigure(lang()) });
  },
  undo() { undo(view); },
  redo() { redo(view); },
  ready: true,
};
toHost({ type: "ready" });
