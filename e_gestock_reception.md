# Module de gestion des réceptions (e_gestock_reception)

## Description
Le module e_gestock_reception gère le processus de réception des articles commandés dans la solution E-GESTOCK pour Odoo 18 Community. Il assure la traçabilité des livraisons, le contrôle de conformité des articles et la mise à jour des stocks.

## Dépendances
- e_gestock_base
- e_gestock_inventory
- e_gestock_purchase
- base
- mail
- product
- purchase
- stock

## Fonctionnalités principales

### 1. Réceptions des commandes

#### 1.1 Réceptions (e_gestock.reception)
- `reference` : Référence unique de la réception (numérotation automatique)
- `date` : Date de réception
- `demande_id` : Référence à la demande d'achat
- `purchase_order_id` : Référence au bon de commande Odoo
- `depot_id` : Dépôt de destination
- `responsable_id` : Responsable de la réception
- `fournisseur_id` : Fournisseur
- `bl_number` : Numéro du bon de livraison fournisseur
- `bl_date` : Date du bon de livraison fournisseur
- `state` : État de la réception (brouillon, confirmé, terminé, annulé)
- `notes` : Notes et commentaires
- `stock_picking_id` : Référence à l'opération de stock Odoo (réception)
- `is_partial` : Indique si c'est une livraison partielle

#### 1.2 Lignes de réception (e_gestock.reception_line)
- `reception_id` : Référence à la réception
- `purchase_line_id` : Référence à la ligne de commande d'achat
- `article_id` : Article concerné
- `designation` : Désignation (pour articles non stockables)
- `quantite_commandee` : Quantité commandée
- `quantite_deja_reçue` : Quantité déjà reçue dans des réceptions précédentes
- `quantite_reçue` : Quantité reçue dans cette livraison
- `quantite_restante` : Quantité restant à recevoir
- `est_conforme` : Indicateur de conformité
- `notes` : Notes sur la conformité ou anomalies
- `stock_move_id` : Référence au mouvement de stock Odoo
- `uom_id` : Unité de mesure

### 2. Contrôle qualité et conformité

#### 2.1 Contrôles de conformité
- Marquage des articles comme conformes/non conformes lors de la réception
- Gestion des anomalies (qualité, quantité, référence)
- Traçabilité des contrôles effectués
- Possibilité de refuser des articles non conformes

#### 2.2 Comités de réception
- Gestion des membres du comité de réception
- Attribution des rôles (président, secrétaire, membres)
- Planification des sessions de réception
- Procès-verbal de réception avec signatures électroniques
- Validation des livraisons par le comité avec quorum requis
- Suivi des actions correctives demandées aux fournisseurs

### 3. Mouvements de stock 

#### 3.1 Création automatique des mouvements de stock
- Génération automatique des mouvements d'entrée en stock
- Mise à jour des quantités disponibles
- Intégration avec le module e_gestock_inventory

#### 3.2 Mise à jour des demandes d'achat
- Passage de la demande d'achat à l'état 'delivered' si toutes les quantités sont reçues
- Gestion des livraisons partielles avec suivi des quantités restant à recevoir
- Historique des réceptions par demande d'achat

### 4. Suivi des fournisseurs

#### 4.1 Évaluation des livraisons
- Suivi des délais de livraison
- Évaluation de la qualité des articles livrés
- Analyse des écarts entre commande et livraison
- Historique des réceptions par fournisseur

#### 4.2 Intégration avec les contrats fournisseurs
- Vérification du respect des conditions contractuelles
- Alerte en cas de non-respect des engagements
- Impact sur la notation du fournisseur

### 5. Intégration au circuit de validation des achats

#### 5.1 Alignement avec le workflow complet
- Adaptation au workflow enrichi du module d'achat (e_gestock_purchase)
- Support du circuit de validation complet incluant CMP, Budget, DCG, DGAAF, DG
- Intégration avec les décisions des comités (CMP, etc.)

#### 5.2 Support des rôles élargis
- Intégration avec le rôle du Comité de réception défini dans le circuit d'achat
- Validation finale de la réception par les membres du comité
- Confirmation de conformité aux spécifications de la commande
- Gestion des réserves et des non-conformités

## Modèles de données

