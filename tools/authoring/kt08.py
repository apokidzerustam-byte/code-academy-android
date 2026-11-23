"""Урок Kotlin 8: Room — локальная база данных: Entity, Dao, Database.
Код проверяется по заглушкам аннотаций Room (tools/kotlin-stubs/android): настоящая генерация кода и работа с SQLite в CI не участвуют."""
from mk import *


def L(code, text, n=1):
    lines = code.split("\n")
    i = next(k for k, ln in enumerate(lines) if text in ln)
    return list(range(i + 1, i + 1 + n))


IMP_E = "import androidx.room.Entity\nimport androidx.room.PrimaryKey\n"
K1 = IMP_E + ('\n@Entity(tableName = "tasks")\ndata class Task(\n    @PrimaryKey(autoGenerate = true) val id: Int = 0,\n    val title: String,\n    val done: Boolean = false\n)\n\n'
              'fun main() {\n    println(Task(title = "Купить хлеб"))\n}\n')
O1 = "Task(id=0, title=Купить хлеб, done=false)\n"
IMP_D = ("import androidx.room.Dao\nimport androidx.room.Delete\nimport androidx.room.Insert\nimport androidx.room.OnConflictStrategy\nimport androidx.room.Query\n"
         "import kotlinx.coroutines.flow.Flow\n")
K2 = IMP_D + ('\n@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks ORDER BY id")\n    fun observeAll(): Flow<List<Task>>\n\n'
              '    @Insert(onConflict = OnConflictStrategy.REPLACE)\n    suspend fun insert(task: Task)\n\n    @Delete\n    suspend fun delete(task: Task)\n}\n')
K3 = ('import androidx.room.Database\nimport androidx.room.RoomDatabase\n\n@Database(entities = [Task::class], version = 1)\nabstract class AppDatabase : RoomDatabase() {\n'
      '    abstract fun taskDao(): TaskDao\n}\n')
K4 = ('@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks WHERE done = :done ORDER BY id")\n    suspend fun byDone(done: Boolean): List<Task>\n\n'
      '    @Query("DELETE FROM tasks WHERE id = :id")\n    suspend fun deleteById(id: Int)\n}\n')

