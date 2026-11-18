package app.codeacademy.content

/** 15 этапов программы из раздела 3 ТЗ. Уроки этапа появляются по мере выпуска контент-пакетов. */
object Curriculum {
    data class Stage(val number: Int, val title: String, val topics: String)

    val stages = listOf(
        Stage(1, "Введение в IT", "Компьютеры, алгоритмы, исходный код, frontend и backend, мышление разработчика"),
        Stage(2, "Подготовка Android", "Файлы, терминал, Python, редактор, библиотеки, Git — всё на телефоне"),
        Stage(3, "Python", "Переменные, условия, циклы, функции, файлы, ООП, JSON, HTTP"),
        Stage(4, "Алгоритмы и структуры данных", "Big O, поиск, сортировка, рекурсия, стек, очередь, деревья, графы"),
        Stage(5, "Git и GitHub", "Репозитории, commit, branch, merge, конфликты, README"),
        Stage(6, "HTML и CSS", "Семантика, формы, Flexbox, Grid, адаптивность, доступность"),
        Stage(7, "JavaScript", "Функции, DOM, события, Promise, async/await, fetch, модули"),
        Stage(8, "Backend и FastAPI", "HTTP, REST, маршруты, валидация, аутентификация, JWT"),
        Stage(9, "Базы данных", "SQL, JOIN, индексы, нормализация, транзакции, SQLite"),
        Stage(10, "Архитектура ПО", "Слои, MVC, MVVM, Clean Architecture, SOLID, DI"),
        Stage(11, "Кибербезопасность", "Модель угроз, SQL Injection, XSS, CSRF, хеширование, секреты"),
        Stage(12, "Тестирование и отладка", "Traceback, unit/integration/E2E, Pytest, Mock"),
        Stage(13, "Android-разработка", "Kotlin, Compose, Coroutines, ViewModel, Room, APK"),
        Stage(14, "Профессиональная разработка", "Code Review, рефакторинг, CI/CD, подпись APK"),
        Stage(15, "Финальный проект", "От идеи и ТЗ до APK и документации"),
    )
}
