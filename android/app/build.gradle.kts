plugins {
    // AGP 9 ships built-in Kotlin support; no separate Kotlin plugin wanted.
    id("com.android.application") version "9.3.0"
}

android {
    namespace = "io.github.munzzyy.liftmath"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.munzzyy.liftmath"
        minSdk = 24
        targetSdk = 36
        versionCode = 20500
        versionName = "2.5.0"
    }

    buildTypes {
        release {
            // Unsigned on purpose: F-Droid signs with its own key.
            isMinifyEnabled = false
            isShrinkResources = false
            vcsInfo.include = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencyLocking {
    lockAllConfigurations()
}

// The web app IS the app. Every build syncs ../../web into assets so the
// wrapper can never drift from what the site serves. sw.js stays out: WebView
// never wires up service worker interception and the assets are already local.
val syncWebAssets = tasks.register<Sync>("syncWebAssets") {
    val webDir = rootProject.layout.projectDirectory.dir("../web")
    from(webDir) {
        exclude("sw.js")
    }
    into(layout.buildDirectory.dir("webassets"))
}

android.sourceSets["main"].assets.srcDir(layout.buildDirectory.dir("webassets").get().asFile)

tasks.named("preBuild") {
    dependsOn(syncWebAssets)
}

dependencies {
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.activity:activity-ktx:1.11.0")
    implementation("androidx.webkit:webkit:1.14.0")
}
