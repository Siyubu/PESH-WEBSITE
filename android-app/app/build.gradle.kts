import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.kapt")
}

// Release signing details live in android-app/keystore.properties (never committed; see README).
val keystoreProps = Properties().apply {
    val file = rootProject.file("keystore.properties")
    if (file.exists()) file.inputStream().use { load(it) }
}

// The server the release app talks to: ./gradlew assembleRelease -PPESH_API_BASE_URL=https://your-domain/api/
val apiBaseUrl: String = providers.gradleProperty("PESH_API_BASE_URL").orNull ?: "https://CHANGE-ME.example.com/api/"

android {
    namespace = "rw.pesh.enroll"
    compileSdk = 34

    defaultConfig {
        applicationId = "rw.pesh.enroll"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    signingConfigs {
        if (keystoreProps.isNotEmpty()) {
            create("release") {
                storeFile = rootProject.file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        debug {
            // Emulator's alias for the host machine, so it can reach a locally-run docker compose stack.
            buildConfigField("String", "DEFAULT_API_BASE_URL", "\"http://10.0.2.2:8000/api/\"")
        }
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("release")
            buildConfigField("String", "DEFAULT_API_BASE_URL", "\"$apiBaseUrl\"")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.1")
    implementation("androidx.activity:activity-compose:1.9.0")

    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    debugImplementation("androidx.compose.ui:ui-tooling")

    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    implementation("androidx.work:work-runtime-ktx:2.9.0")

    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
}

// Refuse to build a release that cannot work: no real server address, or one without HTTPS.
tasks.matching { it.name == "preReleaseBuild" }.configureEach {
    doFirst {
        require(!apiBaseUrl.contains("CHANGE-ME")) {
            "Set your server first: ./gradlew assembleRelease -PPESH_API_BASE_URL=https://your-domain/api/"
        }
        require(apiBaseUrl.startsWith("https://")) { "PESH_API_BASE_URL must start with https:// (got $apiBaseUrl)" }
        require(keystoreProps.isNotEmpty()) { "keystore.properties not found. See android-app/README.md (Releasing)." }
    }
}
