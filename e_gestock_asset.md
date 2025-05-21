# Module de gestion des immobilisations (e_gestock_asset)

## Description
Le module e_gestock_asset permet la gestion des immobilisations dans la solution E-GESTOCK pour Odoo 18 Community. Il assure le suivi du cycle de vie des biens immobilisés depuis leur acquisition jusqu'à leur sortie du patrimoine, en passant par leur utilisation et leur maintenance.

## Dépendances
- e_gestock_base
- e_gestock_inventory
- base
- mail
- web

## Fonctionnalités principales

### 1. Enregistrement des immobilisations

#### 1.1 Immobilisations (e_gestock.asset)
- `reference` : Référence unique de l'immobilisation
- `name` : Nom de l'immobilisation
- `article_id` : Article E-GESTOCK associé (optionnel)
- `type_id` : Type d'immobilisation
- `date_acquisition` : Date d'acquisition
- `date_mise_service` : Date de mise en service
- `valeur_acquisition` : Valeur d'acquisition
- `valeur_residuelle` : Valeur résiduelle
- `duree_amortissement` : Durée d'amortissement (en années)
- `methode_amortissement` : Méthode d'amortissement (linéaire, dégressif)
- `structure_id` : Structure propriétaire
- `section_id` : Section propriétaire
- `responsable_id` : Responsable
- `localisation` : Localisation physique
- `state` : État (en stock, en service, en maintenance, hors service, cédé)
- `note` : Notes et observations

#### 1.2 Types d'immobilisations (e_gestock.asset_type)
- `code` : Code unique du type
- `name` : Nom du type
- `account_asset_id` : Compte d'actif
- `account_depreciation_id` : Compte d'amortissement
- `account_expense_id` : Compte de charge
- `duree_amortissement` : Durée d'amortissement par défaut
- `methode_amortissement` : Méthode d'amortissement par défaut

#### 1.3 Acquisitions d'immobilisations
- Création à partir des articles E-GESTOCK achetés
- Saisie manuelle des informations
- Calcul automatique des paramètres d'amortissement
- Génération du tableau d'amortissement
- Suivi des documents liés à l'acquisition

### 2. Suivi du cycle de vie

#### 2.1 Affectations (e_gestock.asset_assignment)
- `asset_id` : Immobilisation concernée
- `utilisateur_id` : Utilisateur affecté
- `date_debut` : Date de début d'affectation
- `date_fin` : Date de fin d'affectation (optionnel)
- `structure_id` : Structure d'affectation
- `section_id` : Section d'affectation
- `localisation` : Localisation pendant l'affectation
- `motif` : Motif de l'affectation
- `state` : État (en cours, terminée)

#### 2.2 Transferts (e_gestock.asset_transfer)
- `asset_id` : Immobilisation concernée
- `date` : Date du transfert
- `structure_origine_id` : Structure d'origine
- `structure_destination_id` : Structure de destination
- `responsable_origine_id` : Responsable d'origine
- `responsable_destination_id` : Responsable de destination
- `motif` : Motif du transfert
- `note` : Notes explicatives

#### 2.3 Sorties d'immobilisations (e_gestock.asset_disposal)
- `asset_id` : Immobilisation concernée
- `date` : Date de sortie
- `motif` : Motif de la sortie (cession, mise au rebut, vol, don)
- `valeur_nette_comptable` : Valeur nette comptable à la date de sortie
- `prix_cession` : Prix de cession (si applicable)
- `plus_value` : Plus-value réalisée (calculée)
- `moins_value` : Moins-value réalisée (calculée)
- `autorisation_id` : Référence à l'autorisation de sortie
- `document_ids` : Documents justificatifs

### 3. Maintenance des immobilisations

#### 3.1 Maintenances (e_gestock.asset_maintenance)
- `reference` : Référence unique de la maintenance
- `asset_id` : Immobilisation concernée
- `date_debut` : Date de début
- `date_fin` : Date de fin (réelle ou prévue)
- `type` : Type de maintenance (préventive, corrective, réglementaire)
- `description` : Description des travaux
- `prestataire_id` : Prestataire (fournisseur)
- `cout` : Coût de la maintenance
- `state` : État (planifiée, en cours, terminée, annulée)
- `responsable_id` : Responsable du suivi
- `note` : Notes et observations

