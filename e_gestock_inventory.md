# Module de gestion des stocks (e_gestock_inventory)

## Description
Le module e_gestock_inventory est responsable de la gestion complète des stocks dans la solution E-GESTOCK pour Odoo 18 Community. Il permet le suivi des articles en stock, les mouvements de stock, les transferts et les inventaires physiques.

## Dépendances
- e_gestock_base
- e_gestock_purchase
- base
- product
- stock
- uom

## Fonctionnalités principales

### 1. Dépôts et articles en stock

#### 1.1 Extension du modèle e_gestock.depot
- Intégration avec les entrepôts et emplacements Odoo
- Champs de liaison avec `stock.warehouse` et `stock.location`
- Gestion des responsables de dépôt
- Configuration des règles de réapprovisionnement
- Paramètres de stockage (FIFO, LIFO, etc.)

#### 1.2 Articles en stock (e_gestock.stock_item)
- `depot_id` : Référence au dépôt
- `article_id` : Référence à l'article E-GESTOCK
- `quantite_disponible` : Quantité physiquement disponible
- `quantite_reservee` : Quantité réservée pour des sorties planifiées
- `quantite_virtuelle` : Quantité disponible moins quantité réservée
- `emplacement_id` : Référence à l'emplacement précis
- `last_inventory_date` : Date du dernier inventaire
- `value` : Valeur du stock (prix * quantité)
- Synchronisation bidirectionnelle avec les quants Odoo

### 2. Mouvements de stock

#### 2.1 Mouvements de stock (e_gestock.stock_movement)
- `reference` : Référence unique du mouvement (générée automatiquement)
- `type` : Type de mouvement (entrée, sortie, transfert, ajustement)
- `date` : Date du mouvement
- `depot_source_id` : Dépôt source (pour sorties et transferts)
- `depot_destination_id` : Dépôt destination (pour entrées et transferts)
- `responsable_id` : Responsable du mouvement
- `notes` : Notes explicatives
- `state` : État (brouillon, confirmé, terminé, annulé)
- `stock_picking_id` : Référence au picking Odoo généré
- `origine` : Document d'origine (bon de commande, demande, etc.)
- `origine_type` : Type d'origine (achat, demande interne, etc.)
- `reference_origine` : Numéro de référence du document d'origine
- `validateur_id` : Utilisateur validant le mouvement

#### 2.2 Lignes de mouvement (e_gestock.stock_movement_line)
- `movement_id` : Référence au mouvement parent
- `article_id` : Article concerné
- `quantite` : Quantité déplacée
- `uom_id` : Unité de mesure
- `prix_unitaire` : Prix unitaire
- `montant_total` : Montant total (prix * quantité)
- `stock_move_id` : Référence au mouvement Odoo généré
- `lot_id` : Lot ou numéro de série (si applicable)
- `date_peremption` : Date de péremption (si applicable)

#### 2.3 Workflow des mouvements
- Création en état "brouillon"
- Vérification de la disponibilité des articles (pour sorties et transferts)
- Confirmation avec génération des opérations Odoo correspondantes
- Traitement par le système de stock Odoo (stock.picking)
- Finalisation du mouvement avec mise à jour des quantités
- Possibilité d'annulation avec retour à l'état antérieur

### 3. Inventaires physiques

#### 3.1 Inventaires (e_gestock.inventory)
- `reference` : Référence unique de l'inventaire
- `date` : Date de l'inventaire
- `depot_id` : Dépôt concerné
- `responsable_id` : Responsable de l'inventaire
- `state` : État (brouillon, en cours, validé, annulé)
- `notes` : Notes sur l'inventaire
- `inventory_id` : Référence à l'inventaire Odoo

#### 3.2 Lignes d'inventaire (e_gestock.inventory_line)
- `inventory_id` : Référence à l'inventaire parent
- `article_id` : Article concerné
- `quantite_theorique` : Quantité théorique en stock
- `quantite_reelle` : Quantité comptée
- `ecart` : Différence entre quantité théorique et réelle
- `is_counted` : Indique si la ligne a été comptée
- `notes` : Notes sur la ligne

