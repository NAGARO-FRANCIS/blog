# 📐 Structure CSS Organisée - Ivoire Connect

## Vue d'ensemble

Tous les styles CSS ont été réorganisés en une structure modulaire, propre et maintenable. Chaque fichier CSS a une responsabilité spécifique et ils sont chargés dans un ordre logique.

## Architecture CSS

```
static/
├── variables.css          # Variables CSS globales (couleurs, espacements, etc.)
├── reset.css             # Réinitialisation des styles navigateur
├── typography.css        # Styles typographiques
├── layout.css           # Conteneurs, grille, flexbox, positionnement
├── components.css       # Composants réutilisables (boutons, cartes, badges, etc.)
├── forms.css            # Styles des formulaires
├── navigation.css       # Navigation, header, footer
├── dashboards.css       # Styles spécifiques des tableaux de bord
├── utilities.css        # Classes utilitaires réutilisables
└── responsive.css       # Media queries et design responsif
```

## Ordre de chargement dans base.html

Les fichiers CSS sont chargés dans cet ordre précis :

```html
1. variables.css       - Variables globales (doit être en premier)
2. reset.css          - Réinitialisation
3. typography.css     - Typographie
4. layout.css         - Layout
5. components.css     - Composants
6. forms.css          - Formulaires
7. navigation.css     - Navigation
8. dashboards.css     - Dashboards
9. utilities.css      - Utilitaires
10. responsive.css    - Responsive (doit être en dernier)
```

## Chaque fichier contient

### 1. **variables.css**
Toutes les variables CSS globales :
- Couleurs (primaires, secondaires, neutres)
- Typographie (familles, tailles, poids)
- Espacements (padding, margin, gaps)
- Radius, ombres, transitions
- Z-index, largeurs max

### 2. **reset.css**
- Réinitialisation universelle (*) 
- Styles de base pour html, body
- Styles par défaut pour titres, paragraphes, listes
- Styles pour images, tableaux, code

### 3. **typography.css**
- Classes pour tailles de texte (.text-sm, .text-lg, etc.)
- Poids de police (.font-bold, .font-semibold, etc.)
- Couleurs de texte (.text-primary, .text-danger, etc.)
- Alignement, décoration, hauteur de ligne
- Utilitaires spécialisés (.truncate, .line-clamp-*, etc.)

### 4. **layout.css**
- Conteneurs (.container, .container-lg, .container-sm)
- Grille CSS (.grid, .grid-cols-*)
- Flexbox (.flex, .flex-col, .items-center, etc.)
- Positionnement (.relative, .absolute, .sticky, etc.)
- Z-index (.z-10, .z-fixed, etc.)
- Affichage (.block, .hidden, .flex, etc.)
- Espacements (.p-md, .m-lg, .gap-lg, etc.)

### 5. **components.css**
- Boutons (.btn, .btn-primary, .btn-lg, etc.)
- Cartes (.card, .card-header, .card-body, etc.)
- Cartes d'annonces (.listing-card)
- Badges (.badge, .badge-success, etc.)
- Alertes (.alert, .alert-danger, etc.)
- Tags (.tag, .tag.active)
- Pagination, breadcrumb, listes
- Avatars, dividers

### 6. **forms.css**
- Groupes de formulaires (.form-group)
- Labels (.label, .label.required)
- Champs de texte, textarea, select
- Checkboxes, radios, switchs
- Fichiers upload (.file-input-label)
- Range sliders
- Validation (.is-valid, .is-invalid)
- Texte d'aide (.form-text, .form-error, etc.)

### 7. **navigation.css**
- Header (.navbar, .navbar-brand)
- Liens de navigation (.nav-links)
- Dropdowns (.nav-dropdown, .dropdown-menu)
- Menu toggle mobile (.menu-toggle)
- Footer (.footer, .footer-section)
- Breadcrumb

### 8. **dashboards.css**
- Layout dashboard (.dashboard-container, .dashboard-sidebar)
- Menu sidebar (.sidebar-menu)
- Sections (.dashboard-section)
- Cartes statistiques (.stat-card)
- Tableaux (.dashboard-table)
- Onglets (.dashboard-tabs)
- Filtres, statuts, actions

### 9. **utilities.css**
- Arrière-plans (.bg-primary, .bg-light, etc.)
- Couleurs (.color-primary, .color-danger, etc.)
- Bordures (.border, .border-top, etc.)
- Radius (.rounded, .rounded-lg, etc.)
- Ombres (.shadow-md, .shadow-lg, etc.)
- Opacité (.opacity-50, .opacity-100, etc.)
- Transformations (.scale-*, .translate-*, etc.)
- Curseurs (.cursor-pointer, .cursor-not-allowed, etc.)
- Transitions, animations
- Dégradés, filtres
- Aspect ratio, skew

