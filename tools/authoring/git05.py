from lib import *

begin_terminal()
scenes = [
 S("intro", "Git и GitHub", """
  До сих пор вся история хранилась на одном компьютере. Но разработка почти всегда командная, и код нужно где-то хранить
  общим. Для этого существуют удалённые репозитории. GitHub — это сервис, который хранит такие репозитории в интернете и
  добавляет к ним удобства: страницы проектов, обсуждения, проверку кода. Git и GitHub — не одно и то же. Git — программа
  для истории, а GitHub — один из мест, где эту историю можно хранить. Сегодня мы попробуем все основные операции с
  удалённым репозиторием, но обойдёмся без интернета: роль GitHub сыграет обычная папка.""",
  nt("**Git** — программа. **GitHub** — сервис для хранения Git-репозиториев. Удалённый репозиторий = *remote*", at="Git и GitHub — не одно")),
 S("remote", "Подключаем удалённый репозиторий", """
  Подготовим проект с одним коммитом. Затем создадим «сервер»: пустой репозиторий с ключом bare, в нём нет рабочих файлов,
  только история. Так устроены репозитории на GitHub. Подключаем его к проекту командой git remote add. Имя origin —
  общепринятое название основного удалённого репозитория. Команда git remote без параметров покажет подключённые.""",
  t("git init -q\necho \"Проект\" > README.md\ngit add README.md\ngit commit -q -m \"Первый коммит\"\n", at="Подготовим"), run("Подготовим"),
  t("git init --bare ../server.git\n", at="создадим «сервер»"), run("создадим «сервер»"),
  t("git remote add origin ../server.git\ngit remote\n", at="Подключаем"), run("Подключаем")),
 S("push", "Отправляем: git push", """
  Команда git push отправляет коммиты на сервер. При первой отправке указываем ключ u, который запоминает связь между
  локальной веткой и серверной. Дальше достаточно писать просто git push. Теперь история есть и на сервере: любой, у кого
  есть доступ, может её скачать.""",
  clr(), t("git push -u origin main\n", at="При первой"), run("При первой")),
 S("clone", "Скачиваем: git clone", """
  Чтобы получить копию чужого проекта, служит git clone. Укажем адрес сервера и имя папки для копии. Представим,
  что это компьютер коллеги: в его папке уже лежит весь проект вместе с историей. Перейдём туда командой cd и посмотрим
  историю.""",
  clr(), t("cd ..\ngit clone -q server.git colleague\ncd colleague\n", at="служит git clone"), run("Укажем"),
  t("ls\ngit log --oneline\n", at="посмотрим"), run("посмотрим")),
 S("pull", "Обмен изменениями", """
  Коллега сделал изменение и отправил его на сервер. Мы возвращаемся в свой проект и забираем новости командой git pull. Git
  скачивает чужие коммиты и сливает их в нашу ветку. Привычный ритм командной работы: перед началом работы делаем pull,
  после завершения — commit и push.""",
  clr(), t('echo "Строка от коллеги" >> README.md\ngit commit -q -am "Правка коллеги"\ngit push -q\n', at="Коллега сделал"), run("Коллега сделал"),
  t("cd ../project\ngit pull\ncat README.md\n", at="Мы возвращаемся"), run("Мы возвращаемся")),
 S("summary", "Итог", """
  Подведём итог. Remote — это удалённый репозиторий, у него есть имя, чаще всего origin. Git push отправляет коммиты, git pull
  забирает и сливает чужие, git clone создаёт полную копию. GitHub добавляет к этому веб-интерфейс и инструменты для командной
  работы. Для работы с настоящим GitHub понадобится интернет и аккаунт, но команды те же самые. Остался последний штрих:
  оформление проекта.""",
  nt("`git remote add origin адрес` · `git push -u origin main` · `git clone адрес папка` · `git pull`", at="Подведём итог")),
]

notes = """
# Удалённые репозитории

```bash
git remote add origin https://github.com/ваш-логин/проект.git
git push -u origin main    # первая отправка
git push                   # дальше — просто так
git clone адрес папка      # скачать проект
git pull                   # забрать чужие коммиты
```

В уроке вместо GitHub используется обычная папка (`git init --bare ../server.git`) — все команды работают так же.

## Ритм работы

1. Начало: `git pull`.
2. Работа: правки → `git add` → `git commit`.
3. Конец: `git push`.

## Запомните

1. `origin` — имя по умолчанию, не волшебное слово.
2. `-u` один раз связывает локальную ветку с серверной.
3. Для GitHub нужен аккаунт и токен доступа; пароль от аккаунта Git не принимает.
"""

