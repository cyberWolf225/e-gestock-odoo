# Spécifications Fonctionnelles Détaillées (SFD)
# Solution E-GESTOCK pour Odoo Community 18

## 1. Présentation générale

### 1.1 Objet du document
Ce document présente les spécifications fonctionnelles détaillées de la solution E-GESTOCK implémentée dans Odoo Community 18, une application de gestion des stocks, des achats et des approvisionnements.

### 1.2 Objectifs de la solution
E-GESTOCK est une solution intégrée visant à :
- Optimiser la gestion des stocks et des approvisionnements
- Dématérialiser les processus d'achats et de demandes
- Assurer un suivi budgétaire précis par structure et par famille d'articles
- Automatiser les workflows d'approbation et de validation
- Offrir une traçabilité complète des opérations
- Faciliter le reporting et l'analyse des données
- S'intégrer parfaitement avec Odoo Community 18 tout en respectant ses contraintes

### 1.3 Dépendances
Les modules E-GESTOCK ne peuvent dépendre que des modules de base d'Odoo Community 18 :
- base
- mail
- product
- uom
- web

### 1.4 Contexte technique
E-GESTOCK sera implémenté sous forme de modules Odoo 18 Community Edition, basés sur la structure standard des modules Odoo:
- `models/` pour les définitions des modèles de données
- `views/` pour les fichiers XML définissant les interfaces utilisateur
- `security/` pour les fichiers de sécurité et de contrôle d'accès
- `data/` pour les données par défaut et séquences
- `controllers/` pour les endpoints API
- `static/` pour les ressources statiques (JS, CSS, images)
- `wizards/` pour les assistants

La version actuelle d'E-GESTOCK est développée avec Laravel, comme l'indiquent les fichiers dans le répertoire `/e-gestock`. La nouvelle implémentation devra assurer une transition fluide des données et des processus métier de la version Laravel vers Odoo 18.

## 2. Architecture fonctionnelle

### 2.1 Structure organisationnelle
La solution s'articule autour d'une organisation hiérarchique :

#### 2.1.1 Structures
Les structures sont les entités organisationnelles principales avec les attributs suivants:
- `code_structure` : Identifiant unique (clé primaire)
- `nom_structure` : Nom descriptif de la structure
- `ref_depot` : Référence au dépôt associé
- `num_structure` : Numéro de structure
- `organisations_id` : Référence à l'organisation parente (peut être null)

#### 2.1.2 Sections
Les sections sont des subdivisions des structures avec les attributs:
- `id` : Identifiant unique (clé primaire)
- `code_section` : Code unique de la section
- `code_structure` : Référence à la structure parente
- `nom_section` : Nom descriptif de la section
- `num_section` : Numéro de la section
- `code_gestion` : Code de gestion associé (peut être null)

#### 2.1.3 Dépôts
Les dépôts sont les points de stockage et possèdent:
- `ref_depot` : Référence unique du dépôt
- Désignation
- Liens avec les structures
- Responsable du dépôt
- Adresse et informations de contact

### 2.2 Organisation des articles
Les articles sont organisés selon une hiérarchie :

#### 2.2.1 Familles d'articles
Les familles d'articles incluent:
- `ref_fam` : Référence unique de la famille 
- `design_fam` : Désignation de la famille
- Description
- Statut actif/inactif
- **Fonction de compte budgétaire** : Chaque famille sert de compte budgétaire pour le suivi et l'allocation des ressources financières