### 1. Réceptions
```python
class Reception(models.Model):
    _name = 'e_gestock.reception'
    _description = 'Réception de commande'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation')
    purchase_order_id = fields.Many2one('purchase.order', string='Bon de commande', required=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', related='purchase_order_id.partner_id', store=True)
    bl_number = fields.Char(string='N° Bon de livraison fournisseur')
    bl_date = fields.Date(string='Date BL fournisseur')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('comite_validation', 'En attente validation comité'),
        ('done', 'Terminée'),
        ('cancel', 'Annulée')
    ], string='État', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('e_gestock.reception_line', 'reception_id', string='Lignes')
    stock_picking_id = fields.Many2one('stock.picking', string='Réception Odoo')
    is_partial = fields.Boolean(string='Livraison partielle', compute='_compute_is_partial', store=True)
    comite_reception_id = fields.Many2one('e_gestock.comite_reception', string='Comité de réception')
    pv_validation = fields.Boolean(string='PV validé', default=False)
    
    @api.onchange('purchase_order_id')
    def _onchange_purchase_order(self):
        if self.purchase_order_id:
            # Récupération de la demande d'achat liée
            demande = self.env['e_gestock.demande_cotation'].search([
                ('purchase_order_id', '=', self.purchase_order_id.id)
            ], limit=1)
            if demande:
                self.demande_id = demande.id
            
            # Génération des lignes de réception
            lines = []
            for po_line in self.purchase_order_id.order_line:
                # Calcul des quantités déjà reçues
                already_received = self._get_already_received_qty(po_line)
                
                # Création de la ligne de réception
                line_vals = {
                    'purchase_line_id': po_line.id,
                    'article_id': self._find_article_from_product(po_line.product_id),
                    'designation': po_line.name,
                    'quantite_commandee': po_line.product_qty,
                    'quantite_deja_reçue': already_received,
                    'quantite_reçue': po_line.product_qty - already_received,
                    'quantite_restante': 0,
                    'uom_id': po_line.product_uom.id,
                }
                lines.append((0, 0, line_vals))
            
            self.line_ids = lines
    
    def action_confirm(self):
        self.ensure_one()
        self.state = 'confirmed'
        
    def action_submit_comite(self):
        self.ensure_one()
        if not self.comite_reception_id:
            raise UserError(_("Veuillez sélectionner un comité de réception avant de soumettre."))
        self.state = 'comite_validation'
        
    def action_done(self):
        self.ensure_one()
        self.state = 'done'
        # Mettre à jour l'état de la demande
        if self.demande_id:
            self.demande_id.write({'state': 'received'})
```

### 2. Lignes de réception
```python
class ReceptionLine(models.Model):
    _name = 'e_gestock.reception_line'
    _description = 'Ligne de réception'
    
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, ondelete='cascade')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Ligne de commande')
    article_id = fields.Many2one('e_gestock.article', string='Article')
    designation = fields.Char(string='Désignation')
    quantite_commandee = fields.Float(string='Quantité commandée', digits='Product Unit of Measure')
    quantite_deja_reçue = fields.Float(string='Quantité déjà reçue', digits='Product Unit of Measure')
    quantite_reçue = fields.Float(string='Quantité reçue', digits='Product Unit of Measure')
    quantite_restante = fields.Float(string='Quantité restante', compute='_compute_quantite_restante', store=True)
    est_conforme = fields.Selection([
        ('oui', 'Conforme'),
        ('non', 'Non conforme'),
        ('partiel', 'Partiellement conforme')
    ], string='Conformité', default='oui')
    notes = fields.Text(string='Notes')
    stock_move_id = fields.Many2one('stock.move', string='Mouvement de stock')
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure')
    
    @api.depends('quantite_commandee', 'quantite_deja_reçue', 'quantite_reçue')
    def _compute_quantite_restante(self):
        for line in self:
            line.quantite_restante = line.quantite_commandee - line.quantite_deja_reçue - line.quantite_reçue
```

### 3. Comités de réception
```python
class ComiteReception(models.Model):
    _name = 'e_gestock.comite_reception'
    _description = 'Comité de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nom', required=True)
    president_id = fields.Many2one('res.users', string='Président', required=True, 
                                  domain=[('groups_id', 'in', [lambda self: self.env.ref('e_gestock.group_reception_manager').id])])
    secretaire_id = fields.Many2one('res.users', string='Secrétaire')
    membre_ids = fields.Many2many('res.users', string='Membres')
    active = fields.Boolean(string='Actif', default=True)
    quorum = fields.Integer(string='Quorum requis', default=3)
    reception_ids = fields.One2many('e_gestock.reception', 'comite_reception_id', string='Réceptions')
    structure_id = fields.Many2one('e_gestock.structure', string='Structure')
    notes = fields.Text(string='Notes')
    
    def action_review_receptions(self):
        self.ensure_one()
        action = {
            'name': _('Réceptions à valider'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception',
            'domain': [('comite_reception_id', '=', self.id), ('state', '=', 'comite_validation')],
            'view_mode': 'tree,form',
            'context': {'default_comite_reception_id': self.id}
        }
        return action
```

