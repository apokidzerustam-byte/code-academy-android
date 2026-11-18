#!/usr/bin/env bash
# Запуск инструментальных тестов на эмуляторе с сохранением замеров (CAPROBE) для отчёта.
# Использование: ci/emulator-tests.sh <gradle-task> [доп. аргументы gradle]
set -u
mkdir -p build/ci
adb logcat -c || true
gradle --no-daemon "$@"
rc=$?
adb logcat -d -s CAPROBE:I > build/ci/probe.log || true
adb logcat -d '*:E' | tail -n 400 > build/ci/errors.log || true
echo "gradle exit code: $rc" >> build/ci/probe.log
exit $rc
