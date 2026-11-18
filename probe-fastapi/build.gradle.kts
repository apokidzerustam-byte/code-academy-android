import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

// -PfastapiSpec=v2 (по умолчанию: актуальный FastAPI + pydantic v2 с Rust-ядром)
// -PfastapiSpec=v2strict (требует pydantic>=2)
// -PfastapiSpec=v1 (запасной: FastAPI 0.99 + pydantic 1.10, чистый Python)
val spec = (findProperty("fastapiSpec") as String?) ?: "v2"

android {
    namespace = "app.codeacademy.probe"
    compileSdk = 35
    defaultConfig {
        applicationId = "app.codeacademy.probe"
        minSdk = 26
        targetSdk = 35
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }

chaquopy {
    defaultConfig {
        version = "3.13"
        pip {
            if (spec == "v1") {
                install("fastapi==0.99.1")
                install("pydantic==1.10.21")
                install("httpx==0.27.2")
                install("uvicorn==0.29.0")
            } else if (spec == "v2strict") {
                // Ожидаемо падает, если pydantic-core (Rust) недоступен для Android.
                install("pydantic>=2")
                install("fastapi")
                install("httpx")
                install("uvicorn")
            } else {
                install("fastapi")
                install("httpx")
                install("uvicorn")
            }
        }
    }
}

dependencies {
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test:runner:1.6.2")
}
