# Spécifications du Module Perdiem

## 1. Présentation générale

### 1.1 Objet du document
Ce document présente les spécifications fonctionnelles du module Perdiem intégré dans la solution E-GESTOCK pour Odoo Community 18. Il détaille les fonctionnalités, les modèles de données, les workflows et les interfaces utilisateur du module.

### 1.2 Contexte
Le module Perdiem fait partie de la solution E-GESTOCK et permet la gestion des demandes de perdiem (indemnités journalières) au sein de l'organisation. Il s'intègre avec les autres modules de la solution, notamment la gestion budgétaire et la comptabilité.

### 1.3 Contexte technique
Le module Perdiem est développé en PHP avec le framework Laravel. Il utilise une base de données relationnelle et s'intègre dans l'architecture globale de la solution E-GESTOCK.

## 2. Modèles de données

### 2.1 Perdiem
Modèle principal pour les demandes de perdiem.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `num_pdm` : Numéro de la demande de perdiem (unique)
- `libelle` : Libellé/description de la demande
- `num_or` : Numéro d'ordre
- `code_gestion` : Code du type de gestion
- `exercice` : Année de l'exercice budgétaire
- `ref_fam` : Référence de la famille d'articles (compte budgétaire)
- `code_structure` : Code de la structure organisationnelle
- `solde_avant_op` : Solde budgétaire avant opération
- `credit_budgetaires_id` : Référence au crédit budgétaire
- `montant_total` : Montant total de la demande
- `flag_engagement` : Indicateur d'engagement budgétaire (booléen)
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### 2.2 DetailPerdiem
Détails des bénéficiaires et montants pour chaque demande de perdiem.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `perdiems_id` : Référence à la demande de perdiem (clé étrangère)
- `nom_prenoms` : Nom et prénoms du bénéficiaire
- `montant` : Montant alloué au bénéficiaire
- `piece` : Document justificatif (fichier)
- `piece_name` : Nom du fichier justificatif
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### 2.3 StatutPerdiem
Suivi des statuts de la demande de perdiem dans le workflow de validation.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `perdiems_id` : Référence à la demande de perdiem (clé étrangère)
- `type_statut_perdiems_id` : Référence au type de statut (clé étrangère)
- `profils_id` : Référence au profil utilisateur (clé étrangère)
- `date_debut` : Date de début du statut
- `date_fin` : Date de fin du statut
- `commentaire` : Commentaire sur le changement de statut
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### 2.4 TypeStatutPerdiem
Types de statuts possibles pour les demandes de perdiem.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `libelle` : Libellé du statut
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### 2.5 SignatairePerdiem
Signataires requis pour la validation des demandes de perdiem.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `profil_fonctions_id` : Référence au profil et fonction du signataire
- `perdiems_id` : Référence à la demande de perdiem
- `flag_actif` : Indicateur d'activation du signataire
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

### 2.6 StatutSignatairePerdiem
Suivi des statuts des signataires dans le processus de validation.

**Champs :**
- `id` : Identifiant unique (clé primaire)
- `signataire_perdiems_id` : Référence au signataire
- `type_statut_sign_id` : Référence au type de statut du signataire
- `profils_id` : Référence au profil utilisateur
- `date_debut` : Date de début du statut
- `date_fin` : Date de fin du statut
- `commentaire` : Commentaire sur le changement de statut
- `created_at` : Date de création
- `updated_at` : Date de dernière modification

## 3. Workflow de validation

Le workflow de validation des demandes de perdiem suit les étapes suivantes :

1. **Création** - Saisie initiale de la demande de perdiem
2. **Soumission pour validation** - La demande est soumise pour validation avec le statut "Soumis pour validation"
3. **Validation hiérarchique** - Validation par les différents niveaux hiérarchiques selon la configuration
4. **Contrôle budgétaire** - Vérification de la disponibilité des fonds
5. **Validation finale** - Approbation finale de la demande
6. **Engagement budgétaire** - Engagement des fonds dans le budget

## 4. Fonctionnalités principales

### 4.1 Création d'une demande de perdiem
- Saisie des informations générales (libellé, structure, famille d'articles)
- Sélection du crédit budgétaire
- Ajout des bénéficiaires et montants
- Calcul automatique du montant total
- Vérification du solde budgétaire disponible

### 4.2 Validation des demandes
- Circuit de validation configurable
- Notification aux validateurs
- Suivi de l'historique des statuts
- Commentaires à chaque étape de validation

### 4.3 Gestion budgétaire
- Contrôle des disponibilités budgétaires
- Engagement des montants sur les crédits budgétaires
- Suivi des consommations budgétaires

### 4.4 Reporting
- Suivi des demandes par statut
- Reporting budgétaire
- Historique des validations

## 5. Interfaces utilisateur

### 5.1 Liste des demandes de perdiem
- Affichage de toutes les demandes avec filtres par statut, période, structure
- Actions contextuelles selon le statut et les droits de l'utilisateur

### 5.2 Formulaire de création/édition
- Saisie des informations générales
- Sélection du crédit budgétaire avec affichage du solde disponible
- Ajout dynamique des bénéficiaires
- Calcul automatique des montants
- Téléchargement de pièces justificatives

### 5.3 Vue détaillée
- Affichage des informations complètes de la demande
- Historique des statuts et validations
- Liste des bénéficiaires et montants
- Pièces jointes

## 6. Intégration avec les autres modules

### 6.1 Gestion budgétaire
- Vérification des crédits disponibles
- Engagement des montants
- Mise à jour des consommations budgétaires

### 6.2 Comptabilité
- Génération des écritures comptables
- Suivi des engagements

### 6.3 Notifications
- Envoi d'emails aux validateurs
- Alertes sur les demandes en attente

## 7. Sécurité et droits d'accès

Les droits d'accès au module Perdiem sont gérés par profils utilisateurs :
- **Administrateur** : Accès complet à toutes les fonctionnalités
- **Gestionnaire** : Création et suivi des demandes
- **Validateur** : Validation des demandes selon son niveau hiérarchique
- **Contrôleur budgétaire** : Validation des aspects budgétaires
- **Utilisateur standard** : Consultation des demandes qui le concernent
