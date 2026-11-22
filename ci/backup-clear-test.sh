#!/usr/bin/env bash
# Критерий этапа 8 на настоящем «Очистить данные» Android:
#   фаза 1 — заполнить данные приложения и сохранить резервную копию + эталонный дамп;
#   pm clear — система удаляет ВСЕ данные приложения;
#   фаза 2 — убедиться, что данных нет, восстановить из копии и сравнить дамп байт в байт.
set -euo pipefail
APP=app.codeacademy
RUNNER=app.codeacademy.test/androidx.test.runner.AndroidJUnitRunner
CLS=app.codeacademy.BackupClearDataTest
TMP=$(mktemp -d)

phase() {
  local out
  out=$(adb shell am instrument -w -e backupPhase "$1" -e class "$CLS" "$RUNNER" | tr -d '\r')
  echo "$out"
  echo "$out" | grep -q "^OK (1 test)" || { echo "Фаза $1 не прошла"; exit 1; }
  # Пропущенный тест тоже даёт «OK»: фаза подтверждается своим файлом-отметкой.
  [ "$(adb shell "run-as $APP cat files/ci-phase$1.ok" 2>/dev/null | tr -d '\r')" = "ok" ] || { echo "Фаза $1 не выполнилась (нет отметки)"; exit 1; }
}

# Файл приложения → компьютер: exec-out на старых эмуляторах иногда обрывает поток — сверяем размер и повторяем.
pull() {
  local want got
  want=$(adb shell "run-as $APP sh -c 'wc -c < files/$1'" | tr -d '\r ')
  for i in 1 2 3 4 5; do
    adb exec-out run-as $APP cat "files/$1" > "$2"
    got=$(wc -c < "$2" | tr -d ' ')
    [ "$got" = "$want" ] && { echo "files/$1 → $got байт"; return 0; }
    echo "files/$1: получено $got из $want байт, повтор $i"
  done
  return 1
}
# Компьютер → файл приложения: через /data/local/tmp и конвейер в run-as (exec-in на API 29 не работает).
push() {
  adb push "$1" /data/local/tmp/ca-transfer >/dev/null
  adb shell "run-as $APP mkdir -p files && cat /data/local/tmp/ca-transfer | run-as $APP sh -c 'cat > files/$2'"
  adb shell rm /data/local/tmp/ca-transfer
  local got want
  got=$(adb shell "run-as $APP sh -c 'wc -c < files/$2'" | tr -d '\r ')
  want=$(wc -c < "$1" | tr -d ' ')
  echo "на устройстве files/$2: $got байт"
  [ "$got" = "$want" ] || { echo "файл $2 не скопирован ($got из $want)"; exit 1; }
}

echo "== Установка приложения и тестов"
gradle --no-daemon -q :app:installDebug :app:installDebugAndroidTest
echo "== Фаза 1: данные и копия"
phase 1
pull ci-backup.zip "$TMP/backup.zip"
pull ci-dump.bin "$TMP/dump.bin"
ls -l "$TMP"/backup.zip "$TMP"/dump.bin
test -s "$TMP/backup.zip" && test -s "$TMP/dump.bin"
unzip -l "$TMP/backup.zip"
echo "== pm clear: Android удаляет все данные приложения"
adb shell pm clear $APP
listing=$(adb shell "run-as $APP ls -A; echo rc=\$?" | tr -d '\r')
echo "$listing" | grep -q "^rc=0$" || { echo "run-as не работает: $listing"; exit 1; }
left=$(echo "$listing" | grep -vE '^(cache|code_cache|rc=0)$' || true)
echo "после очистки в папке приложения: [${left}]"
[ -z "$left" ] || { echo "Данные не удалены"; exit 1; }
echo "== Возвращаем файл копии (как если бы ученик выбрал его в «Загрузках»)"
push "$TMP/backup.zip" ci-backup.zip
push "$TMP/dump.bin" ci-dump.bin
echo "== Фаза 2: данных нет → восстановление → сравнение байт в байт"
phase 2
echo "Резервная копия: экспорт → pm clear → импорт — данные совпали байт в байт"
