# Naumur – Application d’appels

Application Django pour piloter des campagnes d’appels : import de bases entreprises, parcours d’appel guidé avec enregistrement audio, suivi des statuts, export consolidé et tableau de bord en temps réel.

## 1) Prérequis
- Python 3.12+ conseillé
- Django 5.2.x (installé via `pip install "Django>=5.2,<5.3"`)
- Navigateurs modernes avec accès micro (HTTPS recommandé hors `localhost`)
- FFmpeg non requis : l’enregistrement se fait côté navigateur en WebM/MP4 puis stocké tel quel.

## 2) Installation locale rapide
```bash
python -m venv .venv
.venv\Scripts\activate  # sur Windows ; utiliser source .venv/bin/activate sur Linux/Mac
pip install "Django>=5.2,<5.3"
python manage.py migrate
python manage.py createsuperuser  # crée l’utilisateur opérateur (mot de passe utilisé à la connexion appels)
python manage.py runserver 0.0.0.0:8000
```
Accéder ensuite à http://127.0.0.1:8000/  
Une base SQLite (`db.sqlite3`) est fournie. Si elle est vide, l’application crée 4 sociétés de démonstration au premier accès au dashboard/contacts.

## 3) Structure principale
- `app_site/settings.py` : configuration Django (SQLite, `MEDIA_ROOT=media`, `CALL_PASSCODE` non utilisé pour l’instant, `ALLOWED_HOSTS=['*']`).
- `home/models.py` : modèles `Company`, `CallRecord`, `Recording`.
- `home/views.py` + `home/templates/home/` : pages Accueil, Dashboard, Contacts, Import, Export, Accès appels, Liste d’appels, Formulaire d’appel.
- `media/recordings/` : fichiers audio générés lors des appels.

## 4) Parcours utilisateur
1) **Connexion opérateur** (`/appels/acces/`)  
   - Entrer le mot de passe de n’importe quel utilisateur Django actif (créé via `createsuperuser` ou l’admin). L’identifiant n’est pas demandé : le mot de passe est testé sur tous les utilisateurs actifs.
2) **Liste d’appels** (`/appels/`)  
   - Tableau paginé (50 lignes) avec statut : `pending` (à appeler), `in_progress`, `callback`, `done`.  
   - Bouton “Lancer un appel” verrouillé si un autre opérateur a déjà mis la fiche “en cours”.
   - Si un enregistrement existe, un bouton “Lecture” permet d’écouter l’audio stocké.
3) **Formulaire d’appel** (`/appels/<id>/remplir/`)  
   - Le passage sur la fiche passe son statut à `in_progress`. En fermant l’onglet sans valider, un appel AJAX la remet en `pending`.  
   - Démarrer le micro (`Lancer le micro`) pour activer les sélecteurs. L’enregistrement est fait via `MediaRecorder`, en WebM/MP4 selon le navigateur.  
   - Option “Continuer sans enregistrement vocal” disponible ; sinon le formulaire exige le démarrage du micro.  
   - Choisir un **Statut numéros** (Invalid, Pas de réponse, Répondeur, Décroche). Si “Décroche”, renseigner ensuite un **Statut appel** :
        - `bad_number` (Mauvais numéro)
        - `not_transformer` (Pas transformateur)
        - `callback` (Rappel – laisse la société en statut `callback`)
        - `refused` (Refus questionnaire)
        - `accepted` (Accepte questionnaire – déclenche les champs niveaux)
   - Si `accepted`, remplir les niveaux : **Présentation**, **Questions libres**, **Questions orientées** (`partial` ou `complete`).  
   - Un horodatage est posé quand vous changez un statut. Soumettre valide l’appel, associe l’utilisateur connecté, et charge le fichier audio dans `media/recordings/call_<id>.ext`.
4) **Dashboard** (`/dashboard/`)  
   - Compteurs d’entreprises, appels, décroché, répartition des statuts contacts/appels.
5) **Contacts** (`/contacts/`)  
   - Liste simple des sociétés avec statut actuel.

## 5) Importer des entreprises (CSV)
- Page : `/import-entreprises/`.
- Le CSV peut avoir des en-têtes ou non, séparateur auto-détecté (`,` ou `;`).
- Colonnes lues (détection souple) : `name`, `phone`, `product`, `activity`, `location`, `legal_form`, `niu`, `validity_score`, `status`.
- Statuts acceptés : `pending`, `in_progress`, `callback`, `done` (sinon `pending`).  
- Étapes : charger le fichier ➜ prévisualisation ➜ “Enregistrer et remplacer la base” : supprime toutes les sociétés existantes puis insère celles du CSV.

## 6) Export des appels
- Page : `/export/`.
- Deux formats : CSV ou “Excel” (TSV avec extension `.xlsm` pour ouverture rapide).
- Colonnes : entreprise, téléphone, produit, activité, localisation, forme, NIU, score, statut numéros, statut appel, niveaux (présentation/libres/orientées), indicateur enquête, horodatage, présence audio.

## 7) Modèles de données
- `Company`  
  - `status` ∈ `{pending, in_progress, callback, done}`  
  - Champs info : `name`, `phone`, `product`, `activity`, `location`, `legal_form`, `niu`, `validity_score`.
- `CallRecord` (lié à `Company` et `User`)  
  - `status_numero` ∈ `{invalid, no_answer, voicemail, answered}`  
  - `call_status` ∈ `{bad_number, not_transformer, callback, refused, accepted}` (optionnel si pas “answered”)  
  - Niveaux : `presentation_level`, `questions_libres_level`, `questions_orientees_level` ∈ `{partial, complete}` ou vide.  
  - Horodatages : `created_at`, `status_marked_at`, `recording_started_at`, `recording_stopped_at`.
- `Recording` (lié à `CallRecord`)  
  - `file` stocké dans `media/recordings/`, `mime_type`, `duration_seconds` (0 par défaut).

## 8) Points d’attention pour la prod
- Remplacer `SECRET_KEY`, désactiver `DEBUG`, fixer `ALLOWED_HOSTS`.
- Servir les fichiers médias (`MEDIA_ROOT/media`) via le serveur web (Nginx/Apache) et sécuriser l’accès.
- Forcer HTTPS pour éviter les blocages micro par le navigateur.
- Sauvegarder régulièrement `db.sqlite3` et le dossier `media/`.
- Mettre en place des comptes utilisateurs dédiés aux opérateurs (un mot de passe par opérateur) ; la page de connexion accepte tout utilisateur actif dont le mot de passe est saisi.

## 9) Raccourcis utiles
- Lancer le serveur : `python manage.py runserver 0.0.0.0:8000`
- Créer un superuser : `python manage.py createsuperuser`
- Réinitialiser les sociétés via un nouvel import CSV : `/import-entreprises/`
- Export des résultats : `/export/`

## 10) Arborescence simplifiée
```
.
├─ manage.py
├─ app_site/
├─ home/
│  ├─ models.py / views.py / forms.py / urls.py
│  └─ templates/home/*.html
├─ media/recordings/        # audio créés après validation d’un appel
└─ db.sqlite3               # base SQLite par défaut
```

Prêt à l’usage : démarrez le serveur, créez un utilisateur, connectez-vous sur `/appels/acces/`, et suivez le parcours d’appel.***
