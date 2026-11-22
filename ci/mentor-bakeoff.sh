#!/usr/bin/env bash
# Сравнение моделей наставника на реальных запросах (один запуск — одна модель).
# Переменные: BAKE_NAME — короткое имя; BAKE_URLS — адреса GGUF через пробел (пробуются по порядку); BAKE_SUFFIX — nothink или -.
# Печатает размер и SHA-256 файла (для ModelHashes.kt), затем ответы модели, скорость и число токенов запроса.
set -euo pipefail
: "${BAKE_NAME:?}" "${BAKE_URLS:?}"
SUFFIX=${BAKE_SUFFIX:--}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
MODELS=${CA_MODELS_DIR:-$HOME/models}
mkdir -p "$MODELS" "$ROOT/app/build/reports"
bash "$ROOT/tools/fetch-llama.sh"
cmake -S "$ROOT/tools/mentor-cli" -B "$ROOT/build/mentor-cli" -G Ninja -DCMAKE_BUILD_TYPE=Release > /dev/null
cmake --build "$ROOT/build/mentor-cli" --target mentor_cli -j "$(nproc)" | tail -n 2
CLI="$ROOT/build/mentor-cli/mentor_cli"

FILE="$MODELS/$BAKE_NAME.gguf"
if [ ! -s "$FILE" ]; then
  for url in $BAKE_URLS; do
    echo "== Загрузка $url"
    if curl -fL --retry 3 -o "$FILE.part" "$url"; then mv "$FILE.part" "$FILE"; break; fi
    repo=$(echo "$url" | sed -E 's#https://huggingface.co/([^/]+/[^/]+)/resolve/.*#\1#')
    echo "не скачалось; файлы в репозитории $repo:"
    curl -fsSL "https://huggingface.co/api/models/$repo" | python3 -c "import sys,json; print('\n'.join(s['rfilename'] for s in json.load(sys.stdin).get('siblings',[])))" || true
  done
fi
mkdir -p "$ROOT/app/build/reports"
if [ ! -s "$FILE" ]; then
  echo "МОДЕЛЬ $BAKE_NAME: не скачана ни по одному адресу" | tee "$ROOT/app/build/reports/mentor-bakeoff.md"
  exit 0
fi
SIZE=$(stat -c %s "$FILE"); SHA=$(sha256sum "$FILE" | cut -d' ' -f1)
echo "МОДЕЛЬ $BAKE_NAME: размер $SIZE, sha256 $SHA"
echo "- \`$BAKE_NAME\`: $SIZE байт, SHA-256 \`$SHA\`" > "$ROOT/app/build/reports/mentor-hashes.md"

cd "$ROOT"
export CA_MENTOR_CLI="$CLI" CA_BAKEOFF="$BAKE_NAME|$FILE|$SUFFIX"
set +e
gradle --no-daemon :app:testDebugUnitTest --tests app.codeacademy.MentorBakeoffTest -i > build/bakeoff-gradle.log 2>&1
rc=$?
set -e
echo "== Итог сравнения"
cat app/build/reports/mentor-bakeoff.md 2>/dev/null || { echo "нет отчёта"; tail -n 60 build/bakeoff-gradle.log; }
echo "== Журнал CLI (последние строки)"
tail -n 30 "app/build/reports/mentor-cli-$BAKE_NAME.log" 2>/dev/null || true
if [ -s app/build/reports/mentor-bakeoff.md ]; then
  { echo "### $BAKE_NAME"; cat app/build/reports/mentor-hashes.md; } >> "${GITHUB_STEP_SUMMARY:-/dev/null}" || true
fi
exit "$rc"
