# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetDisposal(models.Model):
    _name = 'e_gestock.asset_disposal'
    _description = 'Cession d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    date = fields.Date(string='Date de cession', required=True, tracking=True, default=fields.Date.today)
    
    # Type de cession
    type = fields.Selection([
        ('sale', 'Vente'),
        ('scrapping', 'Mise au rebut'),
        ('donation', 'Don'),
        ('theft', 'Vol/Perte'),
        ('other', 'Autre')
    ], string='Type de cession', required=True, tracking=True, default='sale')
    
    # Informations financières
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    valeur_comptable = fields.Monetary(string='Valeur comptable', tracking=True)
    prix_cession = fields.Monetary(string='Prix de cession', tracking=True)
    plus_moins_value = fields.Monetary(string='Plus/moins-value', compute='_compute_plus_moins_value', store=True, tracking=True)
    
    # Informations complémentaires
    motif = fields.Text(string='Motif de la cession', tracking=True)
    note = fields.Text(string='Notes', tracking=True)
    
    # Destinataire (en cas de vente ou don)
    partner_id = fields.Many2one('res.partner', string='Destinataire', tracking=True)
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Documents
    document = fields.Binary(string='Document de cession', attachment=True)
    document_filename = fields.Char(string='Nom du fichier document')
    
    # Contraintes SQL
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de cession doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer automatiquement la référence."""
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset_disposal') or 'Nouveau'
            
            # Récupération de la valeur comptable de l'immobilisation
            if vals.get('asset_id') and not vals.get('valeur_comptable'):
                asset = self.env['e_gestock.asset'].browse(vals.get('asset_id'))
                vals['valeur_comptable'] = asset.valeur_acquisition  # À remplacer par la valeur nette comptable réelle
        
        return super(AssetDisposal, self).create(vals_list)
    
    @api.depends('valeur_comptable', 'prix_cession')
    def _compute_plus_moins_value(self):
        """Calcule la plus ou moins-value de la cession."""
        for record in self:
            record.plus_moins_value = record.prix_cession - record.valeur_comptable
    
    def action_confirm(self):
        """Confirme la cession."""
        self.ensure_one()
        self.state = 'confirmed'
        
        # Mise à jour de l'état de l'immobilisation
        if self.type == 'scrapping':
            self.asset_id.state = 'scrapped'
        else:
            self.asset_id.state = 'disposed'
        
        # Désactivation de l'immobilisation
        self.asset_id.active = False
        
        return True
    
    def action_cancel(self):
        """Annule la cession."""
        self.ensure_one()
        self.state = 'cancelled'
        return True
