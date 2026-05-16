# 🎨 Design System - Ivoire Connect

**Documentation complète du Design System professionnel**

---

## Table des Matières

1. [Overview](#overview)
2. [CSS Variables](#css-variables)
3. [Composants](#composants)
4. [Utilitaires](#utilitaires)
5. [Responsive Design](#responsive-design)
6. [Best Practices](#best-practices)

---

## Overview

Le Design System d'Ivoire Connect repose sur **CSS Variables** pour une maintenabilité maximale et une cohérence parfaite.

### Architecture

```
Design System (design-system.css)
├── Variables CSS
├── Composants réutilisables
├── Utilitaires
└── Responsive breakpoints

Custom Styles (custom-styles.css)
├── Navbar & Header
├── Footer
├── Cards & Layouts
└── Animations
```

### Avantages

✅ **Cohérence** - Même style partout  
✅ **Maintenabilité** - Changez une variable = change partout  
✅ **Professionnel** - Design moderne et polished  
✅ **Responsive** - Fonctionne sur tous les appareils  
✅ **Accessible** - WCAG AA minimum  

---

## CSS Variables

### Couleurs Principales

```css
/* Couleurs de base */
--primary: #007bff;           /* Bleu principal - Actions */
--primary-dark: #0056b3;      /* Bleu foncé - Hover */
--primary-light: #e7f1ff;     /* Bleu clair - Background */

--success: #28a745;           /* Vert - Succès */
--danger: #dc3545;            /* Rouge - Erreurs */
--warning: #ffc107;           /* Orange - Avertissements */
--info: #17a2b8;              /* Cyan - Infos */

--dark: #212529;              /* Noir - Texte principal */
--light: #f8f9fa;             /* Blanc cassé - Backgrounds */
--white: #ffffff;             /* Blanc - Purs */
```

### Couleurs Neutres

```css
--gray-900: #212529;          /* Très foncé */
--gray-800: #343a40;
--gray-700: #495057;
--gray-600: #6c757d;          /* Gris standard */
--gray-500: #adb5bd;
--gray-400: #ced4da;
--gray-300: #dee2e6;
--gray-200: #e9ecef;
--gray-100: #f8f9fa;          /* Très clair */
```

### Utilisation

```html
<!-- Couleur primaire -->
<button style="background: var(--primary)">Cliquez</button>

<!-- Couleur de succès -->
<div style="color: var(--success)">✅ Succès!</div>

<!-- Couleur neutre -->
<p style="color: var(--gray-600)">Texte secondaire</p>
```

---

## Espacement (Spacing)

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px - Standard */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

### Utilisation

```css
/* Padding */
.card {
    padding: var(--spacing-lg);        /* 24px */
}

/* Margin */
.form-group {
    margin-bottom: var(--spacing-md);  /* 16px */
}

/* Gap (Flexbox) */
.flex-container {
    display: flex;
    gap: var(--spacing-md);            /* 16px entre items */
}
```

---

## Typographie

### Font Sizes

```css
--font-size-base: 1rem;           /* 16px - Standard */
--font-size-sm: 0.875rem;         /* 14px */
--font-size-lg: 1.125rem;         /* 18px */
--font-size-xl: 1.25rem;          /* 20px */
--font-size-2xl: 1.5rem;          /* 24px */
--font-size-3xl: 1.875rem;        /* 30px */
```

### Font Weights

```css
--font-weight-normal: 400;        /* Regular */
--font-weight-medium: 500;        /* Medium */
--font-weight-semibold: 600;      /* Semi-bold */
--font-weight-bold: 700;          /* Bold */
```

### Utilisation

```html
<h1 style="font-size: var(--font-size-3xl); font-weight: var(--font-weight-bold);">
    Titre principal
</h1>

<p style="font-size: var(--font-size-base); color: var(--gray-600);">
    Texte standard
</p>

<small style="font-size: var(--font-size-sm);">
    Texte petit
</small>
```

---

## Ombres (Shadows)

```css
--shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);      /* Standard */
--shadow-lg: 0 10px 30px rgba(0, 0, 0, 0.15);
```

### Utilisation

```css
.card {
    box-shadow: var(--shadow-md);     /* Ombre standard */
    border-radius: 8px;
}

.card:hover {
    box-shadow: var(--shadow-lg);     /* Ombre au survol */
}
```

---

## Transitions

```css
--transition-fast: all 0.2s ease;
--transition-base: all 0.3s ease;      /* Standard */
--transition-slow: all 0.5s ease;
```

### Utilisation

```css
.button {
    background: var(--primary);
    transition: var(--transition-base);
}

.button:hover {
    background: var(--primary-dark);
    transform: translateY(-2px);
}
```

---

## Composants

### Boutons

```html
<!-- Bouton primaire -->
<button class="btn btn-primary">Bouton primaire</button>

<!-- Bouton secondaire -->
<button class="btn btn-secondary">Bouton secondaire</button>

<!-- Bouton danger -->
<button class="btn btn-danger">Supprimer</button>

<!-- Bouton large -->
<button class="btn btn-primary btn-lg">Bouton large</button>

<!-- Bouton small -->
<button class="btn btn-primary btn-sm">Bouton petit</button>
```

**Styles**

```css
.btn {
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: 8px;
    font-weight: var(--font-weight-semibold);
    transition: var(--transition-base);
    border: none;
    cursor: pointer;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: var(--primary-dark);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 123, 255, 0.3);
}

.btn-lg {
    padding: var(--spacing-lg) var(--spacing-xl);
    font-size: var(--font-size-lg);
}
```

---

### Formulaires

```html
<fieldset class="form-section">
    <legend>Informations Personnelles</legend>
    
    <div class="form-group">
        <label for="name">Nom complet</label>
        <input 
            type="text" 
            id="name" 
            class="form-input" 
            placeholder="Jean Dupont"
        >
    </div>
    
    <div class="form-group">
        <label for="email">Email</label>
        <input 
            type="email" 
            id="email" 
            class="form-input"
            placeholder="jean@example.com"
        >
    </div>
    
    <div class="form-group">
        <label for="message">Message</label>
        <textarea 
            id="message" 
            class="form-input" 
            rows="4"
        ></textarea>
    </div>
</fieldset>
```

**Styles**

```css
.form-section {
    background: white;
    border-radius: 12px;
    padding: var(--spacing-xl);
    margin-bottom: var(--spacing-xl);
    box-shadow: var(--shadow-md);
}

.form-section legend {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--spacing-lg);
    color: var(--dark);
}

.form-group {
    margin-bottom: var(--spacing-lg);
}

.form-group label {
    display: block;
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--spacing-sm);
    color: var(--dark);
}

.form-input {
    width: 100%;
    padding: var(--spacing-md);
    border: 2px solid var(--gray-300);
    border-radius: 8px;
    font-size: var(--font-size-base);
    transition: var(--transition-base);
    background: white;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--primary-light);
}
```

---

### Cartes (Cards)

```html
<div class="card">
    <div class="card-body">
        <h3>Titre de la carte</h3>
        <p>Contenu de la carte</p>
    </div>
</div>
```

**Styles**

```css
.card {
    background: white;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    overflow: hidden;
    transition: var(--transition-base);
}

.card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px);
}

.card-body {
    padding: var(--spacing-lg);
}
```

---

### Alertes

```html
<div class="alert alert-success">✅ Opération réussie!</div>
<div class="alert alert-danger">❌ Une erreur s'est produite</div>
<div class="alert alert-warning">⚠️ Attention!</div>
<div class="alert alert-info">ℹ️ Information</div>
```

**Styles**

```css
.alert {
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: 8px;
    margin-bottom: var(--spacing-md);
    border-left: 4px solid transparent;
}

.alert-success {
    background-color: #d4edda;
    border-color: var(--success);
    color: #155724;
}

.alert-danger {
    background-color: #f8d7da;
    border-color: var(--danger);
    color: #721c24;
}

.alert-warning {
    background-color: #fff3cd;
    border-color: var(--warning);
    color: #856404;
}

.alert-info {
    background-color: #d1ecf1;
    border-color: var(--info);
    color: #0c5460;
}
```

---

## Utilitaires

### Spacing Utilities

```css
/* Margin */
.mt-1 { margin-top: var(--spacing-sm); }
.mt-2 { margin-top: var(--spacing-md); }
.mb-1 { margin-bottom: var(--spacing-sm); }
.mb-2 { margin-bottom: var(--spacing-md); }

/* Padding */
.p-1 { padding: var(--spacing-sm); }
.p-2 { padding: var(--spacing-md); }
```

### Text Utilities

```css
.text-center { text-align: center; }
.text-primary { color: var(--primary); }
.text-muted { color: var(--gray-600); }
.text-bold { font-weight: var(--font-weight-bold); }
```

### Display Utilities

```css
.d-flex { display: flex; }
.d-grid { display: grid; }
.gap-2 { gap: var(--spacing-md); }
.w-100 { width: 100%; }
.h-100 { height: 100%; }
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first */
0px - 576px              /* Mobile */
576px - 768px            /* Tablet petite */
768px - 992px            /* Tablet grande */
992px+                   /* Desktop */
```

### Utilisation

```css
/* Mobile (par défaut) */
.container {
    display: grid;
    grid-template-columns: 1fr;
}

/* Tablet */
@media (min-width: 768px) {
    .container {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1200px) {
    .container {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### Exemples d'Utilisation

```html
<!-- Container responsive -->
<div class="container">
    Contenu centré max-width 1200px
</div>

<!-- Grid responsive -->
<div class="row">
    <div class="col-md-6">50% mobile, 50% tablet, 50% desktop</div>
    <div class="col-md-6">50% mobile, 50% tablet, 50% desktop</div>
</div>
```

---

## Best Practices

### ✅ À FAIRE

```html
<!-- Utiliser les CSS variables -->
<button style="background: var(--primary); padding: var(--spacing-md);">
    Cliquez-moi
</button>

<!-- Utiliser les classes réutilisables -->
<div class="card">
    <div class="card-body">
        <h3>Titre</h3>
    </div>
</div>

<!-- Structure sémantique -->
<fieldset class="form-section">
    <legend>Formulaire</legend>
    <div class="form-group">
        <label for="input">Label</label>
        <input id="input" class="form-input">
    </div>
</fieldset>
```

### ❌ À ÉVITER

```html
<!-- Pas de couleurs hardcodées -->
<button style="background: #007bff;">❌ Mauvais</button>

<!-- Pas de styles inline complexes -->
<div style="padding: 1rem; margin: 2rem; background: white; border-radius: 12px;">
    ❌ Mauvais - Utiliser les classes
</div>

<!-- Pas de structure non-sémantique -->
<div style="font-weight: bold; font-size: 1.5rem;">
    ❌ Mauvais - Utiliser <h2> ou <h3>
</div>
```

### Performance

- ✅ Minifiez le CSS en production
- ✅ Utilisez des images optimisées
- ✅ Lazy-load les images
- ✅ Compressez les fichiers CSS/JS

---

## Dark Mode

```css
@media (prefers-color-scheme: dark) {
    :root {
        --dark: #f0f0f0;
        --light: #1e1e1e;
        --primary-light: #1a3a52;
    }
}
```

---

## Support Navigateurs

- ✅ Chrome 49+
- ✅ Firefox 31+
- ✅ Safari 9.1+
- ✅ Edge 15+
- ✅ iOS Safari 9.3+

---

**Version**: 1.0.0  
**Dernière mise à jour**: May 14, 2026  
**Mainteneur**: Ivoire Connect Team
