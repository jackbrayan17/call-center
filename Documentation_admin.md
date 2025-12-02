## Documentation côté administrateur
Cette partie est destinée aux responsables techniques ou aux personnes qui gèrent la base d'entreprises et le suivi des appels.

### Accès et comptes
- Les comptes utilisateurs sont créés côté administrateur (interface Django admin ou script).
- Mot de passe d'accès aux appels : unique, partagé aux opérateurs, à changer périodiquement.

### Données entreprises
- Import CSV : remplace toute la liste. Vérifiez le fichier en préproduction si possible.
- Export CSV/Excel : récupère l'historique des appels et leurs statuts.
- Sauvegarde locale (sqlite) : copiez `db.sqlite3` régulièrement ou migrez vers une base serveur si plusieurs opérateurs.

### Statuts et qualité des données
- Veillez à ce que les opérateurs remplissent Présentation, Questions libres, Questions orientées pour obtenir des enquêtes « Complet ».
- Surveillez les statuts d'enquête par filière dans le tableau de bord pour repérer les secteurs en retard.

### Enregistrements et transcription
- Les fichiers audio sont stockés dans `media/recordings/` avec le nom de l'entreprise et la date.
- La transcription repose sur Whisper Web (chargé via internet) ; le premier chargement peut être plus long.

### Tableau de bord
- Métriques : appels réussis uniquement (statut « accepté »).
- Graphiques : répartition par filière, part des appels avec/sans audio, statuts d'enquête par filière.

### Journalisation et sessions (audit)
- Toutes les requêtes sont journalisées : utilisateur, IP, session, user-agent, URL, code HTTP, durée, date/heure, résumé du payload.
- Connexions/déconnexions : enregistrées (heure, IP, session) et marquées actives/inactives.
- Sessions actives : visibles dans l'admin (SessionSnapshot) avec dernière activité.
- Export CSV des logs : dans l'admin, sélectionnez des lignes AuditLog puis action « Exporter en CSV ».
- Rétention : les journaux plus anciens que 90 jours sont nettoyés automatiquement.

### Maintenance et sécurité
- Changer régulièrement le mot de passe d'accès aux appels et les mots de passe admin.
- Limiter l'accès à l'interface admin aux personnes autorisées.
- Maintenir navigateur et système à jour pour éviter les problèmes de micro ou de sécurité.