use_file("Main.kt")
scenes = [
    scene("intro", "Зачем приложению база данных", """
      Представьте записную книжку: вы закрыли её, положили в ящик, и завтра запись всё ещё на месте. Приложение закрывается, телефон перезагружается, а задачи пользователя должны остаться. Для этого данные надо где-то хранить. Для
      небольших настроек подходят простые пары ключ-значение, о них мы уже говорили. А для списков, у которых есть структура, например
      задач с названием и отметкой, нужна база данных. В Андроиде встроена база SQLite: это маленькая реляционная база в одном файле, внутри
      приложения. С её языком SQL вы знакомы по соответствующему этапу курса. Писать запросы и разбирать курсор вручную долго и легко
      ошибиться, поэтому Google сделал библиотеку Room. Вы описываете таблицы классами, а запросы пишете в аннотациях. Остальной код Room
      создаёт сам при сборке, и ошибки в запросах находятся ещё до запуска приложения.""",
          [NOTE("**Room** — надстройка над SQLite: таблицы — классы, запросы — аннотации, проверка запросов при сборке.", at="Google сделал"),
           NOTE("Три части: `@Entity` (таблица) · `@Dao` (запросы) · `@Database` (сама база)", at="Остальной код")]),
    scene("entity", "Entity: таблица как класс", """
      Первая часть называется Entity, то есть сущность. Это обычный класс данных, помеченный аннотацией Entity: каждый его экземпляр —
      одна строка таблицы, а каждое поле — столбец. Название таблицы задаём параметром tableName. У каждой строки должен быть уникальный
      ключ, его отмечают аннотацией PrimaryKey. Параметр autoGenerate просит базу выдавать номера самостоятельно: при вставке мы ставим ноль,
      а база подставит следующий свободный номер. Для остальных полей достаточно типа: строка, число, логическое значение. Запустим пример:
      новая задача, у которой номер пока ноль, а отметка выполнения ложь.""",
          [CLEAR(), T(K1, at="Первая часть"), HL(L(K1, "@Entity"), at="аннотацией Entity"), HL(L(K1, "@PrimaryKey"), at="отмечают аннотацией PrimaryKey"),
           HL(L(K1, "val title"), at="Для остальных полей"), RUN(at="Запустим пример"), OUT(O1, at="Запустим пример")]),
    scene("dao", "Dao: запросы к таблице", """
      Вторая часть называется Dao, объект доступа к данным. Это интерфейс: вы описываете функции, а реализацию Room напишет сама. Над функцией
      ставят аннотацию с её назначением. Query принимает обычный SQL: здесь мы выбираем все задачи по порядку номеров. Insert добавляет
      строку, а параметр onConflict говорит, что делать, если строка с таким ключом уже есть: REPLACE заменит её. Delete удаляет строку.
      Обратите внимание на слово suspend: Room не разрешает обращаться к базе из главного потока, поэтому функции записи объявляют как suspend
      и вызывают из корутин. Для чтения удобно возвращать Flow: каждый раз, когда таблица меняется, он присылает свежий список, и
      экран обновляется сам.""",
          [CLEAR(), T(K2, at="Вторая часть"), HL(L(K2, "@Query"), at="Query принимает"), HL(L(K2, "@Insert", 2), at="Insert добавляет"),
           HL(L(K2, "@Delete", 2), at="Delete удаляет"), HL(L(K2, "suspend fun insert"), at="слово suspend"), HL(L(K2, "Flow<List<Task>>"), at="возвращать Flow")]),
    scene("database", "Database: сама база", """
      Третья часть, сама база. Это абстрактный класс, который наследует RoomDatabase и помечен аннотацией Database. В аннотации перечисляют
      все сущности и указывают версию схемы. В теле класса по одной абстрактной функции на каждый Dao: через неё вы получаете доступ к
      запросам. Экземпляр базы создают один раз на всё приложение, вызовом Room databaseBuilder с контекстом, классом базы и именем файла.
      Создавать его заново на каждом экране нельзя: открытая база дорогая. Версию схемы увеличивают, когда меняется структура таблиц,
      например добавляется столбец. Тогда нужно описать миграцию: как перенести старые данные в новую структуру. Без неё Room не откроет
      базу и приложение упадёт.""",
          [CLEAR(), T(K3, at="Третья часть"), HL(L(K3, "@Database"), at="аннотацией Database"), HL(L(K3, "version = 1"), at="указывают версию"),
           HL(L(K3, "abstract fun taskDao"), at="по одной абстрактной функции")]),
    scene("params", "Параметры запросов", """
      В запросах часто нужны значения от программы, например какие задачи показать. Их передают через параметры функции и ссылаются на них в
      SQL двоеточием и именем. Важно, чтобы имя в запросе совпадало с именем параметра функции: двоеточие и done, а параметр тоже называется
      done. Если имена разные, Room сообщит об ошибке при сборке. Это ещё и защита от внедрения SQL: значения подставляются как данные, а не
      склеиваются со строкой запроса. Никогда не собирайте SQL из строк пользователя вручную. Вторая функция в примере удаляет строку
      по номеру: у запроса на удаление нет результата, поэтому функция ничего не возвращает.""",
          [CLEAR(), T(K4, at="В запросах часто"), HL(L(K4, ":done"), at="двоеточием и именем"), HL(L(K4, "suspend fun byDone"), at="параметр тоже называется"),
           HL(L(K4, "DELETE"), at="удаляет строку")]),
    scene("usage", "База, ViewModel и экран вместе", """
      Теперь соберём всё, что мы изучили, в одну цепочку. Экран показывает список и принимает нажатия. ViewModel держит состояние и запускает
      корутины. Dao достаёт и записывает данные. А база лежит в файле на телефоне. Когда пользователь нажимает кнопку добавления, экран
      сообщает ViewModel, та запускает корутину в своей области и вызывает insert у Dao. База меняется, поток чтения присылает новый список,
      и экран обновляется сам, ни одной строчки ручной перерисовки. Между ViewModel и Dao часто ставят ещё один слой, репозиторий. Он
      прячет, откуда данные: из базы, из сети или из памяти, и ViewModel не знает подробностей. Так приложение остаётся понятным даже тогда,
      когда растёт. Это называют многослойной архитектурой, и к ней мы вернёмся на отдельном этапе курса.""",
          [CLEAR(), NOTE("Экран → событие → **ViewModel** → `viewModelScope.launch { dao.insert(task) }`", at="Когда пользователь нажимает"),
           NOTE("**База** меняется → `Flow` присылает новый список → экран перерисован", at="поток чтения присылает"),
           NOTE("Репозиторий скрывает источник данных: база, сеть или память", at="часто ставят ещё один слой")]),
    scene("mistakes", "Типичные ошибки", """
      Четыре типичные ошибки. Первая: забыли PrimaryKey. Room не соберётся: у таблицы нет ключа. Вторая: функция записи без suspend и вызов из
      главного потока. Приложение упадёт с сообщением о доступе к базе из главного потока. Третья: имя параметра в SQL не совпадает с
      именем параметра функции. Четвёртая: поменяли поля сущности, но не подняли версию схемы и не написали миграцию. На телефоне, где
      уже стоит старая версия, приложение при запуске упадёт. Эти ошибки Room ловит при сборке или при первом запуске, и читать их надо
      внимательно: сообщения подробные.""",
          [NOTE("Ошибка 1: нет `@PrimaryKey` → таблицу нельзя собрать.", at="Первая"),
           NOTE("Ошибка 2: запрос без `suspend`/`Flow` из главного потока → падение.", at="Вторая"),
           NOTE("Ошибка 3: `:done` в SQL ≠ имя параметра функции → ошибка сборки.", at="Третья"),
           NOTE("Ошибка 4: изменили сущность без новой версии и миграции → падение у тех, у кого стоит старая база.", at="Четвёртая")]),
    scene("summary", "Итог", """
      Подведём итог. Room связывает три части. Entity описывает таблицу классом, у которого есть PrimaryKey. Dao описывает запросы интерфейсом: Query,
      Insert, Delete. Database собирает сущности и Dao в одну базу с версией. Запись делают в suspend-функциях, а читать удобно потоком Flow.
      Параметры запросов передают через двоеточие и имя. При изменении структуры повышают версию и пишут миграцию. В заданиях вы опишете
      сущность, напишете Dao и исправите запрос с неверным параметром. Критерий прохождения: решить не меньше трёх заданий из четырёх. Как и
      раньше, проверка идёт на компьютере по упрощённым аннотациям: настоящая работа Room с SQLite проверяется только в готовом проекте.""",
          [NOTE("`@Entity` + `@PrimaryKey` → таблица · `@Dao` + `@Query/@Insert/@Delete` → запросы · `@Database(entities, version)` → база", at="Подведём итог"),
           NOTE("Запись — `suspend`, чтение — `Flow`; `:имя` в SQL = имя параметра.", at="Запись делают")]),
]

