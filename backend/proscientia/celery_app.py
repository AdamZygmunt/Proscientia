import os
from celery import Celery

# Domyślne ustawienie modułu z ustawieniami Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proscientia.settings")

app = Celery("proscientia")

# Czytaj konfigurację z Django settings, klucze z prefiksem CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatyczne wykrywanie tasków z INSTALLED_APPS
app.autodiscover_tasks()

# Alias – jakbyś chciał używać nazwy celery_app w kodzie
celery_app = app
