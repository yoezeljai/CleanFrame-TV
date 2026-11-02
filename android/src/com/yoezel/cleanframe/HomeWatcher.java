package com.yoezel.cleanframe;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;

import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * Fire OS has no default-launcher setting, and Fire OS 5 won't enable a third-party
 * accessibility service. Instead this service follows the system log (READ_LOGS is granted
 * once over adb). When the Home intent starts Amazon's launcher it immediately covers the
 * screen with the last snapshot of CleanFrame, then asks for CleanFrame itself. Android
 * holds background activity starts for ~5 s after Home, so the snapshot (which swallows
 * remote keys) bridges that gap and is removed once CleanFrame resumes. Amazon's home
 * loads untouched underneath; the service stays idle just after boot so Amazon's sign-in
 * and home services can start. CleanFrame's "Fire TV Home" and Settings actions pause it.
 */
public class HomeWatcher extends Service {
    static final String AMAZON_LAUNCHER = "com.amazon.tv.launcher";
    private static final long BOOT_QUIET_MS = 3 * 60000, COVER_MAX_MS = 12000;
    private static volatile long allowUntil = 0;
    static volatile Bitmap snapshot;
    private static HomeWatcher running;
    private final Handler main = new Handler(Looper.getMainLooper());
    private Thread reader;
    private volatile Process logcat;
    private View cover;

    static void allowAmazonHome(long ms) { allowUntil = SystemClock.elapsedRealtime() + ms; }

    static boolean isHomeLaunch(String line) {
        return line.contains("START u0") && line.contains("android.intent.category.HOME") && line.contains(AMAZON_LAUNCHER);
    }

    /** Called by MainActivity when it is in front again. */
    static void coverDone() {
        final HomeWatcher w = running;
        if (w != null) w.main.post(new Runnable() { public void run() { w.hideCover(); } });
    }

    private WindowManager.LayoutParams coverParams(boolean shown) {
        int flags = WindowManager.LayoutParams.FLAG_FULLSCREEN | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN;
        if (!shown) flags |= WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE;
        return new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.TYPE_SYSTEM_ALERT, flags, PixelFormat.OPAQUE);
    }

    /* The cover window stays attached but invisible, so showing it is a visibility flip
       rather than a new full-screen window (which takes this stick about a second). */
    private void prepareCover() {
        if (cover != null) return;
        ImageView v = new ImageView(this);
        v.setScaleType(ImageView.ScaleType.FIT_XY);
        v.setBackgroundColor(Color.BLACK);
        v.setFocusable(true);
        v.setOnKeyListener(new View.OnKeyListener() { public boolean onKey(View x, int code, KeyEvent e) { return true; } });
        v.setVisibility(View.INVISIBLE);
        try {
            ((WindowManager) getSystemService(Context.WINDOW_SERVICE)).addView(v, coverParams(false));
            cover = v;
        } catch (Exception e) { Log.w("CleanFrameHome", "cover failed", e); }
    }

    /** Called by MainActivity after it saves a fresh snapshot. */
    static void snapshotReady() {
        final HomeWatcher w = running;
        if (w != null) w.main.post(new Runnable() { public void run() {
            w.prepareCover();
            if (w.cover != null && snapshot != null) ((ImageView) w.cover).setImageBitmap(snapshot);
        } });
    }

    private void showCover() {
        prepareCover();
        if (cover == null || cover.getVisibility() == View.VISIBLE) return;
        cover.setVisibility(View.VISIBLE);
        ((WindowManager) getSystemService(Context.WINDOW_SERVICE)).updateViewLayout(cover, coverParams(true));
        cover.requestFocus();
        main.postDelayed(new Runnable() { public void run() { hideCover(); } }, COVER_MAX_MS);
    }

    private void hideCover() {
        if (cover == null || cover.getVisibility() != View.VISIBLE) return;
        cover.setVisibility(View.INVISIBLE);
        ((WindowManager) getSystemService(Context.WINDOW_SERVICE)).updateViewLayout(cover, coverParams(false));
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        running = this;
        main.post(new Runnable() { public void run() { prepareCover(); } });
        if (reader == null || !reader.isAlive()) {
            reader = new Thread(new Runnable() { public void run() { follow(); } }, "HomeWatcher");
            reader.start();
        }
        return START_STICKY;
    }

    private void follow() {
        while (!Thread.currentThread().isInterrupted()) {
            try {
                // -T 1 starts at the newest line, so Home presses from before this start are ignored.
                logcat = Runtime.getRuntime().exec(new String[] { "logcat", "-T", "1", "-v", "brief", "ActivityManager:I", "*:S" });
                BufferedReader in = new BufferedReader(new InputStreamReader(logcat.getInputStream()));
                String line;
                while ((line = in.readLine()) != null) {
                    long now = SystemClock.elapsedRealtime();
                    if (!isHomeLaunch(line) || now < BOOT_QUIET_MS || now < allowUntil) continue;
                    main.post(new Runnable() { public void run() { showCover(); } });
                    Intent i = new Intent(this, MainActivity.class);
                    i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
                    startActivity(i);
                }
            } catch (Exception e) { Log.w("CleanFrameHome", "logcat failed", e); }
            SystemClock.sleep(2000);
        }
    }

    @Override
    public void onDestroy() {
        if (cover != null) try { ((WindowManager) getSystemService(Context.WINDOW_SERVICE)).removeView(cover); } catch (Exception e) { /* already gone */ }
        cover = null;
        running = null;
        if (reader != null) reader.interrupt();
        if (logcat != null) logcat.destroy();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }
}
