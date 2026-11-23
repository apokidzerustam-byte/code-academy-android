from lib import *

RUN = 'import unittest\n\n\ndef run(case):\n    result = unittest.TestResult()\n    unittest.defaultTestLoader.loadTestsFromTestCase(case).run(result)\n    print("запущено", result.testsRun, "· провалено", len(result.failures), "· ошибок", len(result.errors))\n\n\n'

begin()
scenes = [
 S("intro", "Модуль unittest", """
  Обычный assert останавливает программу на первой же неудаче, и мы не узнаем, сколько ещё проверок упало. Для серьёзной
  работы в стандартной библиотеке Python есть модуль unittest. Он запускает каждый тест отдельно, собирает все неудачи и
  сообщает итог: сколько проверок прошло и какие упали. На своём компьютере его запускают командой python
  минус m unittest. Здесь мы запустим тесты из кода и напечатаем итог сами, чтобы увидеть, как всё устроено.""",
  nt("`unittest` — тесты в стандартной библиотеке: каждый тест — отдельный метод класса", at="Для серьёзной")),
 S("case", "Класс с тестами", """
  Тесты группируются в класс, наследующий от TestCase. Каждый метод, имя которого начинается с test, — отдельный тест.
  Внутри используются методы проверки: assertEqual сравнивает два значения. Напишем функцию сложения и два теста. Мы
  загрузим класс, запустим тесты и напечатаем итог. Оба теста проходят.""",
  clr(), t(RUN + "def add(a, b):\n    return a + b\n\n\n", at="Тесты группируются"),
  t("class TestAdd(unittest.TestCase):\n    def test_positive(self):\n        self.assertEqual(add(2, 3), 5)\n\n    def test_negative(self):\n        self.assertEqual(add(-1, -1), -2)\n\n\nrun(TestAdd)\n", at="Напишем функцию"), run("Оба теста")),
 S("methods", "Методы проверки", """
  Кроме assertEqual есть и другие методы. assertTrue и assertFalse проверяют истинность. assertIn — что элемент входит в
  коллекцию. assertIsNone — что значение равно None. А для дробных чисел служит assertAlmostEqual: он сравнивает с
  небольшим допуском, потому что ноль целых одна десятая плюс две десятых не равно ровно трём десятым. Вот тест, в
  котором применены все эти методы.""",
  clr(), t(RUN, at="Кроме"),
  t("class TestMethods(unittest.TestCase):\n    def test_all(self):\n        self.assertTrue(5 > 3)\n        self.assertFalse(\"a\" in \"bcd\")\n        self.assertIn(2, [1, 2, 3])\n        self.assertIsNone({}.get(\"нет\"))\n        self.assertAlmostEqual(0.1 + 0.2, 0.3)\n\n\nrun(TestMethods)\n", at="Вот тест"), run("Вот тест")),
 S("fail", "Провал и ошибка", """
  Различают два вида неудач. Провал, по-английски failure, — это когда проверка не сошлась: ожидали пять, получили четыре. Ошибка,
  error, — когда в самом тесте или в коде произошло исключение, например деление на ноль. Для разработчика разница важна: провал
  говорит, что результат неверный, а ошибка — что код вообще упал. Итог показывает оба счётчика отдельно.""",
  clr(), t(RUN + "class TestMix(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(2 + 2, 4)\n\n    def test_fail(self):\n        self.assertEqual(2 + 2, 5)\n\n    def test_error(self):\n        self.assertEqual(1 / 0, 1)\n\n\nrun(TestMix)\n", at="Различают"), run("Итог показывает")),
 S("raises", "Проверяем исключения", """
  Иногда правильное поведение — это именно ошибка. Функция проверки возраста должна возбуждать ValueError для отрицательных
  значений. Проверить это помогает контекстный менеджер assertRaises: если внутри блока исключение произошло, тест проходит, а
  если нет — падает. Так мы проверяем и нормальную работу, и реакцию на неверные данные.""",
  clr(), t(RUN + "def check_age(age):\n    if age < 0:\n        raise ValueError(\"возраст отрицательный\")\n    return age\n\n\n", at="Функция проверки"),
  t("class TestAge(unittest.TestCase):\n    def test_valid(self):\n        self.assertEqual(check_age(20), 20)\n\n    def test_negative(self):\n        with self.assertRaises(ValueError):\n            check_age(-1)\n\n\nrun(TestAge)\n", at="Проверить это"), run("Так мы")),
 S("setup", "Подготовка: setUp", """
  Часто каждому тесту нужен свежий объект. Метод setUp запускается перед каждым тестом и готовит исходное состояние. Возьмём
  простую корзину покупок. Перед каждым тестом создаётся пустая корзина, поэтому тесты не влияют друг на друга. Это важное
  правило: тесты должны быть независимыми и проходить в любом порядке.""",
  clr(), t(RUN + "class Cart:\n    def __init__(self):\n        self.items = []\n\n    def add(self, name):\n        self.items.append(name)\n\n\n", at="Возьмём"),
  t("class TestCart(unittest.TestCase):\n    def setUp(self):\n        self.cart = Cart()\n\n    def test_empty(self):\n        self.assertEqual(len(self.cart.items), 0)\n\n    def test_add(self):\n        self.cart.add(\"хлеб\")\n        self.assertEqual(self.cart.items, [\"хлеб\"])\n\n\nrun(TestCart)\n", at="Перед каждым"), run("Это важное")),
 S("summary", "Итог", """
  Подведём итог. В unittest тесты — методы класса, имена которых начинаются с test. Для проверок есть набор методов assert,
  а для ошибок — контекстный менеджер assertRaises. Метод setUp готовит свежее состояние перед каждым тестом. Результат
  различает провалы и ошибки. На практике вы будете запускать тесты одной командой и читать итог. А сейчас — задания: от
  чтения результатов до тестов, которые ловят спрятанные ошибки.""",
  nt("`class T(unittest.TestCase)` · `test_...` · `assertEqual/True/In/Raises` · `setUp`", at="Подведём итог")),
]

