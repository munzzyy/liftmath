package io.github.munzzyy.liftmath

import android.annotation.SuppressLint
import android.content.Intent
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.util.TypedValue
import android.view.ViewGroup
import android.view.WindowManager
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.OnBackPressedCallback
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewAssetLoader
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import org.json.JSONObject

class MainActivity : ComponentActivity() {

    companion object {
        const val ASSET_HOST = "appassets.androidplatform.net"
        const val ORIGIN = "https://$ASSET_HOST"
        const val START_URL = "$ORIGIN/index.html"
        const val MAX_SHARE_CHARS = 4000

        // The page's JavaScript uses ?? (Chrome 80). Below 84 and 86 it only loses flex gap and the custom focus ring.
        const val MIN_WEBVIEW = 80
    }

    private lateinit var webView: WebView
    private lateinit var root: FrameLayout
    private var pageTheme: String? = null

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            window.isStatusBarContrastEnforced = false
            window.isNavigationBarContrastEnforced = false
        }

        root = FrameLayout(this)
        setContentView(root)
        applyChrome()

        // Inset the container, not the WebView: WebView padding moves its paint but not Chromium's hit-testing.
        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime(),
            )
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        // An old WebView can't parse the page's script and would open to tabs that do nothing.
        val webViewProblem = webViewProblem()
        if (webViewProblem != null) {
            root.addView(problemView(webViewProblem), matchParent())
            return
        }

        webView = WebView(this)
        webView.setBackgroundColor(Color.TRANSPARENT)
        root.addView(webView, matchParent())

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            allowFileAccessFromFileURLs = false
            allowUniversalAccessFromFileURLs = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
                WebSettingsCompat.setAlgorithmicDarkeningAllowed(this, false)
            }
        }

        if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(webView, "NativeApp", setOf(ORIGIN)) { _, message, _, isMainFrame, _ ->
                if (isMainFrame) handleMessage(message.data)
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest,
            ): WebResourceResponse? = assetLoader.shouldInterceptRequest(request.url)

            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest,
            ): Boolean {
                val url = request.url
                if (url.scheme == "https" && url.host == ASSET_HOST) return false
                runCatching { startActivity(Intent(Intent.ACTION_VIEW, url)) }
                return true
            }
        }

        webView.loadUrl(START_URL)

        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (webView.canGoBack()) {
                        webView.goBack()
                    } else {
                        isEnabled = false
                        onBackPressedDispatcher.onBackPressed()
                    }
                }
            },
        )
    }

    // Chrome/NN from the user agent, since some WebView packages number their own versions differently.
    private fun webViewProblem(): String? {
        val userAgent = try {
            WebSettings.getDefaultUserAgent(this)
        } catch (e: RuntimeException) {
            return getString(R.string.webview_missing)
        }
        val major = Regex("""Chrome/(\d+)""").find(userAgent)?.groupValues?.get(1)?.toIntOrNull() ?: return null
        return if (major < MIN_WEBVIEW) getString(R.string.webview_too_old, MIN_WEBVIEW, major) else null
    }

    private fun problemView(message: String): ScrollView {
        val pad = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, 24f, resources.displayMetrics).toInt()
        val title = TextView(this).apply {
            setTextAppearance(android.R.style.TextAppearance_Material_Headline)
            text = getString(R.string.webview_title)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 22f)
            setTypeface(typeface, Typeface.BOLD)
        }
        ViewCompat.setAccessibilityHeading(title, true)
        val body = TextView(this).apply {
            setTextAppearance(android.R.style.TextAppearance_Material_Body1)
            text = message
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 17f)
            setLineSpacing(0f, 1.3f)
            setPadding(0, pad / 2, 0, 0)
        }
        val column = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(pad, pad, pad, pad)
            addView(title)
            addView(body)
        }
        return ScrollView(this).apply {
            addView(column, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        }
    }

    private fun matchParent() =
        FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)

    // uiMode is in configChanges so a system theme flip keeps the WebView alive; repaint the chrome by hand.
    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        applyChrome()
    }

    private fun handleMessage(data: String?) {
        val msg = runCatching { JSONObject(data ?: return) }.getOrNull() ?: return
        when (msg.optString("type")) {
            "share" -> share(msg.optString("text"))
            "theme" -> {
                pageTheme = msg.optString("theme").takeIf { it == "dark" || it == "light" }
                applyChrome()
            }
            "keepAwake" -> if (msg.optBoolean("on")) {
                window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            } else {
                window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            }
        }
    }

    private fun share(text: String) {
        if (text.isBlank()) return
        val send = Intent(Intent.ACTION_SEND)
            .setType("text/plain")
            .putExtra(Intent.EXTRA_TEXT, text.take(MAX_SHARE_CHARS))
        runCatching { startActivity(Intent.createChooser(send, null)) }
    }

    private fun applyChrome() {
        val dark = when (pageTheme) {
            "dark" -> true
            "light" -> false
            else -> (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
                Configuration.UI_MODE_NIGHT_YES
        }
        root.setBackgroundColor(ContextCompat.getColor(this, if (dark) R.color.bg_dark else R.color.bg_light))
        WindowCompat.getInsetsController(window, root).apply {
            isAppearanceLightStatusBars = !dark
            isAppearanceLightNavigationBars = !dark
        }
    }
}
