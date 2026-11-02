package com.yoezel.cleanframe;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Full-screen WebView showing the CleanFrame page from assets, with a small bridge for launching apps. */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        web.setFocusable(true);
        web.setFocusableInTouchMode(true);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        // Fire TV runs at 2x density; lay the page out at 1920 CSS px so CleanFrame's own fit() sees the full screen.
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setSupportZoom(false);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);  // Everything is local except the small weather request.
        web.setWebViewClient(new WebViewClient());
        web.addJavascriptInterface(new Bridge(), "CleanFrameAndroid");
        web.setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
        setContentView(web);
        web.loadUrl("file:///android_asset/www/index.html");
        web.requestFocus();
        startService(new Intent(this, HomeWatcher.class));
    }

    /* The Fire TV remote's Back reaches the page as CleanFrame's own Back; it never leaves the launcher. */
    @Override
    public boolean dispatchKeyEvent(KeyEvent e) {
        int code = e.getKeyCode();
        if (code == KeyEvent.KEYCODE_BACK || code == KeyEvent.KEYCODE_MENU) {
            if (e.getAction() == KeyEvent.ACTION_UP)
                web.evaluateJavascript("window.ShoreQA && window.ShoreQA.nav('back')", null);
            return true;
        }
        return super.dispatchKeyEvent(e);
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
        web.requestFocus();
        HomeWatcher.coverDone();
    }

    @Override
    protected void onPause() {
        // The Home helper shows this picture the instant Home is pressed, until CleanFrame is back.
        try {
            if (web.getWidth() > 0) {
                // Half resolution keeps the cover at ~1 MB; it is only on screen for a few seconds.
                Bitmap b = Bitmap.createBitmap(web.getWidth() / 2, web.getHeight() / 2, Bitmap.Config.RGB_565);
                Canvas c = new Canvas(b);
                c.scale(0.5f, 0.5f);
                web.draw(c);
                HomeWatcher.snapshot = b;
                HomeWatcher.snapshotReady();
            }
        } catch (Throwable t) { /* Keep the previous snapshot. */ }
        web.onPause();
        super.onPause();
    }

    private boolean start(Intent i) {
        if (i == null) return false;
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        try { startActivity(i); return true; } catch (Exception e) { return false; }
    }

    private Intent launchIntent(String pkg) {
        PackageManager pm = getPackageManager();
        Intent i = pm.getLeanbackLaunchIntentForPackage(pkg);
        return i != null ? i : pm.getLaunchIntentForPackage(pkg);
    }

    class Bridge {
        @JavascriptInterface
        public boolean launch(String pkg) { return start(launchIntent(pkg)); }

        /* Opens Amazon's own home screen without the Home button watcher bouncing it back. */
        @JavascriptInterface
        public boolean fireHome() {
            HomeWatcher.allowAmazonHome(120000);
            Intent i = new Intent(Intent.ACTION_MAIN);
            i.setPackage(HomeWatcher.AMAZON_LAUNCHER);
            i.addCategory(Intent.CATEGORY_HOME);
            return start(i) || start(launchIntent(HomeWatcher.AMAZON_LAUNCHER));
        }

        @JavascriptInterface
        public boolean settings() {
            HomeWatcher.allowAmazonHome(600000);
            return start(new Intent(android.provider.Settings.ACTION_SETTINGS)) || start(launchIntent("com.amazon.tv.settings"));
        }

        /** Installed apps with a TV or phone launcher entry, as JSON [{id, name}]. */
        @JavascriptInterface
        public String apps() {
            PackageManager pm = getPackageManager();
            Set<String> seen = new HashSet<String>();
            JSONArray out = new JSONArray();
            String[] cats = { Intent.CATEGORY_LEANBACK_LAUNCHER, Intent.CATEGORY_LAUNCHER };
            try {
                for (String cat : cats) {
                    Intent q = new Intent(Intent.ACTION_MAIN);
                    q.addCategory(cat);
                    List<ResolveInfo> list = pm.queryIntentActivities(q, 0);
                    for (ResolveInfo r : list) {
                        ApplicationInfo a = r.activityInfo.applicationInfo;
                        if (getPackageName().equals(a.packageName) || !seen.add(a.packageName)) continue;
                        JSONObject o = new JSONObject();
                        o.put("id", a.packageName);
                        o.put("name", String.valueOf(r.loadLabel(pm)));
                        out.put(o);
                    }
                }
            } catch (Exception e) { /* An empty list is reported to the page as no apps. */ }
            return out.toString();
        }
    }
}
