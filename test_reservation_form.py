#!/usr/bin/env python
"""
Test: Formulaire de réservation (Reservation form validation)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from logement.forms import ReservationForm
from logement.models import Logement, Reservation
from datetime import datetime, timedelta

print("=" * 80)
print("TEST: Formulaire de réservation")
print("=" * 80)

# Créer un utilisateur et un logement hôtel
print("\n1️⃣ Création du logement test")
user, _ = User.objects.get_or_create(
    username='louise_test',
    defaults={'email': 'louise@test.com', 'first_name': 'Louise'}
)
profile, _ = Profile.objects.get_or_create(
    user=user,
    defaults={'account_type': 'hotel', 'role': 'proprietaire'}
)

logement = Logement.objects.create(
    titre='Ban hotel',
    description='Une hôtel bien chic',
    ville='Man',
    quartier='zone',
    type_logement='villa',
    proprietaire=user,
    account_type='hotel',
    prix_par_nuit=50000,
    frais_nettoyage=999.99,
)

print(f"✅ Logement créé: {logement.id} (type: {logement.account_type})")

# Données de réservation
print("\n2️⃣ Données de réservation")
tomorrow = datetime.now().date() + timedelta(days=1)
next_week = tomorrow + timedelta(days=7)

reservation_data = {
    'date_arrivee': tomorrow.strftime('%Y-%m-%d'),
    'date_depart': next_week.strftime('%Y-%m-%d'),
    'nombre_personnes': '4',
    'nombre_chambres': '2',
    'client_nom': 'Francis Nagaro',
    'client_email': 'nagarofrancis697@gmail.com',
    'client_telephone': '0103280809',
    'remarques': 'DSF',
}

print(f"  Dates: {tomorrow} à {next_week}")
print(f"  Client: {reservation_data['client_nom']}")

# Test 3: Valider le formulaire
print("\n3️⃣ Validation du formulaire")
form = ReservationForm(data=reservation_data, logement=logement)
print(f"Formulaire valide: {form.is_valid()}")
if not form.is_valid():
    print("ERREURS:")
    for field, errors in form.errors.items():
        print(f"  {field}: {errors}")
    sys.exit(1)

# Test 4: Sauvegarder la réservation
print("\n4️⃣ Sauvegarde de la réservation")
try:
    reservation = form.save(commit=False)
    reservation.logement = logement
    reservation.prix_par_nuit = logement.prix_par_nuit or 0
    if logement.frais_nettoyage:
        reservation.frais_nettoyage_reservation = logement.frais_nettoyage
    reservation.save()
    print(f"✅ Réservation sauvegardée: {reservation.id}")
    print(f"  Logement: {reservation.logement.titre}")
    print(f"  Client: {reservation.client_nom}")
    print(f"  Dates: {reservation.date_arrivee} à {reservation.date_depart}")
    print(f"  Nuits: {reservation.nombre_nuits}")
    print(f"  Montant final: {reservation.montant_final}")
except Exception as e:
    print(f"❌ ERREUR lors de la sauvegarde: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print("\n✅ Réservation fonctionnelle!")
print("   - Formulaire valide: ✅")
print("   - Validation du modèle: ✅")
print("   - Sauvegarde: ✅")
print("\n🎉 Louise peut maintenant réserver!")

# Cleanup
reservation.delete()
logement.delete()
