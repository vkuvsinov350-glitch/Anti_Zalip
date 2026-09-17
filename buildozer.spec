[app]

# Название приложения
title = Детектор залипания
package.name = zaliptracker
package.domain = org.zalip

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 3.0

# Требования — что устанавливать внутрь APK
requirements = python3,kivy,plyer,android,pyjnius

# Ориентация — портретная
orientation = portrait
fullscreen = 0

# Иконка (пока стандартная)
# icon.filename = %(source.dir)s/icon.png

# Разрешения Android
android.permissions = VIBRATE,POST_NOTIFICATIONS,WAKE_LOCK,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,SCHEDULE_EXACT_ALARM

# Версия API
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24

# Архитектуры (arm64 — современные телефоны, armeabi-v7a — старые)
android.archs = arm64-v8a, armeabi-v7a

# Разрешить отладку (для логов)
android.debug = 1
android.release = 0

# Не перезаписывать APK
android.accept_sdk_license = True

# Порядок загрузки модулей
android.entrypoint = org.kivy.android.PythonActivity
android.apptheme = "@android:style/Theme.NoTitleBar"

# Boot-сервис (автозапуск)
# services = MyService:./service.py

[buildozer]

log_level = 2
warn_on_root = 1