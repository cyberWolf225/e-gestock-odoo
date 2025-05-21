# Documentation des Groupes d'Utilisateurs E-GESTOCK

## Introduction

Ce document décrit la structure des groupes d'utilisateurs dans le système E-GESTOCK. Les groupes d'utilisateurs définissent les droits d'accès aux différentes fonctionnalités du système.

Tous les groupes sont définis dans le module de base (`e_gestock_base`) pour assurer une gestion centralisée des droits d'accès.

## Structure des Groupes

### Groupes de Base

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur | `group_e_gestock_user` | Accès de base aux fonctionnalités E-GESTOCK (lecture seule) |
| Administrateur | `group_e_gestock_admin` | Gestion complète du système E-GESTOCK |

### Groupes Administratifs

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Direction Générale | `group_e_gestock_direction` | Direction générale |
| Validateur DG | `group_dg_validator` | Validation par le Directeur Général (montants ≥ 5 000 000) |
| Validateur DGAA | `group_dgaa_validator` | Validation par le Directeur Général Adjoint (montants < 5 000 000) |

### Groupes Structurels

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Responsable Section | `group_section_manager` | Gestion au niveau section |
| Responsable Structure | `group_structure_manager` | Gestion au niveau structure |

### Groupes Achats

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Achats | `group_e_gestock_purchase_user` | Consultation et création des demandes d'achats |
| Gestionnaire Achats | `group_e_gestock_purchase_manager` | Gestion complète des achats |
| Gestionnaire Cotations | `group_e_gestock_quotation_manager` | Gestion des demandes de cotation |
| Responsable DMP | `group_e_gestock_resp_dmp` | Gestion des marchés publics |

### Groupes Inventaire

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Inventaire | `group_e_gestock_inventory_user` | Consultation des données d'inventaire |
| Gestionnaire Inventaire | `group_e_gestock_inventory_manager` | Gestion complète des inventaires |
| Responsable Dépôt | `group_e_gestock_resp_depot` | Gestion des dépôts |

### Groupes Réception

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Réception | `group_e_gestock_reception_user` | Consultation des réceptions |
| Gestionnaire Réception | `group_e_gestock_reception_manager` | Gestion complète des réceptions |

### Groupes Budget

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Budget | `group_e_gestock_budget_user` | Consultation des données budgétaires |
| Gestionnaire Budget | `group_e_gestock_budget_manager` | Gestion complète des budgets |
| Contrôleur Budgétaire | `group_e_gestock_budget_controller` | Contrôle des budgets |
| Engageur Budgétaire | `group_e_gestock_budget_engager` | Engagement des budgets |
| Responsable DFC | `group_e_gestock_resp_dfc` | Direction financière et comptable |
| Validateur DFC | `group_dfc_validator` | Validation financière |

### Groupes Demandes de Fonds

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Gestionnaire Demandes de Fonds | `group_e_gestock_fund_request_manager` | Gestion des demandes de fonds |
| Validateur Demandes de Fonds | `group_e_gestock_fund_request_validator` | Validation des demandes de fonds |

### Groupes Fournisseurs

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Fournisseurs | `group_e_gestock_supplier_user` | Consultation des données fournisseurs |
| Responsable Fournisseurs | `group_e_gestock_supplier_manager` | Gestion complète des fournisseurs |

### Groupes Immobilisations

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Immobilisations | `group_e_gestock_asset_user` | Consultation des immobilisations |
| Responsable Immobilisations | `group_e_gestock_asset_manager` | Gestion complète des immobilisations |
| Maintenance Immobilisations | `group_e_gestock_asset_maintenance` | Gestion des maintenances des immobilisations |
| Comptable Immobilisations | `group_e_gestock_asset_accountant` | Gestion des aspects comptables des immobilisations |

### Groupes Perdiems

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Utilisateur Perdiems | `group_e_gestock_perdiem_user` | Consultation des perdiems |
| Demandeur Perdiems | `group_e_gestock_perdiem_requester` | Création et soumission des demandes de perdiem |
| Validateur Perdiems | `group_e_gestock_perdiem_validator` | Validation des demandes de perdiem |
| Responsable Perdiems | `group_e_gestock_perdiem_manager` | Gestion complète des perdiems |

### Groupes Travaux

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Gestionnaire Travaux | `group_e_gestock_work_manager` | Gestion des travaux |
| Superviseur Travaux | `group_e_gestock_work_supervisor` | Supervision des travaux |

### Groupes Validation

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Visualiseur des Validations | `group_e_gestock_validation_viewer` | Visualisation des validations |

### Groupes Externes

| Groupe | ID Technique | Description |
|--------|--------------|-------------|
| Fournisseur | `group_e_gestock_fournisseur` | Accès limité pour les fournisseurs via le portail |
| API Mobile | `group_e_gestock_api_mobile` | Accès limité pour l'application mobile |

## Hiérarchie des Groupes

La hiérarchie des groupes est définie par le champ `implied_ids`. Par exemple, le groupe `Gestionnaire Achats` hérite des droits du groupe `Utilisateur Achats`.

Voici quelques exemples de hiérarchie :

- `Administrateur` > `Utilisateur`
- `Gestionnaire Achats` > `Utilisateur Achats` > `Utilisateur`
- `Responsable Structure` > `Responsable Section` > `Utilisateur`
- `Gestionnaire Budget` > `Utilisateur Budget` > `Utilisateur`

## Groupes Obsolètes

Les groupes suivants sont obsolètes et ont été remplacés par de nouveaux groupes :

| Ancien Groupe | Nouveau Groupe |
|---------------|----------------|
| Gestionnaire des achats (Ancien) | Utilisateur Achats |
| Responsable des achats (Ancien) | Gestionnaire Achats |
| Gestionnaire des Cotations (Ancien) | Gestionnaire Cotations |
| Contrôleur Budgétaire (Ancien) | Contrôleur Budgétaire |
| Engageur Budgétaire (Ancien) | Engageur Budgétaire |
| Responsable Réception (Ancien) | Gestionnaire Réception |
| Responsable contrôle budgétaire (Ancien) | Contrôleur Budgétaire |

## Migration des Utilisateurs

Un script de migration a été créé pour migrer les utilisateurs des anciens groupes vers les nouveaux groupes. Ce script se trouve dans le répertoire `custom/e_gestock_base/scripts/migrate_user_groups.py`.

Pour exécuter le script, utilisez la commande suivante :

```bash
cd /chemin/vers/odoo
python3 custom/e_gestock_base/scripts/migrate_user_groups.py
```

## Recommandations

1. Utilisez toujours les nouveaux IDs de groupe dans le code.
2. Ne créez pas de nouveaux groupes dans les autres modules. Tous les groupes doivent être définis dans le module de base.
3. Si vous avez besoin d'un nouveau groupe, ajoutez-le au fichier `e_gestock_security_optimized.xml` dans le module de base.
4. Documentez clairement le rôle de chaque groupe dans le code.
