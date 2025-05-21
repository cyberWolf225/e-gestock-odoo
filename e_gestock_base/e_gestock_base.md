# Module de base (e_gestock_base)

## Description
Le module e_gestock_base constitue le socle fondamental de la solution E-GESTOCK pour Odoo 18 Community. Il définit la structure organisationnelle, les articles et les fonctionnalités communes utilisées par tous les autres modules.

## Dépendances
- base
- mail
- product
- uom
- web

## Fonctionnalités principales

### 1. Gestion des structures organisationnelles

#### 1.1 Structures (e_gestock.structure)
- `code_structure` : Identifiant unique (clé primaire)
- `nom_structure` : Nom descriptif de la structure
- `ref_depot` : Référence au dépôt associé
- `num_structure` : Numéro de structure
- `organisations_id` : Référence à l'organisation parente (peut être null)

#### 1.2 Sections (e_gestock.section)
- `id` : Identifiant unique (clé primaire)
- `code_section` : Code unique de la section
- `code_structure` : Référence à la structure parente
- `nom_section` : Nom descriptif de la section
- `num_section` : Numéro de la section
- `code_gestion` : Code de gestion associé (peut être null)

#### 1.3 Dépôts (e_gestock.depot)
- `ref_depot` : Référence unique du dépôt
- `designation` : Désignation du dépôt
- `structure_id` : Relation avec la structure
- `responsable_id` : Responsable du dépôt
- Informations de contact et d'adresse

### 2. Organisation des articles

#### 2.1 Familles d'articles (e_gestock.famille)
- `ref_fam` : Référence unique de la famille (ex: 632510) - Numérotation manuelle
- `design_fam` : Désignation de la famille (nom de la famille)
- `active` : Statut actif/inactif
- `date` : Date de création de la famille d'articles
- **Fonction de compte budgétaire** : Chaque famille sert de compte budgétaire
- `article_ids` : Liste des articles associés à cette famille
- `article_count` : Nombre d'articles dans cette famille (champ calculé)


#### 2.2 Catégories d'articles (e_gestock.categorie)
- `name` : Nom de la catégorie
- `code` : Code unique de la catégorie
- `description` : Description de la catégorie
- `active` : Indicateur actif/inactif



