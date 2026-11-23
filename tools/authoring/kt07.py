"""Урок Kotlin 7: ViewModel и StateFlow — хранение состояния экрана, однонаправленный поток данных.
Код проверяется по заглушкам (tools/kotlin-stubs/android): ViewModel, StateFlow, collectAsState упрощены (без перерисовок и потоков)."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP_VM = ("import androidx.lifecycle.ViewModel\nimport kotlinx.coroutines.flow.MutableStateFlow\nimport kotlinx.coroutines.flow.StateFlow\n"
          "import kotlinx.coroutines.flow.asStateFlow\n")
K1 = IMP_VM + ('\nclass CounterViewModel : ViewModel() {\n    private val _count = MutableStateFlow(0)\n    val count: StateFlow<Int> = _count.asStateFlow()\n\n'
               '    fun increment() {\n        _count.value += 1\n    }\n}\n')
IMP_UP = "import androidx.lifecycle.ViewModel\nimport kotlinx.coroutines.flow.MutableStateFlow\nimport kotlinx.coroutines.flow.StateFlow\nimport kotlinx.coroutines.flow.asStateFlow\nimport kotlinx.coroutines.flow.update\n"
K2 = IMP_UP + ('\ndata class TasksUiState(val tasks: List<String> = emptyList(), val loading: Boolean = false)\n\n'
               'class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n'
               '    fun add(title: String) {\n        _state.update { it.copy(tasks = it.tasks + title) }\n    }\n}\n\n'
               'fun main() {\n    val vm = TasksViewModel()\n    vm.add("Хлеб")\n    vm.add("Сыр")\n    println(vm.state.value.tasks)\n    println(vm.state.value.loading)\n}\n')
O2 = "[Хлеб, Сыр]\nfalse\n"
IMP_UI = ("import androidx.compose.foundation.layout.Column\nimport androidx.compose.material3.Button\nimport androidx.compose.material3.Text\n"
          "import androidx.compose.runtime.Composable\nimport androidx.compose.runtime.collectAsState\nimport androidx.compose.runtime.getValue\n")
K3 = IMP_UI + ('\n@Composable\nfun CounterScreen(viewModel: CounterViewModel) {\n    val count by viewModel.count.collectAsState()\n    Column {\n        Text("Счёт: $count")\n'
               '        Button(onClick = { viewModel.increment() }) {\n            Text("+1")\n        }\n    }\n}\n')

K5 = K1 + ('\nfun main() {\n    val vm = CounterViewModel()\n    vm.increment()\n    check(vm.count.value == 1) { "ожидали 1" }\n    println("Проверка прошла")\n}\n')
O5 = "Проверка прошла\n"

use_file("Main.kt")
scenes = [
    scene("intro", "Зачем нужна ViewModel", """
      В прошлом уроке состояние жило прямо в функции интерфейса. Для счётчика этого хватит, но в настоящем приложении есть список задач,
      загрузка из сети, сохранение в базу. Если держать всё это в функциях интерфейса, они превратятся в свалку: вперемешку рисование,
      правила и работа с данными, и ни одну часть нельзя проверить отдельно. Кроме того, при повороте экрана Андроид пересоздаёт всё, и
      обычное состояние теряется. Для этого в Андроиде придумали ViewModel. Это обычный класс, который хранит состояние экрана и логику его
      изменения. Он живёт дольше экрана и переживает повороты. Функции интерфейса лишь показывают то, что лежит во ViewModel, и сообщают
      ей о действиях пользователя. Состояние, которое она отдаёт наружу, обычно описывают потоком StateFlow.""",
          [NOTE("**ViewModel**: хранит состояние экрана и логику; переживает поворот; не знает про кнопки и текст.", at="Это обычный класс"),
           NOTE("`ViewModel` · `MutableStateFlow` / `StateFlow` · `update { it.copy(…) }` · `collectAsState()`", at="Состояние, которое она отдаёт")]),
    scene("stateflow", "Класс ViewModel и StateFlow", """
      Вот ViewModel счётчика. Она наследует класс ViewModel. Внутри лежит MutableStateFlow: это ячейка, которая хранит значение и
      сообщает подписчикам, когда оно меняется. Начальное значение ноль. Ячейку делают приватной, и по договорённости её имя начинают с
      подчёркивания. Наружу отдают только чтение: свойство count типа StateFlow, которое получают вызовом asStateFlow. Так экран может
      смотреть значение, но не может подменить его снаружи. Любое изменение проходит через методы ViewModel, например increment. В этом
      порядок: один владелец данных и один способ их менять.""",
          [CLEAR(), T(K1, at="Вот ViewModel"), HL(L(K1, "class CounterViewModel"), at="Она наследует"), HL(L(K1, "private val"), at="Ячейку делают приватной"),
           HL(L(K1, "val count"), at="Наружу отдают"), HL(L(K1, "fun increment", 3), at="через методы ViewModel")]),
    scene("update", "Обновление состояния через update", """
      Состояние экрана обычно состоит из нескольких полей, и его описывают классом данных, например, список задач и признак загрузки.
      Чтобы изменить одно поле, берут текущее состояние и делают копию. Для этого у MutableStateFlow есть функция update: она получает
      лямбду, в которой it — старое состояние, и записывает то, что лямбда вернула. Здесь мы создаём копию с задачей, добавленной в
      конец списка. Старый список не меняется, потому что плюс создаёт новый. Запустим пример: после двух добавлений в списке две
      задачи, а признак загрузки остался ложью. Функция update ещё и безопасна, если несколько корутин меняют состояние одновременно.""",
          [CLEAR(), T(K2, at="Состояние экрана"), HL(L(K2, "data class"), at="классом данных"), HL(L(K2, "update {"), at="функция update"),
           HL(L(K2, "it.tasks + title"), at="Здесь мы создаём"), RUN(at="Запустим пример"), OUT(O2, at="Запустим пример")]),
    scene("collect", "Экран подписывается на состояние", """
      Осталось показать значение на экране. Функция интерфейса получает ViewModel и вызывает collectAsState. Она превращает поток в
      состояние Compose: когда значение в потоке меняется, экран перерисовывается. Слово by позволяет читать счёт как обычную переменную,
      но не забудьте импорт getValue. Нажатие кнопки вызывает метод ViewModel. Заметьте цикл: экран показывает состояние, пользователь
      нажимает, событие уходит во ViewModel, она меняет состояние, и экран снова показывает новое значение. Данные движутся по кругу в
      одном направлении, поэтому такой подход называют однонаправленным потоком данных. Если прочитать count.value напрямую, экран не
      узнает об изменениях: подписки не будет.""",
          [CLEAR(), T(K3, at="Осталось показать"), HL(L(K3, "collectAsState"), at="вызывает collectAsState"), HL(L(K3, "Text("), at="читать счёт"),
           HL(L(K3, "viewModel.increment"), at="вызывает метод ViewModel")]),
    scene("get", "Как экран получает ViewModel", """
      Откуда экран берёт ViewModel? Создавать её вручную через конструктор нельзя: тогда при повороте появится новая, и данные потеряются.
      Её просит у системы функция viewModel: система создаёт объект один раз и возвращает тот же после поворота. Если ViewModel нужны
      зависимости, например репозиторий, подключают фабрику или внедрение зависимостей. Эти приёмы обычно изучают в Android Studio на
      настоящем проекте. Здесь важна идея: экран не создаёт и не уничтожает ViewModel, а лишь получает её. Для запуска долгой работы
      у ViewModel есть viewModelScope, о котором мы говорили в уроке про корутины: корутины в нём отменяются, когда ViewModel больше не нужна.""",
          [CLEAR(), NOTE("`val vm: CounterViewModel = viewModel()` — система создаёт объект один раз и сохраняет при повороте.", at="Её просит"),
           NOTE("`viewModelScope.launch { … }` — корутины отменяются вместе с ViewModel.", at="у ViewModel есть viewModelScope")]),
    scene("testing", "ViewModel легко проверить", """
      Ещё одно достоинство ViewModel: это обычный класс, и проверять его можно без телефона и без экрана. Достаточно создать объект,
      вызвать метод и посмотреть на значение. Если оно не совпало с ожидаемым, функция check бросит исключение с вашим сообщением.
      Запустим такой пример: создаём счётчик, нажимаем один раз и проверяем, что значение равно единице. Проверка проходит, и мы видим
      сообщение. Именно поэтому логику стараются держать во ViewModel, а не в функциях интерфейса: её можно проверять быстро и
      автоматически на обычном компьютере, а затем уже подключать к экрану. В настоящих проектах для этого пишут тесты на JUnit, но идея
      та же: подготовить данные, выполнить действие и сравнить результат.""",
          [CLEAR(), T(K5, at="Достаточно создать"), HL(L(K5, "vm.increment()"), at="вызвать метод"), HL(L(K5, "check("), at="функция check"),
           RUN(at="Запустим такой"), OUT(O5, at="Запустим такой")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: отдавать наружу изменяемый MutableStateFlow. Тогда любой экран может подменить данные. Отдавайте
      StateFlow через asStateFlow. Вторая: читать value напрямую вместо collectAsState. Экран не перерисуется. Третья: менять список на
      месте, например добавлять элемент в изменяемый список внутри состояния. Ссылка прежняя, и подписчики не видят изменения. Создавайте
      копию через copy и плюс. Четвёртая: хранить во ViewModel ссылки на экран или кнопки. ViewModel живёт дольше экрана, и
      ссылки приведут к утечке памяти.""",
          [NOTE("Ошибка 1: публичный `MutableStateFlow` → приватный `_state` + публичный `StateFlow` через `asStateFlow()`.", at="Первая"),
           NOTE("Ошибка 2: `viewModel.count.value` в функции интерфейса → `by viewModel.count.collectAsState()`.", at="Вторая"),
           NOTE("Ошибка 3: правка списка на месте → `copy(tasks = it.tasks + title)`.", at="Третья"),
           NOTE("Ошибка 4: ссылки на экран во ViewModel → утечка памяти.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. ViewModel хранит состояние экрана и логику, переживает поворот и не знает ни про кнопки, ни про текст. Состояние хранят
      в приватном MutableStateFlow, а наружу отдают StateFlow. Изменения делают через update и copy. Экран подписывается через collectAsState
      и посылает события методам ViewModel. Данные идут по кругу в одном направлении: состояние вниз, события вверх. В заданиях вы напишете
      ViewModel счётчика, добавите обновление списка, исправите экран без подписки и предскажете результат. Критерий прохождения: решить не
      меньше трёх заданий из четырёх. Помните: проверка идёт на компьютере по упрощённым моделям ViewModel и StateFlow, настоящее поведение
      потоков проверяется только в готовом проекте.""",
          [NOTE("`private val _state = MutableStateFlow(…)` + `val state: StateFlow<…> = _state.asStateFlow()`", at="Состояние хранят"),
           NOTE("Экран: `val s by vm.state.collectAsState()`; события: `vm.метод()`.", at="Экран подписывается")]),
]

notes = """
# Kotlin: ViewModel и StateFlow

ViewModel хранит состояние экрана и логику его изменения. Она переживает поворот экрана и не знает про кнопки и текст.

```kotlin
class CounterViewModel : ViewModel() {
    private val _count = MutableStateFlow(0)               // изменяемое — приватно
    val count: StateFlow<Int> = _count.asStateFlow()       // наружу — только чтение

    fun increment() {
        _count.value += 1
    }
}
```

Сложное состояние — класс данных; меняют его через `update` и `copy`:

```kotlin
data class TasksUiState(val tasks: List<String> = emptyList(), val loading: Boolean = false)

_state.update { it.copy(tasks = it.tasks + title) }
```

Экран подписывается и посылает события:

```kotlin
@Composable
fun CounterScreen(viewModel: CounterViewModel) {
    val count by viewModel.count.collectAsState()
    Column {
        Text("Счёт: $count")
        Button(onClick = { viewModel.increment() }) { Text("+1") }
    }
}
```

**Поток данных:** состояние → экран → событие → ViewModel → новое состояние.

- Не отдавайте наружу `MutableStateFlow`; не читайте `.value` в функции интерфейса — экран не обновится.
- Не меняйте списки на месте: создавайте копию.
- Не храните во ViewModel ссылки на экран.
- **Ограничение проверки:** заглушки в CI выполняют код последовательно: потоков, подписок и перерисовок нет, `collectAsState` просто читает текущее значение. Правила настоящего Compose закреплены структурными проверками заданий. В приложении на телефоне этот код не запускается.
"""

# --- a1: CounterViewModel ---
S1 = K1.replace(IMP_VM, IMP_VM)
PRE1 = IMP_VM + "\n"
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "CounterViewModel"},
    {"id": "base", "type": "contains", "pattern": "class\\s+CounterViewModel\\s*:\\s*ViewModel\\s*\\(\\s*\\)", "message": "Класс должен наследовать ViewModel: class CounterViewModel : ViewModel()"},
    {"id": "priv", "type": "contains", "pattern": "private\\s+val\\s+_count\\s*=\\s*MutableStateFlow\\s*\\(\\s*0\\s*\\)", "message": "Изменяемое состояние — приватное: private val _count = MutableStateFlow(0)"},
    {"id": "pub", "type": "contains", "pattern": "val\\s+count\\s*:\\s*StateFlow\\s*<\\s*Int\\s*>\\s*=\\s*_count\\.asStateFlow\\s*\\(\\s*\\)", "message": "Наружу отдайте только чтение: val count: StateFlow<Int> = _count.asStateFlow()"},
    {"id": "inc", "type": "function", "name": "increment", "paramTypes": [], "returns": "Unit"},
    {"id": "logic", "hidden": True, "type": "contains", "pattern": "_count\\s*\\.\\s*(value\\s*(\\+=\\s*1|=\\s*_count\\s*\\.\\s*value\\s*\\+\\s*1)|update\\s*\\{)", "message": "increment должен увеличивать значение на 1: _count.value += 1"},
], "jvm": {"main": "fun main() {\n    val vm = CounterViewModel()\n    vm.increment()\n    vm.increment()\n    println(vm.count.value)\n}", "expected_stdout": "2"}}
a1 = asg("a1-counter-vm", "write", "ViewModel счётчика",
         "Напишите класс `CounterViewModel`, наследующий `ViewModel`. Внутри: приватное состояние `_count` (`MutableStateFlow` со значением 0), публичное только для чтения свойство "
         "`count: StateFlow<Int>` (через `asStateFlow()`) и метод `increment()`, который увеличивает счёт на 1.",
         "Хранить состояние во ViewModel и скрывать изменяемую часть.", "—", "После двух вызовов increment() значение count равно 2.",
         ["Импорты уже в шаблоне."],
         hints("Класс наследует ViewModel: после имени ставят двоеточие и ViewModel().", "Изменяемая ячейка нужна только внутри класса, поэтому она private.",
               "Её создаёт MutableStateFlow(0); имя по договорённости начинается с подчёркивания.", "Наружу отдают тот же поток, но с типом StateFlow<Int>: у MutableStateFlow для этого есть asStateFlow().",
               "Метод increment() делает _count.value += 1."),
         t1, S1, "Изменяемое состояние спрятано внутри, наружу виден только StateFlow. Любое изменение проходит через метод increment.",
         ["Класс наследует ViewModel.", "Приватный _count и публичный count.", "Метод increment."],
         [(PRE1 + 'class CounterViewModel : ViewModel() {\n    val count = MutableStateFlow(0)\n    fun increment() {\n        count.value += 1\n    }\n}\n', "Наружу отдан MutableStateFlow: любой код сможет подменить значение."),
          (PRE1 + 'class CounterViewModel {\n    private val _count = MutableStateFlow(0)\n    val count: StateFlow<Int> = _count.asStateFlow()\n    fun increment() {\n        _count.value += 1\n    }\n}\n', "Класс не наследует ViewModel."),
          (PRE1 + 'class CounterViewModel : ViewModel() {\n    private val _count = MutableStateFlow(0)\n    val count: StateFlow<Int> = _count.asStateFlow()\n    fun increment() {\n        _count.value = 1\n    }\n}\n', "Метод всегда записывает 1 вместо увеличения на 1.")],
         starter=PRE1 + "// Напишите класс CounterViewModel\n")

# --- a2: TasksViewModel.add ---
PRE2 = IMP_UP + "\ndata class TasksUiState(val tasks: List<String> = emptyList(), val loading: Boolean = false)\n\n"
S2 = PRE2 + ('class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n'
             '    fun add(title: String) {\n        _state.update { it.copy(tasks = it.tasks + title) }\n    }\n}\n')
ST2 = PRE2 + ('class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n'
              '    // Допишите метод add(title: String): добавьте задачу в конец списка\n}\n')
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "TasksViewModel"},
    {"id": "add", "type": "function", "name": "add", "paramTypes": ["String"], "returns": "Unit"},
    {"id": "upd", "type": "contains", "pattern": "_state\\.update\\s*\\{", "message": "Меняйте состояние через _state.update { … }", "hint": "update безопасно заменяет состояние результатом лямбды"},
    {"id": "copy", "type": "contains", "pattern": "it\\.copy\\s*\\(\\s*tasks\\s*=", "message": "Создайте копию состояния: it.copy(tasks = …)"},
    {"id": "plus", "hidden": True, "type": "contains", "pattern": "it\\.tasks\\s*\\+\\s*title", "message": "Новый список получают операцией it.tasks + title (старый не меняется)"},
], "jvm": {"main": "fun main() {\n    val vm = TasksViewModel()\n    vm.add(\"Хлеб\")\n    vm.add(\"Сыр\")\n    println(vm.state.value.tasks)\n    println(vm.state.value.loading)\n}", "expected_stdout": "[Хлеб, Сыр]\nfalse"}}
a2 = asg("a2-add-task", "complete", "Добавить задачу",
         "В `TasksViewModel` допишите метод `add(title: String)`: он должен добавить задачу в **конец** списка `tasks` состояния. Меняйте состояние через `_state.update { … }` и создавайте копию `copy`, "
         "не изменяя старый список.",
         "Обновлять состояние ViewModel через update и copy.", "add(\"Хлеб\"), add(\"Сыр\")", "tasks = [Хлеб, Сыр], loading = false.",
         ["Остальной код класса не меняйте."],
         hints("Состояние хранится в _state; менять его нужно не присваиванием полей, а функцией update.", "В лямбде update параметр it — старое состояние.",
               "Новое состояние — копия старого: it.copy(…).", "В копии заменяется поле tasks: it.tasks + title создаёт новый список с добавленной задачей.",
               "_state.update { it.copy(tasks = it.tasks + title) }."),
         t2, S2, "update передаёт в лямбду старое состояние и сохраняет её результат. copy делает новое состояние, а плюс создаёт новый список: старые объекты не меняются.",
         ["Метод add.", "Состояние обновляется через update и copy."],
         [(PRE2 + 'class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n    fun add(title: String) {\n        _state.update { it.copy(tasks = listOf(title)) }\n    }\n}\n', "Список заменяется целиком: прежние задачи теряются."),
          (PRE2 + 'class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n    fun add(title: String) {\n        _state.value = _state.value.copy(tasks = _state.value.tasks + title)\n    }\n}\n', "Работает, но состояние нужно менять через update: так безопаснее при одновременных изменениях."),
          (PRE2 + 'class TasksViewModel : ViewModel() {\n    private val _state = MutableStateFlow(TasksUiState())\n    val state: StateFlow<TasksUiState> = _state.asStateFlow()\n\n    fun add(title: String) {\n        _state.update { it.copy(tasks = title + it.tasks) }\n    }\n}\n', "Задача добавляется не в конец, и тип не сходится.")],
         starter=ST2)

# --- a3: fix collectAsState ---
PRE3 = IMP_UI + IMP_VM.replace("import androidx.compose", "import androidx.compose") + "\n"
VMCODE = 'class CounterViewModel : ViewModel() {\n    private val _count = MutableStateFlow(0)\n    val count: StateFlow<Int> = _count.asStateFlow()\n    fun increment() {\n        _count.value += 1\n    }\n}\n\n'
HEAD3 = ("import androidx.lifecycle.ViewModel\nimport androidx.compose.foundation.layout.Column\nimport androidx.compose.material3.Button\nimport androidx.compose.material3.Text\n"
         "import androidx.compose.runtime.Composable\nimport kotlinx.coroutines.flow.MutableStateFlow\nimport kotlinx.coroutines.flow.StateFlow\nimport kotlinx.coroutines.flow.asStateFlow\n")
BAD3 = HEAD3 + "\n" + VMCODE + '@Composable\nfun CounterScreen(viewModel: CounterViewModel) {\n    val count = viewModel.count.value\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { viewModel.increment() }) {\n            Text("+1")\n        }\n    }\n}\n'
S3 = (HEAD3 + "import androidx.compose.runtime.collectAsState\nimport androidx.compose.runtime.getValue\n\n" + VMCODE +
      '@Composable\nfun CounterScreen(viewModel: CounterViewModel) {\n    val count by viewModel.count.collectAsState()\n    Column {\n        Text("Счёт: $count")\n        Button(onClick = { viewModel.increment() }) {\n            Text("+1")\n        }\n    }\n}\n')
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "function", "name": "CounterScreen", "paramTypes": ["CounterViewModel"], "returns": "Unit"},
    {"id": "collect", "type": "contains", "pattern": "viewModel\\.count\\.collectAsState\\s*\\(\\s*\\)", "message": "Подпишитесь на поток: viewModel.count.collectAsState()",
     "hint": "Чтение .value не подписывает экран на изменения"},
    {"id": "by", "hidden": True, "type": "contains", "pattern": "\\bval\\s+count\\s+by\\b", "message": "Объявите val count by viewModel.count.collectAsState()"},
    {"id": "noval", "hidden": True, "type": "not_contains", "pattern": "\\.count\\.value", "message": "Не читайте .value в функции интерфейса: экран не перерисуется"},
    {"id": "imp1", "hidden": True, "type": "contains", "pattern": "import\\s+androidx\\.compose\\.runtime\\.collectAsState\\b", "message": "Добавьте import androidx.compose.runtime.collectAsState"},
    {"id": "imp2", "hidden": True, "type": "contains", "pattern": "import\\s+androidx\\.compose\\.runtime\\.getValue\\b", "message": "Для by нужен import androidx.compose.runtime.getValue"},
], "jvm": {"main": "fun main() {\n    val vm = CounterViewModel()\n    println(stubs.ComposeLog.render { CounterScreen(vm) })\n    stubs.ComposeLog.click(0)\n    println(vm.count.value)\n}",
           "expected_stdout": "Column\n  Text(Счёт: 0)\n  Button\n    Text(+1)\n1"}}
a3 = asg("a3-collect", "fix", "Экран не обновляется",
         "Экран счётчика читает `viewModel.count.value` напрямую, поэтому после нажатия не перерисовывается: подписки на поток нет. Исправьте функцию `CounterScreen`: "
         "получите счёт через `val count by viewModel.count.collectAsState()` и добавьте импорты `collectAsState` и `getValue` из `androidx.compose.runtime`.",
         "Подписывать экран на StateFlow.", "—", "Первый показ: «Счёт: 0»; нажатие вызывает increment.",
         ["Класс CounterViewModel менять не нужно."],
         hints("Compose перерисовывает функцию, только когда меняется состояние Compose, а чтение .value потока таким состоянием не является.", "Поток нужно превратить в состояние Compose.",
               "Для этого у StateFlow есть функция collectAsState().", "Результат читают через by, как обычную переменную, поэтому нужен ещё один импорт.",
               "val count by viewModel.count.collectAsState() и импорты collectAsState и getValue."),
         t3, S3, "collectAsState подписывает экран на StateFlow и превращает его в состояние Compose. Когда ViewModel меняет значение, экран перерисуется.",
         ["Подписка collectAsState.", "by с нужными импортами.", "Нет чтения .value."],
         [(BAD3, "Ошибка осталась: .value не подписывает экран на изменения."),
          (HEAD3 + "import androidx.compose.runtime.collectAsState\n\n" + VMCODE + '@Composable\nfun CounterScreen(viewModel: CounterViewModel) {\n    val count = viewModel.count.collectAsState()\n    Column {\n        Text("Счёт: ${count.value}")\n        Button(onClick = { viewModel.increment() }) {\n            Text("+1")\n        }\n    }\n}\n', "Работает, но без by: объявите val count by … и импорт getValue."),
          (HEAD3 + "import androidx.compose.runtime.getValue\n\n" + VMCODE + '@Composable\nfun CounterScreen(viewModel: CounterViewModel) {\n    val count by viewModel.count\n    Column {\n        Text("Счёт: $count")\n    }\n}\n', "Нет collectAsState и кнопки.")],
         starter=BAD3)

# --- a4: predict ---
CODE4 = ('import kotlinx.coroutines.flow.MutableStateFlow\nimport kotlinx.coroutines.flow.update\n\ndata class Ui(val items: List<String>, val loading: Boolean)\n\n'
         'fun main() {\n    val state = MutableStateFlow(Ui(emptyList(), true))\n    state.update { it.copy(items = it.items + "хлеб") }\n'
         '    state.update { it.copy(items = it.items + "сыр", loading = false) }\n    val old = state.value\n    state.update { it.copy(items = emptyList()) }\n'
         '    println(old.items)\n    println(state.value.items.size)\n    println(state.value.loading)\n}\n')
ans4 = "[хлеб, сыр]\n0\nfalse"
a4 = asg("a4-predict", "predict", "Старое и новое состояние",
         "Что выведет программа? Каждая строка вывода — с новой строки (список печатается в квадратных скобках через запятую с пробелом).",
         "Понять, что update создаёт новое состояние, а старое остаётся прежним.", "—", "Три строки.", [],
         hints("update создаёт новое состояние через copy и не меняет старое.", "После двух update в списке две задачи, loading стал false.",
               "Переменная old хранит состояние на момент второго update.", "Третий update опустошает список в новом состоянии, а old остаётся прежним.",
               "Первая строка — старый список, вторая — размер нового списка, третья — loading."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "После двух update: [хлеб, сыр] и loading = false. old сохраняет это состояние, а третий update делает копию с пустым списком: размер 0, loading остаётся false.",
         ["Все три строки верны."],
         [("[]\n0\nfalse", "old — прежнее состояние: оно не изменилось третьим update."),
          ("[хлеб, сыр]\n2\nfalse", "Размер считается по новому состоянию: после третьего update список пуст."),
          ("[хлеб, сыр]\n0\ntrue", "Второй update поставил loading = false, и третий копирует это значение.")],
         code=CODE4)

skills = {"kt.viewmodel": "ViewModel и StateFlow", "kt.udf": "Однонаправленный поток данных", "kt.collect": "Подписка экрана на состояние"}
write_lesson("kt-07-viewmodel", "Kotlin: ViewModel и StateFlow",
             "Хранить состояние экрана во ViewModel, менять его через update и copy и подписывать экран через collectAsState.",
             list(skills), ["kt-06-state"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Публичный MutableStateFlow", "fix": "Сделайте его приватным (_state) и отдайте наружу StateFlow через asStateFlow()."},
              {"mistake": "Чтение .value в функции интерфейса", "fix": "Используйте by viewModel.state.collectAsState(): так экран перерисуется."},
              {"mistake": "Правка списка на месте", "fix": "Создавайте копию через copy и операцию +."},
              {"mistake": "Ссылки на экран во ViewModel", "fix": "ViewModel живёт дольше экрана: не храните View, Context активности и кнопки."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-07-viewmodel" not in data["lessons"]:
    data["lessons"].append("kt-07-viewmodel")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
