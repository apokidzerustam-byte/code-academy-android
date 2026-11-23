"""Урок Kotlin 4: корутины — suspend, async/await, launch, обработка ошибок. Длина озвучки по ТЗ (≈6–7 мин).
Код с kotlinx.coroutines компилируется в CI вместе с заглушками (tools/kotlin-stubs/android): они выполняют всё
последовательно, поэтому в сценах и тестах только детерминированный вывод — такой же, как у настоящих корутин."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


K1 = ('import kotlinx.coroutines.*\n\nsuspend fun loadPrice(name: String): Int {\n    delay(100)\n    return name.length * 10\n}\n\n'
      'fun main() = runBlocking {\n    val price = loadPrice("хлеб")\n    println("Цена: $price")\n}\n')
O1 = "Цена: 40\n"
K2 = ('import kotlinx.coroutines.*\n\nsuspend fun loadPrice(name: String): Int {\n    delay(100)\n    return name.length * 10\n}\n\n'
      'fun main() = runBlocking {\n    val a = async { loadPrice("хлеб") }\n    val b = async { loadPrice("молоко") }\n'
      '    println("Сумма: ${a.await() + b.await()}")\n}\n')
O2 = "Сумма: 100\n"
K3 = ('import androidx.lifecycle.ViewModel\nimport kotlinx.coroutines.*\n\nclass TasksViewModel(private val repo: Repo) : ViewModel() {\n'
      '    fun refresh() {\n        viewModelScope.launch {\n            val tasks = withContext(Dispatchers.IO) { repo.load() }\n'
      '            show(tasks)\n        }\n    }\n}\n')
K4 = ('import kotlinx.coroutines.*\n\nsuspend fun loadUser(id: Int): String {\n    delay(50)\n    if (id < 0) throw IllegalArgumentException("нет такого номера")\n'
      '    return "Аня"\n}\n\nfun main() = runBlocking {\n    try {\n        println(loadUser(1))\n        println(loadUser(-1))\n'
      '    } catch (e: IllegalArgumentException) {\n        println("Ошибка: ${e.message}")\n    }\n}\n')
O4 = "Аня\nОшибка: нет такого номера\n"

KC = ('import kotlinx.coroutines.*\n\nfun CoroutineScope.startLoading(): Job {\n    val job = launch {\n        repeat(1000) {\n            ensureActive()\n'
      '            // тяжёлый шаг загрузки\n        }\n    }\n    return job\n}\n\nfun stop(job: Job) {\n    job.cancel()\n}\n')

use_file("Main.kt")
scenes = [
    scene("intro", "Зачем нужны корутины", """
      Приложение на Андроиде работает с экраном в одном главном потоке. Если в этом потоке загружать данные из сети или читать
      большую базу, экран замирает: кнопки не нажимаются, анимация встаёт, а через несколько секунд система предлагает закрыть
      приложение. Поэтому долгую работу нельзя делать прямо в обработчике нажатия. Корутина решает задачу изящно. Это
      вычисление, которое умеет приостанавливаться. Представьте официанта: он принял заказ, передал его на кухню и не стоит у плиты,
      а идёт к другим столикам; когда блюдо готово, возвращается к первому. Корутина работает так же: пока оно ждёт ответ, поток свободен и занимается другими делами, а когда
      ответ пришёл, вычисление продолжается с того же места. Код при этом читается сверху вниз, как обычный, без вложенных
      обратных вызовов. Сегодня мы разберём три слова: suspend, async и launch, а ещё научимся ловить ошибки.""",
          [NOTE("Главный поток нельзя блокировать: долгую работу выносят в **корутину**. Она приостанавливается, а не занимает поток.", at="Корутина решает"),
           NOTE("`suspend` · `launch` · `async` / `await` · `withContext` · `try / catch`", at="Сегодня мы разберём")]),
    scene("suspend", "Функция suspend", """
      Функцию, которая может приостанавливаться, помечают словом suspend. Вот функция loadPrice: она изображает загрузку цены.
      Внутри стоит вызов delay — это пауза на сто миллисекунд, но пауза без блокировки потока. Потом функция возвращает
      длину названия, умноженную на десять. Вызывать suspend-функцию можно только из другой suspend-функции или из корутины.
      Чтобы запустить первую корутину в обычной программе, используют runBlocking: она ждёт завершения всего, что внутри.
      На Андроиде вместо неё берут готовые области, о них поговорим ниже. Внутри корутины вызов loadPrice выглядит как обычный:
      результат кладём в переменную и печатаем. Запустим: для слова хлеб цена получится сорок.""",
          [CLEAR(), T(K1, at="Функцию, которая"), HL(L(K1, "suspend fun"), at="помечают словом suspend"), HL(L(K1, "delay"), at="Внутри стоит вызов delay"),
           HL(L(K1, "runBlocking"), at="используют runBlocking"), HL(L(K1, "val price"), at="результат кладём в переменную"), RUN(at="Запустим"), OUT(O1, at="Запустим")]),
    scene("async", "Параллельные загрузки: async", """
      Теперь нужно загрузить две цены. Если вызывать loadPrice одну за другой, ожидания сложатся: сначала сто миллисекунд на
      хлеб, потом ещё сто на молоко. Но загрузки друг от друга не зависят, и их выгодно запустить одновременно. Для этого
      есть async. Он запускает корутину и сразу возвращает обещание результата, которое называется Deferred. Мы запускаем
      две корутины, и обе уже ждут параллельно. Когда результат понадобится, вызываем await: он дожидается и отдаёт значение.
      Складываем две цены и печатаем сумму: сорок плюс шестьдесят, сто. Общее время при этом около ста миллисекунд, а не
      двухсот. Это похоже на то, как вы ставите стирку и, пока она идёт, готовите ужин: два дела идут одновременно.""",
          [CLEAR(), T(K2, at="Теперь нужно"), HL(L(K2, "val a"), at="Для этого есть async"), HL(L(K2, "val b"), at="Мы запускаем"),
           HL(L(K2, "await"), at="вызываем await"), RUN(at="Складываем две цены"), OUT(O2, at="Складываем две цены")]),
    scene("scope", "Области и диспетчеры", """
      Откуда на Андроиде берётся корутина? Её запускают в области, у которой есть жизненный цикл. У модели представления
      ViewModel такая область называется viewModelScope: когда экран закрывается окончательно, все её корутины отменяются сами,
      и работа не утекает. Запускает корутину функция launch: она ничего не возвращает, это запуск и забыли. Если внутри нужна
      тяжёлая работа, например чтение из базы или сети, её оборачивают в withContext с диспетчером Dispatchers.IO: этот
      диспетчер использует отдельные потоки для ввода и вывода. Результат возвращается обратно, и остальной код продолжает
      работать в главном потоке. Диспетчер — это распорядитель потоков: Main работает с экраном, IO — с сетью и файлами, Default — с тяжёлыми
      вычислениями. Здесь мы только показываем код: он использует классы Андроида, поэтому на телефоне его не
      запустить.""",
          [CLEAR(), T(K3, at="Откуда на Андроиде"), HL(L(K3, "viewModelScope"), at="такая область называется"), HL(L(K3, "launch"), at="Запускает корутину функция launch"),
           HL(L(K3, "withContext"), at="её оборачивают в withContext")]),
    scene("errors", "Ошибки в корутинах", """
      Что если загрузка не удалась? В корутинах работают обычные исключения и обычный блок try catch. Функция loadUser
      выбрасывает исключение для отрицательного номера. В корутине мы вызываем её дважды. Первый вызов проходит и печатает
      имя. Второй бросает исключение, управление переходит в catch, и мы печатаем сообщение об ошибке. Важное правило: ловите
      ошибки там, где можете на них осмысленно ответить. Например, показать пользователю сообщение и кнопку повтора, а не
      оставить экран пустым. Ещё удобно возвращать из загрузки не исключение, а результат с признаком успеха; к этому приёму мы вернёмся, когда
      подключим базу данных. Если исключение никто не поймал, оно отменит родительскую корутину и приложение может упасть.""",
          [CLEAR(), T(K4, at="Что если загрузка"), HL(L(K4, "throw"), at="выбрасывает исключение"), HL(L(K4, "println(loadUser(1))"), at="Первый вызов"),
           HL(L(K4, "catch"), at="управление переходит"), RUN(at="Важное правило"), OUT(O4, at="Важное правило")]),
    scene("cancel", "Отмена и структурированная работа", """
      У корутин есть важное свойство: они выстроены в дерево. Корутина, запущенная внутри другой, становится её дочерней. Родитель
      не считается завершённым, пока не закончат все дети, а если отменить родителя, отменятся и дети. Это называется
      структурированной конкурентностью, и именно она не даёт работе утекать. Представьте экран с загрузкой списка. Пользователь
      ушёл назад, экран закрылся, область корутин отменилась, и загрузка прекращается сама. Отменить отдельную корутину можно
      и вручную: launch возвращает Job, у которого есть метод cancel. Отмена кооперативная: корутина замечает её в местах
      приостановки, например в delay, и в этот момент выбрасывает специальное исключение. Поэтому внутри долгого цикла полезно
      иногда вызывать ensureActive.""",
          [CLEAR(), T(KC, at="Отменить отдельную"), HL(L(KC, "val job"), at="launch возвращает Job"), HL(L(KC, "cancel"), at="метод cancel"),
           HL(L(KC, "ensureActive"), at="ensureActive")]),
    scene("mistakes", "Типичные ошибки", """
      Разберём четыре типичные ошибки. Первая: вызов suspend-функции из обычной функции. Компилятор сообщит, что так нельзя.
      Решение простое: пометьте вашу функцию словом suspend или запустите корутину через launch. Вторая ошибка: две независимые
      загрузки идут одна за другой. Приложение работает, но вдвое медленнее, чем могло бы. Запустите их через async и достаньте
      результаты вызовом await. Третья ошибка: runBlocking внутри обработчика нажатия. Код компилируется и даже работает, но
      главный поток замирает. Используйте область корутин экрана и launch. Четвёртая ошибка: async без области. Функция async
      определена только внутри области корутин, поэтому её вызывают в coroutineScope или в готовой области вроде viewModelScope.""",
          [NOTE("Ошибка 1: `suspend` вызвана из обычной функции → пометьте вызывающую `suspend` или запустите `launch`.", at="Первая"),
           NOTE("Ошибка 2: загрузки по очереди → `async` + `await`.", at="Вторая ошибка"),
           NOTE("Ошибка 3: `runBlocking` в обработчике → `launch` в области экрана.", at="Третья ошибка"),
           NOTE("Ошибка 4: `async` без области → `coroutineScope { … }`.", at="Четвёртая ошибка")]),
    scene("summary", "Итог", """
      Подведём итог. Suspend-функция умеет приостанавливаться и вызывается только из другой suspend-функции или корутины. Delay
      ждёт без блокировки потока. Launch запускает корутину без результата, async возвращает Deferred, а await достаёт
      значение. Независимые загрузки запускайте через async, чтобы ждать их одновременно. Тяжёлую работу переносите в
      withContext с диспетчером Dispatchers.IO. Ошибки ловите обычным try catch. Не используйте runBlocking на главном потоке
      Андроида: он блокирует его так же, как долгая загрузка прямо в обработчике. В заданиях вы напишете suspend-функции,
      запустите параллельные загрузки и исправите вызов, который не компилируется. Критерий прохождения: решить не меньше трёх
      заданий из четырёх.""",
          [NOTE("`suspend fun` · `delay(мс)` · `async { … }.await()` · `launch { … }` · `withContext(Dispatchers.IO) { … }`", at="Подведём итог"),
           NOTE("Не блокируйте главный поток: на Андроиде `runBlocking` в обработчиках не используют.", at="Не используйте runBlocking")]),
]

notes = """
# Kotlin: корутины

