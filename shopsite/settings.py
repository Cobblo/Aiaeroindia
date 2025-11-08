from pathlib import Path
from decouple import config
import os

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent  # <-- keep ONLY this

# --- Core ---
SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-only-not-for-prod")
DEBUG = config("DEBUG", cast=bool, default=True)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=lambda v: [h for h in v.split(",") if h])  # e.g. "localhost,127.0.0.1"

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # your apps
    "core",
    "accounts",
    "catalog",
    "cart.apps.CartConfig",
    "orders",
    "payments",
    "blog",
    "customers",
    "team.apps.TeamConfig",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # serves static files in prod after collectstatic
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "shopsite.urls"

# --- Templates ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # put any project-level templates here
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_summary",  # custom
            ],
        },
    },
]

WSGI_APPLICATION = "shopsite.wsgi.application"

# --- DB ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Password validators ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static / Media ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]                 # your source static
STATIC_ROOT = BASE_DIR / "staticfiles"                   # collectstatic target
# WhiteNoise: additionally serve compressed files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Security / CSRF ---
CSRF_TRUSTED_ORIGINS = [
    config("CSRF_ORIGIN", default="http://localhost:8000"),
    "http://127.0.0.1:8000",
]
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week

# --- Auth redirects ---
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "core:home"

# --- Email ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="aiaero44@gmail.com")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="njwh ywko nzzl cypg")  # use App Password
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Ai-Aero <aiaero44@gmail.com>")
EMAIL_TIMEOUT = 20

# --- Misc ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_URL = config("SITE_URL", default="https://www.aiaeroindia.com")

# --- Razorpay (keep your keys in .env ideally) ---
RAZORPAY_KEY_ID = config("RAZORPAY_KEY_ID", default="rzp_test_xc0LpuVfsigL9y")
RAZORPAY_KEY_SECRET = config("RAZORPAY_KEY_SECRET", default="0ylEFHvHTpiGyl2j3Yx1graX")
