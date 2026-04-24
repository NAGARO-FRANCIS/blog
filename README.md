# 🏠 Coloc.ai - Plateforme de Colocation et Logement en Côte d'Ivoire

**Une plateforme moderne et professionnelle pour trouver ou publier des annonces de logement et colocation en Côte d'Ivoire.**

## 🎯 Caractéristiques principales

### Pour les propriétaires/gestionnaires
- 📸 **Publier avec photos** - Jusqu'à 5 photos de haute qualité par annonce
- 🏠 **Annonces détaillées** - Type, surface, équipements, etc.
- 🔍 **Visibilité optimale** - Annonces bien structurées pour la recherche
- ✅ **Professionnel** - Design moderne et crédible
- 💬 **Messagerie intégrée** - Communiquer directement avec les intéressés

### Pour les locataires/colocs
- 🔎 **Recherche avancée** - Filtrer par budget, ville, équipements
- ❤️ **Favoris** - Marquer vos annonces préférées
- 📧 **Notifications** - Recevoir les nouvelles annonces
- 💬 **Messagerie sécurisée** - Discuter avec les propriétaires
- 📱 **Mobile-friendly** - Rechercher sur téléphone ou ordinateur

## 🚀 Installation

### Prérequis
- Python 3.10+
- pip (gestionnaire de paquets Python)
- Git (optionnel)

### Étapes d'installation

1. **Cloner le repository** (ou télécharger les fichiers)
```bash
cd c:\projet\pro\ivoire
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Appliquer les migrations**
```bash
python manage.py migrate
```

4. **Créer un compte administrateur**
```bash
python manage.py createsuperuser
```

5. **Démarrer le serveur**
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
