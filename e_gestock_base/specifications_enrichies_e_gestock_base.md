# Spécifications Enrichies du Module e_gestock_base

## 1. Introduction

Le module e_gestock_base constitue le socle fondamental de la solution E-GESTOCK pour Odoo 18 Community. Il définit la structure organisationnelle, les articles et les fonctionnalités communes utilisées par tous les autres modules.

## 2. Dépendances

- base
- mail
- product
- uom
- web

## 3. Structures de données

### 3.1 Structure organisationnelle

#### 3.1.1 Structures (e_gestock.structure)

Modèle représentant les entités organisationnelles principales.

**Champs:**
- `code_structure` : Identifiant unique (Integer, clé primaire) - Ex: 9101, 9102, etc.
- `nom_structure` : Nom descriptif de la structure (Char) - Ex: "CONSEIL D'ADMINISTRATION", "DIRECTION GENERALE", etc.
- `ref_depot` : Référence au dépôt associé (Many2one vers e_gestock.depot)
- `num_structure` : Numéro de structure (Integer)
- `organisation_id` : Référence à l'organisation parente (Many2one vers e_gestock.organisation)
- `section_ids` : Liste des sections associées (One2many vers e_gestock.section)
- `active` : Statut actif/inactif (Boolean, default=True)
- `created_at` : Date de création (Datetime, readonly)
- `updated_at` : Date de dernière mise à jour (Datetime, readonly)

**Données initiales:**
Le système contient 49 structures incluant:
- Directions (Direction Générale, Direction Comptabilité, etc.)
- APS (Agences de Protection Sociale) par localité
- Établissements médicaux
- Structures administratives

#### 3.1.2 Sections (e_gestock.section)

Modèle représentant les subdivisions des structures.

**Champs:**
- `id` : Identifiant unique (Integer, clé primaire)
- `code_section` : Code unique de la section (Char) - Format: {code_structure}{numéro séquentiel} (Ex: 910101)
- `code_structure` : Référence à la structure parente (Many2one vers e_gestock.structure)
- `nom_section` : Nom descriptif de la section (Char)
- `num_section` : Numéro de la section (Char)
- `code_gestion` : Code de gestion associé (Many2one vers e_gestock.type_gestion)
- `active` : Statut actif/inactif (Boolean, default=True)
- `created_at` : Date de création (Datetime, readonly)
- `updated_at` : Date de dernière mise à jour (Datetime, readonly)

**Données initiales:**
Le système contient plus de 400 sections réparties dans les différentes structures, principalement avec un code de gestion "G" (Administration).

#### 3.1.3 Dépôts (e_gestock.depot)

Modèle représentant les points de stockage physique.

**Champs:**
- `id` : Identifiant unique (Integer)
- `ref_depot` : Référence unique du dépôt (Integer, clé primaire) - Ex: 83, 51, etc.
- `design_dep` : Désignation du dépôt (Char) - Ex: "Dépôt principal du siège", "APS Bouake", etc.
- `tel_dep` : Numéro de téléphone (Char)
- `adr_dep` : Adresse (Char)
- `principal` : Indicateur de dépôt principal (Boolean) - "1" pour dépôt principal, "0" sinon
- `code_ville` : Code de la ville (Integer, FK)
- `structure_ids` : Structures associées à ce dépôt (One2many vers e_gestock.structure)
- `warehouse_id` : Entrepôt Odoo correspondant (Many2one vers stock.warehouse)
- `location_id` : Emplacement Odoo correspondant (Many2one vers stock.location)
- `active` : Statut actif/inactif (Boolean, default=True)
- `created_at` : Date de création (Datetime, readonly)
- `updated_at` : Date de dernière mise à jour (Datetime, readonly)

**Données initiales:**
Le système contient 20 dépôts, dont:
- Dépôt principal du siège (ref_depot: 83, principal: 1)
- Dépôts régionaux (San Pedro, Bouaké, Daloa, etc.)
- Dépôts médicaux (Centre médical du personnel, CMS Yopougon, etc.)

### 3.2 Organisation des articles

#### 3.2.1 Familles d'articles (e_gestock.famille)

Modèle représentant les regroupements d'articles qui servent également de comptes budgétaires.

**Champs:**
- `ref_fam` : Référence unique de la famille (Char, clé primaire) - Ex: 610225, 632510, etc.
- `design_fam` : Désignation de la famille (Char)
- `description` : Description détaillée (Text)
- `article_ids` : Liste des articles associés (One2many vers e_gestock.article)
- `article_count` : Nombre d'articles dans cette famille (Integer, calculé)
- `active` : Statut actif/inactif (Boolean, default=True)
- `date` : Date de création de la famille (Date)

