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
const dark = window.matchMedia("(prefers-color-scheme: dark)");

function notify(doc) {
  if (window.AndroidBridge) window.AndroidBridge.onChange(doc.toString());
}

const view = new EditorView({
  parent: document.getElementById("editor"),
  state: EditorState.create({
    doc: "print('Привет, мир')\n",
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
      EditorView.lineWrapping,
      EditorView.updateListener.of((u) => { if (u.docChanged) notify(u.state.doc); }),
    ],
  }),
});

dark.addEventListener("change", (e) => view.dispatch({ effects: theme.reconfigure(e.matches ? oneDark : []) }));

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
    view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text } });
  },
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
notify(view.state.doc);