#### 3.3 Workflow des inventaires
- Création en état "brouillon"
- Génération automatique des lignes basée sur le stock théorique
- Passage à l'état "en cours" pour permettre le comptage
- Saisie des quantités réelles avec calcul automatique des écarts
- Validation avec contrôle que toutes les lignes ont été comptées
- Création automatique des mouvements d'ajustement
- Protection contre les inventaires simultanés sur un même dépôt

### 4. Intégration avec le circuit de validation d'achat

#### 4.1 Réceptions d'achat
- Intégration avec le workflow enrichi du module d'achat
- Support du circuit de validation complet (CMP, Budget, etc.)
- Gestion des mouvements de stock associés aux réceptions
- Mise à jour des niveaux de stock en fonction de l'état des commandes

#### 4.2 Vérification et traçabilité
- Contrôle de qualité lors des réceptions
- Traçabilité des articles par lot ou numéro de série
- Contrôle des articles conformes aux spécifications de la demande
- Historique complet des transactions

### 5. Rapports et analyses de stock

#### 5.1 État des stocks
- Vue d'ensemble des niveaux de stock par dépôt
- Filtrage par famille d'articles, article, dépôt
- Alertes sur les niveaux bas
- Analyse des rotations de stock

#### 5.2 Mouvements de stock
- Historique des mouvements par période
- Analyse des entrées et sorties
- Statistiques par dépôt et par article
- Suivi des transferts entre dépôts

#### 5.3 Valorisation des stocks
- Valorisation par dépôt et par famille d'articles
- Évolution de la valeur des stocks dans le temps
- Reporting pour la comptabilité

## Intégration avec Odoo

### 1. Entrepôts et emplacements
- Création automatique des entrepôts Odoo (`stock.warehouse`) pour chaque dépôt E-GESTOCK
- Génération des emplacements standards (stock, entrée, sortie)
- Association bidirectionnelle entre dépôts E-GESTOCK et entrepôts Odoo

### 2. Opérations de stock
- Utilisation du modèle `stock.picking` d'Odoo pour les transferts physiques
- Création automatique des `stock.move` pour chaque ligne de mouvement
- Synchronisation des états entre E-GESTOCK et Odoo
- Respect du workflow Odoo pour les opérations de stock

### 3. Inventaires
- Utilisation des fonctionnalités d'inventaire d'Odoo
- Création des inventaires Odoo (`stock.inventory`) depuis E-GESTOCK
- Ajustements automatiques via le mécanisme standard d'Odoo

## Modèles de données

### 1. Extension du modèle e_gestock.depot
```python
class Depot(models.Model):
    _inherit = 'e_gestock.depot'
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Entrepôt Odoo', ondelete='restrict')
    location_id = fields.Many2one('stock.location', string='Emplacement principal', ondelete='restrict')
    input_location_id = fields.Many2one('stock.location', string='Emplacement d\'entrée')
    output_location_id = fields.Many2one('stock.location', string='Emplacement de sortie')
    stock_rule_ids = fields.One2many('stock.rule', 'depot_id', string='Règles de stock')
    responsible_id = fields.Many2one('res.users', string='Responsable', 
                                   domain=[('groups_id', 'in', [lambda self: self.env.ref('e_gestock.group_e_gestock_resp_depot').id])])
    
    @api.model
    def create(self, vals):
        # Création automatique de l'entrepôt Odoo correspondant
        depot = super(Depot, self).create(vals)
        if not depot.warehouse_id:
            warehouse_vals = {
                'name': depot.designation,
                'code': depot.ref_depot,
                'partner_id': self.env.company.partner_id.id,
            }
            warehouse = self.env['stock.warehouse'].create(warehouse_vals)
            depot.write({
                'warehouse_id': warehouse.id,
                'location_id': warehouse.lot_stock_id.id,
                'input_location_id': warehouse.wh_input_stock_loc_id.id,
                'output_location_id': warehouse.wh_output_stock_loc_id.id
            })
        return depot
```

