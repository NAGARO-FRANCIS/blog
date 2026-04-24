# Coloc.ai - Commandes utiles

## Installation et Setup

```bash
# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Démarrer le serveur
python manage.py runserver
```

## Gestion des migrations

```bash
# Créer les migrations
python manage.py makemigrations logement colocation accounts messagerie

# Voir les migrations non appliquées
python manage.py showmigrations

# Afficher les migrations appliquées pour une app
python manage.py showmigrations logement

# Revenir à une migration précédente
python manage.py migrate logement 0001
```

## Gestion de la base de données

```bash
# Créer une sauvegarde des données
python manage.py dumpdata --format=json > backup.json

# Restaurer les données
python manage.py loaddata backup.json

# Réinitialiser la base de données
python manage.py flush
```

## Tests

```bash
# Lancer tous les tests
python manage.py test

# Lancer les tests d'une app
python manage.py test logement
python manage.py test colocation

# Avec verbose
python manage.py test --verbosity=2
```

## Collecte des fichiers statiques

```bash
# Collecter les fichiers statiques pour la production
python manage.py collectstatic --noinput
```

## Shell Django

```bash
# Accéder au shell Django
python manage.py shell

# Exemples de commandes
from logement.models import Logement
logements = Logement.objects.all()
logement = Logement.objects.get(pk=1)
```

## Nettoyage

```bash
# Supprimer les fichiers mis en cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Supprimer la base de données et recommencer
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Structure des uploads

Les fichiers uploadés sont organisés par:
```
media/
├── logements/
│   └── YYYY/MM/
│       └── photos de logements
└── colocations/
    └── YYYY/MM/
        └── photos de colocations
```

## Permissions et authentification

```python
# Dans les views
from django.contrib.auth.decorators import login_required

@login_required
def ma_vue(request):
    # Votre code
    pass
```

## Configuration pour la production

1. Définir `DEBUG = False` dans settings.py
2. Ajouter `ALLOWED_HOSTS` approprié
3. Configurer une base de données de production (PostgreSQL)
4. Configurer un service de fichiers (S3, etc)
5. Ajouter HTTPS
6. Configurer les variables d'environnement
7. Utiliser un serveur WSGI (Gunicorn, uWSGI)

---

Pour plus d'informations, consultez la documentation Django:
https://docs.djangoproject.com/
