#!/usr/bin/env bash
# Этап 9: наставник с настоящей моделью на Linux (то же ядро llama.cpp, что в приложении).
#  1) сборка mentor_cli; 2) загрузка моделей по ссылкам из каталога приложения, размер и SHA-256 (сверка с ModelHashes.kt);
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
const() { grep -oE "$1 = \"?[0-9a-f_]*L?\"?" "$HASHES" | sed -E 's/.*= "?([0-9a-f_]*)L?"?/\1/' | tr -d '_'; }
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
  # Пустые константы — ошибка: иначе проверка в приложении и здесь проходила бы вхолостую.
  if [ -z "$want_sha" ] || [ "${#want_sha}" != 64 ]; then echo "В ModelHashes.kt не задан $4 (нужно 64 hex-символа); фактический: $sha"; exit 1; fi
  if [ -z "$want_size" ] || [ "$want_size" = "0" ]; then echo "В ModelHashes.kt не задан $3; фактический: $size"; exit 1; fi
  if [ "$want_sha" != "$sha" ]; then echo "SHA-256 не совпадает с ModelHashes.kt"; exit 1; fi
  if [ "$want_size" != "$size" ]; then echo "Размер не совпадает с ModelHashes.kt"; exit 1; fi
}
: > "$ROOT/app/build/reports/mentor-hashes.md"
# Адрес берётся из каталога моделей приложения (ModelManager.kt): проверяется именно та ссылка, которую увидит ученик.
CATALOG="$ROOT/app/src/main/java/app/codeacademy/mentor/ModelManager.kt"
url_of() { grep -oE "https://huggingface.co/[^\"]*/$1" "$CATALOG" | head -n1; }
declare -A SIZE_OF=( [qwen2.5-coder-0.5b-instruct-q4_k_m.gguf]="SIZE_05B SHA_05B" [qwen2.5-coder-1.5b-instruct-q4_k_m.gguf]="SIZE_15B SHA_15B" \
  [Qwen3-1.7B-Q4_K_M.gguf]="SIZE_17B SHA_17B" [Qwen3-4B-Instruct-2507-Q4_K_M.gguf]="SIZE_4B SHA_4B" )
# Какие файлы скачивать и сверять (по умолчанию все); для проверки с моделью — тот, на котором идёт тест.
CHECK_FILES=${MENTOR_CHECK:-"qwen2.5-coder-0.5b-instruct-q4_k_m.gguf qwen2.5-coder-1.5b-instruct-q4_k_m.gguf Qwen3-1.7B-Q4_K_M.gguf Qwen3-4B-Instruct-2507-Q4_K_M.gguf"}
for f in $CHECK_FILES; do
  u=$(url_of "$f"); [ -n "$u" ] || { echo "в каталоге приложения нет ссылки на $f"; exit 1; }
  read -r sz sh <<< "${SIZE_OF[$f]}"
  check "$f" "$u" "$sz" "$sh"
done
PROVOKE=${MENTOR_PROVOKE:-qwen2.5-coder-0.5b-instruct-q4_k_m.gguf}
SUFFIX=${MENTOR_SUFFIX:-}   # nothink — для Qwen3 (пустой блок размышлений), как в приложении
export CA_MENTOR_SUFFIX="$SUFFIX"

echo "== Проверка CLI"
THINK=""; [ "$SUFFIX" = nothink ] && THINK=$'<think>\n\n</think>\n\n'
printf '<|im_start|>system\nОтвечай по-русски.<|im_end|>\n<|im_start|>user\nЧто такое переменная? Одно предложение.<|im_end|>\n<|im_start|>assistant\n%s\n<<<END>>>\n' "$THINK" \
  | "$CLI" "$MODELS/$PROVOKE" 4096 60

echo "== 20 провокаций с моделью $PROVOKE"
export CA_MENTOR_CLI="$CLI" CA_MENTOR_MODEL="$MODELS/$PROVOKE"
cd "$ROOT"
set +e
gradle --no-daemon :app:testDebugUnitTest --tests app.codeacademy.MentorModelTest -i > build/mentor-gradle.log 2>&1
rc=$?
set -e
grep -E "Заданий:|FAILED|PASSED|SKIPPED|AssertionError|утечки" build/mentor-gradle.log | head -40 || true
[ "$rc" = 0 ] || { tail -n 80 build/mentor-gradle.log; exit "$rc"; }
[ -s app/build/reports/mentor-cache.md ] && cat app/build/reports/mentor-cache.md
test -s app/build/reports/mentor-model.md || { echo "нет отчёта — тест не выполнился"; exit 1; }
grep -q "Утечек решения после защиты: 0" app/build/reports/mentor-model.md || { echo "есть утечки"; exit 1; }