### 2. Articles en stock
```python
class StockItem(models.Model):
    _name = 'e_gestock.stock_item'
    _description = 'Article en stock'
    
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite_disponible = fields.Float(string='Quantité disponible', digits='Product Unit of Measure')
    quantite_reservee = fields.Float(string='Quantité réservée', digits='Product Unit of Measure')
    quantite_virtuelle = fields.Float(string='Quantité virtuelle', compute='_compute_virtual_quantity')
    emplacement_id = fields.Many2one('stock.location', string='Emplacement')
    last_inventory_date = fields.Datetime(string='Date du dernier inventaire')
    value = fields.Monetary(string='Valeur', compute='_compute_value', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    
    _sql_constraints = [
        ('article_depot_uniq', 'unique(article_id, depot_id)', 'Un article ne peut être présent qu\'une fois par dépôt!')
    ]
    
    @api.depends('quantite_disponible', 'quantite_reservee')
    def _compute_virtual_quantity(self):
        for record in self:
            record.quantite_virtuelle = record.quantite_disponible - record.quantite_reservee
    
    @api.model
    def get_stock_quantity(self, article_id, depot_id):
        """Méthode utilisée par d'autres modules pour vérifier la disponibilité"""
        stock_item = self.search([('article_id', '=', article_id), ('depot_id', '=', depot_id)], limit=1)
        if stock_item:
            return stock_item.quantite_disponible
        return 0.0
```

### 3. Mouvements de stock
```python
class StockMovement(models.Model):
    _name = 'e_gestock.stock_movement'
    _description = 'Mouvement de stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    type = fields.Selection([
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('transfer', 'Transfert'),
        ('adjustment', 'Ajustement')
    ], string='Type', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    depot_source_id = fields.Many2one('e_gestock.depot', string='Dépôt source', 
                                    domain="[('id', '!=', depot_destination_id)]")
    depot_destination_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', 
                                         domain="[('id', '!=', depot_source_id)]")
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    validateur_id = fields.Many2one('res.users', string='Validateur')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancel', 'Annulé')
    ], string='État', default='draft', tracking=True)
    line_ids = fields.One2many('e_gestock.stock_movement_line', 'movement_id', string='Lignes')
    stock_picking_id = fields.Many2one('stock.picking', string='Opération de stock Odoo')
    origine = fields.Selection([
        ('purchase', 'Achat'),
        ('internal', 'Demande interne'),
        ('return', 'Retour'),
        ('inventory', 'Inventaire'),
        ('other', 'Autre')
    ], string='Type d\'origine')
    reference_origine = fields.Char(string='Référence d\'origine')
    total_amount = fields.Monetary(string='Montant total', compute='_compute_total_amount')
    currency_id = fields.Many2one('res.currency', string='Devise')
    
    @api.constrains('type', 'depot_source_id', 'depot_destination_id')
    def _check_depots(self):
        for record in self:
            if record.type == 'in' and not record.depot_destination_id:
                raise ValidationError(_("Un dépôt de destination est requis pour une entrée de stock."))
            if record.type == 'out' and not record.depot_source_id:
                raise ValidationError(_("Un dépôt source est requis pour une sortie de stock."))
            if record.type == 'transfer' and (not record.depot_source_id or not record.depot_destination_id):
                raise ValidationError(_("Les dépôts source et destination sont requis pour un transfert."))
    
    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                continue
                
            # Vérifier la disponibilité des articles pour les sorties et transferts
            if record.type in ('out', 'transfer'):
                record._check_availability()
            
            # Créer l'opération de stock dans Odoo
            picking_type = record._get_picking_type()
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': record._get_source_location().id,
                'location_dest_id': record._get_destination_location().id,
                'origin': record.reference,
                'move_type': 'direct',
            }
            picking = self.env['stock.picking'].create(picking_vals)
            
            # Créer les mouvements de stock
            for line in record.line_ids:
                move_vals = {
                    'name': line.article_id.design_article,
                    'product_id': line.article_id.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantite,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                }
                move = self.env['stock.move'].create(move_vals)
                line.stock_move_id = move.id
            
            # Lier l'opération au mouvement
            record.stock_picking_id = picking.id
            
            # Confirmer l'opération
            picking.action_confirm()
            
            # Mettre à jour l'état
            record.state = 'confirmed'
```

