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

    defaultConfig {
        applicationId = "app.codeacademy"
        minSdk = 26
        targetSdk = 35
        // Номер сборки CI: каждая новая версия ставится поверх предыдущей.
        val run = System.getenv("GITHUB_RUN_NUMBER")?.toIntOrNull() ?: 1
        versionCode = run
        versionName = "0.0.8-proto.$run"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk {
            // arm64 — телефоны, x86_64 — эмулятор в CI.
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    signingConfigs {
        // Постоянный ключ прототипа (в репозитории, пароль «android», как у debug-ключа).
        // Без него CI каждый раз создавал новый debug-ключ, и новая версия не ставилась поверх старой.
        // Не для публикации в магазине: релизный ключ будет храниться в GitHub Secrets (этап 11).
        create("prototype") {
            storeFile = rootProject.file("signing/prototype.keystore")
            storePassword = "android"
            keyAlias = "codeacademy-proto"
            keyPassword = "android"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("prototype")
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("prototype")
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
