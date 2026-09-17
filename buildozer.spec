[app]
title = Детектор залипания
package.name = zaliptracker
package.domain = org.zalip
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 3.0
requirements = python3,kivy,plyer,android,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = VIBRATE,POST_NOTIFICATIONS,WAKE_LOCK,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,SCHEDULE_EXACT_ALARM
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.debug = 1
android.release = 0
android.accept_sdk_license = True
android.entrypoint = org.kivy.android.PythonActivity
android.apptheme = "@android:style/Theme.NoTitleBar"

[buildozer]
log_level = 2
warn_on_root = 1