notes = """
# Kotlin: Room — локальная база данных

Room — надстройка над SQLite: таблицы описывают классами, запросы — аннотациями, ошибки в запросах находятся при сборке.

```kotlin
@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val title: String,
    val done: Boolean = false
)

@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks ORDER BY id")
    fun observeAll(): Flow<List<Task>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(task: Task)

    @Delete
    suspend fun delete(task: Task)
}

@Database(entities = [Task::class], version = 1)
abstract class AppDatabase : RoomDatabase() {
    abstract fun taskDao(): TaskDao
}
```

| Аннотация | Роль |
|---|---|
| `@Entity` | класс = таблица, поле = столбец |
| `@PrimaryKey` | уникальный ключ строки (`autoGenerate` — номера выдаёт база) |
| `@Dao` | интерфейс с запросами |
| `@Query("SQL")` | запрос; параметры — `:имя` = имя параметра функции |
| `@Insert` / `@Delete` | вставка / удаление (`onConflict = REPLACE` заменяет строку с тем же ключом) |
| `@Database` | список сущностей и версия схемы |

- Запись — `suspend` или из корутины: Room запрещает доступ к базе из главного потока.
- Чтение удобно отдавать потоком `Flow<List<…>>`: экран обновится при изменении таблицы.
- Менять сущность без новой версии и миграции нельзя.
- Не собирайте SQL из пользовательских строк: передавайте значения параметрами.
- **Ограничение проверки:** в CI аннотации Room — упрощённые заглушки: проверяются синтаксис, типы и структура кода. Генерация реализации, проверка SQL и работа с настоящим SQLite проверяются только при сборке готового Android-проекта. На телефоне в приложении этот код не запускается.
"""

