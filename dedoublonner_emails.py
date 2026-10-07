import os
import sys
import collections

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ivoire.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
appliquer = '--appliquer' in sys.argv

groupes = collections.defaultdict(list)
for u in User.objects.exclude(email='').order_by('id'):
    groupes[u.email.strip().lower()].append(u)

total = 0
for email, users in groupes.items():
    if len(users) < 2:
        continue
    garde, autres = users[0], users[1:]
    print(f"{email} : conservé pour {garde.username} (id {garde.id})")
    local, _, domaine = email.partition('@')
    local = local.split('+')[0]
    for u in autres:
        nouveau = f"{local}+u{u.id}@{domaine}"
        print(f"   {u.username} (id {u.id}) : {u.email} -> {nouveau}")
        if appliquer:
            u.email = nouveau
            u.save(update_fields=['email'])
        total += 1

if not total:
    print("Aucun doublon.")
elif not appliquer:
    print("\nSimulation seulement. Pour appliquer : python dedoublonner_emails.py --appliquer")
else:
    print(f"\n{total} adresse(s) modifiée(s).")