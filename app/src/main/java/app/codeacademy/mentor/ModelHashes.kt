package app.codeacademy.mentor

// Размер и SHA-256 официальных GGUF-файлов Qwen (Hugging Face, Qwen/Qwen2.5-Coder-*-Instruct-GGUF, ветка main).
// Измерены в CI по скачанным файлам 22.11.2026; job «Наставник с моделью» (ci/mentor-model-test.sh) сверяет их при каждой сборке.
internal const val SIZE_05B = 491_400_064L
internal const val SHA_05B = "1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"
internal const val SIZE_15B = 1_117_320_768L
internal const val SHA_15B = "cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046"