# --- a1: Entity ---
PRE1 = IMP_E + "\n"
S1 = PRE1 + '@Entity(tableName = "tasks")\ndata class Task(\n    @PrimaryKey(autoGenerate = true) val id: Int = 0,\n    val title: String,\n    val done: Boolean = false\n)\n'
t1 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "cls", "type": "class", "name": "Task"},
    {"id": "ent", "raw": True, "type": "contains", "pattern": "@Entity\\s*\\(\\s*tableName\\s*=\\s*\"tasks\"\\s*\\)\\s*data\\s+class\\s+Task\\b", "message": "Над классом: @Entity(tableName = \"tasks\"), класс — data class Task"},
    {"id": "pk", "type": "contains", "pattern": "@PrimaryKey\\s*\\(\\s*autoGenerate\\s*=\\s*true\\s*\\)\\s*val\\s+id\\s*:\\s*Int\\s*=\\s*0", "message": "Ключ: @PrimaryKey(autoGenerate = true) val id: Int = 0"},
    {"id": "title", "type": "contains", "pattern": "\\bval\\s+title\\s*:\\s*String\\b", "message": "Нужно поле val title: String"},
    {"id": "done", "type": "contains", "pattern": "\\bval\\s+done\\s*:\\s*Boolean\\s*=\\s*false\\b", "message": "Нужно поле val done: Boolean = false"},
], "jvm": {"main": "fun main() {\n    println(Task(title = \"хлеб\"))\n    println(Task(7, \"сыр\", true))\n}", "expected_stdout": "Task(id=0, title=хлеб, done=false)\nTask(id=7, title=сыр, done=true)"}}
a1 = asg("a1-entity", "write", "Таблица задач",
         "Опишите сущность Room: `data class Task` с аннотацией `@Entity(tableName = \"tasks\")`. Поля: `id: Int` (первичный ключ с автогенерацией, значение по умолчанию 0), "
         "`title: String` и `done: Boolean` (по умолчанию `false`). Все поля — `val`.",
         "Описать таблицу Room классом.", "—", "Task(title = «хлеб») → Task(id=0, title=хлеб, done=false).",
         ["Импорты Entity и PrimaryKey уже в шаблоне."],
         hints("Каждая строка таблицы — объект класса, каждый столбец — поле.", "Класс данных помечается аннотацией @Entity; имя таблицы задаёт tableName.",
               "У первичного ключа аннотация @PrimaryKey; параметр autoGenerate = true просит базу выдавать номера.", "Поле id имеет тип Int и значение по умолчанию 0, чтобы при вставке не указывать номер.",
               "Поля title и done: String и Boolean (по умолчанию false). Всё в круглых скобках после имени класса, через запятую."),
         t1, S1, "Entity превращает класс в таблицу tasks. PrimaryKey с autoGenerate позволяет базе выдавать номера, а значения по умолчанию удобны при создании новых задач.",
         ["@Entity с tableName.", "Ключ с autoGenerate.", "Поля title и done."],
         [(PRE1 + '@Entity(tableName = "tasks")\ndata class Task(\n    val id: Int = 0,\n    val title: String,\n    val done: Boolean = false\n)\n', "Нет @PrimaryKey: у таблицы не будет ключа."),
          (PRE1 + 'data class Task(\n    @PrimaryKey(autoGenerate = true) val id: Int = 0,\n    val title: String,\n    val done: Boolean = false\n)\n', "Нет @Entity: класс не станет таблицей."),
          (PRE1 + '@Entity(tableName = "tasks")\ndata class Task(\n    @PrimaryKey(autoGenerate = true) val id: Int = 0,\n    val title: String\n)\n', "Нет поля done.")],
         starter=PRE1 + "// Опишите сущность Task\n")

