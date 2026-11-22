#!/usr/bin/env bash
# Этап 9: настоящая модель на эмуляторе. Файл модели (CA_MENTOR_MODEL) кладётся в files/models
# приложения тем же путём, каким его скопирует приложение после выбора в «Загрузках».
set -euo pipefail
APP=app.codeacademy
RUNNER=app.codeacademy.test/androidx.test.runner.AndroidJUnitRunner
MODEL=${CA_MENTOR_MODEL:?путь к файлу модели}
NAME=$(basename "$MODEL")

echo "== Установка приложения и тестов"
gradle --no-daemon -q :app:installDebug :app:installDebugAndroidTest
echo "== Копирование модели ($(du -h "$MODEL" | cut -f1)) в files/models"
adb push "$MODEL" /data/local/tmp/ca-model.gguf >/dev/null
adb shell "run-as $APP mkdir -p files/models && cat /data/local/tmp/ca-model.gguf | run-as $APP sh -c 'cat > files/models/$NAME'"
adb shell rm /data/local/tmp/ca-model.gguf
got=$(adb shell "run-as $APP sh -c 'wc -c < files/models/$NAME'" | tr -d '\r ')
want=$(wc -c < "$MODEL" | tr -d ' ')
[ "$got" = "$want" ] || { echo "модель скопирована не полностью: $got из $want"; exit 1; }
echo "== Тест с моделью"
out=$(adb shell am instrument -w -e mentorModel "$NAME" -e class app.codeacademy.MentorOnDeviceTest#realModelOnDevice "$RUNNER" | tr -d '\r')
echo "$out"
echo "$out" | grep -q "^OK (1 test)" || { echo "тест с моделью не прошёл"; exit 1; }
[ "$(adb shell "run-as $APP cat files/ci-mentor.ok" 2>/dev/null | tr -d '\r')" = "ok" ] || { echo "тест с моделью не выполнился (нет отметки)"; exit 1; }
adb shell "run-as $APP sh -c 'rm -f files/models/* files/ci-mentor.ok cache/*.gguf'"
echo "Модель на устройстве: ответы получены, решение не выдано, сеть не использовалась"
