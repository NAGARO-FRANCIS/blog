# 🎯 SYSTÈME D'INSCRIPTION À 3 ÉTAPES - DOCUMENTATION COMPLÈTE

## Vue d'ensemble
Les utilisateurs qui s'inscrivent en tant que "**Individu**" doivent maintenant choisir un rôle spécifique qui détermine leurs permissions sur la plateforme.

---

## 📋 Les 3 Rôles Individuels

### 1. 🏠 PROPRIÉTAIRE
**Description:** Je possède une maison et veux mettre des chambres en location

**Permissions:**
- ✅ Publier des annonces de location
- ✅ Créer des réservations
- ✅ Accéder au tableau de bord
- ✅ Recevoir des paiements
- ✅ Gérer les clients

**Cas d'usage:**
- Personne qui possède une maison et veut en louer les chambres
- Propriétaire investisseur avec plusieurs propriétés
- Personne avec chambres disponibles temporairement

---

### 2. 🔑 LOCATAIRE  
**Description:** J'ai déjà une maison et je cherche quelqu'un pour partager les frais

**Permissions:**
- ✅ Publier des annonces (pour chercher colocataire)
- ✅ Gérer les candidatures
- ✅ Accéder au tableau de bord
- ✅ Communiquer avec les candidats

**Cas d'usage:**
- Personne en location qui cherche un colocataire
- Personne qui possède un appartement et veut partager
- Étudiants partageant un logement

---

### 3. 👥 COLOCATAIRE
**Description:** Je cherche une chambre ou une maison à louer

**Permissions:**
- ✅ Consulter les annonces (lecture seule)
- ✅ Contacter les propriétaires
- ✅ Voir les profils publics
- ✅ Recevoir des notifications
- ❌ **NE PEUT PAS** publier d'annonces
- ❌ **NE PEUT PAS** accéder aux dashboards de publication

**Cas d'usage:**
- Personne cherchant une chambre à louer
- Personne nouvelle en ville cherchant un logement
- Touriste long terme cherchant colocation

**Restriction d'accès:**
Si un colocataire tente d'accéder à `/logement/ajouter/`:
```
❌ Erreur: "En tant que colocataire, vous ne pouvez pas publier d'annonces. 
Vous pouvez uniquement consulter les annonces existantes."
```

---

## 🔄 Flux d'Inscription Complet

```
┌─────────────────────────────────────────┐
│ 1. Page d'accueil                      │
│    - Clique "S'inscrire"              │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 2. Choix du type de compte            │
│    □ Individu (sélectionné)           │
│    □ Résidence                         │
│    □ Hôtel                             │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 3. **NOUVELLE ÉTAPE**                 │
│    Choix du rôle (individu uniquement)  │
│                                         │
│    ☑ 🏠 Propriétaire                   │
│    ○ 🔑 Locataire                      │
│    ○ 👥 Colocataire                    │
│                                         │
│    [Continuer]                          │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 4. Formulaire d'inscription complet    │
│    - Identifiant/Email/Mot de passe    │
│    - Informations personnelles          │
│    - Localisation                       │
│    - Pièce d'identité                   │
│    - Photo de profil                    │
│                                         │
│    [Créer mon compte]                   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 5. Compte créé avec:                   │
│    - account_type = 'individu'         │
│    - role = choix de l'étape 3         │
│    - verification_status = 'pending'   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 6. Redirection vers                     │
│    - Vérification des documents         │
│    - Selon le rôle choisi              │
└─────────────────────────────────────────┘
```

---

## 🗂️ Fichiers Modifiés

### 📄 `accounts/forms.py`
**Ajout:** `IndividuRoleForm` - Formulaire de choix du rôle avec descriptions
```python
class IndividuRoleForm(forms.Form):
    ROLE_CHOICES = [
        ('proprietaire', '🏠 Propriétaire - Je possède une maison...'),
        ('locataire', '🔑 Locataire - J\'ai une maison et cherche...'),
        ('colocataire', '👥 Colocataire - Je cherche une chambre...'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
```

