from settings.base import *
from settings.base import BASE_DIR

DEBUG =True 
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}