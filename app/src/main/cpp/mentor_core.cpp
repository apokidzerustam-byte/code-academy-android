#include "mentor_core.h"

#include "llama.h"

#include <algorithm>
#include <chrono>
#include <vector>

namespace mentor {

namespace {
double now_ms() {
    using namespace std::chrono;
    return duration<double, std::milli>(steady_clock::now().time_since_epoch()).count();
}

void batch_set(llama_batch_ext * batch, const llama_token * tokens, int32_t n, llama_pos pos0, bool logits_last) {
    llama_batch_ext_clear(batch);
    for (int32_t i = 0; i < n; ++i) {
        const int32_t idx = llama_batch_ext_add_token(batch, 0, tokens[i]);
        const llama_pos pos = pos0 + i;
        llama_batch_ext_set_pos(batch, idx, &pos);
    }
    if (logits_last && n > 0) llama_batch_ext_set_output_logits(batch, n - 1, true);
}
} // namespace

size_t utf8_complete_prefix(const std::string & s) {
    // Идём с конца: если последний символ начат, но не закончен — отрезаем его начало.
    const size_t n = s.size();
    size_t i = n;
    int back = 0;
    while (i > 0 && back < 4) {
        const auto c = static_cast<unsigned char>(s[i - 1]);
        if ((c & 0xC0) != 0x80) { // начало символа (или ASCII)
            size_t len = 1;
            if ((c & 0xE0) == 0xC0) len = 2;
            else if ((c & 0xF0) == 0xE0) len = 3;
            else if ((c & 0xF8) == 0xF0) len = 4;
            return (n - (i - 1) >= len) ? n : i - 1;
        }
        --i;
        ++back;
    }
    return n; // некорректная последовательность — отдаём как есть
}

Engine::~Engine() {
    if (ctx_) llama_free(ctx_);
    if (model_) llama_model_free(model_);
}

bool Engine::abort_cb(void * data) {
    return static_cast<Engine *>(data)->stop_.load();
}

std::string Engine::load(const std::string & path, int n_ctx, int n_threads, int n_threads_batch) {
    cached_.clear();
    if (ctx_) { llama_free(ctx_); ctx_ = nullptr; }
    if (model_) { llama_model_free(model_); model_ = nullptr; }
    llama_model_params mp = llama_model_default_params();
    mp.n_gpu_layers = 0; // только CPU: предсказуемо на любом телефоне
    model_ = llama_model_load_from_file(path.c_str(), mp);
    if (!model_) return "не удалось загрузить модель (файл повреждён или не GGUF)";
    llama_context_params cp = llama_context_default_params();
    cp.n_ctx = static_cast<uint32_t>(n_ctx);
    cp.n_batch = static_cast<uint32_t>(n_ctx);
    cp.n_ubatch = 512;
    cp.n_threads = n_threads;
    cp.n_threads_batch = n_threads_batch;
    cp.no_perf = true;
    cp.abort_callback = &Engine::abort_cb;
    cp.abort_callback_data = this;
    ctx_ = llama_init_from_model(model_, cp);
    if (!ctx_) {
        llama_model_free(model_);
        model_ = nullptr;
        return "не хватило памяти для контекста модели";
    }
    n_ctx_ = n_ctx;
    n_threads_ = n_threads;
    n_threads_batch_ = n_threads_batch;
    return "";
}

std::string Engine::system_info() {
    const char * s = llama_print_system_info();
    return s ? std::string(s) : std::string();
}

std::string Engine::description() const {
    if (!model_) return "";
    char buf[256];
    const int n = llama_model_desc(model_, buf, sizeof(buf));
    std::string d = n > 0 ? std::string(buf, std::min<int>(n, sizeof(buf) - 1)) : "";
    return d + " | потоки " + std::to_string(n_threads_) + "/" + std::to_string(n_threads_batch_);
}

GenStats Engine::generate(const std::string & prompt, const GenParams & p, const PieceCallback & on_piece) {
    GenStats st;
    if (!ctx_) { st.error = "модель не загружена"; return st; }
    stop_.store(false);
    const llama_vocab * vocab = llama_model_get_vocab(model_);

    const int n_prompt = -llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()), nullptr, 0, true, true);
    std::vector<llama_token> tokens(std::max(n_prompt, 1));
    if (llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()), tokens.data(),
                       static_cast<int32_t>(tokens.size()), true, true) < 0) {
        st.error = "не удалось разбить запрос на токены";
        return st;
    }
    st.prompt_tokens = n_prompt;
    const int budget = std::min(p.max_tokens, n_ctx_ - n_prompt - 1);
    if (budget <= 0) { st.error = "запрос не помещается в контекст модели"; return st; }

    llama_sampler * smpl = llama_sampler_chain_init(llama_sampler_chain_default_params());
    llama_sampler_chain_add(smpl, llama_sampler_init_penalties(llama_vocab_n_tokens(vocab), 64, p.repeat_penalty, 0.0f, 0.0f));
    if (p.temperature <= 0.0f) {
        llama_sampler_chain_add(smpl, llama_sampler_init_greedy());
    } else {
        llama_sampler_chain_add(smpl, llama_sampler_init_top_k(p.top_k));
        llama_sampler_chain_add(smpl, llama_sampler_init_top_p(p.top_p, 1));
        llama_sampler_chain_add(smpl, llama_sampler_init_temp(p.temperature));
        llama_sampler_chain_add(smpl, llama_sampler_init_dist(p.seed));
    }
    llama_batch_ext * batch = llama_batch_ext_init(ctx_);

    // Общее начало с прошлым запросом (системные правила, условие задания) уже посчитано — берём из памяти контекста.
    // Последний токен запроса пересчитывается всегда: по нему получают вероятности первого токена ответа.
    llama_memory_t mem = llama_get_memory(ctx_);
    int keep = 0;
    const int limit = std::min<int>(static_cast<int>(cached_.size()), n_prompt - 1);
    while (keep < limit && cached_[keep] == tokens[keep]) ++keep;
    if (keep > 0 && !llama_memory_seq_rm(mem, 0, keep, -1)) keep = 0;
    if (keep == 0) llama_memory_clear(mem, true);
    cached_.clear(); // пока идёт вычисление, содержимое памяти не соответствует никакому запросу
    st.prompt_cached = keep;

    double t0 = now_ms();
    batch_set(batch, tokens.data() + keep, n_prompt - keep, keep, true);
    int rc = llama_process(ctx_, LLAMA_PROCESS_TYPE_DECODE, batch);
    st.prompt_ms = now_ms() - t0;
    std::string pending; // байты незавершённого символа UTF-8
    int pos = n_prompt;
    t0 = now_ms();
    if (rc == 2 || stop_.load()) st.stopped = true;
    else if (rc != 0) st.error = "ошибка вычисления запроса (" + std::to_string(rc) + ")";
    while (st.error.empty() && !st.stopped) {
        if (st.generated_tokens >= budget) { st.truncated = true; break; }
        llama_token tok = llama_sampler_sample(smpl, ctx_, -1);
        if (llama_vocab_is_eog(vocab, tok)) break;
        char buf[256];
        const int n = llama_token_to_piece(vocab, tok, buf, sizeof(buf), 0, false);
        if (n < 0) { st.error = "ошибка преобразования токена"; break; }
        pending.append(buf, n);
        st.generated_tokens++;
        const size_t ok = utf8_complete_prefix(pending);
        if (ok > 0) {
            if (!on_piece(pending.substr(0, ok))) { st.stopped = true; break; }
            pending.erase(0, ok);
        }
        if (stop_.load()) { st.stopped = true; break; }
        batch_set(batch, &tok, 1, pos++, true);
        rc = llama_process(ctx_, LLAMA_PROCESS_TYPE_DECODE, batch);
        if (rc == 2) { st.stopped = true; break; }
        if (rc != 0) { st.error = "ошибка генерации (" + std::to_string(rc) + ")"; break; }
    }
    if (!pending.empty() && st.error.empty() && !st.stopped) on_piece(pending);
    st.gen_ms = now_ms() - t0;
    // Запрос остаётся в кэше (ответ из памяти убирается); после остановки или ошибки память очищается целиком.
    if (st.error.empty() && !st.stopped && llama_memory_seq_rm(mem, 0, n_prompt, -1)) cached_.assign(tokens.begin(), tokens.begin() + n_prompt);
    else llama_memory_clear(mem, true);
    llama_batch_ext_free(batch);
    llama_sampler_free(smpl);
    return st;
}

} // namespace mentor