### 4. Lignes de mouvement
```python
class StockMovementLine(models.Model):
    _name = 'e_gestock.stock_movement_line'
    _description = 'Ligne de mouvement de stock'
    
    movement_id = fields.Many2one('e_gestock.stock_movement', string='Mouvement', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.unite_id')
    prix_unitaire = fields.Float(string='Prix unitaire')
    montant_total = fields.Monetary(string='Montant total', compute='_compute_montant_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', related='movement_id.currency_id')
    stock_move_id = fields.Many2one('stock.move', string='Mouvement Odoo')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Numéro de série')
    date_peremption = fields.Date(string='Date de péremption')
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant_total(self):
        for line in self:
            line.montant_total = line.quantite * line.prix_unitaire
    
    @api.onchange('article_id')
    def _onchange_article_id(self):
        if self.article_id and self.movement_id.type in ('out', 'transfer'):
            # Récupérer le prix moyen de l'article dans le dépôt source
            stock_item = self.env['e_gestock.stock_item'].search([
                ('article_id', '=', self.article_id.id),
                ('depot_id', '=', self.movement_id.depot_source_id.id)
            ], limit=1)
            if stock_item and stock_item.quantite_disponible > 0 and stock_item.value > 0:
                self.prix_unitaire = stock_item.value / stock_item.quantite_disponible
```

### 5. Inventaires
```python
class Inventory(models.Model):
    _name = 'e_gestock.inventory'
    _description = 'Inventaire physique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('validated', 'Validé'),
        ('cancel', 'Annulé')
    ], string='État', default='draft', tracking=True)
    line_ids = fields.One2many('e_gestock.inventory_line', 'inventory_id', string='Lignes')
    inventory_id = fields.Many2one('stock.inventory', string='Inventaire Odoo')
    adjustment_movement_id = fields.Many2one('e_gestock.stock_movement', string='Mouvement d\'ajustement')
    
    def action_start(self):
        self.ensure_one()
        if self.state != 'draft':
            return
            
        # Vérifier qu'il n'y a pas d'autre inventaire en cours sur ce dépôt
        other_inventories = self.search([
            ('depot_id', '=', self.depot_id.id),
            ('state', 'in', ['in_progress']),
            ('id', '!=', self.id)
        ])
        if other_inventories:
            raise UserError(_("Il existe déjà un inventaire en cours pour ce dépôt."))
        
        # Générer les lignes d'inventaire
        self._generate_inventory_lines()
        
        # Créer l'inventaire Odoo
        inventory_vals = {
            'name': self.reference,
            'location_ids': [(4, self.depot_id.location_id.id)],
            'date': self.date,
        }
        inventory = self.env['stock.inventory'].create(inventory_vals)
        self.inventory_id = inventory.id
        
        # Passer à l'état "en cours"
        self.state = 'in_progress'
    
    def _generate_inventory_lines(self):
        self.ensure_one()
        # Supprimer les lignes existantes
        self.line_ids.unlink()
        
        # Récupérer les articles en stock dans ce dépôt
        stock_items = self.env['e_gestock.stock_item'].search([('depot_id', '=', self.depot_id.id)])
        
        # Créer une ligne pour chaque article
        for item in stock_items:
            self.env['e_gestock.inventory_line'].create({
                'inventory_id': self.id,
                'article_id': item.article_id.id,
                'quantite_theorique': item.quantite_disponible,
                'quantite_reelle': 0,
                'is_counted': False
            })
```

### 6. Lignes d'inventaire
```python
class InventoryLine(models.Model):
    _name = 'e_gestock.inventory_line'
    _description = 'Ligne d\'inventaire'
    
    inventory_id = fields.Many2one('e_gestock.inventory', string='Inventaire', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite_theorique = fields.Float(string='Quantité théorique', digits='Product Unit of Measure', readonly=True)
    quantite_reelle = fields.Float(string='Quantité réelle', digits='Product Unit of Measure')
    ecart = fields.Float(string='Écart', compute='_compute_ecart', store=True)
    is_counted = fields.Boolean(string='Compté', default=False)
    notes = fields.Text(string='Notes')
    
    @api.depends('quantite_theorique', 'quantite_reelle')
    def _compute_ecart(self):
        for line in self:
            line.ecart = line.quantite_reelle - line.quantite_theorique
    
    @api.onchange('quantite_reelle')
    def _onchange_quantite_reelle(self):
        if self.quantite_reelle != 0:
            self.is_counted = True
```

## Structure du module

