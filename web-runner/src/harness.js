// Код внутри iframe ученика. Функция сериализуется через toString() и вставляется в
// страницу первым скриптом, поэтому она не должна обращаться к внешним переменным модуля.
/* eslint-disable no-var */
export function caHarness(cfg) {
  "use strict";
  var post = function (m) {
    m.__ca = cfg.nonce;
    try { parent.postMessage(m, "*"); } catch (e) { /* родитель недоступен */ }
  };
  var used = 0;
  var cut = false;
  function emit(stream, text) {
    if (cut) return;
    if (used + text.length > cfg.maxOutput) {
      text = text.slice(0, Math.max(0, cfg.maxOutput - used));
      cut = true;
    }
    used += text.length;
    post({ t: "out", stream: stream, text: text, cut: cut });
  }

  // ---- Форматирование значений как в консоли --------------------------------
  function fmt(v, depth, seen, top) {
    var t = typeof v;
    if (v === null) return "null";
    if (t === "undefined") return "undefined";
    if (t === "string") return top ? v : JSON.stringify(v);
    if (t === "number") return Object.is(v, -0) ? "-0" : String(v);
    if (t === "boolean") return String(v);
    if (t === "bigint") return v + "n";
    if (t === "symbol") return v.toString();
    if (t === "function") return "[Function: " + (v.name || "(анонимная)") + "]";
    if (seen.indexOf(v) >= 0) return "[Circular]";
    if (v instanceof Error) return (v.name || "Error") + ": " + v.message;
    if (v instanceof Date) return isNaN(v) ? "Invalid Date" : v.toISOString();
    if (v instanceof RegExp) return String(v);
    if (typeof Element !== "undefined" && v instanceof Element) {
      var s = "<" + v.tagName.toLowerCase();
      for (var i = 0; i < v.attributes.length && i < 4; i++) s += " " + v.attributes[i].name + '="' + v.attributes[i].value + '"';
      return s + ">";
    }
    if (typeof Node !== "undefined" && v instanceof Node) return "#" + (v.nodeName || "node").replace(/^#/, "");
    if (depth > 3) return Array.isArray(v) ? "[Array]" : "[Object]";
    seen = seen.concat([v]);
    var parts = [];
    var more = 0;
    if (Array.isArray(v)) {
      for (var j = 0; j < v.length; j++) {
        if (j >= 100) { more = v.length - 100; break; }
        parts.push(j in v ? fmt(v[j], depth + 1, seen, false) : "<пусто>");
      }
      return "[" + parts.join(", ") + (more ? ", … ещё " + more : "") + "]";
    }
    if (v instanceof Map) {
      v.forEach(function (val, key) { if (parts.length < 100) parts.push(fmt(key, depth + 1, seen, false) + " => " + fmt(val, depth + 1, seen, false)); });
      return "Map(" + v.size + ") {" + parts.join(", ") + "}";
    }
    if (v instanceof Set) {
      v.forEach(function (val) { if (parts.length < 100) parts.push(fmt(val, depth + 1, seen, false)); });
      return "Set(" + v.size + ") {" + parts.join(", ") + "}";
    }
    if (typeof Promise !== "undefined" && v instanceof Promise) return "Promise {…}";
    var keys = Object.keys(v);
    for (var k = 0; k < keys.length; k++) {
      if (k >= 100) { more = keys.length - 100; break; }
      var key = /^[A-Za-z_$][\w$]*$/.test(keys[k]) ? keys[k] : JSON.stringify(keys[k]);
      parts.push(key + ": " + fmt(v[keys[k]], depth + 1, seen, false));
    }
    var name = v.constructor && v.constructor !== Object && v.constructor.name ? v.constructor.name + " " : "";
    if (!parts.length) return name + "{}";
    return name + "{" + parts.join(", ") + (more ? ", … ещё " + more : "") + "}";
  }
  function line(args) {
    var out = [];
    for (var i = 0; i < args.length; i++) out.push(fmt(args[i], 0, [], true));
    return out.join(" ") + "\n";
  }

  function errorText(e) {
    if (e && typeof e === "object" && "message" in e) {
      return (e.name || "Error") + ": " + e.message;
    }
    return "Uncaught " + fmt(e, 0, [], false);
  }
  function lineOf(e, fallback) {
    if (e && e.__caLine) return e.__caLine;
    var m = e && typeof e.stack === "string" && e.stack.match(/:(\d+):\d+\)?\s*$/m);
    return m ? +m[1] : fallback || 0;
  }

  // ---- Консоль -----------------------------------------------------------------
  var c = window.console;
  var out = function () { emit("stdout", line(arguments)); };
  var err = function () { emit("stderr", line(arguments)); };
  c.log = out; c.info = out; c.debug = out;
  c.warn = err; c.error = err;
  c.table = function (data) { emit("stdout", fmt(data, 0, [], false) + "\n"); };

  // alert/prompt/confirm: модальные окна в песочнице запрещены — эмулируем.
  var input = (cfg.stdin || "").split("\n");
  if (input.length && input[input.length - 1] === "") input.pop();
  window.alert = function (m) { emit("stdout", "[alert] " + (m === undefined ? "" : String(m)) + "\n"); };
  window.confirm = function (m) { emit("stdout", "[confirm] " + (m === undefined ? "" : String(m)) + " → OK\n"); return true; };
  window.prompt = function () { return input.length ? input.shift() : null; };

  var reported = 0;
  function reportError(e, lineNo) {
    if (reported++ > 50) return;
    post({ t: "error", text: errorText(e), line: lineOf(e, lineNo), name: (e && e.name) || "Error" });
  }
  window.addEventListener("error", function (ev) {
    ev.preventDefault();
    reportError(ev.error || { name: "Error", message: ev.message }, ev.lineno);
  });
  window.addEventListener("unhandledrejection", function (ev) {
    ev.preventDefault();
    reportError(ev.reason, 0);
  });

  // ---- Защита циклов -----------------------------------------------------------
  var starts = {};
  var counts = {};
  // После первой остановки цикла любая следующая проверка цикла снова бросает ту же ошибку:
  // её нельзя «проглотить» try/catch во внешнем цикле.
  var dead = null;
  window.__caL = {
    s: function (id) { if (dead) throw dead; starts[id] = Date.now(); counts[id] = 0; },
    c: function (id, ln) {
      if (dead) throw dead;
      if ((++counts[id] & 63) === 0 && Date.now() - starts[id] > cfg.loopMs) {
        starts[id] = Date.now();
        var e = new Error("цикл в строке " + ln + " работает дольше " + cfg.loopMs / 1000 +
          " с — похоже, он бесконечный. Проверьте условие выхода из цикла.");
        e.name = "InfiniteLoopError";
        e.__caLine = ln;
        dead = e;
        throw e;
      }
    },
  };

  // ---- Проверки (код тестов пишет автор курса) --------------------------------
  function plain(v, depth) {
    // Значение для сравнения в JSON: функции, DOM и т. п. — их текстовое представление.
    if (v === undefined) return { __undefined: true };
    if (v === null || typeof v === "string" || typeof v === "boolean") return v;
    if (typeof v === "number") return isFinite(v) ? v : { __number: String(v) };
    if (Array.isArray(v)) return depth > 20 ? fmt(v, 0, [], false) : v.map(function (x) { return plain(x, depth + 1); });
    if (typeof v === "object" && (v.constructor === Object || !v.constructor) && depth <= 20) {
      var o = {};
      Object.keys(v).forEach(function (k) { o[k] = plain(v[k], depth + 1); });
      return o;
    }
    return fmt(v, 0, [], false);
  }
  window.__caExport = function (getters) { window.__caGet = getters; };
  window.addEventListener("message", function (ev) {
    var m = ev.data;
    if (!m || m.__ca !== cfg.nonce || ev.source !== parent) return;
    if (m.t === "eval") {
      var reply = function (ok, value, e) {
        post({ t: "value", id: m.id, ok: ok, value: ok ? plain(value, 0) : null, error: e ? errorText(e) : null, errorName: e ? e.name || "Error" : null });
      };
      try {
        var v;
        if (m.kind === "function") {
          var getter = window.__caGet && window.__caGet[m.name];
          var fn = getter ? getter() : undefined;
          if (typeof fn !== "function") {
            post({ t: "value", id: m.id, ok: false, missing: true, error: "Функция " + m.name + "() не найдена. Проверьте имя и что она объявлена." });
            return;
          }
          v = fn.apply(null, m.args || []);
        } else {
          var test = window.__caTests && window.__caTests[m.index];
          if (!test) throw new Error("нет теста " + m.index);
          v = test();
        }
        if (v && typeof v.then === "function") {
          var done = false;
          setTimeout(function () { if (!done) { done = true; reply(false, null, { name: "Timeout", message: "Promise не завершился за " + cfg.asyncMs / 1000 + " с" }); } }, cfg.asyncMs);
          v.then(function (x) { if (!done) { done = true; reply(true, x); } },
            function (e) { if (!done) { done = true; reply(false, null, e); } });
        } else reply(true, v);
      } catch (e) {
        reply(false, null, e);
      }
    }
  });
  window.addEventListener("load", function () {
    setTimeout(function () { post({ t: "loaded" }); }, cfg.settleMs);
  });
}
