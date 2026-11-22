#!/usr/bin/env bash
# Запуск инструментальных тестов на эмуляторе с сохранением замеров (CAPROBE) для отчёта.
# Использование: ci/emulator-tests.sh <gradle-task> [доп. аргументы gradle]
set -u
mkdir -p build/ci
adb logcat -G 16M || true
adb logcat -c || true
gradle --no-daemon "$@"
rc=$?
# Этап 8: резервная копия переживает настоящее «Очистить данные» (pm clear).
if [ "$rc" = 0 ]; then
  bash ci/backup-clear-test.sh 2>&1 | tee build/ci/backup-clear.log
  rc=${PIPESTATUS[0]}
fi
# Этап 9: настоящая модель наставника на устройстве (если CI её скачал).
if [ "$rc" = 0 ] && [ -n "${CA_MENTOR_MODEL:-}" ]; then
  bash ci/mentor-device-test.sh 2>&1 | tee build/ci/mentor-device.log
  rc=${PIPESTATUS[0]}
fi
# Этап 10: холодный старт и память (замер, не проверка; сбой замера сборку не валит).
if [ "$rc" = 0 ] && [ -f app/build/outputs/apk/debug/app-debug.apk ]; then
  bash ci/startup-measure.sh app/build/outputs/apk/debug/app-debug.apk 2>&1 | tee -a build/ci/startup-run.log
fi
adb logcat -d -s CAPROBE:I CAPROBE:E CAPLAYER:I CAPLAYER:W > build/ci/probe.log || true
adb logcat -d '*:E' | tail -n 400 > build/ci/errors.log || true
echo "exit code: $rc" >> build/ci/probe.log
echo "===== CAPROBE ====="
cat build/ci/probe.log
echo "===== ERRORS (runner/binder) ====="
grep -iE "codeacademy|binder|Transaction|FATAL|signal" build/ci/errors.log | tail -60
echo "===== TEST FAILURES (TestRunner, первые строки стека) ====="
adb logcat -d -s TestRunner:E | grep -vE "^\s*$" | grep -vE "\sat (androidx|java|kotlin|org\.junit|android)\." | head -n 150 || true
echo "===== CRASHES (AndroidRuntime / WebView) ====="
adb logcat -d -s AndroidRuntime:E cr_AwContents:W cr_AwRenderProcessGoneDetail:W chromium:E | grep -vE "^\s*$" | tail -n 60 || true
echo "===== FAILED TESTS ====="
grep -rhoE '<testcase [^>]*name="[^"]*"[^>]*>[[:space:]]*<failure message="[^"]{0,400}' */build/outputs/androidTest-results 2>/dev/null | head -40
exit $rc
