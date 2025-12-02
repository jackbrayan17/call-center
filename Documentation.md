# Documentation de l'application d'appels Naumur

Ce guide s'adresse à toute personne (même débutante) qui utilise l'application pour passer des appels, enregistrer, transcrire et suivre les résultats. Aucune connaissance technique n'est nécessaire.

## Comment utiliser l'application

### 1. Accéder à la zone d'appels
- Ouvrez l'application dans votre navigateur (adresse fournie par votre administrateur).
- Cliquez sur « Appels » puis entrez le mot de passe communiqué. Pas de création de compte requise.

### 2. Parcours d'appel (liste des entreprises)
- Vous voyez la liste des entreprises à joindre, avec leur statut et l'inspecteur associé.
- Pour trouver une entreprise :
  - Tapez un nom, une activité ou un téléphone dans la barre de recherche.
  - Filtrez par produit/filière via la liste déroulante.
- Cliquez sur « Lancer un appel » pour ouvrir le formulaire de l'entreprise choisie.

### 3. Formulaire d'appel (pendant l'appel)
1) **Enregistrement vocal**
   - Cliquez « Lancer le micro » pour démarrer. Quand l'enregistrement tourne, seuls « Pause » puis « Continuer » restent visibles.
   - Si besoin, cliquez « Continuer sans enregistrement vocal ».
2) **Statuts**
   - Sélectionnez d'abord le « Statut numéros » (ex. décroché).
   - Si décroché, choisissez le « Statut appel » (accepté, rappel, refusé...).
   - Si l'appel est « accepté », renseignez les niveaux : Présentation, Questions libres, Questions orientées.
   - Le **Statut d'enquête** se calcule automatiquement :
     - **Complet** : tous les niveaux sont à « complete ».
     - **Partiel** : au moins un niveau est à « partial ».
     - **Incomplet** : sinon.
3) **Transcription en direct**
   - L'application tente de transcrire automatiquement pendant l'enregistrement (modèle Whisper dans le navigateur).
   - Bouton « Transcrire » pour relancer manuellement.
   - Boutons « Copier » et « Télécharger » pour récupérer le texte.
   - Note : le chargement du modèle nécessite internet et peut prendre du temps.
4) **Valider**
   - Cliquez « Valider l'enregistrement » pour sauvegarder l'appel, le statut, l'audio et la transcription.

### 4. Importer des entreprises (CSV)
- Menu « Import CSV ».
- Importez un fichier CSV (séparateur virgule ou point-virgule détecté automatiquement).
- En-têtes reconnus : `name`, `phone`, `product`, `activity`, `location`, `legal_form`, `niu`, `validity_score`, `status`.
- Vérifiez l'aperçu puis confirmez pour remplacer la liste actuelle d'entreprises.

### 5. Exporter les appels
- Menu « Export ».
- Choisissez CSV ou Excel (xlsm) pour récupérer tous les appels avec leurs statuts et l'indicateur audio (oui/non).

### 6. Tableau de bord
- Cartes de synthèse : appels réussis, entreprises, appels aboutis.
- Graphiques :
  - Camembert par filière (appels réussis).
  - Camembert appels réussis avec/sans enregistrement.
  - Barres empilées : statuts d'enquête (Complet/Partiel/Incomplet) par filière.
- Badges de statuts des contacts : en attente, en cours, rappel, terminé.

### 7. Bonnes pratiques
- Tester le micro avant un appel réel.
- Attendre le chargement du modèle de transcription si vous l'utilisez.
- Exporter régulièrement si vous travaillez sur une base locale.

### 8. Dépannage rapide
- **Micro non détecté** : autorisez le micro dans votre navigateur.
- **Transcription lente** : patienter lors du premier chargement (internet requis).
- **Statuts figés** : rafraîchir la page et vérifier que l'application est bien ouverte dans le navigateur.

## Glossaire des mots-clés
- **Statut numéros** : résultat du numéro appelé (décroché, répondeur, invalide...).
- **Statut appel** : issue de la conversation (accepté, rappel, refusé, mauvais numéro...).
- **Statut d'enquête** : niveau de complétion du questionnaire (Complet, Partiel, Incomplet) calculé à partir des trois niveaux.
- **Présentation / Questions libres / Questions orientées** : sections du questionnaire à renseigner si l'appel est accepté.
- **Filière / Produit** : secteur ou produit principal de l'entreprise.
- **Enregistrement vocal** : fichier audio capturé pendant l'appel (format webm/mp4).
- **Transcription** : texte généré automatiquement à partir de l'audio (Whisper Web).
- **Appels réussis** : appels marqués comme « acceptés ».
- **Avec audio / Sans audio** : indique si un enregistrement vocal est associé à l'appel.

## Support
Pour toute demande (accès, mots de passe, déploiement), contactez votre administrateur technique.