notes = """
# unittest

```python
import unittest

def add(a, b):
    return a + b

class TestAdd(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative(self):
        self.assertEqual(add(-1, -1), -2)
```

На компьютере: `python -m unittest`.

## Методы проверки

- `assertEqual(a, b)`, `assertTrue(x)`, `assertFalse(x)`
- `assertIn(x, коллекция)`, `assertIsNone(x)`
- `assertAlmostEqual(a, b)` — для дробей
- `with self.assertRaises(ValueError): ...` — ожидаем исключение

## Провал и ошибка

Провал (failure) — проверка не сошлась. Ошибка (error) — исключение в коде или в тесте.

## setUp

Метод `setUp` выполняется перед каждым тестом и создаёт свежее состояние.
"""

HARNESS_PRE = '''import unittest


def good(s):
    t = "".join(c.lower() for c in s if c.isalnum())
    return t == t[::-1]


def bug1(s):
    t = "".join(c for c in s if c.isalnum())
    return t == t[::-1]


def bug2(s):
    t = s.lower()
    return t == t[::-1]


def bug3(s):
    t = "".join(c.lower() for c in s if c.isalnum())
    return bool(t) and t == t[::-1]


impl = {"good": good, "bug1": bug1, "bug2": bug2, "bug3": bug3}[input().strip()]


class Tests(unittest.TestCase):
'''
HARNESS_POST = '''

result = unittest.TestResult()
unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
print("PASS" if result.wasSuccessful() else "FAIL")
'''
def pal(body): return HARNESS_PRE + body + HARNESS_POST
OK_BODY = '''    def test_simple(self):
        self.assertTrue(impl("level"))
        self.assertFalse(impl("hello"))

    def test_case(self):
        self.assertTrue(impl("Level"))

    def test_punctuation(self):
        self.assertTrue(impl("А роза упала на лапу Азора"))
        self.assertTrue(impl("Madam, I'm Adam"))

    def test_empty(self):
        self.assertTrue(impl(""))
'''
CASES = [("good\n", False), ("bug1\n", False), ("bug2\n", True), ("bug3\n", True)]

a1 = predict_task("a1-result", "Итог прогона",
  'import unittest\n\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(len("abc"), 3)\n\n    def test_b(self):\n        self.assertEqual("a" * 2, "aaa")\n\n    def test_c(self):\n        self.assertEqual(10 // 0, 0)\n\n    def test_d(self):\n        self.assertTrue([])\n\n\nresult = unittest.TestResult()\nunittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)\nprint(result.testsRun, len(result.failures), len(result.errors))\nprint(result.wasSuccessful())\n',
  [("4 3 0\nFalse", "Деление на ноль — это ошибка (error), а не провал."), ("4 2 1\nTrue", "Раз есть неудачи, итог не успешен."), ("3 2 1\nFalse", "Тестов четыре.")],
  hints("Прогон выполнит четыре теста: test_a, test_b, test_c, test_d.", "test_a проходит.", "test_b не сходится: провал. test_d тоже: пустой список ложен.", "test_c падает с ZeroDivisionError — это ошибка, а не провал.", "Печатается: запущено, провалов, ошибок; затем успешность."),
  "Failure — не сошлась проверка (test_b, test_d); error — исключение внутри теста (test_c). Успех — только если нет ни того, ни другого.")

