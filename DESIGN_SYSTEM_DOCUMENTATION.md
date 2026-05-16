# 🎨 Ivoire Connect - Design System Documentation

## Overview

Ivoire Connect utilise un **design system complet** pour maintenir la cohérence visuelle, l'accessibilité et la performance à travers toute la plateforme.

## 📁 Architecture CSS

### Fichiers principaux :

1. **`static/design-system.css`** (450+ lignes)
   - Variables CSS (colors, spacing, typography, shadows)
   - Composants réutilisables (buttons, forms, cards, alerts)
   - Utilitaires (spacing, flexbox, grid, responsive)
   - Base reset et styles sémantiques

2. **`static/custom-styles.css`** (600+ lignes)
   - Styles spécifiques à Ivoire Connect
   - Navigation et footer personnalisés
   - Cartes de publication
   - Progress bars et étapes
   - Modals et notifications
   - Image galleries et badges

3. **`templates/base.html`** [UPDATED]
   - Header professionnel avec navigation responsive
   - Footer avec 4 sections (About, Links, Support, Contact)
   - Messages flash intégrés
   - Mobile-first design

## 🎯 Design System Variables

### Colors

```css
--color-primary: #007bff;          /* Bleu principal */
--color-secondary: #6c757d;        /* Gris secondaire */
--color-success: #28a745;          /* Vert de succès */
--color-danger: #dc3545;           /* Rouge d'erreur */
--color-warning: #ffc107;          /* Jaune d'avertissement */
--color-info: #17a2b8;             /* Cyan d'info */
--color-light: #f8f9fa;            /* Gris clair */
--color-dark: #212529;             /* Gris foncé */
--color-white: #ffffff;            /* Blanc */
```

### Spacing

```css
--spacing-xs: 0.25rem;    /* 4px */
--spacing-sm: 0.5rem;     /* 8px */
--spacing-md: 1rem;       /* 16px */
--spacing-lg: 1.5rem;     /* 24px */
--spacing-xl: 2rem;       /* 32px */
--spacing-2xl: 3rem;      /* 48px */
```

### Typography

```css
--font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
--font-size-base: 1rem;           /* 16px */
--font-size-lg: 1.125rem;         /* 18px */
--font-size-xl: 1.25rem;          /* 20px */
--font-size-2xl: 1.5rem;          /* 24px */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### Shadows

```css
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 12px 20px rgba(0, 0, 0, 0.15);
```

### Transitions

```css
--transition-fast: 0.15s ease;
--transition-base: 0.3s ease;
--transition-slow: 0.5s ease;
```

## 🧩 Composants Principaux

### Buttons

```html
<!-- Primary Button -->
<button class="btn btn-primary">Action</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">Retour</button>

<!-- Large Button -->
<button class="btn btn-primary btn-lg">Continuer</button>

<!-- Danger Button -->
<button class="btn btn-danger">Supprimer</button>
```

### Forms

```html
<!-- Form Group -->
<div class="form-group">
    <label for="email" class="form-label">Email</label>
    <input type="email" id="email" class="form-input" placeholder="votre@email.com">
</div>

<!-- Form Select -->
<select class="form-select">
    <option>Choisir...</option>
</select>

<!-- Checkbox -->
<div class="form-check">
    <input type="checkbox" id="agree" class="form-check-input">
    <label for="agree" class="form-check-label">Je suis d'accord</label>
</div>
```

### Cards

```html
<div class="card">
    <div class="card-header">Titre</div>
    <div class="card-body">Contenu</div>
    <div class="card-footer">Pied de page</div>
</div>
```

### Alerts

```html
<div class="alert alert-success">✅ Succès!</div>
<div class="alert alert-danger">❌ Erreur!</div>
<div class="alert alert-warning">⚠️ Attention!</div>
<div class="alert alert-info">ℹ️ Information</div>
```

### Badges

```html
<span class="badge badge-primary">Principal</span>
<span class="badge badge-success">Succès</span>
<span class="badge badge-danger">Danger</span>
```

## 📱 Responsive Breakpoints

```css
Mobile-first approach:
- Default: 0 - 576px (Mobile)
- Tablet: 576px - 768px 
- Desktop: 768px+
- Large Desktop: 1200px+
```

## 🎨 Utility Classes

### Spacing

```html
<!-- Margin Top -->
<div class="mt-1">4px top margin</div>
<div class="mt-5">48px top margin</div>

