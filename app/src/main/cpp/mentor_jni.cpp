// JNI для app.codeacademy.mentor.NativeLlm. Работает только в процессе :mentor (MentorService):
// падение или нехватка памяти при работе модели не роняют основное приложение.
#include <jni.h>
#include <android/log.h>

#include <memory>
#include <string>
#include <thread>

#include "ggml-backend.h"
#include "llama.h"
#include "mentor_core.h"
#include "mentor_text.h"

#define TAG "CodeAcademyMentor"

namespace {

std::string to_utf8(JNIEnv * env, jstring s) {
    if (!s) return "";
    const jsize n = env->GetStringLength(s);
    const jchar * chars = env->GetStringChars(s, nullptr);
    std::string out = mentor::utf16_to_utf8(reinterpret_cast<const char16_t *>(chars), static_cast<size_t>(n));
    env->ReleaseStringChars(s, chars);
    return out;
}

jstring to_java(JNIEnv * env, const std::string & s) {
    const std::u16string u = mentor::utf8_to_utf16(s);
    return env->NewString(reinterpret_cast<const jchar *>(u.data()), static_cast<jsize>(u.size()));
}

void throw_state(JNIEnv * env, const std::string & msg) {
    jclass cls = env->FindClass("java/lang/IllegalStateException");
    if (cls) env->ThrowNew(cls, msg.c_str());
}

void log_cb(ggml_log_level level, const char * text, void *) {
    if (level >= GGML_LOG_LEVEL_WARN) __android_log_print(ANDROID_LOG_WARN, TAG, "%s", text);
}

mentor::Engine * engine(jlong h) { return reinterpret_cast<mentor::Engine *>(h); }

} // namespace

extern "C" JNIEXPORT void JNICALL
Java_app_codeacademy_mentor_NativeLlm_00024Init_nativeInit(JNIEnv * env, jclass, jstring libDir) {
    llama_log_set(log_cb, nullptr);
    const std::string dir = to_utf8(env, libDir);
    // Варианты CPU-бэкенда (с dotprod/i8mm и без) лежат рядом с библиотекой; ggml выбирает подходящий процессору.
    ggml_backend_load_all_from_path(dir.c_str());
    llama_backend_init();
}

extern "C" JNIEXPORT jlong JNICALL
Java_app_codeacademy_mentor_NativeLlm_00024Init_nativeLoad(JNIEnv * env, jclass, jstring path, jint nCtx, jint nThreads) {
    auto e = std::make_unique<mentor::Engine>();
    const std::string err = e->load(to_utf8(env, path), nCtx, nThreads);
    if (!err.empty()) {
        throw_state(env, err);
        return 0;
    }
    __android_log_print(ANDROID_LOG_INFO, TAG, "модель загружена: %s", e->description().c_str());
    return reinterpret_cast<jlong>(e.release());
}

extern "C" JNIEXPORT jstring JNICALL
Java_app_codeacademy_mentor_NativeLlm_nativeDescribe(JNIEnv * env, jobject, jlong h) {
    return to_java(env, h ? engine(h)->description() : "");
}

extern "C" JNIEXPORT jstring JNICALL
Java_app_codeacademy_mentor_NativeLlm_nativeGenerate(JNIEnv * env, jobject, jlong h, jstring prompt, jint maxTokens,
                                                    jfloat temperature, jint seed, jobject callback) {
    if (!h) { throw_state(env, "модель не загружена"); return nullptr; }
    jclass cbCls = env->GetObjectClass(callback);
    jmethodID onPiece = env->GetMethodID(cbCls, "onPiece", "(Ljava/lang/String;)Z");
    if (!onPiece) return nullptr;
    mentor::GenParams p;
    p.max_tokens = maxTokens;
    p.temperature = temperature;
    p.seed = static_cast<uint32_t>(seed);
    const mentor::GenStats st = engine(h)->generate(to_utf8(env, prompt), p, [&](const std::string & piece) {
        jstring js = to_java(env, piece);
        const jboolean go = env->CallBooleanMethod(callback, onPiece, js);
        env->DeleteLocalRef(js);
        if (env->ExceptionCheck()) return false;
        return go == JNI_TRUE;
    });
    if (env->ExceptionCheck()) return nullptr;
    const std::string json = std::string("{\"promptTokens\":") + std::to_string(st.prompt_tokens) +
        ",\"generatedTokens\":" + std::to_string(st.generated_tokens) +
        ",\"promptMs\":" + std::to_string(static_cast<long>(st.prompt_ms)) +
        ",\"genMs\":" + std::to_string(static_cast<long>(st.gen_ms)) +
        ",\"stopped\":" + (st.stopped ? "true" : "false") +
        ",\"truncated\":" + (st.truncated ? "true" : "false") + "}";
    if (!st.error.empty()) { throw_state(env, st.error); return nullptr; }
    return to_java(env, json);
}

extern "C" JNIEXPORT void JNICALL
Java_app_codeacademy_mentor_NativeLlm_nativeStop(JNIEnv *, jobject, jlong h) {
    if (h) engine(h)->stop();
}

extern "C" JNIEXPORT void JNICALL
Java_app_codeacademy_mentor_NativeLlm_nativeFree(JNIEnv *, jobject, jlong h) {
    delete engine(h);
}
