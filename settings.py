"""
Django settings for ivoire project.
Version corrigée : bilingue FR/EN, email SMTP via .env, cookies/CSRF, CSP Django 6.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.csp import CSP

# ---------------------------------------------------------------------------
# Chemins et variables d'environnement
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = Path(__file__).resolve().parent

# Ordre : .env.local (dans ivoire/), puis ivoire/.env, puis .env à la racine.
# load_dotenv n'écrase pas les valeurs déjà définies.
load_dotenv(PROJECT_DIR / '.env.local')
load_dotenv(PROJECT_DIR / '.env')
load_dotenv(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Sécurité de base
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-8%g05@gf^wfr_j=#k#+1bilpi)veftxmq1wym-me13p9fdp_rp'  # Clé dev uniquement
)

# En production, toujours False (mettre DEBUG=True dans le .env en local)
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,192.168.1.56').split(',')
    if host.strip()
]

# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profil'          # vérifie : ton serveur actuel utilisait 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'colocation:colocation_home'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'logement',
    'colocation',
    'messagerie',
    'accounts',
    # 'adminpanel',   # décommente si cette app existe dans ton projet
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',            # langue FR/EN (après Session, avant Common)
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',  # CSP (mode rapport, voir plus bas)
]

ROOT_URLCONF = 'ivoire.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ivoire.context_processors.unread_messages_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'ivoire.wsgi.application'

# ---------------------------------------------------------------------------
# Base de données
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

# ---------------------------------------------------------------------------
# Validation des mots de passe
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalisation : français (source) + anglais
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'fr'

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et médias
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'ivoire' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# Email
# Pour envoyer de vrais emails (Gmail), mets dans le .env :
#   EMAIL_HOST=smtp.gmail.com
#   EMAIL_PORT=587
#   EMAIL_USE_TLS=True
#   EMAIL_HOST_USER=ton.adresse@gmail.com
#   EMAIL_HOST_PASSWORD=mot_de_passe_application_16_caracteres
# Sans ces variables, les emails s'affichent dans le terminal (backend console).
# ---------------------------------------------------------------------------
EMAIL_BACKEND_ENV = os.getenv('EMAIL_BACKEND', '').strip()
EMAIL_HOST = os.getenv('EMAIL_HOST', '').strip()
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').replace(' ', '').strip()
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_TIMEOUT = 20

if EMAIL_BACKEND_ENV:
    EMAIL_BACKEND = EMAIL_BACKEND_ENV
elif EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@localhost')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ACCOUNT_ACTIVATION_DAYS = 7

# ---------------------------------------------------------------------------
# Sécurité production (HTTPS uniquement quand DEBUG=False)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

X_FRAME_OPTIONS = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.56:8000'
    ).split(',')
    if origin.strip()
]

# ---------------------------------------------------------------------------
# Cookies
# 'Lax' (et non 'Strict') pour ne pas être déconnecté au retour d'un lien
# externe ou d'un paiement (CinetPay).
# CSRF_COOKIE_HTTPONLY = False pour que le JavaScript (AJAX) puisse lire le jeton.
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

SECURE_REDIRECT_EXEMPT = []

# ---------------------------------------------------------------------------
# Content Security Policy (Django 6) : mode RAPPORT uniquement.
# Rien n'est bloqué ; regarde la console du navigateur, ajuste les sources
# (Google Fonts, CDN, Stripe...), puis renomme en SECURE_CSP pour appliquer.
# ---------------------------------------------------------------------------
SECURE_CSP_REPORT_ONLY = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF, CSP.UNSAFE_INLINE],
    'style-src': [CSP.SELF, CSP.UNSAFE_INLINE],
    'img-src': [CSP.SELF, 'data:', 'https:'],
    'font-src': [CSP.SELF],
    'connect-src': [CSP.SELF],
    'frame-ancestors': [CSP.NONE],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'