a2 = stdout_task("a2-palindrome-tests", "Тесты на палиндром",
  "Функция `is_palindrome(s)` определяет, читается ли строка одинаково слева направо и справа налево **без учёта регистра, пробелов и знаков препинания**. В программе спрятаны версии `good`, `bug1`, `bug2`, `bug3`. Допишите методы в класс `Tests` (используйте `impl`) так, чтобы для `good` выводилось `PASS`, а для каждой неверной версии — `FAIL`.",
  pal(OK_BODY), CASES,
  [(pal("    def test_simple(self):\n        self.assertTrue(impl(\"level\"))\n        self.assertFalse(impl(\"hello\"))\n"), "Не проверены регистр, знаки и пустая строка."),
   (pal("    def test_a(self):\n        self.assertTrue(impl(\"level\"))\n        self.assertFalse(impl(\"hello\"))\n        self.assertTrue(impl(\"Level\"))\n        self.assertTrue(impl(\"Madam, I'm Adam\"))\n"), "Нет проверки пустой строки: bug3 не пойман."),
   (pal("    def test_a(self):\n        self.assertTrue(impl(\"level\"))\n        self.assertTrue(impl(\"Level\"))\n        self.assertTrue(impl(\"\"))\n        self.assertFalse(impl(\"hello\"))\n"), "Нет строк с пробелами и знаками: bug2 не пойман."),
   (pal("    def test_a(self):\n        self.assertFalse(impl(\"level\"))\n"), "Тест неверен: на правильной версии падает.")],
  hints("Сначала запустите программу со входом good: должно быть PASS.", "Каждая неверная версия ломается на своём виде входа.", "Проверьте строку с заглавными буквами, строку с пробелами и знаками, и пустую строку.", "Нужен и один отрицательный пример: строка, которая не палиндром.", "Один метод test_… может содержать несколько проверок, но удобнее разделять."),
  "Хорошие тесты покрывают разные классы входов: обычный, с другим регистром, с пробелами и знаками, пустой. Каждый класс «убивает» свой баг.",
  starter=pal("    def test_todo(self):\n        pass\n"), input_text="Название версии: good, bug1, bug2 или bug3.", expected_text="PASS для верной версии и FAIL для каждой неверной.")

a3 = fn_task("a3-raises", "Функция, которая бросает исключение",
  "Тест ожидает: `withdraw(balance, amount)` возвращает новый баланс; если `amount` больше `balance` или `amount <= 0`, возбуждает `ValueError`.\n\n```python\nwith self.assertRaises(ValueError):\n    withdraw(100, 500)\n```",
  "withdraw", "def withdraw(balance, amount):\n    if amount <= 0 or amount > balance:\n        raise ValueError(\"неверная сумма\")\n    return balance - amount\n",
  [[100, 30], {"args": [100, 500], "expected_error": "ValueError"}, ([100, 100], True), {"args": [100, 0], "expected_error": "ValueError", "hidden": True}, {"args": [50, -5], "expected_error": "ValueError", "hidden": True}, ([10, 1], True)],
  [("def withdraw(balance, amount):\n    if amount > balance:\n        raise ValueError(\"неверная сумма\")\n    return balance - amount\n", "Нулевая и отрицательная суммы принимаются."),
   ("def withdraw(balance, amount):\n    if amount <= 0 or amount >= balance:\n        raise ValueError(\"неверная сумма\")\n    return balance - amount\n", "Снять ровно весь баланс нельзя — ошибочная граница.")],
  hints("Есть два недопустимых случая: сумма не положительна и сумма больше баланса.", "Недопустимое — raise ValueError.", "Допустимое — вернуть остаток.", "Условия можно объединить через or.", "Снять весь баланс (amount == balance) — допустимо."),
  "Исключение — часть контракта функции. Граница (ровно весь баланс) — типичное место для ошибок, поэтому её нужно проверить.")