# --- a2: Dao ---
PRE2 = IMP_D + "\n" + 'data class Task(val id: Int = 0, val title: String, val done: Boolean = false)\n\n'
S2 = PRE2 + ('@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks ORDER BY id")\n    fun observeAll(): Flow<List<Task>>\n\n'
             '    @Insert(onConflict = OnConflictStrategy.REPLACE)\n    suspend fun insert(task: Task)\n\n    @Delete\n    suspend fun delete(task: Task)\n}\n')
t2 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "dao", "type": "contains", "pattern": "@Dao\\s+interface\\s+TaskDao\\b", "message": "Над интерфейсом TaskDao нужна аннотация @Dao"},
    {"id": "q", "raw": True, "type": "contains", "pattern": "@Query\\s*\\(\\s*\"SELECT\\s+\\*\\s+FROM\\s+tasks[^\"]*\"\\s*\\)\\s*fun\\s+observeAll\\s*\\(\\s*\\)\\s*:\\s*Flow\\s*<\\s*List\\s*<\\s*Task\\s*>\\s*>", "message": "Чтение: @Query(\"SELECT * FROM tasks …\") fun observeAll(): Flow<List<Task>>"},
    {"id": "ins", "type": "contains", "pattern": "@Insert\\s*\\(\\s*onConflict\\s*=\\s*OnConflictStrategy\\.REPLACE\\s*\\)\\s*suspend\\s+fun\\s+insert\\s*\\(\\s*task\\s*:\\s*Task\\s*\\)", "message": "Вставка: @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun insert(task: Task)"},
    {"id": "del", "type": "contains", "pattern": "@Delete\\s*suspend\\s+fun\\s+delete\\s*\\(\\s*task\\s*:\\s*Task\\s*\\)", "message": "Удаление: @Delete suspend fun delete(task: Task)"},
], "jvm": {"main": ("fun main() = kotlinx.coroutines.runBlocking {\n    val table = kotlinx.coroutines.flow.MutableStateFlow(emptyList<Task>())\n"
                    "    val dao = object : TaskDao {\n        override fun observeAll(): Flow<List<Task>> = table\n"
                    "        override suspend fun insert(task: Task) { table.value = table.value.filter { it.id != task.id } + task }\n"
                    "        override suspend fun delete(task: Task) { table.value = table.value - task }\n    }\n"
                    "    dao.insert(Task(1, \"хлеб\"))\n    dao.insert(Task(2, \"сыр\"))\n    dao.delete(Task(1, \"хлеб\"))\n    println(table.value)\n}"),
           "expected_stdout": "[Task(id=2, title=сыр, done=false)]"}}
