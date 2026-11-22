import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.devtools.ksp")
    id("com.chaquo.python")
}

android {
    namespace = "app.codeacademy"
    compileSdk = 35
    // NDK и CMake — как в официальном примере llama.cpp для Android (llama.android).
    ndkVersion = "29.0.13113456"

    defaultConfig {
        applicationId = "app.codeacademy"
        minSdk = 26
        targetSdk = 35
        // Номер сборки CI: каждая новая версия ставится поверх предыдущей.
        val run = System.getenv("GITHUB_RUN_NUMBER")?.toIntOrNull() ?: 1
        versionCode = run
        // Сборка тега v1.2.3 получает версию 1.2.3 (CA_VERSION_NAME из CI); обычные сборки — 0.10.0-mvp.<номер>.
        versionName = System.getenv("CA_VERSION_NAME")?.takeIf { it.isNotBlank() } ?: "0.10.0-mvp.$run"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk {
            // arm64 — телефоны, x86_64 — эмулятор в CI.
            // caAbi=x86_64 (ORG_GRADLE_PROJECT_caAbi) — только для эмулятора в CI (вдвое быстрее сборка llama.cpp).
            abiFilters += (providers.gradleProperty("caAbi").orNull?.let { listOf(it) } ?: listOf("arm64-v8a", "x86_64"))
        }
        // ИИ-наставник: llama.cpp (исходники — tools/fetch-llama.sh, фиксированный коммит).
        externalNativeBuild {
            cmake {
                arguments += listOf("-DCMAKE_BUILD_TYPE=Release")
            }
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.31.6"
        }
    }

    packaging {
        jniLibs {
            // Варианты CPU-бэкенда ggml загружаются через dlopen из папки библиотек приложения:
            // библиотеки должны быть распакованы при установке (как в примере llama.android).
            useLegacyPackaging = true
        }
    }

    // Релизный ключ (этап 10): если заданы переменные окружения, релиз подписывается им,
    // иначе — постоянным ключом прототипа. Порядок и риски — docs/RELEASE.md.
    val releaseStoreFile = System.getenv("CA_RELEASE_KEYSTORE")?.takeIf { it.isNotBlank() }?.let { file(it) }
    val hasReleaseKey = releaseStoreFile != null && releaseStoreFile.isFile &&
        !System.getenv("CA_RELEASE_STORE_PASSWORD").isNullOrBlank() &&
        !System.getenv("CA_RELEASE_KEY_ALIAS").isNullOrBlank()

    signingConfigs {
        // Постоянный ключ прототипа (в репозитории, пароль «android», как у debug-ключа).
        // Без него CI каждый раз создавал новый debug-ключ, и новая версия не ставилась поверх старой.
        // Не для публикации в магазине: настоящий релизный ключ хранится только в секретах (docs/RELEASE.md).
        create("prototype") {
            storeFile = rootProject.file("signing/prototype.keystore")
            storePassword = "android"
            keyAlias = "codeacademy-proto"
            keyPassword = "android"
        }
        if (hasReleaseKey) {
            create("release") {
                storeFile = releaseStoreFile
                storePassword = System.getenv("CA_RELEASE_STORE_PASSWORD")
                keyAlias = System.getenv("CA_RELEASE_KEY_ALIAS")
                keyPassword = System.getenv("CA_RELEASE_KEY_PASSWORD")?.takeIf { it.isNotBlank() }
                    ?: System.getenv("CA_RELEASE_STORE_PASSWORD")
            }
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("prototype")
        }
        release {
            // R8 не включён сознательно: Chaquopy, Pyodide-мост, JNI и kotlinx.serialization требуют
            // отдельных правил, а выигрыш в размере мал (основной вес — модели и Python/Pyodide). См. TECHNICAL_DECISIONS.
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName(if (hasReleaseKey) "release" else "prototype")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    sourceSets {
        // Контент-пакеты курса (content/packs) попадают в assets/packs.
        getByName("main").assets.srcDir("../content")
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }

    androidResources {
        // WebAssembly и stdlib Pyodide читаются быстрее без сжатия в APK.
        noCompress += listOf("wasm", "zip")
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
}

chaquopy {
    defaultConfig {
        version = "3.13"
        // FastAPI для режима A (урок «Веб-API»). pydantic-core v2 (Rust) для Android недоступен,
        // поэтому pydantic 1.10 на чистом Python — версии подобраны зондом probe-fastapi.
        pip {
            install("fastapi==0.125.0")
            install("pydantic==1.10.27")
            install("httpx==0.28.1")
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.04.00")
    implementation(composeBom)
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.webkit:webkit:1.13.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.1")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
    implementation("androidx.navigation:navigation-compose:2.8.9")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.datastore:datastore-preferences:1.1.4")
    implementation("androidx.compose.material:material-icons-core")

    val room = "2.7.2"
    implementation("androidx.room:room-runtime:$room")
    implementation("androidx.room:room-ktx:$room")
    ksp("androidx.room:room-compiler:$room")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.1")

    debugImplementation("androidx.compose.ui:ui-test-manifest")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.room:room-testing:$room")

    androidTestImplementation(composeBom)
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test:rules:1.6.1")
    androidTestImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.1")
}