Корутина — вычисление, которое умеет приостанавливаться, не занимая поток. Так экран не замирает во время долгой работы.

```kotlin
import kotlinx.coroutines.*

suspend fun loadPrice(name: String): Int {
    delay(100)                       // пауза без блокировки потока
    return name.length * 10
}

fun main() = runBlocking {           // запускает первую корутину
    val a = async { loadPrice("хлеб") }     // параллельно
    val b = async { loadPrice("молоко") }
    println("Сумма: ${a.await() + b.await()}")   // 100
}
```

| Слово | Что делает |
|---|---|
| `suspend` | функция может приостанавливаться; вызывается из корутины или другой suspend-функции |
| `launch { … }` | запускает корутину, результата нет |
| `async { … }` | запускает корутину и возвращает `Deferred`; значение — `await()` |
| `withContext(Dispatchers.IO) { … }` | выполняет блок в потоках ввода-вывода и возвращает результат |
| `delay(мс)` | пауза без блокировки потока |
| `viewModelScope` | область корутин ViewModel: отменяется, когда экран закрыт навсегда |

Ошибки ловят обычным `try { … } catch (e: Exception) { … }`.

- Независимые загрузки запускайте через `async` — ждать придётся дольше всего одну из них, а не сумму.
- `runBlocking` блокирует поток: он нужен в `main` и тестах, а не в обработчиках экрана Андроида.
- Примеры с `viewModelScope` используют классы Андроида: на телефоне они не запускаются, их проверяют на компьютере и в CI.
- Проверка заданий в CI идёт на упрощённой модели корутин (всё выполняется последовательно), поэтому задания проверяют результат, а не порядок выполнения.
"""

PRE = ("import kotlinx.coroutines.*\n\nsuspend fun loadPrice(name: String): Int {\n    delay(10)\n    return name.length * 10\n}\n\n")

# --- a1: последовательные загрузки ---
S1 = PRE + 'suspend fun total(): Int {\n    val bread = loadPrice("хлеб")\n    val cheese = loadPrice("сыр")\n    return bread + cheese\n}\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "total", "paramTypes": [], "returns": "Int"},
    {"id": "susp", "type": "contains", "pattern": "\\bsuspend\\s+fun\\s+total\\b", "message": "Функция, которая вызывает suspend-функции, сама должна быть suspend"},
    {"id": "bread", "hidden": True, "type": "contains", "raw": True, "pattern": "loadPrice\\s*\\(\\s*\"хлеб\"\\s*\\)", "message": "Загрузите цену хлеба: loadPrice(\"хлеб\")"},
    {"id": "cheese", "hidden": True, "type": "contains", "raw": True, "pattern": "loadPrice\\s*\\(\\s*\"сыр\"\\s*\\)", "message": "Загрузите цену сыра: loadPrice(\"сыр\")"},
    {"id": "plus", "hidden": True, "type": "contains", "pattern": "\\+", "message": "Цены нужно сложить"},
], "jvm": {"main": "fun main() = runBlocking {\n    println(total())\n}", "expected_stdout": "70"}}
a1 = asg("a1-total", "write", "Сумма двух цен",
         "Функция `loadPrice(name)` уже написана — она «загружает» цену товара. Допишите **suspend-функцию** `total(): Int`, которая получает цены товаров «хлеб» и «сыр» "
         "(вызовите `loadPrice(\"хлеб\")` и `loadPrice(\"сыр\")` одну за другой) и возвращает их **сумму**.",
         "Вызывать suspend-функции из suspend-функции.", "—", "Сумма цен: 40 + 30 = 70.",
         ["Функцию loadPrice не меняйте."],
         hints("Заголовок: suspend fun total(): Int.", "Одна suspend-функция может вызывать другие как обычные: результат кладут в переменную.",
               "Цену хлеба получите вызовом loadPrice(\"хлеб\"), цену сыра — loadPrice(\"сыр\").", "Результаты складывают оператором плюс.",
               "Тело: val bread = loadPrice(\"хлеб\"); val cheese = loadPrice(\"сыр\"); return bread + cheese."),
         t1, S1, "Функция total помечена suspend, поэтому может вызывать loadPrice. Обе загрузки идут по очереди, результаты складываются: 40 + 30 = 70.",
         ["Есть suspend fun total(): Int.", "Загружены обе цены.", "Цены сложены."],
         [(PRE + 'fun total(): Int {\n    return loadPrice("хлеб") + loadPrice("сыр")\n}\n', "Нет слова suspend: обычная функция не может вызывать suspend-функцию."),
          (PRE + 'suspend fun total(): Int {\n    return loadPrice("хлеб")\n}\n', "Загружена только одна цена: сыр пропущен."),
          (PRE + 'suspend fun total(): Int {\n    return loadPrice("хлеб") * loadPrice("сыр")\n}\n', "Цены перемножаются, а нужно сложить.")],
         starter=PRE + "// Допишите suspend fun total(): Int\n")

# --- a2: параллельные загрузки ---
S2 = PRE + 'suspend fun totalParallel(): Int = coroutineScope {\n    val bread = async { loadPrice("хлеб") }\n    val cheese = async { loadPrice("сыр") }\n    bread.await() + cheese.await()\n}\n'
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "totalParallel", "paramTypes": [], "returns": "Int"},
    {"id": "susp", "type": "contains", "pattern": "\\bsuspend\\s+fun\\s+totalParallel\\b", "message": "Функция должна быть suspend"},
    {"id": "async", "type": "contains", "pattern": "\\basync\\b[\\s\\S]*\\basync\\b", "message": "Запустите обе загрузки через async, чтобы они шли параллельно", "hint": "Каждая загрузка — отдельный async { … }"},
    {"id": "await", "hidden": True, "type": "contains", "pattern": "\\bawait\\s*\\(\\s*\\)[\\s\\S]*\\bawait\\s*\\(\\s*\\)", "message": "Результат каждого async достают вызовом await()"},
    {"id": "scope", "hidden": True, "type": "contains", "pattern": "\\bcoroutineScope\\b", "message": "async запускают внутри области: coroutineScope { … }"},
], "jvm": {"main": "fun main() = runBlocking {\n    println(totalParallel())\n}", "expected_stdout": "70"}}
a2 = asg("a2-parallel", "write", "Загрузки одновременно",
         "Загрузка цены хлеба и сыра не зависит друг от друга. Напишите `suspend fun totalParallel(): Int`, которая запускает **обе загрузки параллельно** через `async` "
         "внутри `coroutineScope { … }` и возвращает сумму цен (`await()` для каждой). Функция `loadPrice` уже есть.",
         "Запускать независимые загрузки параллельно.", "—", "Сумма цен: 70.",
         ["Используйте async и await, а не последовательные вызовы."],
         hints("Заголовок: suspend fun totalParallel(): Int = coroutineScope { … }.", "async { … } запускает корутину и сразу возвращает Deferred.",
               "Запустите две корутины: val bread = async { loadPrice(\"хлеб\") } и такую же для сыра.", "Значение достают методом await().",
               "Последняя строка блока: bread.await() + cheese.await()."),
         t2, S2, "Обе корутины стартуют сразу, и ждать приходится только самую долгую. Результат каждой достаётся через await.",
         ["suspend fun totalParallel(): Int.", "Обе загрузки через async.", "Результаты через await и сложены."],
         [(PRE + 'suspend fun totalParallel(): Int = coroutineScope {\n    loadPrice("хлеб") + loadPrice("сыр")\n}\n', "Загрузки идут по очереди — async не использован."),
          (PRE + 'suspend fun totalParallel(): Int = coroutineScope {\n    val bread = async { loadPrice("хлеб") }\n    bread.await() + loadPrice("сыр")\n}\n', "Параллельно запущена только одна загрузка."),
          (PRE + 'suspend fun totalParallel(): Int {\n    val bread = async { loadPrice("хлеб") }\n    val cheese = async { loadPrice("сыр") }\n    return bread.await() + cheese.await()\n}\n', "async нужна область: оберните тело в coroutineScope { … }.")],
         starter=PRE + "// Допишите suspend fun totalParallel(): Int\n")

# --- a3: fix — вызов suspend из обычной функции ---
BAD3 = 'import kotlinx.coroutines.*\n\nsuspend fun loadName(): String {\n    delay(10)\n    return "Аня"\n}\n\nfun greeting(): String = "Привет, " + loadName()\n'
S3 = 'import kotlinx.coroutines.*\n\nsuspend fun loadName(): String {\n    delay(10)\n    return "Аня"\n}\n\nsuspend fun greeting(): String = "Привет, " + loadName()\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "greeting", "paramTypes": [], "returns": "String"},
    {"id": "susp", "type": "contains", "pattern": "\\bsuspend\\s+fun\\s+greeting\\b", "message": "Функция, вызывающая suspend-функцию, должна быть suspend",
     "hint": "Компилятор: «Suspend function can be called only from a coroutine or another suspend function»"},
    {"id": "noblock", "hidden": True, "type": "not_contains", "pattern": "\\brunBlocking\\b", "message": "runBlocking блокирует поток — на Андроиде так не делают"},
], "jvm": {"main": "fun main() = runBlocking {\n    println(greeting())\n}", "expected_stdout": "Привет, Аня"}}
a3 = asg("a3-suspend-call", "fix", "Вызов suspend-функции",
         "Код не компилируется: обычная функция `greeting` вызывает suspend-функцию `loadName`. Исправьте так, чтобы программа собиралась и функция `greeting()` возвращала `Привет, Аня`. "
         "Не используйте `runBlocking`: он блокирует поток.",
         "Понимать, где можно вызывать suspend-функции.", "—", "Строка «Привет, Аня».",
         ["Тип результата String не меняйте."],
         hints("Компилятор говорит: suspend-функцию можно вызвать только из корутины или другой suspend-функции.", "У функции greeting нет слова suspend.",
               "Пометьте greeting словом suspend: тогда она тоже сможет приостанавливаться.", "runBlocking заставил бы поток ждать — на Андроиде главный поток блокировать нельзя.",
               "Слово suspend ставят перед fun: suspend fun greeting()."),
         t3, S3, "Вызвать suspend-функцию можно только из suspend-функции или корутины. Значит, greeting тоже должна быть suspend; вызывающий код запустит её в корутине.",
         ["Функция помечена suspend.", "runBlocking не используется."],
         [(BAD3, "Ошибка осталась: обычная функция вызывает suspend-функцию."),
          ('import kotlinx.coroutines.*\n\nsuspend fun loadName(): String {\n    delay(10)\n    return "Аня"\n}\n\nfun greeting(): String = runBlocking { "Привет, " + loadName() }\n',
           "Компилируется, но runBlocking блокирует поток; в Андроиде функция должна быть suspend."),
          ('import kotlinx.coroutines.*\n\nsuspend fun loadName(): String {\n    delay(10)\n    return "Аня"\n}\n\nfun greeting(): String = "Привет, Аня"\n', "Загрузка имени убрана вместо исправления вызова.")],
         starter=BAD3)

# --- a4: predict ---
CODE4 = ('import kotlinx.coroutines.*\n\nsuspend fun step(n: Int): Int {\n    delay(10)\n    return n * 2\n}\n\nfun main() = runBlocking {\n'
         '    val first = step(1)\n    val second = async { step(first) }\n    val third = step(second.await())\n    println("$first $third")\n'
         '    try {\n        check(third > 10) { "мало" }\n    } catch (e: IllegalStateException) {\n        println("Ошибка: ${e.message}")\n    }\n}\n')
ans4 = "2 8\nОшибка: мало"
a4 = asg("a4-predict", "predict", "Что напечатает программа?",
         "Что выведет программа? Каждая строка вывода — с новой строки.",
         "Проследить цепочку suspend-вызовов и исключение.", "—", "Две строки.", [],
         hints("Сначала first = step(1): функция удваивает число.", "second запускает step(first), то есть step(2).", "third = step(second.await()) — удвоение результата второй загрузки.",
               "Первая строка печатает first и third через пробел.", "check(third > 10) падает, если условие ложно: сравните третье число с десятью."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "first = 2, second = step(2) = 4, third = step(4) = 8. Первая строка — «2 8». Проверка 8 > 10 ложна, check бросает IllegalStateException с сообщением «мало», и catch печатает вторую строку.",
         ["Обе строки верны."],
         [("2 8", "Условие check(third > 10) ложно, поэтому исключение сработает и напечатается вторая строка."),
          ("2 4\nОшибка: мало", "Третье число — результат step(second.await()), то есть 8, а не 4."),
          ("1 4\nОшибка: мало", "first = step(1) = 2, а не 1.")],
         code=CODE4)

skills = {"kt.suspend": "Функции suspend", "kt.async": "async, await и launch", "kt.scope": "Области и диспетчеры корутин"}
write_lesson("kt-04-coroutines", "Kotlin: корутины",
             "Писать suspend-функции, запускать независимые загрузки параллельно через async и ловить ошибки в корутинах.",
             list(skills), ["kt-03-collections"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Вызов suspend-функции из обычной функции", "fix": "Пометьте вызывающую функцию словом suspend или запустите корутину (launch, async)."},
              {"mistake": "Две независимые загрузки идут по очереди", "fix": "Запустите обе через async и вызовите await: ждать придётся только самую долгую."},
              {"mistake": "runBlocking в обработчике экрана", "fix": "Он блокирует главный поток; запускайте корутину в viewModelScope через launch."},
              {"mistake": "async без области", "fix": "async вызывают внутри coroutineScope { … } или в области вроде viewModelScope."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-04-coroutines" not in data["lessons"]:
    data["lessons"].append("kt-04-coroutines")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
