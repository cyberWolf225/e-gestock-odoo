# Module de gestion des achats et cotations (e_gestock_purchase)

## Description
Le module e_gestock_purchase gère l'ensemble du processus d'achat dans la solution E-GESTOCK pour Odoo 18 Community, depuis la demande initiale jusqu'à la génération des bons de commande, en passant par le processus de cotation des fournisseurs.

## Dépendances
- e_gestock_base
- e_gestock_budget
- e_gestock_supplier
- base
- mail
- product
- purchase

## Fonctionnalités principales

### 1. Demandes de cotation et achats

#### 1.1 Demandes de cotation (e_gestock.demande_cotation)
- `reference` : Référence unique (format: Année/Structure/DC/Séquence)
- `date` : Date de création
- `demandeur_id` : Utilisateur demandeur
- `exercice_id` : Exercice budgétaire (ex: 2025)
- `structure_id` : Structure concernée (ex: 9101 - CONSEIL D'ADMINISTRATION)
- `compte_budg_id` : Compte budgétaire (famille d'articles, ex: 632510)
- `designation_compte` : Désignation du compte budgétaire (calculé depuis famille)
- `gestion_id` : Type de gestion (ex: G)
- `designation_gestion` : Désignation de la gestion (ex: Administration)
- `intitule` : Intitulé de la demande
- `is_stockable` : Indique si les articles sont stockables (case à cocher)
- `solde_disponible` : Solde budgétaire disponible (calculé)
- `montant_total` : Montant total de la demande
- `note` : Note explicative
- `state` : État de la demande (workflow complet)
- `urgence_signalee` : Indique si la demande est urgente
- `memo_motivation` : Mémo de motivation (pièce jointe)

#### 1.2 Lignes de demande de cotation (e_gestock.demande_cotation_line)
- `demande_id` : Référence à la demande de cotation
- `article_id` : Article (pour demandes stockables)
- `ref_article` : Référence de l'article (relié à article_id)
- `designation` : Désignation de l'article
- `description` : Description détaillée
- `quantite` : Quantité demandée
- `quantite_accordee` : Quantité accordée par le responsable des achats
- `unite_id` : Unité de mesure
- `echantillon` : Fichier d'échantillon (pièce jointe)
- `is_selected` : Indique si la ligne est sélectionnée pour validation

#### 1.3 Demandes de cotation aux fournisseurs (e_gestock.demande_cotation_fournisseur)
- `demande_id` : Référence à la demande de cotation
- `supplier_id` : Fournisseur concerné
- `date_envoi` : Date d'envoi
- `date_echeance` : Date d'échéance
- `code_echeance` : Code d'échéance
- `state` : État de la demande (envoyée, reçue, etc.)
- `type_achat` : Type d'achat
- `taux_acompte` : Taux d'acompte

### 2. Processus de cotation

#### 2.1 Cotations fournisseurs (e_gestock.cotation)
- `reference` : Référence unique
- `demande_id` : Référence à la demande de cotation
- `supplier_id` : Fournisseur concerné
- `date` : Date de la cotation
- `date_expiration` : Date d'expiration de l'offre
- `montant_total` : Montant total de la cotation
- `state` : État de la cotation
- `is_best_offer` : Indique si c'est la meilleure offre
- `purchase_order_id` : Référence au bon de commande généré
- `delai_livraison` : Délai de livraison proposé (en jours)
- `conditions_paiement` : Conditions de paiement
- `currency_id` : Devise utilisée 
- `remise_generale` : Remise générale appliquée
- `tva` : Taux de TVA applicable
- `bl_attachment` : Pièce jointe du bon de livraison
- `date_livraison` : Date de livraison prévue ou réalisée

#### 2.2 Lignes de cotation (e_gestock.cotation_line)
- `cotation_id` : Référence à la cotation
- `demande_line_id` : Référence à la ligne de demande de cotation
- `article_id` : Article
- `ref_article` : Référence de l'article
- `designation` : Désignation
- `description` : Description
- `quantite` : Quantité
- `quantite_a_servir` : Quantité proposée par le fournisseur
- `unite_id` : Unité de mesure
- `prix_unitaire` : Prix unitaire proposé
- `montant` : Montant total de la ligne
- `remise_ligne` : Remise appliquée à la ligne
- `echantillon` : Fichier d'échantillon proposé par le fournisseur

### 3. Gestion des bons de commande

#### 3.1 Bons de commande (extension de purchase.order)
- `demande_cotation_id` : Référence à la demande de cotation d'origine
- `cotation_id` : Référence à la cotation sélectionnée
- `state_approbation` : État d'approbation (workflow complet)
- `signataire_ids` : Signataires sélectionnés
- `commentaires_validation` : Commentaires des différents validateurs
- `date_retrait` : Date de retrait par le fournisseur
- `date_livraison_prevue` : Date de livraison prévue
- `date_livraison_reelle` : Date de livraison réelle
- `comite_reception_id` : Comité de réception assigné

### 4. Contrôle budgétaire

#### 4.1 Vérification des fonds disponibles
- Contrôle automatique du solde disponible dans le budget
- Affichage du solde disponible dans le formulaire de demande
- Blocage des demandes en cas de fonds insuffisants avec message "Oups! pas de budget disponible"
- Alertes sur seuils de consommation

## Rôles et responsabilités

### 1. Gestionnaire des achats
Responsable de l'initiation des demandes d'achat et de leur suivi initial.
- Création des demandes d'achat
- Modification des demandes à l'état brouillon
- Transfert des demandes au responsable des achats
- Consultation de l'état des demandes

### 2. Responsable des achats
Supervise les demandes d'achat et gère le processus de cotation.
- Validation des demandes d'achat
- Ajustement des quantités accordées
- Création des demandes de cotation
- Sélection des fournisseurs pour les demandes de cotation
- Analyse des cotations reçues
- Sélection du fournisseur mieux-disant
- Édition des bons de commande

### 3. Fournisseur
Intervient pour répondre aux demandes de cotation et assurer la livraison.
- Réception des demandes de cotation
- Soumission des offres de prix
- Retrait des bons de commande
- Livraison des commandes
- Suivi de l'état des commandes

### 4. Responsable CMP
Supervise le processus de passation des marchés.
- Validation des demandes de cotation
- Validation du choix du fournisseur mieux-disant
- Transfert des demandes de cotation aux fournisseurs

### 5. Responsable contrôle budgétaire
Assure la conformité budgétaire des acquisitions.
- Contrôle des disponibilités budgétaires
- Visa des bons de commande

### 6. Chef Département DCG
Intervient dans le circuit de validation.
- Visa des bons de commande
- Transfert au Responsable DCG

### 7. Responsable DCG
Validation financière des bons de commande.
- Visa des bons de commande
- Transfert à la Direction Générale

### 8. DGAAF
Validation des bons de commande de montants inférieurs au seuil défini.
- Validation finale des bons de commande de son ressort
- Retour possible au Responsable DCG en cas de rejet

### 9. DG
Validation des bons de commande de montants importants.
- Validation finale des bons de commande de son ressort
- Retour possible au Responsable CMP en cas de rejet

### 10. Comité de réception
Responsable de la réception des livraisons.
- Validation des livraisons
- Contrôle de conformité des articles livrés
- Saisie des quantités réceptionnées

## Processus détaillé et workflow

### 1. Création et validation des demandes d'achat
1. **Création par le Gestionnaire des achats**
   - Saisie des informations de base (compte budgétaire, structure, gestion)
   - Saisie de l'intitulé et des articles
   - Possibilité de joindre un mémo de motivation
   - Ajout d'articles avec le bouton (+)

2. **Transfert au Responsable des achats**
   - Le Gestionnaire utilise le bouton de transfert
   - La demande passe à l'état "submitted"

3. **Validation par le Responsable des achats**
   - Sélection des lignes à valider (case à cocher)
   - Saisie des quantités accordées
   - Validation avec commentaire possible
   - La demande passe à l'état "validated"

### 2. Processus de cotation
1. **Création de la demande de cotation**
   - Le Responsable des achats sélectionne le code et délai d'échéance
   - Définition du type d'achat et taux d'acompte
   - Présélection des fournisseurs

2. **Validation par le Responsable CMP**
   - Transfert de la demande de cotation au Responsable CMP
   - Validation pour envoi aux fournisseurs
   - La demande passe à l'état "quotation"

3. **Envoi aux fournisseurs**
   - Le Responsable des achats transfère la demande aux fournisseurs sélectionnés
   - Les fournisseurs reçoivent une notification

4. **Réponse des fournisseurs**
   - Saisie de la devise
   - Saisie des quantités à servir et prix unitaires
   - Application de remises par ligne et générale
   - Saisie du taux de TVA
   - Possibilité de joindre un échantillon
   - Soumission de l'offre

5. **Sélection du mieux-disant**
   - Le Responsable des achats analyse les cotations reçues
   - Sélection de la meilleure offre
   - La demande passe à l'état "quoted" puis "selected"

6. **Validation par le Responsable CMP**
   - Transfert de la sélection au Responsable CMP
   - Validation du choix du fournisseur

### 3. Circuit de validation du bon de commande
1. **Contrôle budgétaire**
   - Le Responsable contrôle budgétaire vérifie la disponibilité
   - Visa avec commentaire possible
   - En cas de rejet, retour au Responsable CMP

2. **Validation Chef Département DCG**
   - Visa avec commentaire possible
   - En cas de rejet, retour au contrôle budgétaire

3. **Validation Responsable DCG**
   - Visa avec commentaire possible
   - En cas de rejet, retour au Chef Département DCG

4. **Validation finale**
   - Si montant < seuil défini: validation par DGAAF
   - Si montant ≥ seuil défini: validation par DG
   - Commentaire possible
   - En cas de rejet, retour au niveau précédent

### 4. Exécution de la commande
1. **Édition du bon de commande**
   - Le Responsable des achats édite le bon de commande
   - Sélection des signataires
   - La demande passe à l'état "po_generated"

2. **Retrait par le fournisseur**
   - Le fournisseur marque le retrait
   - Saisie de la date de livraison prévue

3. **Livraison**
   - Le fournisseur effectue la livraison
   - Téléchargement du bon de livraison
   - Passage à l'état "delivered"

4. **Validation par le comité de réception**
   - Contrôle de conformité
   - Saisie des quantités réellement réceptionnées
   - Confirmation de la réception
   - Finalisation du processus d'achat

## États du workflow

### 1. États des demandes de cotation
- `draft` : Brouillon
- `submitted` : Soumise au Responsable des achats
- `validated` : Validée par le Responsable des achats
- `budget_checked` : Budget vérifié
- `approved` : Approuvée
- `engaged` : Engagée
- `quotation` : En attente de cotation
- `quoted` : Cotations reçues
- `selected` : Fournisseur sélectionné
- `po_generated` : Bon de commande généré
- `delivered` : Livrée
- `received` : Réceptionnée
- `cancelled` : Annulée

### 2. États des cotations
- `draft` : Brouillon
- `sent` : Envoyée au fournisseur
- `submitted` : Soumise par le fournisseur
- `confirmed` : Confirmée
- `selected` : Sélectionnée comme meilleure offre
- `rejected` : Rejetée
- `po_generated` : Bon de commande généré

### 3. États d'approbation des bons de commande
- `draft` : Brouillon
- `cmp_validated` : Validé par CMP
- `budget_validated` : Validé par contrôle budgétaire
- `dcg_dept_validated` : Validé par Chef Département DCG
- `dcg_validated` : Validé par Responsable DCG
- `dgaaf_validated` : Validé par DGAAF
- `dg_validated` : Validé par DG
- `approved` : Approuvé
- `withdrawn` : Retiré par le fournisseur
- `delivered` : Livré
- `received` : Réceptionné
- `cancelled` : Annulé

## Modèles de données

### 1. Demandes de cotation
```python
class DemandeCotation(models.Model):
    _name = 'e_gestock.demande_cotation'
    _description = 'Demande de cotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='N° Demande', required=True, readonly=True, default='Nouveau', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    demandeur_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user, required=True)
    exercice_id = fields.Many2one('e_gestock.exercice', string='Exercice', required=True, tracking=True)
    
    # Structure et budget
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    compte_budg_id = fields.Many2one('e_gestock.famille', string='Compte budg.', required=True, tracking=True)
    designation_compte = fields.Char(related='compte_budg_id.design_fam', string='Désignation compte', readonly=True)
    gestion_id = fields.Many2one('e_gestock.type_gestion', string='Gestion', required=True, tracking=True)
    designation_gestion = fields.Char(related='gestion_id.designation', string='Désignation gestion', readonly=True)
    
    # Caractéristiques de la demande
    intitule = fields.Char(string='Intitulé', required=True, tracking=True)
    is_stockable = fields.Boolean(string='Commande stockable', default=True, tracking=True)
    solde_disponible = fields.Monetary(string='Solde disponible', compute='_compute_solde_disponible', store=False)
    montant_total = fields.Monetary(string='Montant Total', compute='_compute_montant_total', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    
    # Notes et commentaires
    note = fields.Text(string='Commentaire')
    urgence_signalee = fields.Boolean(string='Urgence signalée', default=False)
    memo_motivation = fields.Binary(string='Mémo de motivation')
    memo_filename = fields.Char(string='Nom du fichier mémo')
    
    # Validation et workflow
    validation_comment = fields.Text(string='Commentaire de validation')
    
    # Lignes et état
    line_ids = fields.One2many('e_gestock.demande_cotation_line', 'demande_id', string='Lignes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('validated', 'Validée'),
        ('budget_checked', 'Budget vérifié'),
        ('approved', 'Approuvée'),
        ('engaged', 'Engagée'),
        ('quotation', 'En attente cotation'),
        ('quoted', 'Cotations reçues'),
        ('selected', 'Fournisseur sélectionné'),
        ('po_generated', 'BC généré'),
        ('delivered', 'Livrée'),
        ('received', 'Réceptionnée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Relations
    cotation_ids = fields.One2many('e_gestock.cotation', 'demande_id', string='Cotations')
    purchase_order_id = fields.Many2one('purchase.order', string='Bon de commande')
    supplier_ids = fields.Many2many('res.partner', string='Fournisseurs présélectionnés')
    
    # Actions du workflow
    def action_submit(self):
        self.state = 'submitted'
        
    def action_validate(self):
        self.state = 'validated'
        
    def action_approve(self):
        self.state = 'approved'
        
    def action_send_quotation(self):
        self.state = 'quotation'
        
    def action_cancel(self):
        self.state = 'cancelled'
```

### 2. Lignes de demande de cotation
```python
class DemandeCotationLine(models.Model):
    _name = 'e_gestock.demande_cotation_line'
    _description = 'Ligne de demande de cotation'
    
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', domain="[('famille_id', '=', parent.compte_budg_id)]")
    ref_article = fields.Char(related='article_id.ref_article', string='Réf.', readonly=True)
    designation = fields.Char(string='Désignation article', required=True)
    description = fields.Text(string='Description article')
    quantite = fields.Float(string='Qté', required=True, default=1.0)
    quantite_accordee = fields.Float(string='Qté accordée', default=0.0)
    unite_id = fields.Many2one('uom.uom', string='Unité')
    echantillon = fields.Binary(string='Échantillon')
    echantillon_filename = fields.Char(string='Nom du fichier')
    is_selected = fields.Boolean(string='Sélectionnée', default=False)
    
    @api.onchange('article_id')
    def _onchange_article_id(self):
        if self.article_id:
            self.designation = self.article_id.design_article
            self.unite_id = self.article_id.unite_id
    
    @api.constrains('article_id', 'designation')
    def _check_article_or_designation(self):
        for line in self:
            if line.demande_id.is_stockable and not line.article_id:
                raise ValidationError(_("Pour une demande stockable, vous devez sélectionner un article."))
            if not line.designation:
                raise ValidationError(_("La désignation est obligatoire."))
```

### 3. Cotations
```python
class Cotation(models.Model):
    _name = 'e_gestock.cotation'
    _description = 'Cotation fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation', required=True, 
                               domain=[('state', '=', 'quotation')], tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True, 
                                domain=[('supplier_rank', '>', 0)], tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    date_expiration = fields.Date(string='Date d\'expiration', tracking=True)
    montant_total = fields.Monetary(string='Montant Total', compute='_compute_montant_total', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('submitted', 'Soumise'),
        ('confirmed', 'Confirmée'),
        ('selected', 'Sélectionnée'),
        ('rejected', 'Rejetée'),
        ('po_generated', 'BC généré')
    ], string='État', default='draft', tracking=True)
    is_best_offer = fields.Boolean(string='Meilleure offre', default=False, tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Bon de commande')
    line_ids = fields.One2many('e_gestock.cotation_line', 'cotation_id', string='Lignes')
    delai_livraison = fields.Integer(string='Délai de livraison (jours)', tracking=True)
    conditions_paiement = fields.Char(string='Conditions de paiement', tracking=True)
    
    # Champs supplémentaires pour les fournisseurs
    remise_generale = fields.Float(string='Remise générale (%)', tracking=True)
    tva = fields.Float(string='TVA (%)', tracking=True)
    bl_attachment = fields.Binary(string='Bon de livraison')
    bl_filename = fields.Char(string='Nom du fichier BL')
    date_livraison = fields.Date(string='Date de livraison')
```

## Structure du module

```
e_gestock_purchase/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── demande_cotation.py
  │   ├── demande_cotation_line.py
  │   ├── demande_cotation_fournisseur.py
  │   ├── cotation.py
  │   ├── cotation_line.py
  │   └── purchase_order_extension.py
  ├── views/
  │   ├── demande_cotation_views.xml
  │   ├── cotation_views.xml
  │   ├── purchase_order_views.xml
  │   └── menu_views.xml
  ├── wizards/
  │   ├── __init__.py
  │   ├── generate_purchase_order_wizard.py
  │   ├── select_suppliers_wizard.py
  │   └── validate_reception_wizard.py
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_purchase_security.xml
  ├── report/
  │   ├── demande_cotation_report.xml
  │   ├── cotation_report.xml
  │   └── purchase_order_report.xml
  └── data/
      ├── sequence_data.xml
      └── purchase_data.xml
```

## Vues principales

### 1. Formulaire de demande de cotation
```xml
<record id="view_demande_cotation_form" model="ir.ui.view">
    <field name="name">e_gestock.demande_cotation.form</field>
    <field name="model">e_gestock.demande_cotation</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <field name="state" widget="statusbar" statusbar_visible="draft,submitted,validated,approved,quotation,selected,po_generated,delivered,received"/>
                <button name="action_submit" string="Transférer" type="object" class="oe_highlight" states="draft"/>
                <button name="action_validate" string="Valider" type="object" class="oe_highlight" states="submitted" groups="e_gestock.group_e_gestock_resp_achats"/>
                <button name="action_approve" string="Approuver" type="object" class="oe_highlight" states="validated" groups="e_gestock.group_e_gestock_resp_achats"/>
                <button name="action_send_quotation" string="Demander cotations" type="object" class="oe_highlight" states="approved"/>
                <button name="action_cancel" string="Annuler" type="object" states="draft,submitted,validated,approved"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="exercice_id" readonly="state != 'draft'"/>
                        <field name="date" readonly="state != 'draft'"/>
                        <field name="demandeur_id" readonly="state != 'draft'"/>
                    </group>
                </group>
                <group>
                    <group>
                        <field name="compte_budg_id" required="1" readonly="state != 'draft'" options="{'no_create': True}"/>
                        <field name="designation_compte" readonly="1"/>
                        <field name="structure_id" required="1" readonly="state != 'draft'" options="{'no_create': True}"/>
                    </group>
                    <group>
                        <field name="gestion_id" required="1" readonly="state != 'draft'" options="{'no_create': True}"/>
                        <field name="designation_gestion" readonly="1"/>
                        <field name="intitule" readonly="state != 'draft'"/>
                        <field name="solde_disponible" readonly="1"/>
                    </group>
                </group>
                <group>
                    <field name="is_stockable" widget="boolean_toggle"/>
                </group>
                <notebook>
                    <page string="Articles" name="lines">
                        <field name="line_ids" widget="one2many_list" mode="tree,kanban">
                            <tree editable="bottom">
                                <field name="is_selected" widget="boolean_toggle" attrs="{'readonly': [('parent.state', '!=', 'submitted')]}"/>
                                <field name="ref_article" readonly="1"/>
                                <field name="article_id" domain="[('famille_id', '=', parent.compte_budg_id)]" 
                                       attrs="{'required': [('parent.is_stockable', '=', True)], 'readonly': [('parent.state', '!=', 'draft')]}"/>
                                <field name="designation" required="1" readonly="parent.state != 'draft'"/>
                                <field name="description" readonly="parent.state != 'draft'"/>
                                <field name="unite_id" readonly="parent.state != 'draft'"/>
                                <field name="quantite" readonly="parent.state != 'draft'"/>
                                <field name="quantite_accordee" attrs="{'readonly': [('parent.state', '!=', 'submitted')]}"/>
                                <field name="echantillon" widget="binary" filename="echantillon_filename"/>
                                <field name="echantillon_filename" invisible="1"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Commentaires" name="commentaires">
                        <group>
                            <field name="urgence_signalee"/>
                            <field name="note" placeholder="Ajouter ici vos commentaires..."/>
                            <field name="memo_motivation" widget="binary" filename="memo_filename"/>
                            <field name="memo_filename" invisible="1"/>
                        </group>
                    </page>
                    <page string="Cotations" name="cotations" attrs="{'invisible': [('state', 'not in', ['quotation', 'quoted', 'selected', 'po_generated', 'delivered', 'received'])]}">
                        <field name="cotation_ids" readonly="1">
                            <tree>
                                <field name="reference"/>
                                <field name="supplier_id"/>
                                <field name="date"/>
                                <field name="montant_total"/>
                                <field name="delai_livraison"/>
                                <field name="state"/>
                                <field name="is_best_offer"/>
                            </tree>
                        </field>
                    </page>
                    <page string="Fournisseurs" name="suppliers" attrs="{'invisible': [('state', 'not in', ['approved', 'quotation'])]}">
                        <field name="supplier_ids" widget="many2many_tags"/>
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

## Rapports et tableaux de bord

### 1. Rapports standards
- Demande de cotation
- Comparatif des cotations
- Suivi des validations
- Bon de commande généré

### 2. Tableaux de bord
- Suivi des demandes par état
- Performance des fournisseurs
- Délais de traitement par étape
- Analyse des demandes par structure et compte budgétaire

## Règles de sécurité

### 1. Accès aux demandes de cotation
- **Groupe Gestionnaire des achats** : Création et consultation des demandes
- **Groupe Responsable des achats** : Validation des demandes
- **Groupe Responsable Structure** : Validation au niveau structure
- **Groupe Contrôleur Budgétaire** : Contrôle budgétaire
- **Groupe Direction** : Approbation finale

### 2. Accès aux cotations
- **Groupe Gestionnaire des achats** : Création et gestion des cotations
- **Groupe Responsable des achats** : Sélection du mieux-disant
- **Groupe Fournisseur** : Accès limité via le portail aux cotations qui les concernent

## Intégration avec d'autres modules

### 1. Module budgétaire
- Contrôle de la disponibilité des fonds
- Engagement budgétaire
- Mise à jour des consommations

### 2. Module fournisseurs
- Intégration avec la gestion des fournisseurs
- Évaluation des performances
- Gestion des cotations

### 3. Module de réception
- Suivi des livraisons
- Mise à jour de l'état des demandes 