### 4. Procès-verbaux de réception
```python
class PVReception(models.Model):
    _name = 'e_gestock.pv_reception'
    _description = 'Procès-verbal de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True)
    comite_id = fields.Many2one('e_gestock.comite_reception', string='Comité', related='reception_id.comite_reception_id')
    president_signature = fields.Boolean(string='Signature président', default=False)
    secretaire_signature = fields.Boolean(string='Signature secrétaire', default=False)
    membre_signature_ids = fields.One2many('e_gestock.pv_signature', 'pv_id', string='Signatures membres')
    quorum_atteint = fields.Boolean(string='Quorum atteint', compute='_compute_quorum_atteint')
    observation = fields.Text(string='Observations')
    decision = fields.Selection([
        ('accepted', 'Accepté'),
        ('accepted_reserve', 'Accepté avec réserves'),
        ('rejected', 'Rejeté')
    ], string='Décision', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft')
    reserve_ids = fields.One2many('e_gestock.pv_reserve', 'pv_id', string='Réserves')
    
    @api.depends('president_signature', 'secretaire_signature', 'membre_signature_ids.signed')
    def _compute_quorum_atteint(self):
        for pv in self:
            signatures_count = (pv.president_signature and 1 or 0) + (pv.secretaire_signature and 1 or 0) + len(pv.membre_signature_ids.filtered('signed'))
            pv.quorum_atteint = signatures_count >= pv.comite_id.quorum
    
    def action_validate(self):
        self.ensure_one()
        if not self.quorum_atteint:
            raise UserError(_("Le quorum n'est pas atteint. Impossible de valider le PV."))
        
        self.state = 'validated'
        self.reception_id.pv_validation = True
        
        # Terminer la réception selon la décision
        if self.decision in ['accepted', 'accepted_reserve']:
            self.reception_id.action_done()
```

### 5. Signatures de PV
```python
class PVSignature(models.Model):
    _name = 'e_gestock.pv_signature'
    _description = 'Signature du PV de réception'
    
    pv_id = fields.Many2one('e_gestock.pv_reception', string='PV', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Membre', required=True)
    signed = fields.Boolean(string='Signé', default=False)
    date_signature = fields.Datetime(string='Date signature')
    
    @api.constrains('user_id')
    def _check_membre_comite(self):
        for signature in self:
            if signature.user_id not in signature.pv_id.comite_id.membre_ids:
                raise ValidationError(_("L'utilisateur doit être membre du comité de réception."))
```

### 6. Réserves sur PV
```python
class PVReserve(models.Model):
    _name = 'e_gestock.pv_reserve'
    _description = 'Réserve sur PV de réception'
    
    pv_id = fields.Many2one('e_gestock.pv_reception', string='PV', required=True, ondelete='cascade')
    line_id = fields.Many2one('e_gestock.reception_line', string='Ligne concernée')
    description = fields.Text(string='Description', required=True)
    action_corrective = fields.Text(string='Action corrective')
    date_echeance = fields.Date(string='Date d\'échéance')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    state = fields.Selection([
        ('open', 'Ouverte'),
        ('closed', 'Résolue')
    ], string='État', default='open')
```

## Structure du module

```
e_gestock_reception/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── reception.py
  │   ├── reception_line.py
  │   ├── comite_reception.py
  │   ├── pv_reception.py
  │   ├── pv_signature.py
  │   └── pv_reserve.py
  ├── views/
  │   ├── reception_views.xml
  │   ├── comite_reception_views.xml
  │   ├── pv_reception_views.xml
  │   └── menu_views.xml
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_reception_security.xml
  ├── data/
  │   └── sequence_data.xml
  ├── wizards/
  │   ├── __init__.py
  │   └── create_pv_wizard.py
  └── report/
      ├── reception_report.xml
      └── pv_report.xml
```

## Vues principales