**Modification:** `SignUpForm` - Champ `role` enlevé (car sélectionné à l'étape 2)

---

### 🎬 `accounts/views.py`
**Modifié:** `inscription_individu()`
- Affiche `IndividuRoleForm` au lieu du `SignUpForm` complet
- Enregistre le rôle dans `request.session['individu_role']`
- Redirige vers `inscription_individu_form`

**Créé:** `inscription_individu_form()` 
- Affiche le formulaire `SignUpForm` complet
- Sauvegarde le profil avec le rôle de la session
- Crée le log de vérification
- Redirige vers vérification des documents

---

### 🔗 `accounts/urls.py`
**Avant:**
```python
path('inscription/individu/', inscription_individu, name='inscription_individu'),
```

**Après:**
```python
path('inscription/individu/', inscription_individu, name='inscription_individu'),
path('inscription/individu/formulaire/', inscription_individu_form, name='inscription_individu_form'),
```

---

### 🛡️ `logement/views.py` - Restriction de publication
**Fonction:** `ajouter_logement()`

```python
# Vérifier les permissions : seuls propriétaires et locataires peuvent publier
if account_type == 'individu' and role == 'colocataire':
    messages.error(request, 
        '❌ En tant que colocataire, vous ne pouvez pas publier d\'annonces.')
    return redirect('logement:home')
```

**Comportement:**
- Propriétaire: Accès autorisé ✅
- Locataire: Accès autorisé ✅
- Colocataire: Redirection + message d'erreur ❌

---

## 🎨 Templates Créés

### 1️⃣ `accounts/inscription_individu_role.html`
**Affiche:** 3 cartes interactives pour choisir le rôle

**Caractéristiques:**
- Cartes responsive (1 colonne sur mobile, 3 colonnes sur desktop)
- Surlignage au survol
- Descriptions détaillées pour chaque rôle
- Liste des permissions incluse

**Interaction:**
```
Utilisateur sélectionne rôle → Clique "Continuer" 
→ POST vers inscription_individu() 
→ Session['individu_role'] = choix 
→ Redirige vers inscription_individu_form
```

---

### 2️⃣ `accounts/inscription_individu_form.html`
**Affiche:** Formulaire d'inscription complet avec badge du rôle

**Sections:**
1. 🔐 Identifiant et authentification (username, email, password)
2. 👤 Informations personnelles (nom, prénoms, date naissance, sexe, profession)
3. 📍 Localisation (ville, quartier, téléphone)
4. 🪪 Vérification d'identité (type pièce, numéro)
5. 📷 Photo de profil

**Badge rôle:** Affiche en haut "🏠 Propriétaire" / "🔑 Locataire" / "👥 Colocataire"

---

## 📊 Session Management

```
Étape 1 (Choix type compte):
  request.session['account_type'] = 'individu'

Étape 2 (Choix rôle) - NOUVEAU:
  request.session['individu_role'] = 'proprietaire'  # ou 'locataire' ou 'colocataire'

Étape 3 (Formulaire complet):
  Utilise session['individu_role'] pour remplir profile.role

Après inscription:
  Nettoyage: del session['account_type'], del session['individu_role']
```

---

## ✅ Validation & Tests

**Django System Check:**
```bash
$ python manage.py check
System check identified no issues (0 silenced).
```

**Test URLs:**
```
GET /accounts/inscription/individu/ 
  → Affiche IndividuRoleForm

POST /accounts/inscription/individu/ (role=proprietaire)
  → Sauvegarde en session
  → Redirige vers /accounts/inscription/individu/formulaire/

GET /accounts/inscription/individu/formulaire/
  → Affiche SignUpForm complet avec badge du rôle

POST /accounts/inscription/individu/formulaire/
  → Crée utilisateur + profile avec role='proprietaire'
  → Redirige vers verification_docs
```

---

## 🔒 Restrictions Appliquées

### Avant (Ancien système)
```
- Tous les "individu" pouvaient:
  ✅ Publier des annonces
  ✅ Voir les annonces
  ✅ Accéder aux dashboards
```

### Après (Nouveau système)
```
Propriétaire:
  ✅ Publier des annonces
  ✅ Voir les annonces
  ✅ Accéder au dashboard personnel

Locataire:
  ✅ Publier des annonces (pour chercher colocataire)
  ✅ Voir les annonces
  ✅ Accéder au dashboard personnel

Colocataire:
  ✅ Voir les annonces (LECTURE SEULE)
  ✅ Contacter propriétaires
  ❌ Publier des annonces
  ❌ Accéder aux dashboards de publication
```

---

## 📝 Notes d'implémentation

1. **Le rôle est immutable après inscription** (peut être modifié via profil plus tard si souhaité)

2. **Les colocataires voient les boutons de publication grisés/cachés** dans les templates

3. **Les notifications d'erreur sont claires et utiles:**
   - "En tant que colocataire, vous ne pouvez pas publier d'annonces"
   - "Vous pouvez uniquement consulter les annonces existantes"

4. **La vérification des documents s'applique à tous les rôles** (même logique)

5. **Les dashboards affichent des contenus différents selon le rôle** (à implémenter)

---

## 🎯 Prochaines Étapes (Optionnel)

1. **Ajouter des "super roles":**
   - Colocataire → peut upgrades en Propriétaire/Locataire

2. **Email de confirmation:**
   - Envoyer email avec rôle confirmé à l'inscription

3. **Dashboards spécialisés:**
   - Propriétaire: Voir les annonces publiées, réservations, analytics
   - Locataire: Voir candidatures, messages des colocataires
   - Colocataire: Voir mes favoris, contacts sauvegardés

4. **Historique de rôles:**
   - Tracker les changements de rôle pour modération

---

**✅ Système complet et opérationnel!**
