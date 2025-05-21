from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class PurchaseWorkflow(models.Model):
    _name = 'e_gestock.purchase_workflow'
    _description = 'Workflow du processus d\'achat'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_creation desc, id desc'

    @api.model
    def _valid_field_parameter(self, field, name):
        # Autoriser le paramètre 'states' sur les champs
        return name == 'states' or super()._valid_field_parameter(field, name)

    # Informations générales
    name = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    date_creation = fields.Datetime(string='Date de création', default=fields.Datetime.now, readonly=True, tracking=True)
    
    # Demandeur
    demandeur_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user, 
                                 required=True, tracking=True, readonly=True, 
                                 states={'draft': [('readonly', False)]})
    
    # Informations budgétaires
    compte_budgetaire_id = fields.Many2one('e_gestock.famille', string='Compte budgétaire', required=True,
                                          tracking=True, readonly=True, 
                                          states={'draft': [('readonly', False)]})
    gestion_id = fields.Many2one('e_gestock.type_gestion', string='Gestion', required=True, 
                                tracking=True, readonly=True, 
                                states={'draft': [('readonly', False)]})
    structure_id = fields.Many2one('e_gestock.structure', string='Structure bénéficiaire', required=True,
                                  tracking=True, readonly=True, 
                                  states={'draft': [('readonly', False)]})
    
    # Informations demande
    intitule = fields.Char(string='Intitulé', required=True, tracking=True, readonly=True,
                         states={'draft': [('readonly', False)]})
    notes = fields.Text(string='Notes', readonly=True, states={'draft': [('readonly', False)]})
    memo_motivation = fields.Binary(string='Mémo de motivation', readonly=True, 
                                   states={'draft': [('readonly', False)]})
    memo_filename = fields.Char(string='Nom du fichier mémo')
    
    # État du workflow
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('validated', 'Validée'),
        ('quotation_request', 'Demande de cotation'),
        ('cmp_validated_request', 'Demande validée par CMP'),
        ('quotation_sent', 'Cotation envoyée aux fournisseurs'),
        ('quotation_received', 'Cotations reçues'),
        ('supplier_selected', 'Fournisseur sélectionné'),
        ('cmp_validated_choice', 'Choix validé par CMP'),
        ('budget_controlled', 'Contrôle budgétaire effectué'),
        ('dcg_dept_validated', 'Validé par Chef Département DCG'),
        ('dcg_validated', 'Validé par Responsable DCG'),
        ('dgaaf_validated', 'Validé par DGAAF'),
        ('dg_validated', 'Validé par DG'),
        ('po_edited', 'Bon de commande édité'),
        ('po_withdrawn', 'Bon de commande retiré'),
        ('delivered', 'Livré'),
        ('received', 'Réceptionné'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Relations avec les autres modèles
    demande_cotation_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation', readonly=True)
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation sélectionnée', readonly=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', readonly=True)
    
    # Liens avec les modules de réception et d'inventaire
    reception_id = fields.Many2one('e_gestock.reception', string='Réception associée', readonly=True)
    stock_movement_id = fields.Many2one('e_gestock.stock_movement', string='Mouvement de stock', readonly=True)
    
    # Lignes de produits
    line_ids = fields.One2many('e_gestock.purchase_workflow_line', 'workflow_id', string='Lignes', 
                              readonly=True, states={'draft': [('readonly', False)]})
    
    # Informations sur les validations
    # Responsable achats
    resp_achat_id = fields.Many2one('res.users', string='Responsable des achats', readonly=True)
    resp_achat_date = fields.Datetime(string='Date validation resp. achats', readonly=True)
    resp_achat_comment = fields.Text(string='Commentaire resp. achats', readonly=True)
    
    # CMP (Demande)
    cmp_request_validator_id = fields.Many2one('res.users', string='Validateur CMP (demande)', readonly=True)
    cmp_request_date = fields.Datetime(string='Date validation CMP (demande)', readonly=True)
    cmp_request_comment = fields.Text(string='Commentaire CMP (demande)', readonly=True)
    
    # CMP (Choix)
    cmp_choice_validator_id = fields.Many2one('res.users', string='Validateur CMP (choix)', readonly=True)
    cmp_choice_date = fields.Datetime(string='Date validation CMP (choix)', readonly=True)
    cmp_choice_comment = fields.Text(string='Commentaire CMP (choix)', readonly=True)
    
    # Contrôle budgétaire
    budget_validator_id = fields.Many2one('res.users', string='Contrôleur budgétaire', readonly=True)
    budget_date = fields.Datetime(string='Date contrôle budgétaire', readonly=True)
    budget_comment = fields.Text(string='Commentaire contrôle budgétaire', readonly=True)
    
    # Chef Département DCG
    dcg_dept_validator_id = fields.Many2one('res.users', string='Chef Département DCG', readonly=True)
    dcg_dept_date = fields.Datetime(string='Date validation Chef Dép. DCG', readonly=True)
    dcg_dept_comment = fields.Text(string='Commentaire Chef Dép. DCG', readonly=True)
    
    # Responsable DCG
    dcg_validator_id = fields.Many2one('res.users', string='Responsable DCG', readonly=True)
    dcg_date = fields.Datetime(string='Date validation Resp. DCG', readonly=True)
    dcg_comment = fields.Text(string='Commentaire Resp. DCG', readonly=True)
    
    # DGAAF
    dgaaf_validator_id = fields.Many2one('res.users', string='DGAAF', readonly=True)
    dgaaf_date = fields.Datetime(string='Date validation DGAAF', readonly=True)
    dgaaf_comment = fields.Text(string='Commentaire DGAAF', readonly=True)
    
    # DG
    dg_validator_id = fields.Many2one('res.users', string='DG', readonly=True)
    dg_date = fields.Datetime(string='Date validation DG', readonly=True)
    dg_comment = fields.Text(string='Commentaire DG', readonly=True)
    
    # Comité de réception
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception', readonly=True)
    reception_date = fields.Datetime(string='Date de réception', readonly=True)
    reception_comment = fields.Text(string='Commentaire réception', readonly=True)
    
    # Informations financières
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    amount_total = fields.Monetary(string='Montant total', compute='_compute_amount', store=True)
    
    # Seuil pour validation DG ou DGAAF
    seuil_validation_dg = fields.Float(string='Seuil de validation DG',
                                     default=lambda self: self.env['ir.config_parameter'].sudo().get_param('e_gestock_purchase.seuil_validation_dg', 5000000.0),
                                     readonly=True)
    needs_dg_validation = fields.Boolean(string='Nécessite validation DG', compute='_compute_validation_level', store=True)
    
    # Champs techniques pour gérer les lectures seules
    lines_readonly = fields.Boolean(compute='_compute_readonly_fields')
    
    @api.depends('state')
    def _compute_readonly_fields(self):
        for record in self:
            record.lines_readonly = record.state != 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('e_gestock.purchase_workflow') or 'Nouveau'
        return super(PurchaseWorkflow, self).create(vals_list)
    
    @api.depends('line_ids.prix_total')
    def _compute_amount(self):
        for record in self:
            record.amount_total = sum(line.prix_total for line in record.line_ids)
    
    @api.depends('amount_total')
    def _compute_validation_level(self):
        for record in self:
            record.needs_dg_validation = record.amount_total >= record.seuil_validation_dg
    
    # Actions du workflow
    def action_submit(self):
        """Soumet la demande d'achat au responsable des achats"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Vous ne pouvez pas soumettre une demande sans articles."))
        self.write({'state': 'submitted'})
        
        # Message de traçabilité
        msg = _("Demande soumise par %s") % self.env.user.name
        self.message_post(body=msg)
        
        return True
    
    def action_validate(self):
        """Validation de la demande par le responsable des achats"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation de la demande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'resp_achat',
                'default_next_state': 'validated',
            }
        }
    
    def action_create_quotation_request(self):
        """Création de la demande de cotation"""
        self.ensure_one()
        # Ouvrir l'assistant de demande de cotation
        return {
            'name': _('Créer une demande de cotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.quotation_request_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def action_validate_cmp_request(self):
        """Validation de la demande de cotation par le responsable CMP"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation CMP'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'cmp_request',
                'default_next_state': 'cmp_validated_request',
            }
        }
    
    def action_send_quotation(self):
        """Envoi de la demande de cotation aux fournisseurs"""
        self.ensure_one()
        if not self.demande_cotation_id:
            raise UserError(_("Aucune demande de cotation n'a été créée."))
        
        # Mettre à jour l'état de la demande de cotation
        self.demande_cotation_id.write({'state': 'quotation'})
        
        # Créer et envoyer les demandes de cotation aux fournisseurs
        suppliers = self.demande_cotation_id.supplier_ids
        for supplier in suppliers:
            demande_cotation_fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].create({
                'demande_id': self.demande_cotation_id.id,
                'supplier_id': supplier.id,
                'state': 'sent',
            })
            # Envoi d'un email au fournisseur (optionnel)
            if supplier.email:
                template = self.env.ref('e_gestock_purchase.email_template_quotation_request')
                if template:
                    template.with_context(supplier_email=supplier.email).send_mail(
                        demande_cotation_fournisseur.id, force_send=True
                    )
        
        self.write({'state': 'quotation_sent'})
        self.message_post(body=_("Demande de cotation envoyée aux fournisseurs"))
        
        return True
    
    def _check_quotations_received(self):
        """Vérifie si toutes les cotations ont été reçues"""
        self.ensure_one()
        
        if not self.demande_cotation_id:
            return False
        
        demandes_fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].search([
            ('demande_id', '=', self.demande_cotation_id.id)
        ])
        
        # Si toutes les demandes ont une cotation associée ou sont annulées
        all_received = all(
            demande.state in ['received', 'cancelled'] 
            for demande in demandes_fournisseur
        )
        
        if all_received and self.state == 'quotation_sent':
            self.write({'state': 'quotation_received'})
            self.message_post(body=_("Toutes les cotations ont été reçues"))
        
        return all_received
    
    def action_select_supplier(self):
        """Sélection du fournisseur mieux disant"""
        self.ensure_one()
        # Ouvrir l'assistant de sélection de fournisseur
        return {
            'name': _('Sélectionner le fournisseur'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_selection_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def action_validate_cmp_choice(self):
        """Validation du choix du fournisseur par le responsable CMP"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation CMP'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'cmp_choice',
                'default_next_state': 'cmp_validated_choice',
            }
        }
    
    def action_budget_control(self):
        """Contrôle budgétaire"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Contrôle budgétaire'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'budget',
                'default_next_state': 'budget_controlled',
            }
        }
    
    def action_validate_dcg_dept(self):
        """Validation par le chef département DCG"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation Chef Département DCG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'dcg_dept',
                'default_next_state': 'dcg_dept_validated',
            }
        }
    
    def action_validate_dcg(self):
        """Validation par le responsable DCG"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation Responsable DCG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'dcg',
                'default_next_state': 'dcg_validated',
            }
        }
    
    def action_validate_dgaaf(self):
        """Validation par le DGAAF"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation DGAAF'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'dgaaf',
                'default_next_state': 'dgaaf_validated',
            }
        }
    
    def action_validate_dg(self):
        """Validation par le DG"""
        self.ensure_one()
        # Ouvrir l'assistant de validation
        return {
            'name': _('Validation DG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
                'default_validation_type': 'dg',
                'default_next_state': 'dg_validated',
            }
        }
    
    def action_edit_po(self):
        """Édition du bon de commande"""
        self.ensure_one()
        # Ouvrir l'assistant d'édition du bon de commande
        return {
            'name': _('Éditer le bon de commande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.po_edit_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def action_withdraw_po(self):
        """Retrait du bon de commande par le fournisseur"""
        self.ensure_one()
        # Ouvrir l'assistant de retrait du bon de commande
        return {
            'name': _('Retrait du bon de commande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.po_withdraw_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def action_deliver(self):
        """Livraison de la commande par le fournisseur"""
        self.ensure_one()
        # Ouvrir l'assistant de livraison
        return {
            'name': _('Livraison de la commande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.delivery_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def action_receive(self):
        """Réception de la commande par le comité de réception"""
        self.ensure_one()
        # Ouvrir l'assistant de réception
        return {
            'name': _('Réception de la commande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }
    
    def _create_reception(self, date_reception, committee_id, comment, line_details):
        """Crée une réception dans le module e_gestock_reception"""
        self.ensure_one()
        
        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande associé à ce workflow."))
        
        # Créer la réception
        reception_vals = {
            'purchase_order_id': self.purchase_order_id.id,
            'date': datetime.now().date(),
            'depot_id': self.structure_id.depot_id.id,
            'responsable_id': self.env.user.id,
            'committee_id': committee_id,
            'notes': comment,
            'bl_date': datetime.now().date()
        }
        
        reception = self.env['e_gestock.reception'].create(reception_vals)
        
        # Créer les lignes de réception
        for line_detail in line_details:
            line_id = line_detail.get('line_id')
            quantite_recue = line_detail.get('quantite_recue')
            
            if line_id and quantite_recue > 0:
                po_line = self.env['e_gestock.purchase_order_line'].browse(line_id)
                
                # Créer la ligne de réception
                self.env['e_gestock.reception_line'].create({
                    'reception_id': reception.id,
                    'purchase_line_id': po_line.id,
                    'article_id': po_line.article_id.id,
                    'quantite_commandee': po_line.product_qty,
                    'quantite_recue': quantite_recue,
                    'uom_id': po_line.product_uom.id,
                })
        
        # Confirmer la réception
        reception.action_confirm()
        
        # Mettre à jour le workflow avec la référence de la réception
        self.write({
            'reception_id': reception.id
        })
        
        return reception
    
    def _create_stock_movement(self, date_reception, depot_id, lines):
        """Crée un mouvement de stock dans le module e_gestock_inventory"""
        self.ensure_one()
        
        # Créer le mouvement de stock (entrée)
        movement_vals = {
            'type': 'in',
            'date': date_reception,
            'depot_destination_id': depot_id,
            'responsable_id': self.env.user.id,
            'validateur_id': self.env.user.id,
            'notes': _("Réception de la commande %s") % self.purchase_order_id.name,
            'origine': 'purchase',
            'reference_origine': self.purchase_order_id.name,
            'state': 'draft',
        }
        
        movement = self.env['e_gestock.stock_movement'].create(movement_vals)
        
        # Créer les lignes de mouvement
        for line in lines:
            po_line = self.env['e_gestock.purchase_order_line'].browse(line.get('line_id'))
            quantite_recue = line.get('quantite_recue')
            
            if quantite_recue > 0:
                self.env['e_gestock.stock_movement_line'].create({
                    'movement_id': movement.id,
                    'article_id': po_line.article_id.id,
                    'quantite': quantite_recue,
                    'prix_unitaire': po_line.price_unit,
                })
        
        # Confirmer et valider le mouvement
        movement.action_confirm()
        movement.action_validate()
        
        # Mettre à jour le workflow avec la référence du mouvement
        self.write({
            'stock_movement_id': movement.id
        })
        
        return movement
    
    def action_cancel(self):
        """Annulation du processus d'achat"""
        self.ensure_one()
        # Ouvrir l'assistant d'annulation
        return {
            'name': _('Annulation du processus'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.cancel_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workflow_id': self.id,
            }
        }


class PurchaseWorkflowLine(models.Model):
    _name = 'e_gestock.purchase_workflow_line'
    _description = 'Ligne de workflow d\'achat'
    
    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    reference = fields.Char(string='Référence', related='article_id.ref_article', readonly=True)
    
    description = fields.Text(string='Description')
    quantite = fields.Float(string='Quantité demandée', required=True, default=1.0)
    quantite_accordee = fields.Float(string='Quantité accordée')
    prix_unitaire = fields.Monetary(string='Prix unitaire')
    prix_total = fields.Monetary(string='Prix total', compute='_compute_prix_total', store=True)
    
    currency_id = fields.Many2one('res.currency', related='workflow_id.currency_id')
    
    # Photo de l'article
    photo = fields.Binary(string='Photo', related='article_id.image', readonly=True)
    filename = fields.Char(string='Nom du fichier', compute='_compute_filename')
    
    @api.depends('article_id')
    def _compute_filename(self):
        for line in self:
            line.filename = line.article_id and (line.article_id.reference or 'photo.png') or 'photo.png'
    
    @api.depends('quantite', 'quantite_accordee', 'prix_unitaire')
    def _compute_prix_total(self):
        for line in self:
            quantite = line.quantite_accordee or line.quantite
            line.prix_total = quantite * (line.prix_unitaire or 0.0) 