**Particularités:**
- Chaque famille sert explicitement de compte budgétaire pour le suivi des allocations et consommations
- La numérotation des familles est manuelle (pas de séquence automatique)

#### 3.2.2 Catégories d'articles (e_gestock.categorie)

Modèle représentant les catégories qui peuvent classifier les articles.

**Champs:**
- `name` : Nom de la catégorie (Char)
- `code` : Code unique de la catégorie (Char)
- `description` : Description de la catégorie (Text)
- `active` : Indicateur actif/inactif (Boolean, default=True)

#### 3.2.3 Articles (e_gestock.article)

Modèle représentant les articles du système.

**Champs:**
- `id` : Identifiant unique (Integer)
- `ref_article` : Référence unique de l'article (Char, clé primaire, généré automatiquement)
- `design_article` : Désignation de l'article (Char) - Ex: "Agrafe 8/4", "Agrafeuse pm (8/4)", etc.
- `famille_id` : Relation avec la famille d'articles (Many2one vers e_gestock.famille)
- `ref_fam` : Référence de la famille (Char, relié à famille_id.ref_fam, stocké pour performance)
- `categorie_id` : Relation avec la catégorie d'articles (Many2one vers e_gestock.categorie)
- `type_articles_id` : Type d'article (Integer, FK)
- `code_unite` : Unité de mesure (Integer, FK) - Lié à uom.uom d'Odoo
- `product_id` : Relation avec product.product d'Odoo (Many2one)
- `flag_actif` : Statut actif/inactif (Boolean, default=True)
- `qr_code` : Code QR unique pour l'article (Char, généré automatiquement)
- `ref_taxe` : Référence à la taxe applicable (Integer, FK, peut être null)
- `created_at` : Date de création (Datetime, readonly)
- `updated_at` : Date de dernière mise à jour (Datetime, readonly)

**Génération des références:**
- Format: {ref_famille}{numéro séquentiel sur 2 chiffres}
- Exemple: Pour un article de la famille 610225, si c'est le premier article, sa référence sera 61022501

**Particularités:**
- Création automatique d'un produit Odoo associé lors de la création d'un article
- Génération automatique d'un code QR unique pour chaque article (pour l'application mobile)

**Données initiales:**
Le système contient des milliers d'articles, classés par familles. Exemple des 10 premiers articles stockés (tous de la famille 610225 - Fournitures de bureau):
1. 61022501 - Agrafe 8/4
2. 61022502 - Agrafeuse pm (8/4)
3. 61022503 - Anneau de reliure 16 mm
...

### 3.3 Types de gestion (e_gestock.type_gestion)

Modèle représentant les types de gestion pour la classification comptable et budgétaire.

**Champs:**
- `id` : Identifiant unique (Integer)
- `code_gestion` : Code du type de gestion (Char) - Ex: "A", "E", "F", "G", etc.
- `libelle_gestion` : Désignation (Char) - Ex: "Risques professionnels", "Administration", etc.
- `active` : Indicateur actif/inactif (Boolean, default=True)
- `created_at` : Date de création (Datetime, readonly)
- `updated_at` : Date de dernière mise à jour (Datetime, readonly)

**Données initiales:**
Le système contient 10 types de gestion:
1. "A" - Risques professionnels
2. "E" - Établissements et œuvres
3. "F" - Prestations familiales
4. "M" - Assurances maladies
5. "S" - Actions sanitaires et sociales
6. "V" - Assurances vieillesses
7. "G" - Administration (type le plus utilisé dans les sections)
8. "I" - Immeubles de rapports
9. "T." - Placements financiers
10. "K" - Mep compta analytique

## 4. Gestion des utilisateurs et droits d'accès

### 4.1 Groupes de sécurité

Définition des 29 groupes d'utilisateurs organisés par domaine fonctionnel.

#### 4.1.1 Groupe de base
- **Utilisateur E-Gestock** (`group_e_gestock_user`) - Accès de base aux fonctionnalités E-Gestock

#### 4.1.2 Groupes administratifs
- **Administrateur** (`group_e_gestock_admin`) - Gestion complète du système
- **Directeur Général/Adjoint** (`group_e_gestock_direction`) - Direction générale
- **Validateur DG** (`group_dg_validator`) - Validation par le Directeur Général (montants ≥ 5 000 000)
- **Validateur DGAA** (`group_dgaa_validator`) - Validation par le Directeur Général Adjoint (montants < 5 000 000)

