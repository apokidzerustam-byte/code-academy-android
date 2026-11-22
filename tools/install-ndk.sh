#!/usr/bin/env bash
# NDK и CMake для llama.cpp (версии как в примере llama.android).
# `yes | sdkmanager` под `set -o pipefail` иногда завершается кодом 141 (SIGPIPE) уже после успешной установки,
# поэтому результат проверяется по наличию папок, а установка повторяется при сетевых сбоях.
set -u
SDK=${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}
NDK=29.0.13113456
CMAKE=3.31.6
ok() { [ -d "$SDK/ndk/$NDK" ] && [ -d "$SDK/cmake/$CMAKE" ]; }
[ -n "$SDK" ] || { echo "ANDROID_HOME не задан"; exit 1; }
ok && exit 0
for attempt in 1 2 3; do
  yes | "$SDK/cmdline-tools/latest/bin/sdkmanager" --install "ndk;$NDK" "cmake;$CMAKE" > /dev/null || true
  ok && { echo "NDK $NDK и CMake $CMAKE установлены"; exit 0; }
  echo "попытка $attempt не удалась, повтор через 10 с"; sleep 10
done
echo "не удалось установить NDK $NDK и CMake $CMAKE"
exit 1
