// Защита от бесконечных циклов в JavaScript ученика.
// В тело каждого цикла вставляется проверка времени; если один запуск цикла идёт дольше
// лимита, выбрасывается понятная ошибка. Вставки не содержат переводов строк —
// номера строк в сообщениях об ошибках совпадают с кодом ученика.
import { parse } from "acorn";
import { ancestor } from "acorn-walk";

const LOOPS = new Set(["ForStatement", "ForInStatement", "ForOfStatement", "WhileStatement", "DoWhileStatement"]);

/** Синтаксическая ошибка с номером строки (1..) и столбца (1..) относительно переданного кода. */
export class JsSyntaxError extends Error {
  constructor(message, line, column) {
    super(message);
    this.name = "SyntaxError";
    this.line = line;
    this.column = column;
  }
}

const RU = [
  [/^Unexpected token/, "Неожиданный символ"],
  [/^Unexpected character '(.*)'/, "Недопустимый символ «$1»"],
  [/^Unterminated string constant/, "Строка не закрыта кавычкой"],
  [/^Unterminated template/, "Шаблонная строка не закрыта обратной кавычкой `"],
  [/^Unterminated comment/, "Комментарий /* не закрыт */"],
  [/^Unterminated regular expression/, "Регулярное выражение не закрыто"],
  [/^Identifier '(.*)' has already been declared/, "Имя «$1» уже объявлено"],
  [/^'return' outside of function/, "return вне функции"],
  [/^Unexpected keyword '(.*)'/, "Неожиданное ключевое слово «$1»"],
  [/^The keyword '(.*)' is reserved/, "Слово «$1» зарезервировано"],
  [/^Assigning to rvalue/, "Присваивать можно только переменной или свойству"],
  [/^Invalid left-hand side in assignment/, "Слева от = должна быть переменная или свойство"],
];

function russian(msg) {
  const clean = msg.replace(/ \(\d+:\d+\)$/, "");
  for (const [re, ru] of RU) if (re.test(clean)) return clean.replace(re, ru);
  return clean;
}

export function parseJs(code, module = false) {
  try {
    return parse(code, {
      ecmaVersion: "latest",
      sourceType: module ? "module" : "script",
      allowHashBang: true,
      locations: true,
    });
  } catch (e) {
    if (e && e.loc) throw new JsSyntaxError(russian(e.message), e.loc.line, e.loc.column + 1);
    throw e;
  }
}

/**
 * Возвращает код с защитой циклов. guard — имя глобального объекта с методами
 * s(id) (начало цикла) и c(id, line) (очередная итерация).
 */
export function protectLoops(code, { module = false, guard = "__caL", idBase = 0 } = {}) {
  const ast = parseJs(code, module);
  const ins = []; // [позиция, текст, порядок]
  let id = idBase;
  ancestor(ast, {
    // acorn-walk вызывает обработчик по типу узла; для циклов — общий код ниже.
    ForStatement: visit, ForInStatement: visit, ForOfStatement: visit,
    WhileStatement: visit, DoWhileStatement: visit,
  });

  function visit(node, _state, ancestors) {
    const n = ++id;
    const line = node.loc.start.line;
    // Цикл оборачивается в блок вместе со всеми метками (иначе continue метка сломается).
    let outer = node;
    for (let i = ancestors.length - 2; i >= 0 && ancestors[i].type === "LabeledStatement"; i--) outer = ancestors[i];
    ins.push([outer.start, `{${guard}.s(${n});`, 0]);
    ins.push([outer.end, `}`, 2]);
    const body = node.body;
    const check = `${guard}.c(${n},${line});`;
    if (body.type === "BlockStatement") {
      ins.push([body.start + 1, check, 1]);
    } else {
      ins.push([body.start, `{${check}`, 1]);
      ins.push([body.end, `}`, 1]);
    }
  }

  // Вставки с конца, чтобы позиции не сдвигались. При равной позиции: закрывающие скобки
  // внешних конструкций идут после внутренних, открывающие — раньше.
  ins.sort((a, b) => b[0] - a[0] || a[2] - b[2]);
  let out = code;
  for (const [pos, text] of ins) out = out.slice(0, pos) + text + out.slice(pos);
  return { code: out, count: id - idBase };
}
