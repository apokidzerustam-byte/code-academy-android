// Ядро локального ИИ-наставника: llama.cpp без сети, один поток генерации.
// Используется и в приложении (через JNI, процесс :mentor), и в CLI для проверки в CI — один и тот же код.
#pragma once

#include <atomic>
#include <cstdint>
#include <functional>
#include <string>

struct llama_model;
struct llama_context;
struct llama_sampler;

namespace mentor {

struct GenParams {
    int max_tokens = 256;
    float temperature = 0.3f;
    float top_p = 0.9f;
    int top_k = 40;
    float repeat_penalty = 1.1f;
    uint32_t seed = 42;
};

struct GenStats {
    int prompt_tokens = 0;
    int generated_tokens = 0;
    double prompt_ms = 0;
    double gen_ms = 0;
    bool stopped = false;   // остановлено извне (кнопка «Стоп», нагрев)
    bool truncated = false; // упёрлись в max_tokens
    std::string error;
};

/** Принимает кусок текста (всегда целые символы UTF-8). Вернуть false — прекратить генерацию. */
using PieceCallback = std::function<bool(const std::string &)>;

/** Сколько байт в начале s образуют целые символы UTF-8 (хвост — начало многобайтного символа). */
size_t utf8_complete_prefix(const std::string & s);

class Engine {
public:
    Engine() = default;
    ~Engine();
    Engine(const Engine &) = delete;
    Engine & operator=(const Engine &) = delete;

    /** Загрузить модель GGUF. n_ctx — окно контекста в токенах. Возвращает пустую строку или текст ошибки. */
    std::string load(const std::string & path, int n_ctx, int n_threads);

    /** Генерация продолжения prompt (уже размеченного шаблоном чата). Потокобезопасна только stop(). */
    GenStats generate(const std::string & prompt, const GenParams & params, const PieceCallback & on_piece);

    /** Запросить остановку текущей генерации (из любого потока). */
    void stop() { stop_.store(true); }

    bool loaded() const { return ctx_ != nullptr; }
    int n_ctx() const { return n_ctx_; }
    std::string description() const;

private:
    llama_model * model_ = nullptr;
    llama_context * ctx_ = nullptr;
    int n_ctx_ = 0;
    std::atomic<bool> stop_{false};
    static bool abort_cb(void * data);
};

} // namespace mentor
