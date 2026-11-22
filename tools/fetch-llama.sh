#!/usr/bin/env bash
# Исходники llama.cpp (MIT) для сборки наставника: фиксированный тег и коммит.
set -euo pipefail
TAG=b12628
COMMIT=8a97fa98ab1a454709bbf5ac979661feaeadec40
DST="$(cd "$(dirname "$0")/.." && pwd)/app/src/main/cpp/llama.cpp"
if [ -d "$DST/.git" ] && [ "$(git -C "$DST" rev-parse HEAD)" = "$COMMIT" ]; then echo "llama.cpp $TAG уже на месте"; exit 0; fi
rm -rf "$DST"
GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 --branch "$TAG" https://github.com/ggml-org/llama.cpp "$DST"
got=$(git -C "$DST" rev-parse HEAD)
[ "$got" = "$COMMIT" ] || { echo "llama.cpp $TAG: ожидался коммит $COMMIT, получен $got"; exit 1; }
echo "llama.cpp $TAG ($COMMIT)"
