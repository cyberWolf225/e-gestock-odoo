# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Asset(models.Model):
    _name = 'e_gestock.asset'
    _description = 'Immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_acquisition desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    name = fields.Char(string='Nom', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)

    # Informations techniques
    article_id = fields.Many2one('e_gestock.article', string='Article E-GESTOCK', tracking=True)
    type_id = fields.Many2one('e_gestock.asset_type', string='Type d\'immobilisation', required=True, tracking=True)
    marque = fields.Char(string='Marque', tracking=True)
    modele = fields.Char(string='Modèle', tracking=True)
    numero_serie = fields.Char(string='Numéro de série', tracking=True)
    qr_code = fields.Char(string='Code QR', readonly=True, copy=False)

    # Dates clés
    date_acquisition = fields.Date(string='Date d\'acquisition', tracking=True)
    date_mise_service = fields.Date(string='Date de mise en service', tracking=True)
    date_debut_garantie = fields.Date(string='Début de garantie', tracking=True)
    date_fin_garantie = fields.Date(string='Fin de garantie', tracking=True)

    # Informations financières
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    valeur_acquisition = fields.Monetary(string='Valeur d\'acquisition', tracking=True)
    valeur_residuelle = fields.Monetary(string='Valeur résiduelle', tracking=True)
    duree_amortissement = fields.Integer(string='Durée amortissement (années)', tracking=True)
    methode_amortissement = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressive')
    ], string='Méthode amortissement', default='linear', tracking=True)

    # Localisation et responsabilité
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True)
    localisation = fields.Char(string='Localisation', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)

    # État et cycle de vie
    state = fields.Selection([
        ('in_stock', 'En stock'),
        ('in_service', 'En service'),
        ('in_maintenance', 'En maintenance'),
        ('out_of_service', 'Hors service'),
        ('disposed', 'Cédé'),
        ('scrapped', 'Mis au rebut')
    ], string='État', default='in_stock', tracking=True)
    active = fields.Boolean(string='Actif', default=True, tracking=True)

    # Relations avec d'autres modèles
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', tracking=True)
    maintenance_ids = fields.One2many('e_gestock.asset_maintenance', 'asset_id', string='Maintenances')
    assignment_ids = fields.One2many('e_gestock.asset_assignment', 'asset_id', string='Affectations')
    transfer_ids = fields.One2many('e_gestock.asset_transfer', 'asset_id', string='Transferts')
    document_ids = fields.One2many('e_gestock.asset_document', 'asset_id', string='Documents')

    # Compteurs pour les vues
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string='Nombre de maintenances')
    assignment_count = fields.Integer(compute='_compute_assignment_count', string='Nombre d\'affectations')
    transfer_count = fields.Integer(compute='_compute_transfer_count', string='Nombre de transferts')
    document_count = fields.Integer(compute='_compute_document_count', string='Nombre de documents')

    # Contraintes SQL
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de l\'immobilisation doit être unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer automatiquement la référence."""
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset') or 'Nouveau'

            # Génération du code QR
            if not vals.get('qr_code'):
                vals['qr_code'] = f"ASSET-{vals.get('reference')}"

            # Récupération des valeurs par défaut du type d'immobilisation
            if vals.get('type_id') and not vals.get('duree_amortissement'):
                asset_type = self.env['e_gestock.asset_type'].browse(vals.get('type_id'))
                vals['duree_amortissement'] = asset_type.duree_amortissement
                vals['methode_amortissement'] = asset_type.methode_amortissement

        return super(Asset, self).create(vals_list)

    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        """Calcule le nombre de maintenances pour l'immobilisation."""
        for record in self:
            record.maintenance_count = len(record.maintenance_ids)

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        """Calcule le nombre d'affectations pour l'immobilisation."""
        for record in self:
            record.assignment_count = len(record.assignment_ids)

    @api.depends('transfer_ids')
    def _compute_transfer_count(self):
        """Calcule le nombre de transferts pour l'immobilisation."""
        for record in self:
            record.transfer_count = len(record.transfer_ids)

    @api.depends('document_ids')
    def _compute_document_count(self):
        """Calcule le nombre de documents pour l'immobilisation."""
        for record in self:
            record.document_count = len(record.document_ids)

    def action_mise_en_service(self):
        """Met l'immobilisation en service."""
        self.ensure_one()
        if not self.date_mise_service:
            self.date_mise_service = fields.Date.today()
        self.state = 'in_service'
        return True

    def action_hors_service(self):
        """Met l'immobilisation hors service."""
        self.ensure_one()
        self.state = 'out_of_service'
        return True

    def action_generate_amortization_lines(self):
        """Ouvre l'assistant pour générer les lignes d'amortissement."""
        self.ensure_one()
        return {
            'name': _('Générer les amortissements'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset.generate.amortization.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_asset_id': self.id},
        }

    def action_view_maintenances(self):
        """Affiche les maintenances de l'immobilisation."""
        self.ensure_one()
        return {
            'name': _('Maintenances'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_maintenance',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_view_assignments(self):
        """Affiche les affectations de l'immobilisation."""
        self.ensure_one()
        return {
            'name': _('Affectations'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_assignment',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_view_transfers(self):
        """Affiche les transferts de l'immobilisation."""
        self.ensure_one()
        return {
            'name': _('Transferts'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_transfer',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_view_documents(self):
        """Affiche les documents de l'immobilisation."""
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_document',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }
