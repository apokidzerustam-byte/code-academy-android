from lib import *

begin()
scenes = [
 S("intro", "Стек и очередь", """
  Структура данных — это способ хранить данные так, чтобы с ними было удобно работать. Сегодня две самые простые и важные
  структуры: стек и очередь. Стек работает как стопка тарелок: положили сверху — берём тоже сверху. Очередь — как очередь в
  магазине: кто пришёл первым, того и обслужили первым. Эти правила кажутся тривиальными, но на них построены история
  браузера, отмена действий в редакторе и планирование задач.""",
  nt("**Стек** — LIFO: последним вошёл, первым вышел. **Очередь** — FIFO: первым вошёл, первым вышел", at="Стек работает")),
 S("stack", "Стек на списке", """
  В Python стек удобно делать на обычном списке. Метод append кладёт элемент на вершину, а метод pop без аргументов снимает
  верхний элемент и возвращает его. Обе операции работают за константное время. Положим три значения и снимем их: порядок
  выхода будет обратным порядку входа. Обратите внимание, что pop у пустого списка вызывает ошибку, поэтому перед снятием
  стоит проверять, что стек не пуст.""",
  clr(), t("stack = []\nstack.append(1)\nstack.append(2)\nstack.append(3)\n", at="Положим три"),
  t("print(stack[-1])\nprint(stack.pop(), stack.pop(), stack.pop())\nprint(len(stack) == 0)\n", at="порядок"), run("Обратите внимание")),
 S("brackets", "Задача: правильные скобки", """
  Классическая задача для стека — проверить, правильно ли расставлены скобки. Идём по строке: открывающую скобку кладём в
  стек, а встретив закрывающую, снимаем верхний элемент и проверяем, что это парная ей открывающая. Если стек пуст или скобки
  не пара, строка неправильная. В конце стек обязан быть пустым, иначе остались незакрытые скобки.""",
  clr(), t('def balanced(s):\n    pairs = {")": "(", "]": "[", "}": "{"}\n    stack = []\n', at="Идём по строке"),
  t("    for ch in s:\n        if ch in \"([{\":\n            stack.append(ch)\n", at="открывающую скобку"),
  t("        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n", at="закрывающую"),
  t("    return not stack\n\nprint(balanced(\"{[()]}\"), balanced(\"([)]\"), balanced(\"((\"))\n", at="В конце"), run("В конце")),
 S("queue", "Очередь на deque", """
  Очередь на обычном списке неудобна: удаление первого элемента сдвигает все остальные и работает медленно. Для очередей в
  стандартной библиотеке есть класс deque из модуля collections. Метод append добавляет в конец, а popleft забирает из начала,
  причём обе операции быстрые. Смоделируем очередь клиентов: пришли трое, первого обслужили.""",
  clr(), t("from collections import deque\n\nqueue = deque()\nqueue.append(\"Аня\")\nqueue.append(\"Борис\")\nqueue.append(\"Вера\")\n", at="Смоделируем"),
  t("print(queue.popleft())\nprint(list(queue), len(queue))\n", at="первого обслужили"), run("первого обслужили")),
 S("potato", "Задача: горячая картошка", """
  Дети стоят по кругу и передают картошку. После каждых k передач тот, у кого она оказалась, выбывает. Игра идёт, пока не
  останется один. Очередь подходит идеально: пока считаем, снимаем человека спереди и ставим его в конец. На k-м
  человеке снимаем и не возвращаем. Последний оставшийся — победитель.""",
  clr(), t("from collections import deque\n\ndef winner(names, k):\n    circle = deque(names)\n    while len(circle) > 1:\n", at="Дети стоят"),
  t("        for _ in range(k - 1):\n            circle.append(circle.popleft())\n        circle.popleft()\n    return circle[0]\n\n", at="снимаем человека"),
  t('print(winner(["Аня", "Борис", "Вера", "Глеб", "Дина"], 3))\n', at="Последний"), run("Последний")),
 S("summary", "Итог", """
  Подведём итог. Стек работает по принципу последним вошёл, первым вышел: список с append и pop. Очередь работает по принципу
  первым вошёл, первым вышел: deque с append и popleft. Стек помогает с вложенностью, скобками, отменой действий, а очередь —
  с порядком обслуживания. Дальше познакомимся с хеш-таблицами, на которых построены словари Python.""",
  nt("Стек: `append` / `pop` · Очередь: `deque.append` / `popleft`", at="Подведём итог")),
]

notes = """
# Стек и очередь

## Стек

```python
stack = []
stack.append(1)
stack.append(2)
print(stack.pop())   # 2
```

## Скобки

```python
def balanced(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack
```

## Очередь

```python
from collections import deque

queue = deque()
queue.append("Аня")
queue.append("Борис")
print(queue.popleft())   # Аня
```

| | Стек | Очередь |
|---|---|---|
| Порядок | LIFO | FIFO |
| Добавить | `append` | `append` |
| Взять | `pop()` | `popleft()` |
"""

a1 = fn_task("a1-balanced", "Правильные скобки", "Напишите `is_balanced(s)`: `True`, если скобки `()`, `[]`, `{}` в строке расставлены правильно (каждая закрывающая имеет парную открывающую, и вложенность не нарушена). Остальные символы игнорируйте.",
  "is_balanced", 'def is_balanced(s):\n    pairs = {")": "(", "]": "[", "}": "{"}\n    stack = []\n    for ch in s:\n        if ch in "([{":\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack\n',
  [["{[()]}"], ["([)]"], ([""], True), (["(("], True), (["))"], True), (["a(b)c[d]"], True), (["(]"], True), (["{[}]"], True)],
  [('def is_balanced(s):\n    return s.count("(") == s.count(")") and s.count("[") == s.count("]") and s.count("{") == s.count("}")\n', "Считаются только количества: порядок и вложенность не проверяются."),
   ('def is_balanced(s):\n    pairs = {")": "(", "]": "[", "}": "{"}\n    stack = []\n    for ch in s:\n        if ch in "([{":\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return True\n', "Не проверено, что стек пуст: незакрытые скобки пропускаются."),
   ('def is_balanced(s):\n    pairs = {")": "(", "]": "[", "}": "{"}\n    stack = []\n    for ch in s:\n        if ch in "([{":\n            stack.append(ch)\n        elif ch in pairs:\n            stack.pop()\n    return not stack\n', "Снятая скобка не сравнивается с парной; на пустом стеке pop падает.")],
  hints("Для вложенности нужна структура «последним вошёл — первым вышел».", "Открывающие скобки кладите в стек.", "Закрывающая должна совпасть с верхней открывающей.", "Если стек пуст при закрывающей — строка неправильная.", "В конце стек должен быть пуст: return not stack."),
  "Стек запоминает порядок открытых скобок; закрывающая обязана соответствовать последней открытой.")

a2 = fn_task("a2-rpn", "Обратная польская запись", "В обратной польской записи оператор стоит после операндов: `[\"3\", \"4\", \"+\"]` = 3 + 4. Напишите `eval_rpn(tokens)` для операций `+`, `-`, `*` над целыми числами и верните результат.\n\nПример: `eval_rpn([\"2\", \"3\", \"4\", \"*\", \"+\"])` → `14`.",
  "eval_rpn", 'def eval_rpn(tokens):\n    stack = []\n    for token in tokens:\n        if token in ("+", "-", "*"):\n            b = stack.pop()\n            a = stack.pop()\n            if token == "+":\n                stack.append(a + b)\n            elif token == "-":\n                stack.append(a - b)\n            else:\n                stack.append(a * b)\n        else:\n            stack.append(int(token))\n    return stack[0]\n',
  [[["2", "3", "4", "*", "+"]], [["3", "4", "+"]], ([["7"]], True), ([["10", "2", "-"]], True), ([["5", "1", "2", "+", "4", "*", "+", "3", "-"]], True), ([["2", "-3", "*"]], True)],
  [('def eval_rpn(tokens):\n    stack = []\n    for token in tokens:\n        if token in ("+", "-", "*"):\n            a = stack.pop()\n            b = stack.pop()\n            if token == "+":\n                stack.append(a + b)\n            elif token == "-":\n                stack.append(a - b)\n            else:\n                stack.append(a * b)\n        else:\n            stack.append(int(token))\n    return stack[0]\n', "Операнды сняты в обратном порядке: вычитание даёт неверный знак."),
   ('def eval_rpn(tokens):\n    stack = []\n    for token in tokens:\n        if token in ("+", "-", "*"):\n            b = stack.pop()\n            a = stack.pop()\n            stack.append(a + b)\n        else:\n            stack.append(int(token))\n    return stack[0]\n', "Любая операция выполняется как сложение.")],
  hints("Числа кладите в стек, операторы применяйте к верхним двум элементам.", "Оператор снимает два числа и возвращает один результат.", "Первым снимается правый операнд b, потом левый a.", "Результат операции снова кладётся в стек.", "В конце единственный элемент стека — ответ."),
  "Стек хранит промежуточные результаты; порядок снятия операндов важен для некоммутативных операций.")

a3 = fn_task("a3-potato", "Горячая картошка", "Напишите `winner(names, k)`: игроки стоят по кругу, картошку передают по кругу, каждый `k`-й по счёту выбывает (счёт продолжается со следующего). Верните имя последнего оставшегося. `k >= 1`.\n\nПример: `winner([\"Аня\", \"Борис\", \"Вера\", \"Глеб\", \"Дина\"], 3)` → `\"Глеб\"`.",
  "winner", "from collections import deque\n\n\ndef winner(names, k):\n    circle = deque(names)\n    while len(circle) > 1:\n        for _ in range(k - 1):\n            circle.append(circle.popleft())\n        circle.popleft()\n    return circle[0]\n",
  [[["Аня", "Борис", "Вера", "Глеб", "Дина"], 3], [["А", "Б", "В"], 1], ([["А"], 5], True), ([["А", "Б"], 2], True), ([["А", "Б", "В", "Г", "Д", "Е"], 2], True), ([["А", "Б", "В", "Г"], 7], True)],
  [("from collections import deque\n\n\ndef winner(names, k):\n    circle = deque(names)\n    while len(circle) > 1:\n        for _ in range(k):\n            circle.append(circle.popleft())\n        circle.popleft()\n    return circle[0]\n", "Сдвиг на k вместо k-1: выбывает не тот игрок."),
   ("def winner(names, k):\n    items = list(names)\n    return items[-1]\n", "Возвращается последний элемент без моделирования игры."),
   ("from collections import deque\n\n\ndef winner(names, k):\n    circle = deque(names)\n    while len(circle) > 1:\n        for _ in range(k - 1):\n            circle.append(circle.popleft())\n        circle.pop()\n    return circle[0]\n", "Выбывает игрок с конца очереди, а не спереди.")],
  hints("Круг удобно моделировать очередью: взять спереди и поставить в конец.", "Пропустите k-1 игроков: каждого переставьте в конец.", "k-го игрока уберите из очереди.", "Повторяйте, пока не останется один игрок.", "circle.append(circle.popleft()) — передача картошки; circle.popleft() — выбывание."),
  "deque.popleft и append моделируют круг: передача — это перенос первого в конец.")

a4 = fn_task("a4-history", "История браузера", "Страницы браузера хранятся в стеке. Команды: `\"visit X\"` — открыть страницу X, `\"back\"` — вернуться на предыдущую (если предыдущей нет, ничего не меняется). Начальная страница — `\"home\"`. Напишите `browse(commands)`, верните название **текущей** страницы после всех команд.\n\nПример: `browse([\"visit a\", \"visit b\", \"back\"])` → `\"a\"`.",
  "browse", 'def browse(commands):\n    stack = ["home"]\n    for command in commands:\n        if command == "back":\n            if len(stack) > 1:\n                stack.pop()\n        else:\n            stack.append(command.split(" ", 1)[1])\n    return stack[-1]\n',
  [[["visit a", "visit b", "back"]], [[]], ([["back", "back"]], True), ([["visit x", "back", "back", "visit y"]], True), ([["visit a", "visit b", "visit c", "back", "back"]], True)],
  [('def browse(commands):\n    stack = ["home"]\n    for command in commands:\n        if command == "back":\n            stack.pop()\n        else:\n            stack.append(command.split(" ", 1)[1])\n    return stack[-1]\n', "Возврат с домашней страницы приводит к ошибке: стек опустошается."),
   ('def browse(commands):\n    stack = ["home"]\n    for command in commands:\n        if command == "back":\n            if len(stack) > 1:\n                stack.pop(0)\n        else:\n            stack.append(command.split(" ", 1)[1])\n    return stack[-1]\n', "Снимается страница с начала, а не с вершины."),
   ('def browse(commands):\n    page = "home"\n    for command in commands:\n        if command != "back":\n            page = command.split(" ", 1)[1]\n    return page\n', "Нет истории: команда back ничего не делает.")],
  hints("История — это стек страниц, текущая страница на вершине.", "Начните со стека [\"home\"].", "visit X — положить X на вершину.", "back — снять вершину, но не опустошайте стек полностью.", "Ответ — stack[-1]."),
  "Стек естественно моделирует историю: вернуться — значит снять верхнюю страницу.")

a5 = predict_task("a5-deque", "Стек и очередь вместе", "from collections import deque\n\nstack = []\nqueue = deque()\nfor x in [1, 2, 3]:\n    stack.append(x)\n    queue.append(x)\nprint(stack.pop(), queue.popleft())\nprint(stack, list(queue))\n",
  [("1 3\n[1, 2] [2, 3]\n", "pop снимает с конца (3), popleft — с начала (1): наоборот."),
   ("3 1\n[2, 3] [1, 2]\n", "После pop из стека остаются первые элементы, а после popleft — последние.")],
  hints("Оба контейнера получили 1, 2, 3 в одном порядке.", "stack.pop() снимает последний положенный элемент.", "queue.popleft() забирает первый положенный.", "В стеке остаётся [1, 2], в очереди — [2, 3].", "Первая строка: 3 1."),
  "Стек отдаёт последний, очередь — первый; остатки в контейнерах различаются.")

mistakes = [
 {"mistake": "Берут из пустого стека", "fix": "Проверьте if stack: перед pop().", "errorType": "IndexError"},
 {"mistake": "Используют list.pop(0) как очередь", "fix": "Для очередей берите deque.popleft(): pop(0) работает за O(n)."},
 {"mistake": "Путают порядок операндов при снятии со стека", "fix": "Первым снимается правый операнд."},
 {"mistake": "Забывают проверить пустоту стека в конце", "fix": "Для скобок: return not stack."}]

finish("alg-06-stack-queue", "Стек и очередь", "Использовать стек и очередь, решать задачи на скобки и моделирование очередей.",
  {"algo.stack": "Стек", "algo.queue": "Очередь (deque)"},
  ["alg-05-fast-sorts", "alg-04-recursion"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="algorithms")