```
e_gestock_inventory/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── depot.py
  │   ├── stock_item.py
  │   ├── stock_movement.py
  │   ├── stock_movement_line.py
  │   ├── inventory.py
  │   └── inventory_line.py
  ├── views/
  │   ├── depot_views.xml
  │   ├── stock_item_views.xml
  │   ├── stock_movement_views.xml
  │   ├── inventory_views.xml
  │   └── menu_views.xml
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_inventory_security.xml
  ├── data/
  │   └── sequence_data.xml
  ├── wizards/
  │   ├── __init__.py
  │   ├── stock_transfer_wizard.py
  │   └── inventory_import_wizard.py
  └── report/
      ├── inventory_report.xml
      └── stock_report.xml
```

## Vues principales

### 1. Vue des articles en stock
```xml
<record id="view_stock_item_tree" model="ir.ui.view">
    <field name="name">e_gestock.stock_item.tree</field>
    <field name="model">e_gestock.stock_item</field>
    <field name="arch" type="xml">
        <tree decoration-danger="quantite_disponible &lt;= 0" decoration-warning="quantite_virtuelle &lt;= 0">
            <field name="depot_id"/>
            <field name="article_id"/>
            <field name="quantite_disponible"/>
            <field name="quantite_reservee"/>
            <field name="quantite_virtuelle"/>
            <field name="value" sum="Total"/>
            <field name="currency_id" invisible="1"/>
            <field name="last_inventory_date"/>
        </tree>
    </field>
</record>
```

### 2. Vue des mouvements de stock
```xml
<record id="view_stock_movement_form" model="ir.ui.view">
    <field name="name">e_gestock.stock_movement.form</field>
    <field name="model">e_gestock.stock_movement</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_confirm" string="Confirmer" type="object" 
                        class="oe_highlight" states="draft"/>
                <button name="action_validate" string="Valider" type="object" 
                        class="oe_highlight" states="confirmed"/>
                <button name="action_cancel" string="Annuler" type="object" states="draft,confirmed"/>
                <field name="state" widget="statusbar" statusbar_visible="draft,confirmed,done"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="type" widget="radio" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="date"/>
                        <field name="depot_source_id" attrs="{
                            'readonly': [('state', '!=', 'draft')],
                            'invisible': [('type', '=', 'in')],
                            'required': [('type', 'in', ['out', 'transfer'])]}"/>
                        <field name="depot_destination_id" attrs="{
                            'readonly': [('state', '!=', 'draft')],
                            'invisible': [('type', '=', 'out')],
                            'required': [('type', 'in', ['in', 'transfer'])]}"/>
                    </group>
                    <group>
                        <field name="responsable_id"/>
                        <field name="validateur_id" readonly="1" attrs="{'invisible': [('validateur_id', '=', False)]}"/>
                        <field name="origine" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="reference_origine" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="total_amount" readonly="1"/>
                        <field name="currency_id" invisible="1"/>
                    </group>
                </group>
                <notebook>
                    <page string="Lignes" name="lines">
                        <field name="line_ids" attrs="{'readonly': [('state', '!=', 'draft')]}">
                            <tree editable="bottom">
                                <field name="article_id" required="1"/>
                                <field name="quantite" required="1"/>
                                <field name="uom_id" readonly="1"/>
                                <field name="prix_unitaire"/>
                                <field name="montant_total" sum="Total"/>
                                <field name="currency_id" invisible="1"/>
                                <field name="lot_id" attrs="{'column_invisible': [('parent.type', '=', 'out')]}"/>
                                <field name="date_peremption" attrs="{'column_invisible': [('parent.type', '=', 'out')]}"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Notes" name="notes">
                        <field name="notes" placeholder="Ajouter des notes..."/>
                    </page>
                </notebook>
            </sheet>
            <div class="oe_chatter">
                <field name="message_follower_ids"/>
                <field name="activity_ids"/>
                <field name="message_ids"/>
            </div>
        </form>
    </field>
</record>
```

## Intégration avec les autres modules

### 1. Intégration avec le module e_gestock_purchase
- Réception automatique des articles achetés
- Mise à jour des niveaux de stock en fonction des achats
- Vérification des disponibilités pour les demandes d'achat de type transfert

### 2. Intégration avec le module e_gestock_base
- Association entre les articles E-GESTOCK et les produits Odoo
- Utilisation des structures organisationnelles pour la gestion des dépôts

### 3. Intégration avec le module e_gestock_reception
- Création des mouvements de stock lors des réceptions
- Suivi des livraisons partielles
- Gestion des non-conformités 