#### 3.2 Planification des maintenances
- Création des plans de maintenance préventive
- Définition des fréquences d'intervention
- Génération automatique des maintenances planifiées
- Alertes sur les maintenances à réaliser
- Suivi du respect du calendrier de maintenance

#### 3.3 Coûts de maintenance
- Suivi détaillé des coûts par intervention
- Analyse des coûts par type de maintenance
- Comparaison des coûts réels vs prévus
- Calcul du coût total de possession (TCO)
- Alertes sur les dépassements de budget

### 4. Gestion documentaire

#### 4.1 Documents liés (e_gestock.asset_document)
- `asset_id` : Immobilisation concernée
- `name` : Nom du document
- `type` : Type de document (facture, garantie, manuel, certificat, etc.)
- `date_emission` : Date d'émission
- `date_expiration` : Date d'expiration (si applicable)
- `emetteur` : Émetteur du document
- `attachment_id` : Pièce jointe
- `note` : Notes et observations

#### 4.2 Suivi des garanties
- Enregistrement des garanties par immobilisation
- Suivi des dates d'expiration
- Alertes avant expiration
- Historique des interventions sous garantie

## Modèles de données

### 1. Immobilisations
```python
class Asset(models.Model):
    _name = 'e_gestock.asset'
    _description = 'Immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    name = fields.Char(string='Nom', required=True, tracking=True)
    article_id = fields.Many2one('e_gestock.article', string='Article E-GESTOCK', tracking=True)
    type_id = fields.Many2one('e_gestock.asset_type', string='Type d\'immobilisation', required=True, tracking=True)
    date_acquisition = fields.Date(string='Date d\'acquisition', tracking=True)
    date_mise_service = fields.Date(string='Date de mise en service', tracking=True)
    valeur_acquisition = fields.Monetary(string='Valeur d\'acquisition', tracking=True)
    valeur_residuelle = fields.Monetary(string='Valeur résiduelle', tracking=True)
    duree_amortissement = fields.Integer(string='Durée amortissement (années)', tracking=True)
    methode_amortissement = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressive')
    ], string='Méthode amortissement', default='linear', tracking=True)
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    localisation = fields.Char(string='Localisation', tracking=True)
    state = fields.Selection([
        ('in_stock', 'En stock'),
        ('in_service', 'En service'),
        ('in_maintenance', 'En maintenance'),
        ('out_of_service', 'Hors service'),
        ('disposed', 'Cédé/Sorti')
    ], string='État', default='in_stock', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    note = fields.Text(string='Notes')
    
    # Relations
    assignment_ids = fields.One2many('e_gestock.asset_assignment', 'asset_id', string='Affectations')
    maintenance_ids = fields.One2many('e_gestock.asset_maintenance', 'asset_id', string='Maintenances')
    transfer_ids = fields.One2many('e_gestock.asset_transfer', 'asset_id', string='Transferts')
    disposal_id = fields.One2many('e_gestock.asset_disposal', 'asset_id', string='Sortie')
    document_ids = fields.One2many('e_gestock.asset_document', 'asset_id', string='Documents')
    amortization_line_ids = fields.One2many('e_gestock.asset_amortization_line', 'asset_id', string='Lignes amortissement')
    
    # Champs calculés
    valeur_nette_comptable = fields.Monetary(string='Valeur nette comptable', compute='_compute_vnc', store=True)
    montant_amortissement_annuel = fields.Monetary(string='Amortissement annuel', compute='_compute_amortissement_annuel', store=True)
    current_assignment_id = fields.Many2one('e_gestock.asset_assignment', string='Affectation actuelle', compute='_compute_current_assignment')
    current_utilisateur_id = fields.Many2one('res.users', string='Utilisateur actuel', compute='_compute_current_utilisateur')
    
    @api.model
    def create(self, vals):
        if vals.get('reference', 'Nouveau') == 'Nouveau':
            vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset') or 'Nouveau'
        return super(Asset, self).create(vals)
    
    @api.depends('valeur_acquisition', 'amortization_line_ids', 'amortization_line_ids.remaining_value')
    def _compute_vnc(self):
        for asset in self:
            if not asset.amortization_line_ids:
                asset.valeur_nette_comptable = asset.valeur_acquisition
            else:
                last_line = asset.amortization_line_ids.sorted(lambda l: l.date)[-1]
                asset.valeur_nette_comptable = last_line.remaining_value
    
    @api.depends('valeur_acquisition', 'valeur_residuelle', 'duree_amortissement')
    def _compute_amortissement_annuel(self):
        for asset in self:
            if asset.duree_amortissement > 0:
                asset.montant_amortissement_annuel = (asset.valeur_acquisition - asset.valeur_residuelle) / asset.duree_amortissement
            else:
                asset.montant_amortissement_annuel = 0
```

