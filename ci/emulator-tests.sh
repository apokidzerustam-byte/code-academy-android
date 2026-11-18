#!/usr/bin/env bash
# Запуск инструментальных тестов на эмуляторе с сохранением замеров (CAPROBE) для отчёта.
# Использование: ci/emulator-tests.sh <gradle-task> [доп. аргументы gradle]
set -u
mkdir -p build/ci
adb logcat -G 16M || true
adb logcat -c || true
gradle --no-daemon "$@"
rc=$?
adb logcat -d -s CAPROBE:I CAPROBE:E CAPLAYER:I CAPLAYER:W > build/ci/probe.log || true
adb logcat -d '*:E' | tail -n 400 > build/ci/errors.log || true
echo "gradle exit code: $rc" >> build/ci/probe.log
echo "===== CAPROBE ====="
cat build/ci/probe.log
echo "===== ERRORS (runner/binder) ====="
grep -iE "codeacademy|binder|Transaction|FATAL|signal" build/ci/errors.log | tail -60
echo "===== TEST FAILURES (TestRunner, первые строки стека) ====="
adb logcat -d -s TestRunner:E | grep -vE "^\s*$" | grep -vE "\sat (androidx|java|kotlin|org\.junit|android)\." | head -n 150 || true
echo "===== FAILED TESTS ====="
grep -rhoE '<testcase [^>]*name="[^"]*"[^>]*>[[:space:]]*<failure message="[^"]{0,400}' */build/outputs/androidTest-results 2>/dev/null | head -40
exit $rc
