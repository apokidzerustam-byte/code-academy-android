#!/usr/bin/env bash
# Этап 9: наставник с настоящей моделью на Linux (то же ядро llama.cpp, что в приложении).
#  1) сборка mentor_cli; 2) загрузка официальных GGUF Qwen2.5-Coder, размер и SHA-256 (сверка с ModelHashes.kt);
#  3) JVM-тест MentorModelTest: 20 провокаций × задания, ответы модели проходят защиту.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
MODELS=${CA_MODELS_DIR:-$HOME/models}
mkdir -p "$MODELS" "$ROOT/app/build/reports"
bash "$ROOT/tools/fetch-llama.sh"
cmake -S "$ROOT/tools/mentor-cli" -B "$ROOT/build/mentor-cli" -G Ninja -DCMAKE_BUILD_TYPE=Release > /dev/null
cmake --build "$ROOT/build/mentor-cli" --target mentor_cli -j "$(nproc)" | tail -n 2
CLI="$ROOT/build/mentor-cli/mentor_cli"

HASHES="$ROOT/app/src/main/java/app/codeacademy/mentor/ModelHashes.kt"
const() { grep -oE "$1 = \"?[0-9a-f]*L?\"?" "$HASHES" | sed -E 's/.*= "?([0-9a-f]*)L?"?/\1/'; }
check() { # имя_файла url SIZE_CONST SHA_CONST
  local f="$MODELS/$1"
  if [ ! -s "$f" ]; then
    echo "== Загрузка $1"
    curl -fL --retry 3 -o "$f.part" "$2" && mv "$f.part" "$f"
  fi
  local size sha want_size want_sha
  size=$(stat -c %s "$f"); sha=$(sha256sum "$f" | cut -d' ' -f1)
  want_size=$(const "$3"); want_sha=$(const "$4")
  echo "МОДЕЛЬ $1: размер $size, sha256 $sha (в приложении: $want_size / ${want_sha:-не задан})"
  echo "- \`$1\`: $size байт, SHA-256 \`$sha\`" >> "$ROOT/app/build/reports/mentor-hashes.md"
  if [ -n "$want_sha" ] && [ "$want_sha" != "$sha" ]; then echo "SHA-256 не совпадает с ModelHashes.kt"; exit 1; fi
  if [ "$want_size" != "0" ] && [ -n "$want_size" ] && [ "$want_size" != "$size" ]; then echo "Размер не совпадает с ModelHashes.kt"; exit 1; fi
}
: > "$ROOT/app/build/reports/mentor-hashes.md"
HF=https://huggingface.co/Qwen
check qwen2.5-coder-0.5b-instruct-q4_k_m.gguf "$HF/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf" SIZE_05B SHA_05B
check qwen2.5-coder-1.5b-instruct-q4_k_m.gguf "$HF/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" SIZE_15B SHA_15B

echo "== Проверка CLI"
printf '<|im_start|>system\nОтвечай по-русски.<|im_end|>\n<|im_start|>user\nЧто такое переменная? Одно предложение.<|im_end|>\n<|im_start|>assistant\n\n<<<END>>>\n' \
  | "$CLI" "$MODELS/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf" 2048 60

echo "== 20 провокаций с моделью 0.5B"
export CA_MENTOR_CLI="$CLI" CA_MENTOR_MODEL="$MODELS/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"
cd "$ROOT"
set +e
gradle --no-daemon :app:testDebugUnitTest --tests app.codeacademy.MentorModelTest -i > build/mentor-gradle.log 2>&1
rc=$?
set -e
grep -E "Заданий:|FAILED|PASSED|SKIPPED|AssertionError|утечки" build/mentor-gradle.log | head -40 || true
[ "$rc" = 0 ] || { tail -n 80 build/mentor-gradle.log; exit "$rc"; }
test -s app/build/reports/mentor-model.md || { echo "нет отчёта — тест не выполнился"; exit 1; }
grep -q "Утечек решения после защиты: 0" app/build/reports/mentor-model.md || { echo "есть утечки"; exit 1; }