#### 2.2.2 Articles
Les articles comprennent:
- `ref_article` : Référence unique de l'article
- `design_article` : Désignation de l'article
- `famille_id` : Relation avec la famille d'articles
- Code QR unique pour chaque article (pour l'application mobile)
- Prix, unité de mesure, type de gestion

#### 2.2.3 Catégories
Les catégories servent de classification des produits et peuvent servir de comptes budgétaires.

### 2.3 Types de gestion
Les types de gestion sont caractérisés par:
- Code du type de gestion
- Désignation
- Indicateur actif/inactif

### 2.4 Exercices budgétaires
Les exercices budgétaires incluent:
- Code de l'exercice (ex: "2025")
- Dates de début et de fin
- État (ouvert/fermé)
- Indicateur actif (un seul exercice actif à la fois)

### 2.5 Crédits budgétaires
Les crédits budgétaires comprennent:
- Structure et section associées
- **Famille d'article servant explicitement de compte budgétaire**
- Type de gestion
- Montant alloué
- Montant consommé
- Solde disponible
- Exercice budgétaire

## 3. Modules fonctionnels

### 3.0 Module API (e_gestock_api)

#### 3.0.1 API REST pour application mobile
- Exposition d'une API REST sécurisée pour l'application mobile
- Authentification par token JWT pour sécuriser les accès
- Endpoints pour accéder aux informations des articles via code QR
- Gestion des droits d'accès spécifiques à l'API
- Journalisation des accès pour audit de sécurité
- Génération et gestion des codes QR pour les articles
- Documentation interactive de l'API avec Swagger/OpenAPI

##### 3.0.1.1 Endpoints principaux
L'API exposera les endpoints suivants:
- `/api/v1/auth` - Authentification et rafraîchissement des jetons
- `/api/v1/products` - Accès aux informations des produits
- `/api/v1/products/qr/{code}` - Lecture des articles via code QR
- `/api/v1/stocks` - Consultation des niveaux de stock
- `/api/v1/suppliers` - Informations sur les fournisseurs
- `/api/v1/movements` - Historique des mouvements de stock

##### 3.0.1.2 Sécurité de l'API
La sécurité de l'API mobile sera assurée par:
- Utilisation obligatoire du protocole HTTPS
- Authentification par jetons JWT avec signature sécurisée
- Validation stricte des entrées utilisateur
- Contrôles d'accès basés sur les profils utilisateur
- Protection contre les attaques CSRF et XSS
- Mécanismes de rate-limiting pour éviter les abus
- Journalisation complète des accès

### 3.1 Module de base (e_gestock_base)

#### 3.1.1 Gestion des structures organisationnelles
- Création et gestion des structures
- Gestion des sections par structure
- Configuration des dépôts
- Définition des types de gestion

#### 3.1.2 Gestion des articles
- Création et gestion des familles d'articles
- Enregistrement des articles E-GESTOCK
- Association automatique avec les produits Odoo
- Gestion des catégories de produits comme comptes budgétaires

#### 3.1.3 Gestion des utilisateurs
- Définition des profils utilisateurs (29 groupes d'utilisateurs différents)
- Attribution des droits d'accès via une matrice de permissions CRUD
- Gestion des groupes de sécurité hiérarchisés
- Centralisation des droits d'accès pour tous les modules E-Gestock
- Gestion des rôles de validation selon les montants (DGA pour montants < 5 000 000, DG pour montants ≥ 5 000 000)
- Organisation des groupes par domaine fonctionnel (administratif, achats, stocks, finances, etc.)

### 3.2 Module de gestion des stocks (e_gestock_inventory)

#### 3.2.1 Dépôts et articles en stock
- Extension du modèle e_gestock.depot pour la gestion des stocks
- Intégration avec les entrepôts et emplacements Odoo (warehouse_id, location_id)
- Gestion des articles en stock par dépôt (e_gestock.stock_item)
- Calcul des quantités disponibles et réservées en temps réel
- Synchronisation bidirectionnelle avec les quants Odoo
- Gestion des responsables de dépôt

#### 3.2.2 Mouvements de stock
- Gestion de quatre types de mouvements : entrées, sorties, transferts et ajustements d'inventaire
- Workflow complet : brouillon → confirmé → terminé (ou annulé)
- Contrôle des disponibilités avant validation des sorties et transferts
- Création automatique des mouvements Odoo (stock.picking, stock.move)
- Traçabilité complète des opérations (date, utilisateur, notes)
- Intégration avec les bons de commande et les inventaires
- Numérotation automatique par séquence selon le type de mouvement

#### 3.2.3 Inventaires physiques
- Planification et réalisation des inventaires par dépôt
- Workflow dédié : brouillon → en cours → validé (ou annulé)
- Génération automatique des lignes d'inventaire basée sur le stock théorique
- Saisie des quantités réelles avec calcul automatique des écarts
- Validation avec contrôle que toutes les lignes ont été comptées
- Création automatique des mouvements d'ajustement
- Traçabilité des écarts d'inventaire
- Protection contre les inventaires simultanés sur un même dépôt

#### 3.2.4 Intégration avec Odoo
- Synchronisation avec le module stock d'Odoo
- Utilisation des emplacements standards (suppliers, customers, inventory)
- Création automatique des entrepôts et emplacements Odoo
- Mise à jour bidirectionnelle des quantités
- Utilisation des unités de mesure Odoo

### 3.3 Module de gestion des achats et cotations

#### 3.3.1 Demandes d'achat
- Création et soumission des demandes d'achat
- Numérotation automatique avec format personnalisé (Année/Structure/Type/Séquence)
- Distinction entre commandes stockables et non stockables
- Workflow de validation complet avec 14 états différents
- Validation hiérarchique (section, structure, responsable achats, DMP)
- Contrôle budgétaire avec vérification des fonds disponibles
- Validation financière (DFC)
- Validation finale par DGA (montant < 5 000 000) ou DG (montant ≥ 5 000 000)
- Engagement budgétaire avec référence et date
- Historique complet des changements d'état
- Traçabilité des validations (date et utilisateur)

#### 3.3.2 Gestion des articles
- Pour les commandes stockables : sélection d'articles existants de la famille spécifiée
- Pour les commandes non stockables : saisie libre des désignations et descriptions
- Contrôle automatique de l'appartenance des articles à la famille sélectionnée
- Calcul automatique des sous-totaux et du montant total
- Création automatique de produits temporaires pour les articles non stockables

#### 3.3.3 Intégration avec les achats Odoo
- Génération automatique des bons de commande Odoo
- Transfert des lignes de demande vers les lignes de commande
- Lien bidirectionnel entre demandes d'achat et bons de commande
- Suivi de l'état de livraison

#### 3.3.4 Processus de cotation
- Enregistrement des offres de prix des fournisseurs pour chaque demande d'achat
- Numérotation automatique des cotations avec préfixe (COT00001, etc.)
- Saisie des prix unitaires et conditions commerciales (délai de livraison, conditions de paiement)
- Calcul automatique des montants totaux par ligne et par cotation
- Comparaison des offres via vues pivot et tableaux comparatifs
- Sélection du fournisseur mieux-disant avec marquage automatique
- Rejet automatique des autres offres lors de la sélection du mieux-disant
- Génération automatique des bons de commande Odoo
- Création automatique de fournisseurs E-Gestock à partir des partenaires Odoo
- Suivi des états des cotations (brouillon, confirmé, sélectionné, rejeté, BC généré)

#### 3.3.5 Réception des commandes (e_gestock_reception)
- Enregistrement des livraisons avec numérotation automatique
- Liaison avec les bons de commande Odoo et les demandes d'achat E-Gestock
- Calcul automatique des quantités restant à recevoir
- Contrôle de conformité des articles avec système de contrôle qualité
- Gestion des livraisons partielles avec suivi des quantités déjà reçues
- Création automatique des mouvements de stock à la validation
- Mise à jour automatique des stocks dans le dépôt de destination
- Suivi des BL fournisseurs (numéro et date)
- Workflow complet : brouillon → confirmé → terminé (ou annulé)
- Mise à jour automatique du statut des demandes d'achat à 'delivered'
- Vues kanban pour suivi visuel des réceptions par état

### 3.4 Module budgétaire (e_gestock_budget)

#### 3.4.1 Exercices budgétaires
- Création et gestion des exercices (ex: "2025")
- Définition des périodes d'activité (date_debut, date_fin)
- Gestion des états (ouvert, fermé)
- Activation/désactivation des exercices (un seul exercice actif à la fois)
- Clôture des exercices avec contrôles de validation
- Suivi des intervenants responsables
- Statistiques de consommation budgétaire

#### 3.4.2 Crédits budgétaires
- Allocation des budgets par structure, section et **famille d'articles (servant de compte budgétaire)**
- Association avec les types de gestion (gestion_id)
- Suivi des consommations budgétaires en temps réel par famille d'articles
- Calcul automatique des montants disponibles par compte budgétaire (famille)
- Alertes sur seuils de consommation (is_below_threshold)
- Contrôle des dépassements avec blocage des opérations
- Visualisation des demandes liées à chaque crédit par famille
- Intégration avec les demandes d'achat et cotations

#### 3.4.3 Dotations budgétaires
- Gestion des dotations par dépôt et famille d'articles
- Suivi des consommations par exercice
- Calcul automatique des dotations disponibles
- Contrôles de validation pour éviter les soldes négatifs
- API pour la vérification des disponibilités budgétaires
- API pour la mise à jour des consommations
- Intégration avec les autres modules (achats, stocks)

#### 3.4.4 Consommations budgétaires
- Suivi détaillé des consommations par période
- Analyse des tendances de consommation
- Tableaux de bord avec indicateurs clés
- Rapports de consommation par structure/section/famille
- Alertes sur dépassements de seuils

### 3.5 Module de gestion des fournisseurs (e_gestock_supplier)

#### 3.5.1 Gestion des fournisseurs
- Enregistrement des fournisseurs avec synchronisation automatique vers les partenaires Odoo
- Catégorisation hiérarchique des fournisseurs (catégories et sous-catégories)
- Gestion complète des informations (adresse, contacts, coordonnées bancaires, etc.)
- Association avec les familles d'articles et produits fournis
- Suivi des performances via un système de notation automatisé
- Statistiques d'achats (montants, délais de livraison, etc.)
- Accès rapide aux cotations, contrats et évaluations associés
- Gestion de l'état actif/inactif des fournisseurs

#### 3.5.2 Contrats fournisseurs
- Gestion complète du cycle de vie des contrats (brouillon, actif, expiré, résilié, renouvelé, annulé)
- Différents types de contrats (cadre, ponctuel, service, maintenance)
- Suivi des dates d'échéance avec alertes automatiques
- Gestion des conditions de paiement et remises négociées
- Clauses spéciales (exclusivité, confidentialité, garantie)
- Système de renouvellement automatique ou manuel
- Gestion des pièces jointes et documents contractuels
- Traçabilité des modifications et historique des contrats

#### 3.5.3 Évaluation des fournisseurs
- Système d'évaluation multicritères (qualité, délais, prix, service)
- Pondération personnalisable des critères d'évaluation
- Calcul automatique des notes globales
- Impact automatique sur la classification du fournisseur
- Suivi des points forts, points faibles et recommandations
- Historique complet des évaluations
- Lien avec les contrats et commandes spécifiques
- Tableaux de bord et rapports d'analyse des performances

#### 3.5.4 Portail fournisseurs
- Accès sécurisé pour les fournisseurs via le portail Odoo
- Visualisation des demandes de cotation en attente
- Interface de saisie des prix et conditions commerciales
- Téléchargement des documents associés aux demandes
- Soumission des offres directement via le portail
- Suivi de l'état des demandes (en attente, soumise, acceptée, refusée)
- Historique des cotations précédentes
- Notifications par email lors de nouvelles demandes
- Accès aux bons de commande générés

### 3.6 Module de gestion des immobilisations (e_gestock_asset)

#### 3.6.1 Enregistrement des immobilisations
- Acquisition et enregistrement
- Suivi du cycle de vie
- Affectation aux utilisateurs
- Intégration avec les articles E-GESTOCK

#### 3.6.2 Maintenance
- Planification des entretiens
- Enregistrement des interventions
- Suivi des coûts de maintenance
- Alertes de maintenance préventive

### 3.7 Module de reporting (e_gestock_reports)

#### 3.7.1 Rapports standards
- État des stocks
- Suivi des demandes d'achat
- Analyse budgétaire
- Performance des fournisseurs

#### 3.7.2 Tableaux de bord
- Indicateurs clés de performance
- Visualisations graphiques
- Alertes et notifications
- Rapports personnalisables

## 4. Modèles de données

### 4.1 Module de base (e_gestock_base)

#### 4.1.1 Structure (e_gestock.structure)
```python
class Structure(models.Model):
    _name = 'e_gestock.structure'
    _description = 'Structure organisationnelle'
    
    code_structure = fields.Char('Code', required=True, index=True)
    nom_structure = fields.Char('Nom', required=True)
    num_structure = fields.Integer('Numéro', required=True)
    ref_depot = fields.Many2one('e_gestock.depot', 'Dépôt de référence')
    organisation_id = fields.Many2one('e_gestock.organisation', 'Organisation parente')
    section_ids = fields.One2many('e_gestock.section', 'code_structure', 'Sections')
    active = fields.Boolean('Actif', default=True)
```

#### 4.1.2 Section (e_gestock.section)
```python
class Section(models.Model):
    _name = 'e_gestock.section'
    _description = 'Section de structure'
    
    code_section = fields.Char('Code', required=True, index=True)
    code_structure = fields.Many2one('e_gestock.structure', 'Structure parente', required=True)
    nom_section = fields.Char('Nom', required=True)
    num_section = fields.Char('Numéro', required=True)
    code_gestion = fields.Many2one('e_gestock.type_gestion', 'Type de gestion')
    active = fields.Boolean('Actif', default=True)
```

#### 4.1.3 Type de Gestion (e_gestock.type_gestion)
```python
class TypeGestion(models.Model):
    _name = 'e_gestock.type_gestion'
    _description = 'Type de gestion'
    
    code = fields.Char('Code', required=True, index=True)
    designation = fields.Char('Désignation', required=True)
    active = fields.Boolean('Actif', default=True)
```

#### 4.1.4 Famille d'Articles (e_gestock.famille)
```python
class FamilleArticle(models.Model):
    _name = 'e_gestock.famille'
    _description = 'Famille d\'articles'
    
    ref_fam = fields.Char('Référence', required=True, index=True)
    design_fam = fields.Char('Désignation', required=True)
    description = fields.Text('Description')
    article_ids = fields.One2many('e_gestock.article', 'famille_id', 'Articles')
    active = fields.Boolean('Actif', default=True)
```

#### 4.1.5 Article (e_gestock.article)
```python
class Article(models.Model):
    _name = 'e_gestock.article'
    _description = 'Article E-Gestock'
    
    ref_article = fields.Char('Référence', required=True, index=True)
    design_article = fields.Char('Désignation', required=True)
    famille_id = fields.Many2one('e_gestock.famille', 'Famille', required=True)
    product_id = fields.Many2one('product.product', 'Produit Odoo', ondelete='cascade')
    qr_code = fields.Char('Code QR', help="Code QR unique pour l'article")
    active = fields.Boolean('Actif', default=True)
    
    @api.model
    def create(self, vals):
        # Génération automatique du code QR
        # Création du produit Odoo associé
        return super().create(vals)
```

#### 4.1.6 Dépôt (e_gestock.depot)
```python
class Depot(models.Model):
    _name = 'e_gestock.depot'
    _description = 'Dépôt'
    
    ref_depot = fields.Char('Référence', required=True, index=True)
    designation = fields.Char('Désignation', required=True)
    responsable_id = fields.Many2one('res.users', 'Responsable')
    structure_ids = fields.One2many('e_gestock.structure', 'ref_depot', 'Structures')
    warehouse_id = fields.Many2one('stock.warehouse', 'Entrepôt Odoo')
    location_id = fields.Many2one('stock.location', 'Emplacement Odoo')
    active = fields.Boolean('Actif', default=True)
```

### 4.2 Module budgétaire (e_gestock_budget)

#### 4.2.1 Exercice (e_gestock.exercice)
```python
class Exercice(models.Model):
    _name = 'e_gestock.exercice'
    _description = 'Exercice budgétaire'
    
    code = fields.Char('Code', required=True, index=True)
    date_debut = fields.Date('Date de début', required=True)
    date_fin = fields.Date('Date de fin', required=True)
    state = fields.Selection([('ouvert', 'Ouvert'), ('ferme', 'Fermé')], 'État', default='ouvert')
    is_active = fields.Boolean('Actif', default=False)
    credit_ids = fields.One2many('e_gestock.credit', 'exercice_id', 'Crédits budgétaires')
    
    @api.constrains('is_active')
    def _check_single_active(self):
        # Vérification qu'un seul exercice est actif à la fois
        pass
```

#### 4.2.2 Crédit Budgétaire (e_gestock.credit)
```python
class CreditBudgetaire(models.Model):
    _name = 'e_gestock.credit'
    _description = 'Crédit budgétaire'
    
    exercice_id = fields.Many2one('e_gestock.exercice', 'Exercice', required=True)
    structure_id = fields.Many2one('e_gestock.structure', 'Structure', required=True)
    section_id = fields.Many2one('e_gestock.section', 'Section')
    famille_id = fields.Many2one('e_gestock.famille', 'Famille d\'articles', required=True)
    gestion_id = fields.Many2one('e_gestock.type_gestion', 'Type de gestion')
    montant_alloue = fields.Float('Montant alloué', required=True)
    montant_consomme = fields.Float('Montant consommé', compute='_compute_consommation')
    montant_disponible = fields.Float('Montant disponible', compute='_compute_disponible')
    is_below_threshold = fields.Boolean('Sous le seuil', compute='_compute_threshold')
    
    def _compute_consommation(self):
        # Calcul de la consommation budgétaire
        pass
    
    def _compute_disponible(self):
        # Calcul du solde disponible
        pass
    
    def _compute_threshold(self):
        # Vérification si le montant est sous le seuil d'alerte
        pass
```

### 4.3 Module de gestion des achats (e_gestock_purchase)

#### 4.3.1 Demande d'Achat (e_gestock.demande_achat)
```python
class DemandeAchat(models.Model):
    _name = 'e_gestock.demande_achat'
    _description = 'Demande d\'achat'
    
    name = fields.Char('Référence', readonly=True)
    date_demande = fields.Date('Date de demande', default=fields.Date.today)
    structure_id = fields.Many2one('e_gestock.structure', 'Structure', required=True)
    section_id = fields.Many2one('e_gestock.section', 'Section', required=True)
    famille_id = fields.Many2one('e_gestock.famille', 'Famille d\'articles', required=True)
    type_commande = fields.Selection([('stockable', 'Stockable'), ('non_stockable', 'Non stockable')], 'Type', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('section_validated', 'Validée Section'),
        ('structure_validated', 'Validée Structure'),
        ('achat_validated', 'Validée Achats'),
        ('dmp_validated', 'Validée DMP'),
        ('budget_checked', 'Contrôle Budget'),
        ('dfc_validated', 'Validée DFC'),
        ('dga_validated', 'Validée DGA'),
        ('dg_validated', 'Validée DG'),
        ('engaged', 'Engagée'),
        ('quotation', 'En cotation'),
        ('quoted', 'Cotée'),
        ('best_selected', 'Mieux disant sélectionné'),
        ('po_generated', 'BC Généré'),
        ('delivered', 'Livrée'),
        ('rejected', 'Rejetée'),
        ('cancelled', 'Annulée')
    ], 'État', default='draft')
    line_ids = fields.One2many('e_gestock.demande_achat.line', 'demande_id', 'Lignes')
    montant_total = fields.Float('Montant Total', compute='_compute_montant')
    credit_id = fields.Many2one('e_gestock.credit', 'Crédit budgétaire')
    engagement_ref = fields.Char('Référence d\'engagement')
    engagement_date = fields.Date('Date d\'engagement')
    purchase_order_id = fields.Many2one('purchase.order', 'Bon de commande Odoo')
    cotation_ids = fields.One2many('e_gestock.cotation', 'demande_id', 'Cotations')
```

## 5. Workflows et processus

### 5.1 Workflow des demandes d'achat
1. **Création** - Par Gestionnaire des achats
2. **Soumission pour validation** - Transfert au responsable de section
3. **Validation section** - Approbation par le responsable de section
4. **Validation structure** - Approbation par le responsable de structure
5. **Validation responsable des achats** - Vérification et approbation
6. **Validation DMP** - Approbation par le responsable DMP
7. **Contrôle budgétaire** - Vérification des fonds disponibles
8. **Validation DFC** - Approbation par la Direction Financière et Comptable
9. **Validation finale** - Approbation par la direction générale :
   - Si montant < 5 000 000 : Validation par le Directeur Général Adjoint (DGA)
   - Si montant ≥ 5 000 000 : Validation par le Directeur Général (DG)
10. **Engagement budgétaire** - Réservation des fonds avec référence
11. **Passage à l'état 'quotation'** - Prêt pour le processus de cotation
12. **Transmission pour cotation** - Envoi aux fournisseurs
13. **Réception des offres** - Collecte des propositions
14. **Sélection du mieux-disant** - Choix du fournisseur
15. **Génération bon de commande** - Création de la commande dans Odoo
16. **Livraison** - Réception des articles

### 5.2 Workflow du processus de cotation
1. **Création** - Création d'une cotation fournisseur pour une demande d'achat en état 'quotation'
2. **Sélection du fournisseur** - Choix du partenaire fournisseur (supplier_rank > 0)
3. **Importation des lignes** - Récupération automatique des lignes de la demande d'achat
4. **Envoi au fournisseur** - Notification au fournisseur via le portail et email
5. **Accès portail fournisseur** - Le fournisseur se connecte au portail pour voir la demande
6. **Saisie des prix par le fournisseur** - Le fournisseur saisit les prix unitaires via le portail
7. **Saisie des conditions par le fournisseur** - Le fournisseur indique ses conditions commerciales (délai, paiement)
8. **Soumission par le fournisseur** - Le fournisseur soumet son offre via le portail
9. **Notification de soumission** - Le système notifie les acheteurs de la réception d'une offre
10. **Confirmation** - Passage de la cotation à l'état 'confirmed' après vérification
11. **Comparaison** - Analyse des différentes cotations reçues pour la même demande
12. **Sélection du mieux-disant** - Marquage d'une cotation comme 'mieux-disant'
    - Les autres cotations sont automatiquement marquées comme 'rejected'
    - La demande d'achat passe à l'état 'quoted'
13. **Validation du mieux-disant** - Passage de la demande d'achat à l'état 'best_selected'
14. **Génération du bon de commande** - Création automatique d'un bon de commande Odoo
    - Création de produits temporaires si nécessaire pour les articles non stockables
    - Transfert des prix et quantités vers le bon de commande
    - Passage de la cotation à l'état 'po_generated'
    - Passage de la demande d'achat à l'état 'po_generated'
15. **Notification au fournisseur** - Le fournisseur est informé via le portail que son offre a été acceptée

### 5.3 Workflow des mouvements de stock
1. **Création** - Création du mouvement avec type (entrée, sortie, transfert, ajustement)
2. **Sélection des dépôts** - Définition des dépôts source et/ou destination selon le type
3. **Ajout des articles** - Sélection des articles et quantités à mouvementer
4. **Confirmation** - Vérification des disponibilités et confirmation du mouvement
5. **Validation** - Création des mouvements Odoo correspondants (stock.picking)
6. **Exécution** - Traitement des mouvements dans Odoo
7. **Mise à jour** - Actualisation des quantités dans les articles en stock

### 5.4 Workflow des inventaires
1. **Création** - Création de l'inventaire pour un dépôt spécifique
2. **Démarrage** - Génération automatique des lignes avec quantités théoriques
3. **Comptage** - Saisie des quantités réelles et marquage des lignes comme comptées
4. **Validation** - Vérification que toutes les lignes sont comptées
5. **Ajustement** - Création automatique d'un mouvement d'ajustement pour les écarts
6. **Finalisation** - Mise à jour des stocks avec les nouvelles quantités

### 5.5 Workflow des réceptions
1. **Création** - Enregistrement de la réception avec référence au bon de commande
2. **Importation des lignes** - Récupération automatique des lignes du bon de commande avec calcul des quantités restant à recevoir
3. **Saisie des quantités** - Ajustement des quantités effectivement reçues
4. **Contrôle qualité** - Vérification et marquage des articles (conforme/non conforme)
5. **Saisie des informations BL** - Enregistrement du numéro et de la date du bon de livraison fournisseur
6. **Confirmation** - Passage de la réception à l'état 'confirmed' avec vérification des quantités
7. **Validation** - Création automatique d'un mouvement de stock d'entrée
8. **Mise à jour des stocks** - Incrémentation automatique des stocks dans le dépôt de destination
9. **Mise à jour de la demande** - Passage de la demande d'achat à l'état 'delivered' si toutes les quantités sont reçues

## 6. Modèles de données complémentaires

### 6.1 Modèle d'API (e_gestock_api)
```python
# Dans controllers/api.py
class EGestockApiController(http.Controller):
    
    @http.route('/api/v1/auth/token', type='json', auth='none', methods=['POST'], csrf=False)
    def get_token(self, login, password, **kw):
        # Authentification et génération du token JWT
        pass
    
    @http.route('/api/v1/product/qr/<code>', type='http', auth='jwt', methods=['GET'])
    def get_product_by_qr(self, code, **kw):
        # Récupération des informations produit via QR code
        product = request.env['e_gestock.article'].sudo().search([('qr_code', '=', code)], limit=1)
        if not product:
            return http.Response(json.dumps({'error': 'Product not found'}), 
                                status=404, content_type='application/json')
        
        # Construction de la réponse avec toutes les infos requises
        data = {
            'article': {
                'ref': product.ref_article,
                'designation': product.design_article,
                'famille': product.famille_id.design_fam,
                'description': product.description or '',
            },
            'fournisseur': {
                'nom': product.last_supplier_id.name,
                'contact': product.last_supplier_id.phone,
            },
            'stock': {
                'quantite_disponible': product.get_stock_quantity(),
                'depots': product.get_stock_by_depot(),
            },
            'mouvements': product.get_recent_movements(),
        }
        
        return http.Response(json.dumps(data), 
                           status=200, content_type='application/json')
```

### 6.2 Structure des modules E-GESTOCK pour Odoo 18

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
  │   ├── article.py
  │   └── depot.py
  ├── views/
  │   ├── structure_views.xml
  │   ├── section_views.xml
  │   ├── type_gestion_views.xml
  │   ├── famille_views.xml
  │   ├── article_views.xml
  │   ├── depot_views.xml
  │   └── menu_views.xml
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_security.xml
  ├── data/
  │   └── e_gestock_data.xml
  └── static/
      ├── description/
      │   └── icon.png
      └── src/
          ├── js/
          └── css/
```

## 7. Gestion des utilisateurs et droits d'accès

### 7.1 Centralisation des droits d'accès
La gestion des droits d'accès est centralisée dans le module de base (e_gestock_base) pour assurer une cohérence à travers tous les modules E-Gestock. Cette approche permet :
- Une gestion unifiée des profils utilisateurs
- Une maintenance simplifiée des droits d'accès
- Une meilleure sécurité et traçabilité
- Une cohérence dans l'attribution des permissions

### 7.2 Profils utilisateurs

#### 7.2.1 Groupe de base
- **Utilisateur E-Gestock** (`group_e_gestock_user`) - Accès de base aux fonctionnalités E-Gestock

#### 7.2.2 Groupes administratifs
- **Administrateur** (`group_e_gestock_admin`) - Gestion complète du système
- **Directeur Général/Adjoint** (`group_e_gestock_direction`) - Direction générale
- **Validateur DG** (`group_dg_validator`) - Validation par le Directeur Général (montants ≥ 5 000 000)
- **Validateur DGAA** (`group_dgaa_validator`) - Validation par le Directeur Général Adjoint (montants < 5 000 000)

#### 7.2.3 Groupes achats
- **Gestionnaire des achats** (`group_e_gestock_gestionnaire_achats`) - Gestion quotidienne des achats
- **Responsable des achats** (`group_e_gestock_resp_achats`) - Supervision des achats
- **Responsable Section** (`group_section_manager`) - Gestion au niveau section
- **Responsable Structure** (`group_structure_manager`) - Gestion au niveau structure
- **Gestionnaire des Cotations** (`group_quotation_manager`) - Gestion des demandes de cotation
- **Visualiseur des Validations** (`group_validation_viewer`) - Consultation des validations

#### 7.2.4 Groupes stocks
- **Gestionnaire des stocks** (`group_e_gestock_gestionnaire_stocks`) - Gestion quotidienne des stocks
- **Responsable des stocks** (`group_e_gestock_resp_stocks`) - Supervision des stocks
- **Responsable Réception** (`group_reception_manager`) - Gestion des réceptions
- **Responsable Dépôt** (`group_e_gestock_resp_depot`) - Gestion des dépôts

#### 7.2.5 Groupes finances
- **Responsable DMP** (`group_e_gestock_resp_dmp`) - Direction des Marchés Publics
- **Responsable contrôle budgétaire** (`group_e_gestock_resp_budget`) - Supervision du budget
- **Contrôleur Budgétaire** (`group_budget_controller`) - Contrôle des budgets
- **Engageur Budgétaire** (`group_budget_engager`) - Engagement des budgets
- **Responsable DFC** (`group_e_gestock_resp_dfc`) - Direction Financière et Comptable
- **Validateur DFC** (`group_dfc_validator`) - Validation financière

#### 7.2.6 Groupes spécifiques modules
- **Gestionnaire Immobilisations** (`group_asset_manager`) - Gestion des immobilisations
- **Gestionnaire Travaux** (`group_works_manager`) - Gestion des travaux
- **Superviseur Travaux** (`group_works_supervisor`) - Supervision des travaux
- **Gestionnaire Perdiems** (`group_perdiem_manager`) - Gestion des perdiems
- **Validateur Perdiems** (`group_perdiem_validator`) - Validation des perdiems
- **Gestionnaire Demandes de Fonds** (`group_fund_request_manager`) - Gestion des demandes de fonds
- **Validateur Demandes de Fonds** (`group_fund_request_validator`) - Validation des demandes de fonds

#### 7.2.7 Groupes externes
- **Fournisseur** (`group_e_gestock_fournisseur`) - Accès limité pour les fournisseurs via le portail
  - Accès aux demandes de cotation qui leur sont adressées
  - Possibilité de saisir et soumettre des offres
  - Consultation des bons de commande générés
  - Accès à l'historique de leurs cotations
- **API Mobile** (`group_e_gestock_api_mobile`) - Accès limité pour l'application mobile
  - Lecture des informations des articles via code QR
  - Consultation des stocks par dépôt
  - Accès aux informations des fournisseurs
  - Consultation des mouvements de stock

### 7.3 Gestion des droits

#### 7.3.1 Principes généraux
- Contrôle d'accès basé sur les groupes de sécurité Odoo
- Restrictions par module fonctionnel
- Permissions spécifiques selon le workflow
- Visibilité des menus en fonction des groupes
- Règles d'accès par structure et section

#### 7.3.2 Matrice des droits
Le système utilise une matrice de droits détaillée qui définit précisément les permissions CRUD (Create, Read, Update, Delete) pour chaque groupe sur les différents modules fonctionnels :

| Groupe | Demandes d'achat | Cotations | Réceptions | Stocks | Budget | Immobilisations | Travaux | Perdiems | Demandes de fonds | Fournisseurs |
|--------|-----------------|-----------|------------|--------|--------|----------------|---------|----------|------------------|-------------|
| Administrateur | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD |
| Gestionnaire des achats | CRU | CRU | CRU | - | - | - | - | - | - | R |
| Responsable des achats | CRU | CRUD | CRUD | - | - | - | - | - | - | CRUD |
| Responsable DMP | RU | RU | - | - | - | - | - | - | - | R |
| Responsable contrôle budgétaire | RU | - | - | - | CRUD | - | - | - | - | - |
| Contrôleur Budgétaire | RU | - | - | - | CRUD | - | - | - | - | - |
| Engageur Budgétaire | RU | - | - | - | CRUD | - | - | - | - | - |
| Responsable DFC | RU | - | - | - | RU | - | - | - | - | - |
| Validateur DFC | RU | - | - | - | RU | - | - | - | - | - |
| Direction Générale | RU | - | - | - | RU | - | RU | RU | RU | R |
| Validateur DG | RU | - | - | - | RU | - | RU | RU | RU | - |
| Validateur DGAA | RU | - | - | - | RU | - | RU | RU | RU | - |
| Gestionnaire des stocks | - | - | RU | CRU | - | - | - | - | - | - |
| Responsable des stocks | - | - | RU | CRUD | - | - | - | - | - | R |
| Responsable Réception | - | - | CRUD | RU | - | - | - | - | - | - |
| Responsable Dépôt | - | - | - | CRUD | - | - | - | CRUD | - | - |

La matrice complète inclut également les droits pour les groupes spécifiques aux modules (immobilisations, travaux, perdiems, demandes de fonds) et le groupe Fournisseur qui a un accès limité via le portail.

#### 7.3.3 Règles de sécurité
Des règles de sécurité spécifiques sont définies pour :
- L'accès multi-société aux structures
- L'accès multi-société aux dépôts
- Les restrictions par structure et section pour les utilisateurs

## 8. Interfaces et intégrations

### 8.1 Interface utilisateur
- Interface web Odoo 18
- Tableaux de bord personnalisés par profil
- Formulaires de saisie structurés
- Vues adaptées aux besoins spécifiques (liste, formulaire, kanban)
- Boutons d'action personnalisés

### 8.2 Intégrations avec Odoo
- Extension des modèles Odoo existants (product.product, product.template, etc.)
- Création de modèles spécifiques à E-Gestock
- Utilisation des API Odoo pour les interactions
- Respect des standards Odoo pour les vues et les actions
- Intégration avec le portail Odoo pour l'accès fournisseurs
- Utilisation du système d'authentification Odoo pour le portail
- Synchronisation bidirectionnelle entre les partenaires Odoo et les fournisseurs E-Gestock

### 8.3 API REST pour application mobile
- Création d'une API REST sécurisée pour l'accès depuis une application mobile
- Authentification par token JWT avec expiration configurable
- Endpoint dédié pour la lecture des informations via code QR
- Accès aux données des articles via leur code QR unique
- Informations accessibles via l'API :
  - Détails de l'article (nom, référence, famille, description)
  - Fournisseur ayant livré l'article (nom, coordonnées)
  - Structure et section ayant demandé l'article
  - Quantité distribuée de l'article
  - Quantité en stock par dépôt/entrepot
  - Historique des mouvements de l'article
- Documentation complète de l'API avec Swagger/OpenAPI
- Gestion des droits d'accès spécifiques pour l'API mobile
- Limitation du taux de requêtes pour éviter les abus
- Journalisation des accès pour audit de sécurité

## 9. Spécifications techniques

### 9.1 Architecture technique
- Modules Odoo 18 Community
- Dépendance uniquement aux modules de base d'Odoo
- Utilisation des vues Odoo 18 (liste au lieu de tree)
- Respect des standards de développement Odoo
- Module dédié e_gestock_api pour l'API REST mobile
- Utilisation du framework de contrôleur HTTP d'Odoo pour l'API

### 9.2 Sécurité
- Groupes de sécurité bien définis
- Droits d'accès précis pour chaque modèle
- Visibilité des menus en fonction des groupes
- Règles d'accès pour les données sensibles
- Sécurisation de l'API REST avec authentification par token
- Groupe de sécurité spécifique pour l'accès à l'API mobile
- Chiffrement des communications API via HTTPS
- Protection contre les attaques CSRF et XSS

### 9.3 Performance
- Optimisation des requêtes SQL
- Indexation des champs fréquemment utilisés
- Utilisation efficace du cache Odoo
- Pagination des résultats pour les grandes listes
- Mise en cache des réponses API pour réduire la charge serveur
- Compression des données API pour optimiser la bande passante
- Optimisation des requêtes API avec champs sélectifs

### 9.4 Plan de mise en œuvre et déploiement
Le déploiement suivra ces étapes:
1. Développement du module de base (`e_gestock_base`)
2. Développement des modules fonctionnels un par un
3. Tests unitaires et d'intégration pour chaque module
4. Tests de performance et d'utilisabilité
5. Migration des données depuis la version Laravel
6. Déploiement en environnement de test
7. Validation fonctionnelle
8. Déploiement en production
9. Support post-déploiement

## 10. Améliorations et spécifications particulières

### 10.1 Interface utilisateur
- Utilisation des vues Odoo 18 (liste au lieu de tree)
- Boutons d'action personnalisés dans les vues liste
- Formulaires adaptés aux besoins spécifiques
- Menus organisés de manière logique et intuitive

### 10.2 Gestion des articles
- Un article E-Gestock doit obligatoirement appartenir à une famille d'articles E-Gestock
- Création automatique d'un produit Odoo lors de la création d'un article E-Gestock
- Synchronisation des données entre les articles E-Gestock et les produits Odoo
- Possibilité de convertir des produits Odoo en articles E-Gestock

### 10.3 Gestion budgétaire

#### 10.3.1 Exercices budgétaires
- Un seul exercice peut être actif à la fois (is_active = True)
- L'exercice actif est utilisé par défaut pour toutes les opérations budgétaires
- Les exercices peuvent être ouverts ou fermés (state = 'ouvert' ou 'ferme')
- La clôture d'un exercice empêche toute nouvelle opération sur cet exercice
- Les dates de début et de fin sont vérifiées pour assurer leur cohérence

#### 10.3.2 Crédits budgétaires
- Les crédits budgétaires sont définis par structure, famille d'articles et type de gestion
- Le système empêche tout dépassement de crédit disponible
- Des alertes sont générées lorsque le crédit disponible passe sous un seuil configurable
- Les crédits peuvent être augmentés en cours d'exercice
- L'historique des modifications est conservé via le système de suivi (tracking)

#### 10.3.3 Intégration avec les demandes d'achat
- **Pour les demandes d'achat, les comptes budgétaires SONT les familles d'articles**
- L'exercice actif (exemple '2025') doit être défini dans le module budget
- Les utilisateurs ne peuvent soumettre une demande que si les fonds sont disponibles sur le compte budgétaire (famille) correspondant
- Pour les commandes stockables, les utilisateurs ne peuvent sélectionner que des produits de la famille choisie (compte budgétaire)
- Pour les commandes non stockables, les utilisateurs peuvent spécifier des descriptions de produits personnalisées, mais doivent les rattacher à une famille d'articles pour la gestion budgétaire
- Le système met automatiquement à jour les consommations budgétaires de la famille concernée lors de la validation des demandes

### 10.4 Menu E-Gestock
- Le clic sur E-Gestock affiche un menu d'options plutôt que d'ouvrir directement une demande d'achat
- Organisation claire des menus et sous-menus
- Séparation des fonctionnalités de configuration et d'utilisation

### 10.5 API Mobile et codes QR
- Génération automatique de codes QR uniques pour chaque article
- Impression des codes QR sur les étiquettes des articles
- Stockage du code QR dans la fiche article pour référence
- Endpoint API dédié `/api/v1/product/qr/{code}` pour la lecture des informations
- Format de réponse JSON standardisé avec toutes les informations requises
- Possibilité de filtrer les informations retournées via paramètres de requête
- Journalisation des scans de codes QR pour analyse statistique
- Interface d'administration pour la gestion des accès API
- Documentation interactive de l'API accessible via l'interface web

### 10.6 Rapports et tableaux de bord avancés

#### 10.6.1 Tableaux de bord par profil
Suite à l'analyse des documents et des captures d'écran, il apparaît que chaque profil utilisateur dispose d'un tableau de bord spécifique :
- **Gestionnaire des achats** : Suivi des demandes d'achat en cours, à traiter et approuvées
- **Responsable des achats** : Vue d'ensemble des performances d'achat, économies réalisées
- **Responsable DMP** : Suivi des cotations et des fournisseurs
- **Contrôleur budgétaire** : État des consommations budgétaires et alertes de dépassement
- **Direction** : Synthèse globale des indicateurs clés (KPI) et performances

#### 10.6.2 Indicateurs de performance
Les KPI suivants ont été identifiés dans les documents et seront implémentés :
- Taux de validation des demandes d'achat
- Délai moyen de traitement par étape de workflow
- Économies réalisées par rapport aux budgets alloués
- Taux de rotation des stocks par famille d'article
- Performance des fournisseurs (délais, qualité, prix)
- Taux d'utilisation des budgets par structure et famille

#### 10.6.3 Rapports spécifiques
Des rapports spécifiques seront développés pour couvrir les besoins identifiés :
- Rapport de suivi des engagements budgétaires
- Rapport d'analyse des prix fournisseurs
- Rapport de consommation des budgets par structure/section
- Rapport des articles à fort taux de rotation
- Rapport des alertes de stock (ruptures potentielles)
- Rapport d'activité par utilisateur (validations, créations)

### 10.7 Migration depuis la version Laravel

#### 10.7.1 Stratégie de migration des données
La migration depuis la version Laravel actuelle d'E-GESTOCK vers Odoo 18 suivra les étapes suivantes :
- Analyse détaillée du schéma de base de données Laravel actuel
- Mapping des données entre les structures Laravel et les modèles Odoo
- Développement d'un outil ETL (Extract-Transform-Load) spécifique
- Validation des données migrées via des jeux de test représentatifs
- Stratégie de conversion des données spécifiques (identifiants, références)

#### 10.7.2 Modèles de données à migrer
D'après l'analyse des fichiers sources, les modèles suivants nécessiteront une migration :
- Structures et sections
- Types de gestion
- Familles d'articles et articles
- Dépôts et stocks
- Exercices et crédits budgétaires
- Demandes d'achat et leurs lignes
- Cotations fournisseurs
- Mouvements de stock
- Utilisateurs et profils

#### 10.7.3 Conservation de la continuité des opérations
Pour assurer une transition fluide, les éléments suivants seront mis en place :
- Conservation des numéros séquentiels actuels pour les documents existants
- Maintien des références externes (codes, identifiants)
- Période de fonctionnement en parallèle des deux systèmes
- Migration progressive par module fonctionnel
- Validation croisée des données et des calculs entre les deux systèmes
- Procédure de rollback en cas de problème majeur

#### 10.7.4 Interface transitoire
Une interface transitoire sera développée pour faciliter la période de cohabitation entre les deux systèmes :
- API d'échange bidirectionnel de données
- Détection des incohérences potentielles entre les deux systèmes
- Journalisation des échanges pour audit
- Interface utilisateur permettant le basculement progressif
- Documentation détaillée des équivalences fonctionnelles entre les deux systèmes

## 11. Glossaire

- **DFC** : Direction Financière et Comptable
- **DGA** : Directeur Général Adjoint
- **DG** : Directeur Général
- **DGAA** : Directeur Général Adjoint aux Affaires Administratives
- **DMP** : Direction des Marchés Publics
- **BC** : Bon de Commande
- **DA** : Demande d'Achat
- **DC** : Demande de Cotation
- **DF** : Demande de Fonds
- **UOM** : Unit of Measure (Unité de mesure)
- **CRUD** : Create, Read, Update, Delete (Créer, Lire, Mettre à jour, Supprimer) - Niveaux de permissions
- **API** : Application Programming Interface (Interface de programmation d'application)
- **REST** : Representational State Transfer (Architecture de conception pour les API web)
- **JWT** : JSON Web Token (Standard pour la création de tokens d'accès)
- **QR Code** : Quick Response Code (Code-barres matriciel permettant de stocker des informations)
- **Famille d'articles** : Regroupement d'articles ayant des caractéristiques communes
- **Compte budgétaire** : Dans E-Gestock, correspond à une famille d'articles pour le suivi budgétaire
- **Exercice budgétaire** : Période comptable (généralement annuelle) pour la gestion des budgets
- **Seuil de validation** : Montant (5 000 000) déterminant le niveau de validation requis (DGA ou DG)
- **Matrice des droits** : Système définissant les permissions CRUD pour chaque groupe d'utilisateurs sur les différents modules
- **Swagger/OpenAPI** : Spécification pour la documentation des API REST

## 12. Fonctionnalités spécifiques complémentaires

### 12.1 Module de gestion des comités de réception

#### 12.1.1 Composition des comités de réception
- Gestion des membres du comité de réception
- Attribution des rôles (président, secrétaire, membres)
- Configuration des droits spécifiques de chaque rôle
- Notification automatique aux membres lors d'une livraison
- Suivi des présences aux sessions de réception

#### 12.1.2 Processus de réception
- Planification des sessions de réception
- Ordre du jour automatisé basé sur les livraisons attendues
- Procès-verbal de réception avec signatures électroniques
- Validation des livraisons par le comité avec quorum requis
- Gestion des réserves et non-conformités identifiées
- Suivi des actions correctives demandées aux fournisseurs

### 12.2 Automatisation des notifications

#### 12.2.1 Alertes et rappels
- Notifications automatiques pour les demandes nécessitant validation
- Rappels avant expiration des délais de validation configurables
- Alertes sur dépassement des délais de validation
- Notifications aux fournisseurs pour les demandes de cotation
- Rappels de date limite pour la soumission des offres
- Alertes sur réception des bons de commande

#### 12.2.2 Intégration avec les canaux de communication
- Notifications par email avec les informations essentielles
- Notifications internes via le système de messagerie Odoo
- Possibilité d'envoi de SMS pour les validations urgentes (via module optionnel)
- Tableau de bord personnalisé par profil utilisateur montrant les actions en attente
- Historique des notifications envoyées et reçues

### 12.3 Fonctionnalités d'exportation et d'impression 

#### 12.3.1 Documents d'achat
- Modèles de documents personnalisés (demandes d'achat, bons de commande)
- Multiples formats d'export (PDF, Excel, CSV)
- Impression par lots de documents (multiples bons de commande)
- Tampons et signatures électroniques sur les documents officiels
- Numérotation automatique des documents avec séquences paramétrables

#### 12.3.2 Analyses et statistiques
- Rapports prédéfinis avec filtres dynamiques
- Tableaux croisés dynamiques pour analyses multidimensionnelles
- Graphiques et visualisations personnalisables
- Export vers Excel pour analyses avancées
- Rapports de comparaison périodiques (mensuels, trimestriels, annuels)

### 12.4 Gestion des devises et taxes

#### 12.4.1 Devises multiples
- Support des transactions en devises étrangères
- Taux de change configurables (fixes ou dynamiques)
- Conversion automatique vers la devise de base pour la comptabilité
- Historique des taux de change utilisés dans les transactions
- Rapports consolidés dans la devise de base

#### 12.4.2 Taxes et frais
- Gestion des différents types de taxes (TVA, droits de douane)
- Application automatique des taxes selon les produits et fournisseurs
- Calcul des frais annexes (transport, assurance)
- Ventilation des frais sur les lignes de commande
- Intégration avec le module comptable d'Odoo

### 12.5 Intégration avec les systèmes externes

#### 12.5.1 Import/Export de données
- Import de catalogues produits externes
- Export des données vers les systèmes comptables
- Interfaces avec les systèmes ERP existants
- Synchonisation avec les bases de données fournisseurs
- Import/Export au format standard (XML, CSV, JSON)

#### 12.5.2 Interopérabilité
- API REST complète pour intégrations tierces 
- Webhooks configurables pour les événements clés
- Authentification sécurisée pour les systèmes externes
- Documentation technique de l'API pour les développeurs
- Environnement de test pour les développements d'intégration

## 13. Plan de formation et accompagnement

### 13.1 Formation des utilisateurs
- Sessions de formation par profil utilisateur
- Documentation contextualisée par type d'utilisateur
- Tutoriels vidéo pour les principales fonctionnalités
- Environnement de formation dédié avec données de test
- Certification des utilisateurs clés

### 13.2 Support et assistance
- Procédures de demande d'assistance
- Niveaux de service (SLA) par type d'incident
- Base de connaissances partagée
- Forum d'entraide entre utilisateurs
- Centre d'assistance pour le support technique

### 13.3 Déploiement et conduite du changement
- Planning de déploiement par phases
- Stratégie de migration des données existantes
- Période de fonctionnement en parallèle
- Procédures de basculement
- Plan de communication et d'accompagnement au changement

## 14. Annexes

### 14.1 Glossaire des termes métier
- Définition détaillée des termes spécifiques au domaine
- Correspondance entre termes métier et concepts techniques
- Acronymes utilisés dans le système

### 14.2 Matrices de permissions détaillées
- Matrice complète des autorisations CRUD par profil utilisateur
- Règles d'accès aux données par structure et section
- Restrictions de visibilité par niveau hiérarchique

### 14.3 Schémas des flux de validation
- Représentations graphiques des workflows de validation
- Diagrammes de séquence des processus clés
- Matrices de responsabilité (RACI) pour les processus stratégiques

### 14.4 Modèles de documents
- Exemples de documents générés par le système
- Nomenclature des documents et règles de nommage
- Formats d'export standard
