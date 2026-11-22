// CLI на том же ядре, что и приложение: для проверки наставника с настоящей моделью в CI (без Android).
// Использование: mentor_cli <model.gguf> [n_ctx] [max_tokens] < запросы
// Запросы разделяются строкой "<<<END>>>"; каждый ответ печатается и завершается строкой "<<<END>>>".
// Статистика — в stderr. Сеть не используется.
#include "llama.h"
#include "mentor_core.h"

#include <algorithm>
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>

static const char * SEP = "<<<END>>>";

static void quiet(ggml_log_level level, const char * text, void *) {
    if (level >= GGML_LOG_LEVEL_ERROR) fputs(text, stderr);
}

int main(int argc, char ** argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s model.gguf [n_ctx] [max_tokens] < prompts\n", argv[0]);
        return 2;
    }
    const int n_ctx = argc > 2 ? std::stoi(argv[2]) : 2048;
    const int max_tokens = argc > 3 ? std::stoi(argv[3]) : 200;
    llama_log_set(quiet, nullptr);
    llama_backend_init();
    mentor::Engine e;
    const int threads = std::max(1u, std::min(8u, std::thread::hardware_concurrency()));
    const std::string err = e.load(argv[1], n_ctx, static_cast<int>(threads));
    if (!err.empty()) {
        fprintf(stderr, "load error: %s\n", err.c_str());
        return 1;
    }
    fprintf(stderr, "model: %s, threads %d\n", e.description().c_str(), threads);
    std::string line, prompt;
    int n = 0;
    while (std::getline(std::cin, line)) {
        if (line != SEP) {
            prompt += line;
            prompt += '\n';
            continue;
        }
        if (!prompt.empty() && prompt.back() == '\n') prompt.pop_back();
        mentor::GenParams p;
        p.max_tokens = max_tokens;
        const mentor::GenStats st = e.generate(prompt, p, [](const std::string & piece) {
            fwrite(piece.data(), 1, piece.size(), stdout);
            return true;
        });
        printf("\n%s\n", SEP);
        fflush(stdout);
        fprintf(stderr, "#%d prompt=%d gen=%d prompt_ms=%.0f gen_ms=%.0f tok/s=%.1f %s\n", ++n, st.prompt_tokens,
                st.generated_tokens, st.prompt_ms, st.gen_ms,
                st.gen_ms > 0 ? st.generated_tokens * 1000.0 / st.gen_ms : 0.0, st.error.c_str());
        prompt.clear();
    }
    llama_backend_free();
    return 0;
}
