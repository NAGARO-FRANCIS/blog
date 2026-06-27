# 🎯 Système des Trois Interfaces Distinctes

## Vue d'ensemble

L'application dispose de **trois interfaces différentes et indépendantes** selon le type de compte de l'utilisateur:

1. **Interface Individu** - Pour les chercheurs de logements et touristes
2. **Interface Résidence** - Pour les gestionnaires de résidences
3. **Interface Hôtel** - Pour les gestionnaires d'hôtels

## Architecture

### Types de Comptes (Profile.account_type)

```python
ACCOUNT_TYPE_CHOICES = [
    ('individu', 'Individu'),
    ('residence', 'Gestionnaire de Résidence'),
    ('hotel', 'Gestionnaire d\'Hôtel'),
]
```

### Flux de Redirection

```
Utilisateur connecté accède à /dashboard/
    ↓
Vue dashboard() détecte le type de compte
    ↓
Redirection vers l'interface appropriée
    ├── 'individu' → dashboard_individu.html (theme: violet)
    ├── 'residence' → dashboard_residence.html (theme: vert)
    └── 'hotel' → dashboard_hotel.html (theme: orange)
```

## Interfaces Détaillées

### 1️⃣ Interface Individu (Violet)

**Fichiers:**
- Template: `templates/accounts/dashboard_individu.html`
- CSS: `static/dashboard_individu.css`
- Vue: `accounts.views.dashboard_individu()`

**Caractéristiques:**
- 👤 Profil utilisateur personnel
- ❤️ Gestion des favoris
- 💬 Conversations avec propriétaires/touristes
- 🔍 Recherche de logements
- 👥 Recherche de touristes

**Stats affichées:**
- Nombre de favoris
- Nombre de conversations
- Statut de vérification

**Actions rapides:**
- Chercher un Logement
- Chercher un Touriste
- Mes Messages
- Mes Favoris

---

### 2️⃣ Interface Résidence (Vert)

**Fichiers:**
- Template: `templates/accounts/dashboard_residence.html`
- CSS: `static/dashboard_residence.css`
- Vue: `accounts.views.dashboard_residence()`

**Caractéristiques:**
- 🏢 Gestion de résidences (studios, T1, T2, etc.)
- 📋 Gestion des réservations
- 👥 Gestion des locataires
- 💳 Suivi des paiements
- 📊 Statistiques de location

**Stats affichées:**
- Nombre de logements
- Nombre de réservations
- Clients actifs
- Statut de vérification professionnelle

**Actions rapides:**
- Ajouter un Logement
- Voir les Réservations
- Messages avec les clients
- Paramètres de l'établissement

**Infos professionnelles affichées:**
- Nom de l'établissement
- SIRET/RCCM
- Représentant légal
- Nombre de chambres/unités
- Localisation

---

### 3️⃣ Interface Hôtel (Orange)

**Fichiers:**
- Template: `templates/accounts/dashboard_hotel.html`
- CSS: `static/dashboard_hotel.css`
- Vue: `accounts.views.dashboard_hotel()`

**Caractéristiques:**
- 🏨 Gestion de chambres d'hôtel
- 📅 Calendrier des réservations
- 👤 Gestion des clients
- 🛏️ Gestion des équipements
- 📊 Taux d'occupation
- ⭐ Avis et évaluations

**Stats affichées:**
- Nombre de chambres
- Nombre de réservations
- Clients actifs
- Statut de vérification

**Actions rapides:**
- Ajouter une Chambre
- Gérer les Réservations
- Liste des Clients
- Messages avec les clients

**Équipements affichables:**
- 📶 WiFi
- 🅿️ Parking
- 🍽️ Restaurant
- 🛎️ Réception 24h
- ❄️ Climatisation
- 💪 Gym

---

## Sécurité

### Protections implémentées:

1. **Authentification requise** - Décorateur `@login_required` sur toutes les vues
2. **Vérification du type de compte** - Redirection automatique si type incorrect
3. **Isolation des interfaces** - Chaque interface ne montre que les données pertinentes

### Code de protection (exemple):

```python
@login_required
def dashboard_individu(request):
    """Dashboard pour les utilisateurs individuels"""
    profile = request.user.profile
    
    # Vérifier que l'utilisateur est bien un individu
    if profile.account_type != 'individu':
        return redirect('accounts:dashboard')
    
    # ... reste du code
```

## Routes URL

```python
# URL principale (redirection)
path('dashboard/', dashboard, name='dashboard')

# URLs spécifiques par type
path('dashboard/individu/', dashboard_individu, name='dashboard_individu')
path('dashboard/residence/', dashboard_residence, name='dashboard_residence')
path('dashboard/hotel/', dashboard_hotel, name='dashboard_hotel')
```

## Navigation

Le bouton **"📊 Dashboard"** dans la barre de navigation:
- ✅ Visible uniquement pour les utilisateurs connectés
- ✅ Redirige automatiquement vers l'interface correcte
- ✅ Thématisé selon le type de compte

## Personnalisation Possible

### Ajouter de nouvelles sections:

```html
<!-- Dans le template spécifique -->
<section class="ma-section">
    <h2>Ma Section</h2>
    <div class="contenu">
        <!-- Contenu spécifique à ce type d'utilisateur -->
    </div>
</section>
```

### Ajouter des données contextuelles:

```python
# Dans la vue
context = {
    'profile': profile,
    'donnee_specifique': valeur,  # Nouvelle donnée
    'statistiques': stats,
}
```

## Thèmes Couleur

| Type | Couleur Primaire | Hex Code | Usage |
|------|-----------------|----------|-------|
| Individu | Violet | #667eea | Header, accents |
| Résidence | Vert | #10b981 | Header, accents |
| Hôtel | Orange | #f59e0b | Header, accents |

## Points d'Amélioration Futurs

- [ ] Ajouter des graphiques de statistiques
- [ ] Implémentation complète des réservations
- [ ] Système de paiement intégré
- [ ] Notifications en temps réel
- [ ] Export de données (PDF/CSV)
- [ ] API pour applications mobiles

## Testing

### Pour tester les trois interfaces:

1. **Créer 3 comptes différents:**
   ```bash
   python manage.py create_prof_profile.py  # Récupère le script d'exemple
   ```

2. **Vérifier la redirection:**
   - Connectez-vous avec un compte individu → `/dashboard/` → redirect vers `/dashboard/individu/`
   - Connectez-vous avec un compte résidence → `/dashboard/` → redirect vers `/dashboard/residence/`
   - Connectez-vous avec un compte hôtel → `/dashboard/` → redirect vers `/dashboard/hotel/`

3. **Vérifier la protection:**
   - Essayez d'accéder à une interface incorrecte
   - Vérifiez que vous êtes redirigé vers la bonne interface

---

**Dernière mise à jour:** Mai 2026