### 2. Types d'immobilisations
```python
class AssetType(models.Model):
    _name = 'e_gestock.asset_type'
    _description = 'Type d\'immobilisation'
    
    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Nom', required=True)
    account_asset_id = fields.Char(string='Compte d\'actif')
    account_depreciation_id = fields.Char(string='Compte d\'amortissement')
    account_expense_id = fields.Char(string='Compte de charge')
    duree_amortissement = fields.Integer(string='Durée amortissement par défaut (années)')
    methode_amortissement = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressive')
    ], string='Méthode amortissement par défaut', default='linear')
    note = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code du type d\'immobilisation doit être unique!')
    ]
```

### 3. Lignes d'amortissement
```python
class AssetAmortizationLine(models.Model):
    _name = 'e_gestock.asset_amortization_line'
    _description = 'Ligne d\'amortissement'
    _order = 'date'
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Séquence')
    date = fields.Date(string='Date')
    amount = fields.Monetary(string='Montant amortissement')
    remaining_value = fields.Monetary(string='Valeur résiduelle')
    depreciated_value = fields.Monetary(string='Valeur amortie')
    currency_id = fields.Many2one('res.currency', string='Devise', related='asset_id.currency_id')
```

### 4. Affectations
```python
class AssetAssignment(models.Model):
    _name = 'e_gestock.asset_assignment'
    _description = 'Affectation d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    utilisateur_id = fields.Many2one('res.users', string='Utilisateur', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', tracking=True)
    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True)
    localisation = fields.Char(string='Localisation', tracking=True)
    motif = fields.Text(string='Motif', tracking=True)
    state = fields.Selection([
        ('active', 'En cours'),
        ('terminated', 'Terminée')
    ], string='État', default='active', tracking=True)
    
    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for assignment in self:
            if assignment.date_fin and assignment.date_fin < assignment.date_debut:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début!"))
```

### 5. Maintenances
```python
class AssetMaintenance(models.Model):
    _name = 'e_gestock.asset_maintenance'
    _description = 'Maintenance d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    type = fields.Selection([
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('regulatory', 'Réglementaire')
    ], string='Type de maintenance', required=True, tracking=True)
    description = fields.Text(string='Description des travaux', tracking=True)
    prestataire_id = fields.Many2one('res.partner', string='Prestataire', domain=[('supplier_rank', '>', 0)], tracking=True)
    cout = fields.Monetary(string='Coût', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='État', default='planned', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    note = fields.Text(string='Notes')
    
    @api.model
    def create(self, vals):
        if vals.get('reference', 'Nouveau') == 'Nouveau':
            vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset_maintenance') or 'Nouveau'
        return super(AssetMaintenance, self).create(vals)
    
    @api.onchange('asset_id')
    def _onchange_asset(self):
        if self.asset_id and self.state in ['planned', 'in_progress']:
            self.asset_id.state = 'in_maintenance'
```

