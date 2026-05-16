# � IVOIRE CONNECT

**Plateforme moderne et professionnelle de location et colocation pour la Côte d'Ivoire**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)]()
[![Django](https://img.shields.io/badge/Django-6.0.4-darkgreen)]()

---

## 📋 Table des Matières

- [À Propos](#à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Installation Rapide](#-installation-rapide)
- [Architecture](#-architecture)
- [Documentation](#-documentation)
- [Développement](#-développement)
- [Support](#-support)

---

## À Propos

Ivoire Connect est une **plateforme complète** permettant aux utilisateurs de publier, chercher et réserver des logements en Côte d'Ivoire.

**Types d'Utilisateurs Supportés:**
- 🏠 **Propriétaires individuels** - Publier des annonces de location
- 🏨 **Hôtels** - Gérer les réservations avec dashboards
- 🏢 **Résidences** - Système de gestion complet
- 👥 **Locataires/Colocataires** - Chercher et réserver

---

## ✨ Fonctionnalités

### 📸 Pour les Propriétaires
- Publier des annonces avec photos (jusqu'à 5)
- Gestion complète des annonces
- Calendrier de disponibilité
- Réservations et paiements
- Messagerie avec locataires
- Statistiques et rapports

### 🔎 Pour les Locataires
- Recherche avancée avec filtres
- Annonces détaillées avec photos
- Réservation sécurisée
- Paiement en ligne (Stripe)
- Messagerie sécurisée
- Design responsive (mobile/desktop)

### 💳 Paiements
- Intégration Stripe
- Paiement sécurisé
- Confirmation automatique
- Reçus par email

---

## 🚀 Installation Rapide

### Prérequis
- Python 3.14+
- Django 6.0.4
- pip

### Étapes

```bash
# 1. Accéder au dossier
cd c:\projet\pro\ivoire

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Appliquer les migrations
python manage.py migrate

# 4. Créer un superutilisateur
python manage.py createsuperuser

# 5. Lancer le serveur
python manage.py runserver
```

Visitez: **http://localhost:8000/**
```bash
python manage.py runserver
```

6. **Accéder à l'application**
```
http://localhost:8000
```

## 📋 Structure de l'application

### Applications Django

#### **logement** - Gestion des logements
- Publiquer des annonces de location
- Gérer les propriétés
- Afficher les détails avec photos

#### **colocation** - Gestion des colocations
- Publier des annonces de colocation
- Rechercher des colocataires
- Gérer les favoris

#### **accounts** - Gestion des utilisateurs
- Inscription et authentification
- Profils utilisateurs
- Vérification des comptes

#### **messagerie** - Communication
- Messagerie privée entre utilisateurs
- Notifications de messages
- Historique des conversations

## 🎨 Design et UX

### Couleurs
- **Primaire**: #5e5dff (Bleu professionnel)
- **Secondaire**: #ff7c7c (Rose moderne)
- **Texte**: #1f2941 (Gris foncé)

### Typographie
- **Police**: Inter, system-ui
- **Responsive**: Optimisé pour mobile, tablette, desktop

## 📊 Modèles de données

### Logement
```python
- titre: CharField
- description: TextField
- type_logement: Choix (Appartement, Maison, Studio, Villa, Chambre)
- prix: DecimalField
- ville: CharField
- quartier: CharField
- surface: DecimalField
- nombre_pieces: PositiveSmallIntegerField
- nombre_chambres: PositiveSmallIntegerField
- nombre_salles_bain: PositiveSmallIntegerField
- etage: PositiveSmallIntegerField
- meuble: BooleanField
- disponible_depuis: DateField
- climatisation: BooleanField
- wifi: BooleanField
- garage: BooleanField
- jardin: BooleanField
- piscine: BooleanField
- cuisine_equipee: BooleanField
- photos: OneToMany (PhotoLogement)
```

### ColocationAnnonce
```python
- ville: CharField
- quartier: CharField
- budget_mensuel: DecimalField
- description: TextField
- surface: DecimalField
- nombre_chambres: PositiveSmallIntegerField
- nombre_salles_bain: PositiveSmallIntegerField
- infos_logement: TextField
- nombre_colocataires: PositiveSmallIntegerField
- profil_recherche: Choix (Étudiant, Professionnel, Couple, Famille)
- conditions_vie: TextField
- meuble: BooleanField
- disponible_depuis: DateField
- durée_minimum: PositiveSmallIntegerField
- climatisation: BooleanField
- wifi: BooleanField
- cuisine_equipee: BooleanField
- garage: BooleanField
- jardin: BooleanField
- photos: OneToMany (PhotoColocation)
- favoris: ManyToMany (Favori)
```

## 🛠️ Configuration

### Fichiers importants

**settings.py** - Configuration Django
- Base de données (SQLite en développement)
- Applications installées
- Templates et static files
- Media files pour les uploads

**urls.py** - Routes principales
- Admin Django
- Pages logement
- Pages colocation
- Pages messagerie
- Pages accounts

## 🔐 Sécurité

✅ Protection CSRF sur tous les formulaires  
✅ Authentification requise pour certaines actions  
✅ Validation des données côté serveur  
✅ Upload de fichiers validé  
✅ Permissions basées sur l'utilisateur  

## 📱 Pages principales

### Publiques
- `/` - Accueil (Logements)
- `/colocation/` - Annonces de colocation
- `/accounts/login/` - Connexion
- `/accounts/inscription/` - Inscription

### Authentifiées
- `/ajouter/` - Ajouter un logement
- `/colocation/publier/` - Publier une colocation
- `/colocation/favoris/` - Mes favoris
- `/messages/` - Messagerie
- `/messages/envoyer/<user_id>/` - Envoyer un message
- `/accounts/profil/` - Mon profil
- `/accounts/edit/` - Modifier le profil

## 📚 Documentation supplémentaire

Consultez les fichiers suivants:
- `AMÉLIORATIONS.md` - Détails des améliorations apportées
- `COMMANDES.md` - Commandes utiles Django

## 🤝 Support et contact

Pour toute question ou problème, veuillez:
1. Vérifier la documentation Django: https://docs.djangoproject.com/
2. Consulter les fichiers d'aide du projet
3. Vérifier les logs d'erreur

## 📄 Licence

Ce projet est fourni à titre d'exemple éducatif.

## 🎓 Stack technique

- **Backend**: Django 6.0.4
- **Base de données**: SQLite (dev) / PostgreSQL (prod recommandé)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Uploads**: Pillow pour la gestion d'images
- **Server**: Django runserver (dev) / Gunicorn (prod)

## ✨ Points forts de cette version

✅ **Professionnel** - Design moderne et épuré  
✅ **Adapté** - Localisé pour la Côte d'Ivoire  
✅ **Complet** - Logements + Colocations + Messagerie  
✅ **Modulaire** - Structure Django classique et extensible  
✅ **Sécurisé** - Bonnes pratiques implémentées  
✅ **Responsive** - Fonctionne sur tous les appareils  
✅ **Photographes** - Support de 5 photos par annonce  

---

**Version**: 2.0 Professionnelle  
**Dernière mise à jour**: 17 avril 2026
