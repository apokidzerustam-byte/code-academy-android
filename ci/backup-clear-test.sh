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
}

echo "== Установка приложения и тестов"
gradle --no-daemon -q :app:installDebug :app:installDebugAndroidTest
echo "== Фаза 1: данные и копия"
phase 1
adb exec-out run-as $APP cat files/ci-backup.zip > "$TMP/backup.zip"
adb exec-out run-as $APP cat files/ci-dump.bin > "$TMP/dump.bin"
ls -l "$TMP"
test -s "$TMP/backup.zip" && test -s "$TMP/dump.bin"
unzip -l "$TMP/backup.zip"
echo "== pm clear: Android удаляет все данные приложения"
adb shell pm clear $APP
left=$(adb shell run-as $APP ls -A 2>/dev/null | tr -d '\r' | grep -vE '^(cache|code_cache)$' || true)
echo "после очистки в папке приложения: [${left}]"
[ -z "$left" ] || { echo "Данные не удалены"; exit 1; }
echo "== Возвращаем файл копии (как если бы ученик выбрал его в «Загрузках»)"
adb exec-in run-as $APP sh -c 'mkdir -p files && cat > files/ci-backup.zip' < "$TMP/backup.zip"
adb exec-in run-as $APP sh -c 'cat > files/ci-dump.bin' < "$TMP/dump.bin"
echo "== Фаза 2: данных нет → восстановление → сравнение байт в байт"
phase 2
echo "Резервная копия: экспорт → pm clear → импорт — данные совпали байт в байт"