### 1. Vue du formulaire de réception
```xml
<record id="view_reception_form" model="ir.ui.view">
    <field name="name">e_gestock.reception.form</field>
    <field name="model">e_gestock.reception</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_confirm" string="Confirmer" type="object" 
                        class="oe_highlight" states="draft"/>
                <button name="action_submit_comite" string="Soumettre au comité" type="object" 
                        class="oe_highlight" states="confirmed"/>
                <button name="action_done" string="Terminer" type="object" groups="e_gestock.group_reception_manager"
                        class="oe_highlight" states="comite_validation" 
                        attrs="{'invisible': [('pv_validation', '=', False)]}"/>
                <button name="action_cancel" string="Annuler" type="object" states="draft,confirmed"/>
                <field name="state" widget="statusbar" 
                       statusbar_visible="draft,confirmed,comite_validation,done"/>
            </header>
            <sheet>
                <div class="oe_button_box" name="button_box">
                    <button name="action_view_pv" type="object" class="oe_stat_button" icon="fa-file-text"
                            attrs="{'invisible': [('state', 'not in', ['comite_validation', 'done'])]}">
                        <field name="pv_count" string="PV" widget="statinfo"/>
                    </button>
                </div>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="date"/>
                        <field name="purchase_order_id" domain="[('state_approbation', '=', 'dg_validated')]" 
                               options="{'no_create': True}" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="demande_id" readonly="1"/>
                        <field name="fournisseur_id" readonly="1"/>
                    </group>
                    <group>
                        <field name="depot_id" options="{'no_create': True}" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="responsable_id"/>
                        <field name="bl_number"/>
                        <field name="bl_date"/>
                        <field name="comite_reception_id" attrs="{'required': [('state', '=', 'confirmed')], 'readonly': [('state', 'not in', ['draft', 'confirmed'])]}"/>
                        <field name="pv_validation" readonly="1"/>
                    </group>
                </group>
                <notebook>
                    <page string="Lignes de réception">
                        <field name="line_ids" attrs="{'readonly': [('state', 'in', ['done', 'cancel'])]}">
                            <tree editable="bottom">
                                <field name="article_id" readonly="1"/>
                                <field name="designation" readonly="1"/>
                                <field name="quantite_commandee" readonly="1"/>
                                <field name="quantite_deja_reçue" readonly="1"/>
                                <field name="quantite_reçue"/>
                                <field name="quantite_restante" readonly="1"/>
                                <field name="uom_id" readonly="1"/>
                                <field name="est_conforme"/>
                                <field name="notes"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Notes">
                        <field name="notes" placeholder="Ajouter des notes sur la réception..."/>
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

### 2. Vue du formulaire de PV de réception
```xml
<record id="view_pv_reception_form" model="ir.ui.view">
    <field name="name">e_gestock.pv_reception.form</field>
    <field name="model">e_gestock.pv_reception</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_validate" string="Valider" type="object" 
                        class="oe_highlight" states="draft"
                        attrs="{'invisible': [('quorum_atteint', '=', False)]}"/>
                <button name="action_cancel" string="Annuler" type="object" states="draft"/>
                <field name="state" widget="statusbar"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="date"/>
                        <field name="reception_id" domain="[('state', '=', 'comite_validation'), ('pv_validation', '=', False)]" 
                               options="{'no_create': True}" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="comite_id" readonly="1"/>
                    </group>
                    <group>
                        <field name="decision" required="1" attrs="{'readonly': [('state', '!=', 'draft')]}"/>
                        <field name="quorum_atteint" readonly="1"/>
                    </group>
                </group>
                <notebook>
                    <page string="Signatures">
                        <group>
                            <field name="president_signature" attrs="{'readonly': [('state', '!=', 'draft')]}" 
                                   widget="boolean_toggle"/>
                            <field name="secretaire_signature" attrs="{'readonly': [('state', '!=', 'draft')]}" 
                                   widget="boolean_toggle"/>
                        </group>
                        <field name="membre_signature_ids" attrs="{'readonly': [('state', '!=', 'draft')]}">
                            <tree editable="bottom">
                                <field name="user_id" domain="[('id', 'in', parent.comite_id.membre_ids)]"/>
                                <field name="signed" widget="boolean_toggle"/>
                                <field name="date_signature" readonly="1"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Réserves" attrs="{'invisible': [('decision', '!=', 'accepted_reserve')]}">
                        <field name="reserve_ids" attrs="{'readonly': [('state', '!=', 'draft')]}">
                            <tree editable="bottom">
                                <field name="line_id" domain="[('reception_id', '=', parent.reception_id)]"/>
                                <field name="description"/>
                                <field name="action_corrective"/>
                                <field name="date_echeance"/>
                                <field name="responsable_id"/>
                                <field name="state" widget="badge" 
                                       decoration-success="state == 'closed'" 
                                       decoration-danger="state == 'open'"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Observations">
                        <field name="observation" placeholder="Ajouter des observations générales..." 
                               attrs="{'readonly': [('state', '!=', 'draft')]}"/>
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

### 1. Intégration avec e_gestock_purchase
- Continuité du circuit de validation depuis le module d'achat
- Respect du workflow enrichi pour les validations 
- Génération des réceptions à partir des commandes validées
- Mise à jour du statut des demandes d'achat et bons de commande

### 2. Intégration avec e_gestock_inventory
- Création automatique des mouvements de stock
- Mise à jour des niveaux de stock après réception
- Traçabilité complète des articles reçus

### 3. Intégration avec e_gestock_supplier
- Impact des évaluations de réception sur la notation des fournisseurs
- Remontée des non-conformités dans l'historique du fournisseur
- Notification des fournisseurs en cas de réception avec réserves

### 4. Rapports
- Rapport détaillé de réception
- Procès-verbal de réception avec signatures
- Tableau de bord des réceptions en cours et validées
- Suivi des réserves et non-conformités 