<!-- Margin Bottom -->
<div class="mb-2">8px bottom margin</div>

<!-- Padding -->
<div class="p-4">24px padding all</div>
```

### Flexbox

```html
<div class="d-flex justify-center align-center gap-2">
    Centered flex container
</div>

<div class="d-flex flex-column gap-3">
    Vertical flex layout
</div>
```

### Text

```html
<p class="text-center">Centré</p>
<p class="text-muted">Gris clair</p>
<p class="text-lg">Texte grand</p>
<p class="text-bold">Texte gras</p>
```

## 🎭 Dark Mode Support

Le design system supporte le dark mode via `prefers-color-scheme`:

```css
@media (prefers-color-scheme: dark) {
    /* Styles sombres */
}
```

## 📚 Templates Appliquées

### ✅ Complètement Redesignées

1. **`accounts/inscription_individu_role.html`**
   - Cartes interactives avec gradients
   - Grid responsive 1-3 colonnes
   - Icônes emoji et descriptions
   - Animation au clic

2. **`templates/base.html`**
   - Navigation moderne avec logo
   - Footer structuré en 4 colonnes
   - Messages flash intégrés
   - Mobile-responsive

### 🔄 À Continuer

1. **`accounts/inscription_individu_form.html`**
   - Sections avec fieldsets
   - Form groups standardisés
   - Boutons cohérents

2. **`logement/detail_logement.html`**
   - Galerie d'images responsive
   - Card pour infos propriété
   - Bouton réservation prominent

3. **`logement/reserver_logement.html`**
   - Form de dates avec calendrier
   - Infos invité
   - Résumé du prix

4. **`logement/paiement_reservation.html`**
   - Stripe integration styling
   - Résumé réservation
   - Statut paiement

5. **`logement/ajouter_logement_base.html`**
   - Sections formulaire
   - Upload photos
   - Prévisualisation

## 🚀 Best Practices

### 1. Toujours utiliser les variables CSS
```css
/* ❌ À éviter */
color: #007bff;

/* ✅ Préférer */
color: var(--color-primary);
```

### 2. Utiliser les classes utilitaires
```html
<!-- ❌ À éviter -->
<div style="margin-top: 16px; padding: 24px;">

<!-- ✅ Préférer -->
<div class="mt-4 p-4">
```

### 3. Composants composables
```html
<!-- ✅ Bon -->
<button class="btn btn-primary btn-lg">
```

### 4. Accessibilité
- Toujours utiliser les labels avec les inputs
- Sémantique HTML correcte
- Contraste suffisant (WCAG AA minimum)

### 5. Performance
- Classes CSS préférer aux styles inline
- Utiliser les composants réutilisables
- Minifier les CSS en production

## 🔧 Customization

Pour ajouter des thèmes supplémentaires, modifier les variables CSS dans `design-system.css`:

```css
:root {
    --color-primary: #007bff;
    /* Modifier ici les valeurs globales */
}

/* Thème alternatif */
body.theme-dark {
    --color-primary: #1E88E5;
    --background: #1a1a1a;
}
```

## 📖 Ressources

- Design System Colors: `design-system.css` (lignes 10-35)
- Component Library: `design-system.css` (lignes 80-250)
- Utilities: `design-system.css` (lignes 250-400)
- Custom Styles: `custom-styles.css` (lignes 1-100+)

## ✨ Prochaines Améliorations

1. ✅ Design system de base créé
2. ✅ CSS variables et composants définis
3. ✅ Navigation et footer redessinés
4. ⏳ Templates restants à appliquer
5. ⏳ Dark mode complet
6. ⏳ Animations et transitions
7. ⏳ Icônes SVG intégrées
8. ⏳ Documentation interactive

---

**Maintenu par**: Équipe Ivoire Connect
**Dernière mise à jour**: 2026
**Version**: 1.0.0