#### 4.1.3 Groupes achats
- **Gestionnaire des achats** (`group_e_gestock_gestionnaire_achats`)
- **Responsable des achats** (`group_e_gestock_resp_achats`)
- **Responsable Section** (`group_section_manager`)
- **Responsable Structure** (`group_structure_manager`)
- **Gestionnaire des Cotations** (`group_quotation_manager`)
- **Visualiseur des Validations** (`group_validation_viewer`)

#### 4.1.4 Groupes stocks
- **Gestionnaire des stocks** (`group_e_gestock_gestionnaire_stocks`) 
- **Responsable des stocks** (`group_e_gestock_resp_stocks`)
- **Responsable Réception** (`group_reception_manager`) 
- **Responsable Dépôt** (`group_e_gestock_resp_depot`)

#### 4.1.5 Groupes finances
- **Responsable DMP** (`group_e_gestock_resp_dmp`)
- **Responsable contrôle budgétaire** (`group_e_gestock_resp_budget`)
- **Contrôleur Budgétaire** (`group_budget_controller`)
- **Engageur Budgétaire** (`group_budget_engager`)
- **Responsable DFC** (`group_e_gestock_resp_dfc`)
- **Validateur DFC** (`group_dfc_validator`)

#### 4.1.6 Groupes spécifiques modules
- **Gestionnaire Immobilisations** (`group_asset_manager`)
- **Gestionnaire Travaux** (`group_works_manager`) 
- **Superviseur Travaux** (`group_works_supervisor`)
- **Gestionnaire Perdiems** (`group_perdiem_manager`) 
- **Validateur Perdiems** (`group_perdiem_validator`)
- **Gestionnaire Demandes de Fonds** (`group_fund_request_manager`)
- **Validateur Demandes de Fonds** (`group_fund_request_validator`)

#### 4.1.7 Groupes externes
- **Fournisseur** (`group_e_gestock_fournisseur`)
- **API Mobile** (`group_e_gestock_api_mobile`)

### 4.2 Matrice des droits
Mise en place d'une matrice détaillée de permissions CRUD pour chaque groupe sur les différents modèles.

### 4.3 Règles de sécurité
- Contrôle d'accès par structure et section
- Restrictions par type de gestion
- Règles d'accès multi-société

## 5. Vues principales

### 5.1 Structures et organisation
- Vue liste des structures
- Vue formulaire des structures
- Vue hiérarchique des structures
- Vue liste des sections
- Vue formulaire des sections

### 5.2 Articles et familles
- Vue liste des familles d'articles
- Vue formulaire des familles d'articles
- Vue liste des catégories
- Vue formulaire des catégories
- Vue liste des articles
- Vue formulaire des articles

### 5.3 Dépôts
- Vue liste des dépôts
- Vue formulaire des dépôts
- Vue carte des dépôts (si coordonnées disponibles)

### 5.4 Administration
- Configuration des types de gestion
- Paramètres généraux du module
- Gestion des séquences

## 6. Intégration avec Odoo

### 6.1 Articles et produits
- Synchronisation bidirectionnelle entre e_gestock.article et product.product
- Création automatique de produits Odoo lors de la création d'articles E-Gestock
- Possibilité de convertir des produits Odoo en articles E-Gestock

### 6.2 Unités de mesure
- Utilisation du module uom d'Odoo pour les unités de mesure

### 6.3 Messagerie et notifications
- Intégration avec le système de messagerie d'Odoo (module mail)
- Notifications des changements importants
- Discussions sur les enregistrements (chatter)

## 7. Fonctions partagées

### 7.1 Génération automatique des références d'articles
Le système génère automatiquement la référence d'un nouvel article en concaténant:
- La référence de la famille d'article (ex: 632510)
- Un numéro séquentiel sur 2 chiffres (01, 02, ...) pour chaque nouvel article de cette famille

Exemple: Pour un nouvel article de la famille 610225, si c'est le premier article, sa référence sera 61022501.

### 7.2 Vérification budgétaire
```python
def verify_budget_availability(self, demande_cotation, raise_if_insufficient=True):
    """
    Vérifie la disponibilité budgétaire pour une demande
    @param demande_cotation: Enregistrement de demande de cotation
    @param raise_if_insufficient: Lever une exception si budget insuffisant
    @return: tuple (disponible: boolean, credit: record, message: str)
    """
    credit = self.env['e_gestock.credit_budget'].search([
        ('structure_id', '=', demande_cotation.structure_id.id),
        ('famille_id', '=', demande_cotation.compte_budg_id.id),
        ('exercise_id', '=', demande_cotation.exercice_id.id),
        ('type_gestion_id', '=', demande_cotation.gestion_id.id)
    ], limit=1)
    
    if not credit:
        message = _("Aucun crédit budgétaire trouvé pour cette combinaison structure/compte/exercice/gestion")
        if raise_if_insufficient:
            raise UserError(message)
        return False, False, message
    
    disponible = credit.montant_disponible >= demande_cotation.montant_total
    message = disponible and _("Budget disponible") or _("Budget insuffisant")
    
    if not disponible and raise_if_insufficient:
        raise UserError(_("Oups! pas de budget disponible. Le montant demandé ({:.2f}) dépasse le disponible ({:.2f})").format(
            demande_cotation.montant_total, credit.montant_disponible))
    
    return disponible, credit, message
```