a4 = stdout_task("a4-setup", "Независимые тесты",
  "Класс `Counter` и его тесты уже написаны, но один тест падает, потому что **тесты влияют друг на друга**: общий объект создан один раз на весь файл. Исправьте программу так, чтобы каждый тест получал свежий `Counter` (через `setUp`), и она напечатала `0 провалов`.",
  'import unittest\n\n\nclass Counter:\n    def __init__(self):\n        self.value = 0\n\n    def hit(self):\n        self.value += 1\n\n\nclass T(unittest.TestCase):\n    def setUp(self):\n        self.counter = Counter()\n\n    def test_start(self):\n        self.assertEqual(self.counter.value, 0)\n\n    def test_hit(self):\n        self.counter.hit()\n        self.assertEqual(self.counter.value, 1)\n\n\nresult = unittest.TestResult()\nunittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)\nprint(len(result.failures), "провалов")\n',
  [""],
  [('import unittest\n\n\nclass Counter:\n    def __init__(self):\n        self.value = 0\n\n    def hit(self):\n        self.value += 1\n\n\nshared = Counter()\n\n\nclass T(unittest.TestCase):\n    def test_hit(self):\n        shared.hit()\n        self.assertEqual(shared.value, 1)\n\n    def test_start(self):\n        self.assertEqual(shared.value, 0)\n\n\nresult = unittest.TestResult()\nunittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)\nprint(len(result.failures), "провалов")\n', "Общий объект сохраняет состояние между тестами.")],
  hints("Тесты запускаются в алфавитном порядке: test_hit раньше test_start.", "Общий объект после test_hit уже имеет значение 1.", "Нужно новое состояние перед каждым тестом.", "Для этого служит метод setUp в классе.", "Создайте Counter в setUp и сохраните в self."),
  "Порядок тестов не гарантирован, поэтому каждый тест должен получать собственное состояние. Метод setUp вызывается перед каждым тестом.",
  type="fix", starter='import unittest\n\n\nclass Counter:\n    def __init__(self):\n        self.value = 0\n\n    def hit(self):\n        self.value += 1\n\n\nshared = Counter()\n\n\nclass T(unittest.TestCase):\n    def test_hit(self):\n        shared.hit()\n        self.assertEqual(shared.value, 1)\n\n    def test_start(self):\n        self.assertEqual(shared.value, 0)\n\n\nresult = unittest.TestResult()\nunittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)\nprint(len(result.failures), "провалов")\n')

a5 = predict_task("a5-almost", "Дроби в тестах",
  'import unittest\n\n\nclass T(unittest.TestCase):\n    def test_equal(self):\n        self.assertEqual(0.1 + 0.2, 0.3)\n\n    def test_almost(self):\n        self.assertAlmostEqual(0.1 + 0.2, 0.3)\n\n    def test_places(self):\n        self.assertAlmostEqual(1.0, 1.01, places=1)\n\n\nresult = unittest.TestResult()\nunittest.defaultTestLoader.loadTestsFromTestCase(T).run(result)\nprint(result.testsRun, len(result.failures))\nprint(sorted(t.id().split(".")[-1] for t, _ in result.failures))\n',
  [("3 0\n[]", "0.1 + 0.2 не равно 0.3 точно: assertEqual падает."), ("3 2\n['test_almost', 'test_equal']", "assertAlmostEqual по умолчанию допускает разницу в 7 знаков — пройдёт."), ("3 1\n['test_places']", "Проваливается именно assertEqual.")],
  hints("0.1 + 0.2 в двоичных дробях равно 0.30000000000000004.", "assertEqual сравнивает точно — и падает.", "assertAlmostEqual по умолчанию округляет до 7 знаков — проходит.", "test_places: разница 0.01 при places=1 — округление до одного знака: проходит.", "Один провал: test_equal."),
  "Дроби нельзя сравнивать точно. assertAlmostEqual сравнивает с допуском: round(a - b, places) == 0.")

mistakes = [
 {"mistake": "Забывают начать имя метода с test", "fix": "unittest запускает только методы с префиксом test — иначе проверок не будет вовсе."},
 {"mistake": "Пишут тесты, зависящие друг от друга", "fix": "Каждому тесту — своё состояние через setUp."},
 {"mistake": "Сравнивают дроби через assertEqual", "fix": "Для дробей используйте assertAlmostEqual."},
 {"mistake": "Путают провал и ошибку", "fix": "Провал — неверный результат, ошибка — исключение в коде."}]

finish("test-02-unittest", "unittest", "Писать тесты на unittest: TestCase, assert-методы, assertRaises, setUp.",
  {"test.unittest": "unittest", "test.raises": "assertRaises", "test.setup": "setUp и независимость тестов"},
  ["test-01-assert"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="testing-debugging")