### 10. **responsive.css**
- Media queries pour tous les breakpoints
- Classes responsives (.d-md-none, .d-sm-block, etc.)
- Classes pour impression (@media print)
- Classes d'accessibilité
- Classes utilitaires responsives

## Variables CSS Disponibles

### Couleurs
```css
--primary: #007bff
--primary-dark: #0056b3
--primary-light: #e7f1ff
--success: #28a745
--danger: #dc3545
--warning: #ffc107
--white: #ffffff
--dark: #212529
--gray-100 à --gray-900
```

### Espacement
```css
--spacing-xs: 0.25rem
--spacing-sm: 0.5rem
--spacing-md: 1rem
--spacing-lg: 1.5rem
--spacing-xl: 2rem
--spacing-2xl: 3rem
```

### Radius
```css
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
--radius-xl: 16px
--radius-full: 9999px
```

### Ombres
```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1)
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1)
```

### Transitions
```css
--transition-fast: 150ms ease-in-out
--transition-base: 250ms ease-in-out
--transition-slow: 350ms ease-in-out
```

## Comment utiliser

### 1. Pour créer un bouton primaire
```html
<button class="btn btn-primary">Cliquez-moi</button>
```

### 2. Pour créer un conteneur centré
```html
<div class="container">Contenu centré</div>
```

### 3. Pour utiliser la grille
```html
<div class="grid grid-cols-3 gap-lg">
    <div>Colonne 1</div>
    <div>Colonne 2</div>
    <div>Colonne 3</div>
</div>
```

### 4. Pour utiliser flexbox
```html
<div class="flex items-center justify-between gap-md">
    <span>Gauche</span>
    <span>Droite</span>
</div>
```

### 5. Pour espacer un élément
```html
<div class="p-lg m-md bg-primary text-white">
    Contenu avec espacements et couleur
</div>
```

### 6. Pour un formulaire
```html
<form>
    <div class="form-group">
        <label for="email" class="required">Email</label>
        <input type="email" id="email" class="form-control">
        <div class="form-text">Votre adresse email</div>
    </div>
</form>
```

### 7. Pour rendre responsif
```html
<!-- Caché sur mobile, visible sur tablette+ -->
<div class="d-md-none">Mobile only</div>

<!-- Visible sur mobile, caché sur tablette+ -->
<div class="d-sm-block hide-on-desktop">Mobile content</div>
```

## Breakpoints Responsifs

```css
xs: 0 - 576px    (téléphones)
sm: 576 - 768px  (petites tablettes)
md: 768 - 992px  (tablettes)
lg: 992 - 1200px (petits écrans)
xl: 1200px+      (grands écrans)
```

## Bonnes pratiques

### ✅ À FAIRE
1. Utiliser les variables CSS pour les valeurs
2. Utiliser les classes utilitaires pour les espacements
3. Utiliser la grille pour les layouts
4. Utiliser flexbox pour l'alignement
5. Utiliser les classes de couleur plutôt que du CSS inline
6. Organiser les breakpoints responsifs

### ❌ À NE PAS FAIRE
1. Ne pas ajouter de CSS inline dans les templates HTML
2. Ne pas créer de nouvelles variables CSS hors de variables.css
3. Ne pas mélanger plusieurs systèmes de layout (grille + float)
4. Ne pas utiliser !important sans raison
5. Ne pas charger les CSS dans le désordre

## Fichiers CSS Obsolètes (À SUPPRIMER)

Les fichiers suivants ont été **fusionnés** dans la nouvelle structure :
- ❌ design-system.css (variables et styles mixtes)
- ❌ custom-styles.css (styles personnalisés - inclus dans les nouveaux fichiers)
- ❌ style.css (styles généraux - inclus dans les nouveaux fichiers)
- ❌ form_fields.css (inclus dans forms.css)
- ❌ dashboard_hotel.css, dashboard_individu.css, dashboard_residence.css (inclus dans dashboards.css)

Ces fichiers peuvent être archivés ou supprimés en toute sécurité.

## Maintenance et Extension

### Pour ajouter une nouvelle couleur
1. Modifier `variables.css`
2. Ajouter une classe utilitaire dans `utilities.css`

### Pour ajouter un nouveau composant
1. Modifier `components.css`
2. Créer des variantes avec les suffixes (-primary, -sm, etc.)

### Pour ajouter un nouveau style spécifique
1. Identifier la catégorie (layout, typo, etc.)
2. Ajouter dans le fichier approprié
3. Utiliser les variables CSS existantes

## Support et Questions

Pour toute question sur la structure CSS, consultez ce fichier de documentation ou examinez le code source des fichiers CSS.

---

**Dernière mise à jour:** 16 Mai 2026  
**Version:** 1.0 - Structure réorganisée
