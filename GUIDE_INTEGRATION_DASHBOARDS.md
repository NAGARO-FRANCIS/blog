# 📚 Guide Pratique - Intégration des Données aux Dashboards

## 🎯 Objectif

Ce guide explique comment connecter les données réelles de votre base de données aux nouveaux dashboards d'hôtel et de résidence.

---

## 📦 Prérequis

Assurez-vous que les modèles suivants existent dans votre projet:

```python
# Dans accounts/models.py
- Profile
- ProfessionalProfile

# Dans colocation/models.py (ou logement/models.py)
- ColocationAnnonce
- Favori
- Photo

# À créer si n'existe pas
- Reservation / Booking
- Review / Avis
- Payment / Paiement
```

---

## 📝 Étape 1: Créer les Modèles Manquants

### Si vous n'avez pas de modèle Reservation

```python
# Dans logement/models.py ou colocation/models.py

from django.db import models
from django.contrib.auth.models import User

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée'),
        ('completed', 'Complétée'),
    ]
    
    property = models.ForeignKey(
        'Logement',
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    guest = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reservations'
    )
    
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.property} - {self.check_in} à {self.check_out}"


class Review(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.CASCADE,
        related_name='review'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )  # 1-5 stars
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('completed', 'Complété'),
            ('failed', 'Échoué'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

Après création, exécutez:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔧 Étape 2: Mettre à Jour les Vues

### Pour le Dashboard Hôtel

```python
# Dans accounts/views.py

from datetime import datetime, timedelta
from django.utils import timezone
from logement.models import Logement, Reservation, Review, Payment

@login_required
def dashboard_hotel(request):
    """Dashboard pour les gestionnaires d'hôtel"""
    profile = request.user.profile
    
    if profile.account_type != 'hotel':
        return redirect('accounts:dashboard')
    
    try:
        prof_profile = profile.professionalprofile
    except:
        prof_profile = None
        return redirect('accounts:profil')
    
    # 1. Compter les chambres
    nb_chambres = Logement.objects.filter(
        owner=request.user,
        type_logement='chambre'
    ).count()
    
    # 2. Compter les réservations du mois courant
    today = timezone.now().date()
    first_day = today.replace(day=1)
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    nb_reservations = Reservation.objects.filter(
        property__owner=request.user,
        check_in__range=[first_day, last_day]
    ).count()
    
    # 3. Clients actifs (derniers 30 jours)
    thirty_days_ago = today - timedelta(days=30)
    nb_clients_actifs = Reservation.objects.filter(
        property__owner=request.user,
        created_at__gte=thirty_days_ago
    ).values('guest').distinct().count()
    
    # 4. Calculer le taux d'occupation
    total_chambres = nb_chambres
    reservations_actuelles = Reservation.objects.filter(
        property__owner=request.user,
        check_in__lte=today,
        check_out__gte=today,
        status__in=['confirmed', 'completed']
    ).count()
    taux_occupation = int((reservations_actuelles / total_chambres * 100)) if total_chambres > 0 else 0
    
    # 5. Revenu du mois
    revenu_mois = Payment.objects.filter(
        reservation__property__owner=request.user,
        created_at__range=[first_day, last_day],
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # 6. Moyenne des avis
    reviews = Review.objects.filter(
        reservation__property__owner=request.user
    )
    if reviews.exists():
        note_moyenne = reviews.aggregate(
            avg=models.Avg('rating')
        )['avg']
        note_moyenne = round(note_moyenne, 1)
        nb_avis = reviews.count()
    else:
        note_moyenne = 0
        nb_avis = 0
    
    # 7. Chambres disponibles aujourd'hui
    chambres_occupees = Reservation.objects.filter(
        property__owner=request.user,
        check_in__lte=today,
        check_out__gte=today,
        status__in=['confirmed', 'completed']
    ).count()
    chambres_disponibles = total_chambres - chambres_occupees
    
    # 8. Réservations récentes (prochaines 5)
    recent_reservations = Reservation.objects.filter(
        property__owner=request.user,
        check_in__gte=today
    ).select_related('guest').order_by('check_in')[:5]
    
    # Préparer les données pour le template
    recent_reservations_data = []
    for res in recent_reservations:
        recent_reservations_data.append({
            'guest_name': res.guest.get_full_name() or res.guest.username,
            'check_in': res.check_in,
            'check_out': res.check_out,
            'status': res.status,
            'amount': res.amount
        })
    
    # 9. Clients récents (tops 6)
    recent_clients = Reservation.objects.filter(
        property__owner=request.user,
        created_at__gte=thirty_days_ago
    ).values_list('guest', flat=True).distinct()[:6]
    
    recent_clients_data = []
    for guest_id in recent_clients:
        try:
            guest = User.objects.get(id=guest_id)
            visits = Reservation.objects.filter(
                guest=guest,
                property__owner=request.user
            ).count()
            # Moyenne note pour ce client
            guest_reviews = Review.objects.filter(
                reservation__guest=guest,
                reservation__property__owner=request.user
            )
            rating = guest_reviews.aggregate(
                avg=models.Avg('rating')
            )['avg'] or 4.5
            
            recent_clients_data.append({
                'name': guest.get_full_name() or guest.username,
                'visits': visits,
                'rating': round(rating, 1)
            })
        except User.DoesNotExist:
            pass
    
    # 10. Avis récents (derniers 5)
    recent_reviews = Review.objects.filter(
        reservation__property__owner=request.user
    ).select_related('reservation__guest').order_by('-created_at')[:5]
    
    recent_reviews_data = []
    for review in recent_reviews:
        recent_reviews_data.append({
            'author': review.reservation.guest.get_full_name() or review.reservation.guest.username,
            'rating': review.rating,
            'date': review.created_at.date(),
            'text': review.text[:200]  # Limiter la longueur
        })
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_chambres': nb_chambres,
        'nb_reservations': nb_reservations,
        'nb_clients_actifs': nb_clients_actifs,
        'taux_occupation': taux_occupation,
        'revenu_mois': f"{revenu_mois:,.0f}",
        'note_moyenne': note_moyenne,
        'nb_avis': nb_avis,
        'chambres_disponibles': chambres_disponibles,
        'recent_reservations': recent_reservations_data,
        'recent_clients': recent_clients_data,
        'recent_reviews': recent_reviews_data,
    }
    
    return render(request, 'accounts/dashboard_hotel.html', context)
