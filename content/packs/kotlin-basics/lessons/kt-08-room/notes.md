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