### 7.3 Recherche d'article depuis un produit
```python
def _find_article_from_product(self, product):
    """
    Trouve l'article E-GESTOCK correspondant à un produit Odoo
    @param product: Enregistrement de produit
    @return: ID de l'article ou False
    """
    article = self.env['e_gestock.article'].search([('product_id', '=', product.id)], limit=1)
    return article.id if article else False
```

## 8. Constantes partagées entre les modules

```python
PURCHASE_STATES = [
    ('draft', 'Brouillon'),
    ('submitted', 'Soumise'),
    ('validated', 'Validée'),
    ('budget_checked', 'Budget vérifié'),  # État synchronisé avec e_gestock_budget
    # Autres états...
]
```

## 9. Structure du module

```
e_gestock_base/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── structure.py
  │   ├── section.py
  │   ├── type_gestion.py
  │   ├── famille.py
  │   ├── categorie.py
  │   ├── article.py
  │   └── depot.py
  ├── views/
  │   ├── structure_views.xml
  │   ├── section_views.xml
  │   ├── type_gestion_views.xml
  │   ├── famille_views.xml
  │   ├── categorie_views.xml
  │   ├── article_views.xml
  │   ├── depot_views.xml
  │   └── menu_views.xml
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_security.xml
  ├── data/
  │   ├── e_gestock_type_gestion_data.xml
  │   ├── e_gestock_structure_data.xml
  │   ├── e_gestock_section_data.xml
  │   ├── e_gestock_depot_data.xml
  │   └── e_gestock_sequence_data.xml
  └── static/
      ├── description/
      │   └── icon.png
      └── src/
          ├── js/
          └── css/
```

## 10. Data Migration

La migration depuis la version Laravel actuelle d'E-GESTOCK vers Odoo 18 nécessitera un processus d'importation de données pour les entités suivantes:

1. **Structures**: 49 structures avec leurs attributs (code, nom, dépôt associé)
2. **Sections**: Plus de 400 sections avec leurs attributs (code, nom, structure parente, type de gestion)
3. **Dépôts**: 20 dépôts avec leurs attributs (référence, désignation, adresse, téléphone)
4. **Types de gestion**: 10 types de gestion (codes et libellés)
5. **Familles d'articles**: Ensemble des familles existantes servant de comptes budgétaires
6. **Articles**: Tous les articles existants avec leurs attributs (référence, désignation, famille, unité)

Les scripts de migration devront être développés avec une validation stricte des données et une vérification des contraintes d'intégrité.

## 11. Interface Utilisateur

L'interface utilisateur du module e_gestock_base sera conçue pour être intuitive et facile d'utilisation, en respectant les standards d'Odoo 18:

1. **Menus et sous-menus**:
   - E-Gestock (menu racine)
     - Configuration
       - Structures et organisation
         - Structures
         - Sections
       - Articles et stocks
         - Familles d'articles
         - Catégories
         - Articles
         - Dépôts
       - Administration
         - Types de gestion
         - Séquences

2. **Vues principales**:
   - Vues liste avec filtres et regroupements
   - Vues formulaire intuitives
   - Actions contextuelles
   - Recherche avancée

3. **Tableaux de bord**:
   - Statistiques sur les articles par famille
   - Compteurs par structure et section
   - Graphiques de répartition

## 12. Tests

Des tests unitaires et d'intégration devront être développés pour assurer la robustesse du module:

1. **Tests unitaires**:
   - Validation des modèles de données
   - Tests des fonctions partagées
   - Vérification des contraintes

2. **Tests d'intégration**:
   - Synchronisation avec les produits Odoo
   - Tests des workflows
   - Vérification des droits d'accès

## 13. Documentation

Une documentation utilisateur et technique devra être fournie:

1. **Documentation utilisateur**:
   - Guide d'utilisation détaillé par fonction
   - Tutoriels pour les opérations courantes
   - FAQ

2. **Documentation technique**:
   - Architecture du module
   - Description des modèles et relations
   - Guide d'extension et de personnalisation 