a2 = asg("a2-dao", "write", "Dao задач",
         "Напишите интерфейс `TaskDao` с аннотацией `@Dao` и тремя функциями. `observeAll(): Flow<List<Task>>` — запрос `SELECT * FROM tasks ORDER BY id`. "
         "`suspend fun insert(task: Task)` — вставка с заменой при конфликте ключей (`onConflict = OnConflictStrategy.REPLACE`). `suspend fun delete(task: Task)` — удаление. Класс `Task` и импорты уже есть.",
         "Описать Dao: запрос, вставку и удаление.", "—", "Интерфейс из трёх функций; в проверке он реализуется в памяти.",
         ["Не добавляйте других функций."],
         hints("Dao — интерфейс с аннотацией @Dao; реализацию Room напишет сама.", "Запрос чтения — аннотация @Query с SQL; чтение удобно отдавать потоком Flow, он присылает новые списки при изменении таблицы.",
               "@Insert принимает параметр onConflict: стратегия REPLACE заменит строку с тем же ключом.", "Запись в базу не разрешена из главного потока, поэтому insert и delete объявляют suspend.",
               "@Delete suspend fun delete(task: Task) — и по такому же образцу insert; чтение — fun observeAll(): Flow<List<Task>>."),
         t2, S2, "@Query описывает чтение (в виде Flow, чтобы экран обновлялся), @Insert и @Delete — запись; их объявляют suspend, чтобы вызывать из корутин, а не из главного потока.",
         ["@Dao interface TaskDao.", "Запрос с Flow.", "Insert с REPLACE и Delete."],
         [(PRE2 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks ORDER BY id")\n    fun observeAll(): Flow<List<Task>>\n\n    @Insert\n    suspend fun insert(task: Task)\n\n    @Delete\n    suspend fun delete(task: Task)\n}\n', "У @Insert не задана стратегия конфликта: нужна REPLACE."),
          (PRE2 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks ORDER BY id")\n    fun observeAll(): List<Task>\n\n    @Insert(onConflict = OnConflictStrategy.REPLACE)\n    suspend fun insert(task: Task)\n\n    @Delete\n    suspend fun delete(task: Task)\n}\n', "Чтение должно возвращать Flow<List<Task>>."),
          (PRE2 + 'interface TaskDao {\n    @Query("SELECT * FROM tasks ORDER BY id")\n    fun observeAll(): Flow<List<Task>>\n\n    @Insert(onConflict = OnConflictStrategy.REPLACE)\n    suspend fun insert(task: Task)\n\n    @Delete\n    suspend fun delete(task: Task)\n}\n', "Нет аннотации @Dao над интерфейсом.")],
         starter=PRE2 + "// Напишите интерфейс TaskDao\n")

# --- a3: fix param name ---
PRE3 = ("import androidx.room.Dao\nimport androidx.room.Query\n\ndata class Task(val id: Int = 0, val title: String, val done: Boolean = false)\n\n")
BAD3 = PRE3 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks WHERE done = :isDone ORDER BY id")\n    suspend fun byDone(done: Boolean): List<Task>\n}\n'
S3 = PRE3 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks WHERE done = :done ORDER BY id")\n    suspend fun byDone(done: Boolean): List<Task>\n}\n'
t3 = {"kind": "kotlin", "cases": [
    {"id": "syntax", "type": "syntax"},
    {"id": "fn", "type": "contains", "pattern": "suspend\\s+fun\\s+byDone\\s*\\(\\s*done\\s*:\\s*Boolean\\s*\\)\\s*:\\s*List\\s*<\\s*Task\\s*>", "message": "Функция: suspend fun byDone(done: Boolean): List<Task> (имя параметра done)"},
    {"id": "bind", "raw": True, "type": "contains", "pattern": "WHERE\\s+done\\s*=\\s*:done\\b", "message": "В SQL ссылка на параметр должна называться так же, как параметр функции: :done",
     "hint": "Room: «Query method parameters should be bound… :isDone is not found»"},
    {"id": "nonconcat", "hidden": True, "raw": True, "type": "not_contains", "pattern": "\"\\s*\\+|\\+\\s*\"", "message": "Не склеивайте SQL из строк: используйте параметр запроса"},
], "jvm": {"main": "fun main() = kotlinx.coroutines.runBlocking {\n    val all = listOf(Task(1, \"хлеб\", true), Task(2, \"сыр\", false))\n    val dao = object : TaskDao {\n        override suspend fun byDone(done: Boolean): List<Task> = all.filter { it.done == done }\n    }\n    println(dao.byDone(false))\n}",
           "expected_stdout": "[Task(id=2, title=сыр, done=false)]"}}
a3 = asg("a3-bind", "fix", "Запрос с параметром",
         "Room не соберёт этот Dao: в SQL стоит ссылка `:isDone`, а параметр функции называется `done`. Исправьте запрос так, чтобы имена совпадали. "
         "Сигнатуру функции `byDone(done: Boolean): List<Task>` менять не нужно.",
         "Передавать параметры в запросы Room.", "—", "Запрос выбирает задачи по отметке done.",
         ["Не склеивайте SQL из строк."],
         hints("Room связывает параметры запроса с параметрами функции по имени.", "В запросе ссылка на параметр пишется с двоеточием.",
               "Сейчас в запросе :isDone, а у функции параметр done.", "Имена должны совпадать посимвольно.", "Замените :isDone на :done."),
         t3, S3, "Двоеточие и имя в SQL связывают значение с параметром функции. Имена должны совпадать, иначе Room выдаст ошибку при сборке.",
         ["Ссылка :done в запросе.", "Сигнатура не изменилась."],
         [(BAD3, "Ошибка осталась: :isDone не совпадает с именем параметра done."),
          (PRE3 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks WHERE done = :done ORDER BY id")\n    suspend fun byDone(isDone: Boolean): List<Task>\n}\n', "Теперь не совпадает имя параметра функции: он должен остаться done."),
          (PRE3 + '@Dao\ninterface TaskDao {\n    @Query("SELECT * FROM tasks WHERE done = " + "true")\n    suspend fun byDone(done: Boolean): List<Task>\n}\n', "Значение зашито в строку SQL: параметр не используется.")],
         starter=BAD3)

# --- a4: predict (REPLACE / IGNORE) ---
CODE4 = ('data class Task(val id: Int, val title: String)\n\nfun main() {\n    val table = mutableMapOf<Int, Task>()\n    fun insertReplace(t: Task) { table[t.id] = t }\n'
         '    fun insertIgnore(t: Task) { table.putIfAbsent(t.id, t) }\n    insertReplace(Task(1, "хлеб"))\n    insertReplace(Task(1, "сыр"))\n    insertIgnore(Task(1, "мёд"))\n'
         '    insertIgnore(Task(2, "чай"))\n    println(table.values.map { it.title })\n    println(table.size)\n}\n')
ans4 = "[сыр, чай]\n2"
a4 = asg("a4-predict", "predict", "Конфликт ключей",
         "Таблица моделируется словарём: ключ — `id`. `insertReplace` работает как `OnConflictStrategy.REPLACE`, а `insertIgnore` — как `IGNORE` (строка с занятым ключом не добавляется). Что выведет программа?",
         "Понять стратегии конфликта при вставке.", "—", "Две строки.", [],
         hints("Ключ в словаре — id: две вставки с одним id дают одну строку.", "insertReplace записывает значение по ключу, прежнее исчезает.",
               "После двух insertReplace для ключа 1 лежит «сыр».", "insertIgnore не меняет занятый ключ, но добавляет свободный.",
               "Первая строка — названия по порядку вставки ключей, вторая — число строк."),
         {"kind": "answer", "expected_answer": ans4}, ans4,
         "Для ключа 1 вторая замена оставляет «сыр»; insertIgnore с ключом 1 ничего не меняет, а с ключом 2 добавляет «чай». Итого два элемента: [сыр, чай].",
         ["Обе строки верны."],
         [("[хлеб, сыр, мёд, чай]\n4", "Ключ 1 один: строки с тем же id заменяют друг друга или игнорируются."),
          ("[хлеб, чай]\n2", "REPLACE заменяет прежнюю строку: для ключа 1 остаётся «сыр»."),
          ("[сыр, мёд, чай]\n3", "IGNORE не добавляет строку, если ключ занят.")],
         code=CODE4)

skills = {"kt.room.entity": "Room: Entity и PrimaryKey", "kt.room.dao": "Room: Dao и запросы", "kt.room.db": "Room: база, версии и миграции"}
write_lesson("kt-08-room", "Kotlin: Room — локальная база данных",
             "Описывать таблицы классами Entity, писать Dao с запросами и понимать роль Database, версии схемы и миграций.",
             list(skills), ["kt-07-viewmodel"], scenes, notes, [a1, a2, a3, a4],
             [{"mistake": "Нет @PrimaryKey", "fix": "У каждой сущности должен быть первичный ключ."},
              {"mistake": "Запись без suspend из главного потока", "fix": "Объявляйте функции записи suspend и вызывайте из корутины; чтение отдавайте Flow."},
              {"mistake": "Имя параметра в SQL не совпадает с параметром функции", "fix": "Ссылка :имя должна совпадать с именем параметра функции."},
              {"mistake": "Изменили сущность без миграции", "fix": "Увеличьте версию базы и опишите миграцию."}],
             min_pass=3, pack="kotlin-basics", runner="kotlin")
f = ROOT / "content/packs/kotlin-basics/pack.json"
data = json.loads(f.read_text("utf-8"))
if "kt-08-room" not in data["lessons"]:
    data["lessons"].append("kt-08-room")
data["skills"].update(skills)
f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
