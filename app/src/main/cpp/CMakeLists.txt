# Локальный ИИ-наставник: llama.cpp (MIT) + ядро наставника. Исходники llama.cpp — tools/fetch-llama.sh
# (фиксированный коммит), без сетевых функций (curl/openssl выключены).
cmake_minimum_required(VERSION 3.22.1)
project(codeacademy_mentor LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(LLAMA_DIR "${CMAKE_CURRENT_LIST_DIR}/llama.cpp" CACHE PATH "исходники llama.cpp")
if(NOT EXISTS "${LLAMA_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "Нет исходников llama.cpp в ${LLAMA_DIR}: выполните tools/fetch-llama.sh")
endif()

# Как в официальном примере llama.android: варианты CPU-бэкенда грузятся во время работы
# (ggml выбирает подходящий процессору: с dotprod/i8mm или базовый armv8).
set(BUILD_SHARED_LIBS ON CACHE BOOL "" FORCE)
set(GGML_BACKEND_DL ON CACHE BOOL "" FORCE)
set(GGML_CPU_ALL_VARIANTS ON CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_LLAMAFILE OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
if(ANDROID_ABI STREQUAL "arm64-v8a")
    set(GGML_SYSTEM_ARCH "ARM" CACHE STRING "" FORCE)
elseif(ANDROID_ABI STREQUAL "x86_64")
    set(GGML_SYSTEM_ARCH "x86" CACHE STRING "" FORCE)
endif()
set(LLAMA_CURL OFF CACHE BOOL "" FORCE)
set(LLAMA_OPENSSL OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_COMMON OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_APP OFF CACHE BOOL "" FORCE)
add_subdirectory("${LLAMA_DIR}" build-llama)

add_library(mentor SHARED mentor_core.cpp mentor_jni.cpp)
target_include_directories(mentor PRIVATE "${LLAMA_DIR}/include" "${LLAMA_DIR}/ggml/include")
target_link_libraries(mentor llama ggml android log)
# 16 КБ страницы (Android 15+)
target_link_options(mentor PRIVATE "-Wl,-z,max-page-size=16384")
