package com.yoezel.cleanframe;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;

/**
 * Opens CleanFrame after the Fire TV has started. The 45 s delay lets Amazon's sign-in and
 * home services finish starting; opening over them straight away left the stick unable to
 * load its home screen.
 */
public class BootReceiver extends BroadcastReceiver {
    private static final long DELAY_MS = 45000;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) return;
        context.startService(new Intent(context, HomeWatcher.class));
        Intent open = new Intent(context, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent later = PendingIntent.getActivity(context, 0, open, PendingIntent.FLAG_UPDATE_CURRENT);
        AlarmManager alarms = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        alarms.set(AlarmManager.ELAPSED_REALTIME, SystemClock.elapsedRealtime() + DELAY_MS, later);
    }
}
