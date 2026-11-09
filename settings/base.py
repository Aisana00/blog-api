# Python modules
from pathlib import Path

# Third-party modules
from django.urls import reverse_lazy

# Project modules
from settings.conf import ALLOWED_HOSTS, ENV_ID, SECRET_KEY  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# ----------------------------------------------
# Apps
#
UNFOLD_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
]
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
]
PROJECT_APPS = [
    "apps.auths",
    "apps.blog",
]
INSTALLED_APPS = UNFOLD_APPS + DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# ----------------------------------------------
# Middleware | Urls | Templates
#
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------------------------------
# Auth
#
AUTH_USER_MODEL = "auths.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

# ----------------------------------------------
# Internationalization | Static
#
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------
# Logging
#
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "app.log",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}

# ----------------------------------------------
# Unfold admin
#
POST_CHANGELIST_URL = "admin:blog_post_changelist"

UNFOLD = {
    "SITE_TITLE": "Blog API",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Admin panel",
    "SITE_SYMBOL": "article",
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "oklch(97% 0.014 254.604)",
            "100": "oklch(93.2% 0.032 255.585)",
            "200": "oklch(88.2% 0.059 254.128)",
            "300": "oklch(80.9% 0.105 251.813)",
            "400": "oklch(70.7% 0.165 254.624)",
            "500": "oklch(62.3% 0.214 259.815)",
            "600": "oklch(54.6% 0.245 262.881)",
            "700": "oklch(48.8% 0.243 264.376)",
            "800": "oklch(42.4% 0.199 265.638)",
            "900": "oklch(37.9% 0.146 265.522)",
            "950": "oklch(28.2% 0.091 267.935)",
        },
    },
    "SITE_DROPDOWN": [
        {
            "icon": "code",
            "title": "GitHub repository",
            "link": "https://github.com/Aisana00/blog-api",
        },
        {
            "icon": "menu_book",
            "title": "Unfold docs",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "COMMAND": {
        "search_models": True,
        "show_history": True,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy(POST_CHANGELIST_URL),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": "Comments",
                        "icon": "chat",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "sell",
                        "link": reverse_lazy("admin:blog_tag_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": reverse_lazy(POST_CHANGELIST_URL),
                },
                {
                    "title": "Published",
                    "link": lambda request: (
                        f"{reverse_lazy(POST_CHANGELIST_URL)}"
                        "?status__exact=published"
                    ),
                },
                {
                    "title": "Drafts",
                    "link": lambda request: (
                        f"{reverse_lazy(POST_CHANGELIST_URL)}"
                        "?status__exact=draft"
                    ),
                },
            ],
        },
    ],
}