#### 2.3 Articles (e_gestock.article)
- `ref_article` : Référence unique de l'article (auto-générée à partir de la référence famille)
- `ref_famille` : Référence de la famille (champ relié)
- `famille_id` : Relation avec la famille d'articles
- `categorie_id` : Relation avec la catégorie d'articles
- `design_article` : Désignation de l'article
- `unite_id` : Unité de mesure (liaison avec uom.uom d'Odoo)
- `active` : Statut actif/inactif
- `product_id` : Relation avec product.product d'Odoo


#### 2.4 Types de gestion (e_gestock.type_gestion)
- `code` : Code du type de gestion
- `designation` : Désignation
- `active` : Indicateur actif/inactif

### 3. Gestion des utilisateurs et droits d'accès

#### 3.1 Groupes de sécurité
Définition des 29 groupes d'utilisateurs organisés par domaine fonctionnel :

##### 3.1.1 Groupe de base
- **Utilisateur E-Gestock** (`group_e_gestock_user`) - Accès de base aux fonctionnalités E-Gestock

##### 3.1.2 Groupes administratifs
- **Administrateur** (`group_e_gestock_admin`) - Gestion complète du système
- **Directeur Général/Adjoint** (`group_e_gestock_direction`) - Direction générale
- **Validateur DG** (`group_dg_validator`) - Validation par le Directeur Général (montants ≥ 5 000 000)
- **Validateur DGAA** (`group_dgaa_validator`) - Validation par le Directeur Général Adjoint (montants < 5 000 000)

##### 3.1.3 Groupes achats
- **Gestionnaire des achats** (`group_e_gestock_gestionnaire_achats`)
- **Responsable des achats** (`group_e_gestock_resp_achats`)
- **Responsable Section** (`group_section_manager`)
- **Responsable Structure** (`group_structure_manager`)
- **Gestionnaire des Cotations** (`group_quotation_manager`)
- **Visualiseur des Validations** (`group_validation_viewer`)

##### 3.1.4 Groupes stocks
- **Gestionnaire des stocks** (`group_e_gestock_gestionnaire_stocks`) 
- **Responsable des stocks** (`group_e_gestock_resp_stocks`)
- **Responsable Réception** (`group_reception_manager`) 
- **Responsable Dépôt** (`group_e_gestock_resp_depot`)

##### 3.1.5 Groupes finances
- **Responsable DMP** (`group_e_gestock_resp_dmp`)
- **Responsable contrôle budgétaire** (`group_e_gestock_resp_budget`)
- **Contrôleur Budgétaire** (`group_budget_controller`)
- **Engageur Budgétaire** (`group_budget_engager`)
- **Responsable DFC** (`group_e_gestock_resp_dfc`)
- **Validateur DFC** (`group_dfc_validator`)

##### 3.1.6 Groupes spécifiques modules
- **Gestionnaire Immobilisations** (`group_asset_manager`)
- **Gestionnaire Travaux** (`group_works_manager`) 
- **Superviseur Travaux** (`group_works_supervisor`)
- **Gestionnaire Perdiems** (`group_perdiem_manager`) 
- **Validateur Perdiems** (`group_perdiem_validator`)
- **Gestionnaire Demandes de Fonds** (`group_fund_request_manager`)
- **Validateur Demandes de Fonds** (`group_fund_request_validator`)

##### 3.1.7 Groupes externes
- **Fournisseur** (`group_e_gestock_fournisseur`)
- **API Mobile** (`group_e_gestock_api_mobile`)

#### 3.2 Matrice des droits
Mise en place d'une matrice détaillée de permissions CRUD pour chaque groupe sur les différents modèles.

#### 3.3 Règles de sécurité
- Contrôle d'accès par structure et section
- Restrictions par type de gestion
- Règles d'accès multi-société

## Vues principales

### 1. Structures et organisation
- Vue liste des structures
- Vue formulaire des structures
- Vue hiérarchique des structures
- Vue liste des sections
- Vue formulaire des sections

### 2. Articles et familles
- Vue liste des familles d'articles
- Vue formulaire des familles d'articles



- Vue liste des catégories
- Vue formulaire des catégories
- Vue liste des articles
- Vue formulaire des articles



### 3. Dépôts
- Vue liste des dépôts
- Vue formulaire des dépôts
- Vue carte des dépôts (si coordonnées disponibles)

### 4. Administration
- Configuration des types de gestion
- Paramètres généraux du module
- Gestion des séquences


## Intégration avec Odoo

### 1. Articles et produits
- Synchronisation bidirectionnelle entre e_gestock.article et product.product
- Création automatique de produits Odoo lors de la création d'articles E-Gestock
- Possibilité de convertir des produits Odoo en articles E-Gestock

### 2. Unités de mesure
- Utilisation du module uom d'Odoo pour les unités de mesure

### 3. Messagerie et notifications
- Intégration avec le système de messagerie d'Odoo (module mail)
- Notifications des changements importants
- Discussions sur les enregistrements (chatter)

### 4. Génération automatique des références d'articles

Le système génère automatiquement la référence d'un nouvel article en concaténant:
- La référence de la famille d'article (ex: 632510)
- Un numéro séquentiel sur 2 chiffres (01, 02, ...) pour chaque nouvel article de cette famille

Exemple: Pour un nouvel article de la famille 632510, si c'est le premier article de cette famille, sa référence sera 63251001. 

# Constantes partagées entre les modules
PURCHASE_STATES = [
    ('draft', 'Brouillon'),
    ('submitted', 'Soumise'),
    ('validated', 'Validée'),
    ('budget_checked', 'Budget vérifié'),  # État synchronisé avec e_gestock_budget
    # Autres états...
] 

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

def _get_already_received_qty(self, po_line):
    """
    Calcule la quantité déjà reçue pour une ligne de commande
    @param po_line: Enregistrement de ligne de commande d'achat
    @return: float - Quantité déjà reçue
    """
    receptions = self.search([
        ('purchase_order_id', '=', po_line.order_id.id),
        ('state', 'in', ['done']),
    ])
    
    already_received = 0.0
    for reception in receptions:
        for line in reception.line_ids.filtered(lambda l: l.purchase_line_id.id == po_line.id):
            already_received += line.quantite_reçue
    
    return already_received
    
def _find_article_from_product(self, product):
    """
    Trouve l'article E-GESTOCK correspondant à un produit Odoo
    @param product: Enregistrement de produit
    @return: ID de l'article ou False
    """
    article = self.env['e_gestock.article'].search([('product_id', '=', product.id)], limit=1)
    return article.id if article else False 

def _check_availability(self):
    """
    Vérifie la disponibilité des articles pour les mouvements de sortie et transfert
    @raise: ValidationError si un article n'est pas disponible en quantité suffisante
    """
    self.ensure_one()
    if self.type not in ('out', 'transfer'):
        return True
        
    depot = self.depot_source_id
    for line in self.line_ids:
        available_qty = self.env['e_gestock.stock_item'].get_stock_quantity(
            line.article_id.id, depot.id)
        if line.quantite > available_qty:
            raise ValidationError(_(
                "Quantité insuffisante pour l'article {} dans le dépôt {}. "
                "Demandé: {}, Disponible: {}"
            ).format(line.article_id.display_name, depot.designation, line.quantite, available_qty))
    
    return True 

@api.model
def create_cotation_from_request(self, demande_cotation_id, data):
    """
    Crée une cotation à partir d'une demande
    @param demande_cotation_id: ID de la demande de cotation
    @param data: Données pour la cotation
    @return: ID de la cotation créée
    """
    # Vérifier l'état de la demande
    demande = self.env['e_gestock.demande_cotation'].browse(demande_cotation_id)
    if demande.state != 'quotation':
        raise UserError(_("Impossible de créer une cotation: la demande n'est pas en état 'En attente cotation'"))
    
    # Créer la cotation
    # ...