SRV = "git init -q\necho a > a.txt\ngit add a.txt\ngit commit -q -m \"Первый\"\ngit init -q --bare ../server.git\n"
a1 = shell_predict("a1-remote", "Какие remote подключены", SRV + "git remote add origin ../server.git\ngit remote add backup ../server.git\ngit remote\ngit remote get-url backup\n",
  [("origin\nbackup\n../server.git", "git remote выводит имена в алфавитном порядке: backup идёт первым."), ("backup\norigin\nbackup", "Команда get-url выводит адрес, а не имя.")],
  hints("Подключены два удалённых репозитория.", "Команда git remote печатает только имена.", "Имена идут в алфавитном порядке.", "git remote get-url backup печатает адрес этого репозитория.", "Результат: backup, origin, затем адрес ../server.git."),
  "git remote показывает имена, git remote get-url имя — адрес.")

a2 = shell_cmd_task("a2-add", "Подключить сервер", "Адрес сервера — `../server.git`. Введите команду, которая **подключает его под именем `origin`** (`git remote add`, имя, адрес).",
  "git remote add origin ../server.git", SRV, "git remote get-url origin",
  [("git remote origin ../server.git", "Не хватает слова add."), ("git clone ../server.git", "Скачивает копию, а не подключает сервер к проекту."), ("git push origin ../server.git", "Отправка, а не настройка.")],
  hints("Подключением серверов занимается git remote.", "Нужно подкоманду add.", "После add — имя, затем адрес.", "Имя: origin; адрес: ../server.git.", "Ответ: git remote add origin ../server.git"),
  "git remote add имя адрес запоминает адрес под коротким именем.")

a3 = shell_cmd_task("a3-push", "Первая отправка", "Сервер `origin` уже подключён. Введите команду **первой отправки ветки `main` с запоминанием связи** (`git push`, ключ `-u`, `origin`, `main`).",
  "git push -u origin main", SRV + "git remote add origin ../server.git\n", "git rev-parse --abbrev-ref main@{upstream}",
  [("git push", "Нет связи с серверной веткой: Git не знает, куда отправлять."), ("git push origin main", "Отправляет, но без ключа -u связь не запоминается."), ("git pull origin main", "Скачивает, а не отправляет.")],
  hints("Отправляет коммиты команда git push.", "Ключ -u запоминает связь веток.", "После ключа: имя сервера и имя ветки.", "Имя сервера origin, ветка main.", "Ответ: git push -u origin main"),
  "С ключом -u дальше достаточно писать git push и git pull без аргументов.")

a4 = shell_cmd_task("a4-clone", "Скачать копию", "На сервере `../server.git` лежит проект. Введите команду, которая **клонирует его в новую папку `copy`** (`git clone`, адрес, имя папки).",
  "git clone ../server.git copy", SRV + "git remote add origin ../server.git\ngit push -q -u origin main\n", "ls copy",
  [("git clone ../server.git", "Копия окажется в папке server, а не copy."), ("git clone copy ../server.git", "Аргументы перепутаны местами."), ("git pull ../server.git copy", "pull не создаёт новую копию проекта.")],
  hints("Для копирования проекта есть git clone.", "Сначала указывают адрес, откуда качать.", "Потом — название папки для копии.", "Адрес ../server.git, папка copy.", "Ответ: git clone ../server.git copy"),
  "git clone адрес папка скачивает весь проект с историей и настраивает origin.")

a5 = shell_predict("a5-pull", "Обмен между двумя копиями", SRV + "git remote add origin ../server.git\ngit push -q -u origin main\ncd ..\ngit clone -q server.git other\ncd other\necho b > b.txt\ngit add b.txt\ngit commit -q -m \"Второй\"\ngit push -q\ncd ../project\ngit pull -q\ngit log --format=%s\nls\n",
  [("Первый\nВторой\na.txt\nb.txt", "Новейший коммит — первым: история идёт от свежего к старому."), ("Второй\nПервый\na.txt", "Файл b.txt тоже попал в проект после pull.")],
  hints("Вторая копия (other) делает коммит и отправляет его на сервер.", "Затем в первом проекте выполняется git pull.", "Pull приносит коммит «Второй» и файл b.txt.", "git log --format=%s показывает сообщения от нового к старому.", "Результат: Второй, Первый, a.txt, b.txt."),
  "git pull скачивает и сливает чужие коммиты; после него в проекте появляются файлы коллеги.")

mistakes = [
 {"mistake": "Пытаются запушить без аккаунта и токена на GitHub", "fix": "GitHub требует токен доступа вместо пароля; создайте его в настройках."},
 {"mistake": "Делают push, не сделав pull, когда коллега уже отправил изменения", "fix": "Сначала git pull, потом git push."},
 {"mistake": "Забывают ключ -u при первой отправке", "fix": "Один раз git push -u origin main, дальше — git push."},
 {"mistake": "Путают Git и GitHub", "fix": "Git работает и без GitHub; GitHub — лишь место хранения."}]

finish("git-05-remote", "Удалённые репозитории и GitHub", "Подключать удалённый репозиторий, отправлять изменения, клонировать и забирать чужие.",
  {"git.remote": "Remote и origin", "git.push": "git push и git pull", "git.clone": "git clone"},
  ["git-04-conflicts"], scenes, notes, [a1, a2, a3, a4, a5], mistakes, pack="git-github", runner="A")