### 6. Documents liés
```python
class AssetDocument(models.Model):
    _name = 'e_gestock.asset_document'
    _description = 'Document d\'immobilisation'
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, ondelete='cascade')
    name = fields.Char(string='Nom', required=True)
    type = fields.Selection([
        ('invoice', 'Facture'),
        ('warranty', 'Garantie'),
        ('manual', 'Manuel'),
        ('certificate', 'Certificat'),
        ('other', 'Autre')
    ], string='Type de document', required=True)
    date_emission = fields.Date(string='Date d\'émission')
    date_expiration = fields.Date(string='Date d\'expiration')
    emetteur = fields.Char(string='Émetteur')
    attachment_id = fields.Many2one('ir.attachment', string='Pièce jointe')
    note = fields.Text(string='Notes')
    
    @api.constrains('date_emission', 'date_expiration')
    def _check_dates(self):
        for doc in self:
            if doc.date_expiration and doc.date_emission and doc.date_expiration < doc.date_emission:
                raise ValidationError(_("La date d'expiration doit être postérieure à la date d'émission!"))
```

## Structure du module

```
e_gestock_asset/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── asset.py
  │   ├── asset_type.py
  │   ├── asset_amortization_line.py
  │   ├── asset_assignment.py
  │   ├── asset_maintenance.py
  │   ├── asset_transfer.py
  │   ├── asset_disposal.py
  │   └── asset_document.py
  ├── views/
  │   ├── asset_views.xml
  │   ├── asset_type_views.xml
  │   ├── asset_assignment_views.xml
  │   ├── asset_maintenance_views.xml
  │   ├── asset_document_views.xml
  │   └── menu_views.xml
  ├── wizard/
  │   ├── __init__.py
  │   ├── asset_generate_amortization_wizard.py
  │   ├── asset_transfer_wizard.py
  │   └── asset_disposal_wizard.py
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_asset_security.xml
  ├── report/
  │   ├── asset_report.xml
  │   └── maintenance_report.xml
  └── data/
      ├── sequence_data.xml
      └── asset_type_data.xml
```

## Rapports et tableaux de bord

### 1. Rapports standards
- Fiche d'immobilisation détaillée
- Inventaire des immobilisations par type/structure
- Planning des maintenances
- Tableau d'amortissement
- État des garanties

### 2. Tableaux de bord
- Vue d'ensemble du parc d'immobilisations
- Répartition par type et par structure
- Coûts de maintenance par immobilisation/type
- Alertes sur les maintenances à prévoir
- Suivi des garanties par échéance

## Workflow des immobilisations

### 1. Cycle de vie d'une immobilisation
1. **Acquisition** - Création de l'immobilisation à la réception de l'achat
2. **Mise en service** - Passage à l'état 'en service' et début de l'amortissement
3. **Utilisation** - Affectation à un utilisateur ou une structure
4. **Maintenance** - Réalisation des opérations de maintenance périodiques
5. **Transfert** - Changement de structure ou de responsable
6. **Sortie** - Cession, mise au rebut ou autre sortie du patrimoine

### 2. Processus de maintenance
1. **Planification** - Création du plan de maintenance préventive
2. **Déclenchement** - Création automatique ou manuelle de l'intervention
3. **Réalisation** - Exécution des travaux de maintenance
4. **Clôture** - Enregistrement des coûts et commentaires
5. **Analyse** - Suivi des coûts et de l'efficacité des interventions

## Règles de sécurité

### 1. Accès aux immobilisations
- **Groupe Gestionnaire Immobilisations** : Création et gestion complète
- **Groupe Utilisateur Immobilisations** : Consultation limitée aux immobilisations qui lui sont affectées
- **Groupe Responsable Structure** : Consultation des immobilisations de sa structure
- **Groupe Direction** : Consultation globale et rapports

### 2. Accès aux maintenances
- **Groupe Gestionnaire Maintenances** : Création et gestion des interventions
- **Groupe Technicien Maintenance** : Exécution et suivi des interventions assignées 