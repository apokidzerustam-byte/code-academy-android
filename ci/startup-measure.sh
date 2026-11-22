#!/usr/bin/env bash
# Холодный старт и память приложения на эмуляторе (ТЗ §19: время запуска, ОЗУ).
# Это цифры эмулятора x86_64 без GPU, а не телефона: они ловят регрессии, но не заменяют замер на устройстве.
# Использование: ci/startup-measure.sh <apk> → build/ci/startup.log. Сбой замера не валит сборку (только запись в лог).
set -u
APK=${1:?укажите APK}
PKG=app.codeacademy
mkdir -p build/ci
LOG=build/ci/startup.log
: > "$LOG"
say() { echo "$*" | tee -a "$LOG"; }

adb install -r "$APK" >/dev/null 2>&1 || { say "ЗАМЕР НЕ УДАЛСЯ: APK не установился"; exit 0; }
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS >/dev/null 2>&1 || true

times=()
for i in 1 2 3 4 5; do
  adb shell am force-stop "$PKG"; sleep 2
  out=$(adb shell am start -W -n "$PKG/.MainActivity" 2>&1 | tr -d '\r')
  t=$(echo "$out" | sed -n 's/^TotalTime: *//p')
  st=$(echo "$out" | sed -n 's/^Status: *//p')
  say "запуск $i: TotalTime=${t:-?} мс, Status=${st:-?}"
  [ -n "$t" ] && times+=("$t")
  sleep 3
done

if [ "${#times[@]}" -gt 0 ]; then
  sorted=($(printf '%s\n' "${times[@]}" | sort -n))
  median=${sorted[$(( ${#sorted[@]} / 2 ))]}
  say "холодный старт: медиана ${median} мс, лучший ${sorted[0]} мс, худший ${sorted[-1]} мс (эмулятор, debug-сборка)"
  [ "$median" -gt 10000 ] && say "ВНИМАНИЕ: медиана выше 10 с (на эмуляторе без GPU)"
else
  say "ЗАМЕР НЕ УДАЛСЯ: нет значений TotalTime"
fi

sleep 5
mem=$(adb shell dumpsys meminfo "$PKG" 2>&1 | tr -d '\r')
pss=$(echo "$mem" | grep -oE "TOTAL PSS: *[0-9]+" | head -1 | grep -oE "[0-9]+$")
[ -z "$pss" ] && pss=$(echo "$mem" | awk '$1=="TOTAL" && $2 ~ /^[0-9]+$/ {print $2; exit}')
if [ -n "$pss" ]; then say "память после запуска (PSS, все процессы приложения): $((pss / 1024)) МБ"; else say "ЗАМЕР НЕ УДАЛСЯ: нет строки TOTAL в meminfo"; fi
say "процессов приложения: $(adb shell ps -A 2>/dev/null | grep -c "$PKG")"
adb shell am force-stop "$PKG"
exit 0