```

### Pour le Dashboard Résidence

```python
# Code similaire avec adaptations pour résidences
# Remplacer 'chambre' par tous les types de logements
# Adapter les termes (locataires vs guests)

@login_required
def dashboard_residence(request):
    """Dashboard pour les gestionnaires de résidence"""
    profile = request.user.profile
    
    if profile.account_type != 'residence':
        return redirect('accounts:dashboard')
    
    try:
        prof_profile = profile.professionalprofile
    except:
        prof_profile = None
        return redirect('accounts:profil')
    
    # Logique similaire au dashboard_hotel
    # Compter TOUS les logements (pas juste les chambres)
    nb_logements = Logement.objects.filter(
        owner=request.user
    ).count()
    
    # Le reste du code est très similaire...
    # (voir dashboard_hotel() pour la structure complète)
    
    context = {
        'profile': profile,
        'prof_profile': prof_profile,
        'nb_logements': nb_logements,
        # ... autres variables
    }
    
    return render(request, 'accounts/dashboard_residence.html', context)
```

---

## 🎨 Étape 3: Personnaliser les Modèles de Données

Si vous utilisez d'autres noms ou structures pour vos modèles, adaptez les imports:

```python
# AVANT (exemple)
from logement.models import Logement, Reservation

# APRÈS (selon votre structure)
from votre_app.models import VotreLogement, VotreReservation
```

---

## ✅ Étape 4: Tester les Changements

1. **Vérifier les imports**:
```bash
python manage.py shell
from logement.models import Reservation
from django.contrib.auth.models import User
```

2. **Tester la vue**:
```bash
python manage.py runserver
# Naviguer vers /dashboard/ avec un compte hôtel/résidence
```

3. **Vérifier les données**:
```bash
# Dans Django shell
from logement.models import Reservation
print(Reservation.objects.count())  # Doit afficher le nombre de réservations
```

---

## 📊 Améliorations Optionnelles

### 1. Ajouter un Cache pour Performance

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache 5 minutes
@login_required
def dashboard_hotel(request):
    # ... code ...
```

### 2. Ajouter des Graphiques avec Chart.js

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<canvas id="occupancyChart"></canvas>

<script>
    const ctx = document.getElementById('occupancyChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Semaine 1', 'Semaine 2', 'Semaine 3', 'Semaine 4'],
            datasets: [{
                label: 'Taux d\'occupation',
                data: [65, 72, 78, 85],
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
            }]
        }
    });
</script>
```

### 3. Ajouter des Exports PDF

```bash
pip install reportlab
```

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_report_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport.pdf"'
    
    c = canvas.Canvas(response, pagesize=letter)
    c.drawString(100, 750, "Rapport de Gestion")
    c.drawString(100, 730, f"Taux d'occupation: {taux_occupation}%")
    c.save()
    
    return response
```

---

## 🐛 Dépannage

### Erreur: "Modèle Reservation n'existe pas"
**Solution**: Créer le modèle et exécuter les migrations

### Les données ne s'affichent pas
**Vérifier**:
1. Les données existent en DB: `python manage.py shell` → `Reservation.objects.count()`
2. Les noms de champs correspondent
3. Les filtres sont corrects

### Performance lente
**Solutions**:
1. Ajouter `.select_related()` pour réduire les requêtes
2. Ajouter `.prefetch_related()` pour relations M2M
3. Ajouter le cache (voir section cache)
4. Indexer les champs souvent filtrés

---

## 📚 Ressources Supplémentaires

- [Django ORM Documentation](https://docs.djangoproject.com/en/stable/topics/db/models/)
- [Django QuerySet API](https://docs.djangoproject.com/en/stable/ref/models/querysets/)
- [Django View Caching](https://docs.djangoproject.com/en/stable/topics/cache/)

---

**Besoin d'aide?** Consultez le code source des vues existantes dans `accounts/views.py`
