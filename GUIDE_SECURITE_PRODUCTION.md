# Guide de Sécurisation de l'Application Ivoire

## ✅ Modifications appliquées

### 1. **Gestion des secrets (SECRET_KEY)**
**Avant:**
```python
SECRET_KEY = 'django-insecure-8%g05@gf^wfr_j=#k#+1bilpi)veftxmq1wym-me13p9fdp_rp'  # Exposée !
```

**Après:**
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-only')  # Chargée depuis variable d'environnement
```

**Comment faire:**
- En production, exporter la clé: `export SECRET_KEY="votre-clé-sécurisée"`
- Générer une nouvelle clé: `python manage.py shell`
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())  # Copier cette clé et l'ajouter à .env
  ```

---

### 2. **Mode DEBUG désactivé en production**
**Avant:** `DEBUG = True` (danger: exposait stack traces, secrets, etc.)

**Après:** 
```python
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
```

**Déploiement:** Ne pas exporter DEBUG en production (reste False par défaut)

---

### 3. **ALLOWED_HOSTS strictement configuré**
**Avant:** `ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '192.168.1.5']`

**Après:** 
```python
ALLOWED_HOSTS_STR = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',')]
```

**Déploiement:** 
```bash
export ALLOWED_HOSTS="example.com,www.example.com"
```

---

### 4. **HTTPS/SSL forcé en production**
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True              # Redirige HTTP → HTTPS
    SESSION_COOKIE_SECURE = True            # Cookies transmis seulement en HTTPS
    CSRF_COOKIE_SECURE = True               # Token CSRF seulement en HTTPS
    SECURE_HSTS_SECONDS = 31536000          # Force HTTPS pendant 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # S'applique aux sous-domaines
    SECURE_HSTS_PRELOAD = True              # Inclut dans preload list des navigateurs
```

**Effet:** Impossible d'accéder via HTTP, empêche les attaques man-in-the-middle

---

### 5. **Protection contre les attaques clickjacking**
```python
X_FRAME_OPTIONS = 'DENY'  # L'app ne peut pas être intégrée dans un iframe
```

---

### 6. **Cookies sécurisés**
```python
SESSION_COOKIE_HTTPONLY = True      # JS ne peut pas accéder au cookie de session
SESSION_COOKIE_SAMESITE = 'Strict'  # Cookie envoyé seulement sur requêtes du même site
CSRF_COOKIE_HTTPONLY = True         # JS ne peut pas accéder au token CSRF
CSRF_COOKIE_SAMESITE = 'Strict'     # Même protection CSRF
```

**Effet:** Prévient le vol de cookies via XSS ou CSRF

---

### 7. **Content Security Policy (CSP)**
```python
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),              # Par défaut, tout vient du site
    'script-src': ("'self'", "'unsafe-inline'"),  # Scripts de confiance
    'style-src': ("'self'", "'unsafe-inline'"),   # CSS de confiance
    'img-src': ("'self'", "data:", "https:"),     # Images HTTPS
    'frame-ancestors': ("'none'",),          # Pas d'iframe externe
}
```

**Effet:** Protège contre les injections XSS et les attaques diverses

---

### 8. **Protection CSRF stricte**
```python
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '...')
```

**Déploiement:**
```bash
export CSRF_TRUSTED_ORIGINS="https://example.com,https://www.example.com"
```

---

## 🚀 Déploiement en production

### Étape 1: Créer le fichier .env
```bash
cp .env.example .env
# Éditer .env avec vos vraies valeurs
```

### Étape 2: Générer SECRET_KEY
```bash
python manage.py shell
```
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())  # Copier dans .env
```

### Étape 3: Configurer les variables d'environnement
```bash
export DEBUG=False
export SECRET_KEY="clé-générée-ci-dessus"
export ALLOWED_HOSTS="example.com,www.example.com"
export CSRF_TRUSTED_ORIGINS="https://example.com,https://www.example.com"
```

### Étape 4: Installer python-decouple pour charger .env
```bash
pip install python-decouple
```

### Étape 5: Modifier settings.py pour utiliser .env
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

---

## 🔒 Sécurité supplémentaire recommandée

### 1. **Base de données en production**
Utiliser PostgreSQL au lieu de SQLite:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### 2. **Certificat SSL/TLS**
- Utiliser Let's Encrypt (gratuit et automatisé)
- Configuration Nginx/Apache pour HTTPS

### 3. **Contrôle d'accès administrateur**
```python
# settings.py
ALLOWED_HOSTS_ADMIN = config('ALLOWED_HOSTS_ADMIN', default='localhost')
# Restreindre /admin/ à certaines IPs
```

### 4. **Logging et monitoring**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}
```

---

## 📋 Checklist de sécurité pour production

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` dans variable d'environnement (>50 caractères)
- [ ] `ALLOWED_HOSTS` restreint aux domaines valides
- [ ] HTTPS/SSL configuré (certificat Let's Encrypt)
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS` configuré
- [ ] Cookies `HTTPONLY` et `SAMESITE` activés
- [ ] CSP (Content Security Policy) configuré
- [ ] Base de données PostgreSQL (pas SQLite)
- [ ] `.env` dans `.gitignore`
- [ ] Logs et monitoring en place
- [ ] Backups de base de données automatisés
- [ ] Firewall/WAF actif

---

## 🧪 Test de sécurité local

```bash
# Vérifier la configuration
python manage.py check --deploy

# Teste les paramètres de sécurité
```

---

## 📞 Résumé des changements appliqués

✅ SECRET_KEY chargé depuis environnement  
✅ DEBUG désactivé par défaut  
✅ ALLOWED_HOSTS contrôlé par environnement  
✅ HTTPS/SSL forcé en production  
✅ Cookies sécurisés (HTTPONLY, SAMESITE, SECURE)  
✅ Protection HSTS (HTTP Strict Transport Security)  
✅ CSP (Content Security Policy) configuré  
✅ Protection contre clickjacking (X-Frame-Options)  
✅ CSRF strictement contrôlé  

**L'application est maintenant sécurisée pour production!**
