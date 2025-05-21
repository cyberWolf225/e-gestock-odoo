# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetTransfer(models.Model):
    _name = 'e_gestock.asset_transfer'
    _description = 'Transfert d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    date = fields.Date(string='Date du transfert', required=True, tracking=True, default=fields.Date.today)
    
    # Informations de transfert
    structure_origine_id = fields.Many2one('e_gestock.structure', string='Structure d\'origine', tracking=True)
    section_origine_id = fields.Many2one('e_gestock.section', string='Section d\'origine', tracking=True)
    localisation_origine = fields.Char(string='Localisation d\'origine', tracking=True)
    
    structure_destination_id = fields.Many2one('e_gestock.structure', string='Structure de destination', required=True, tracking=True)
    section_destination_id = fields.Many2one('e_gestock.section', string='Section de destination', tracking=True)
    localisation_destination = fields.Char(string='Localisation de destination', tracking=True)
    
    # Responsables
    responsable_origine_id = fields.Many2one('res.users', string='Responsable d\'origine', tracking=True)
    responsable_destination_id = fields.Many2one('res.users', string='Responsable de destination', tracking=True)
    
    # Informations complémentaires
    motif = fields.Text(string='Motif du transfert', tracking=True)
    note = fields.Text(string='Notes', tracking=True)
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Documents
    document = fields.Binary(string='Document de transfert', attachment=True)
    document_filename = fields.Char(string='Nom du fichier document')
    
    # Contraintes SQL
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de transfert doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer automatiquement la référence."""
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset_transfer') or 'Nouveau'
            
            # Récupération des informations de l'immobilisation
            if vals.get('asset_id') and not vals.get('structure_origine_id'):
                asset = self.env['e_gestock.asset'].browse(vals.get('asset_id'))
                vals['structure_origine_id'] = asset.structure_id.id
                vals['section_origine_id'] = asset.section_id.id if asset.section_id else False
                vals['localisation_origine'] = asset.localisation
                vals['responsable_origine_id'] = asset.responsable_id.id if asset.responsable_id else False
        
        return super(AssetTransfer, self).create(vals_list)
    
    def action_confirm(self):
        """Confirme le transfert."""
        self.ensure_one()
        self.state = 'confirmed'
        
        # Mise à jour des informations de l'immobilisation
        self.asset_id.write({
            'structure_id': self.structure_destination_id.id,
            'section_id': self.section_destination_id.id if self.section_destination_id else False,
            'localisation': self.localisation_destination,
            'responsable_id': self.responsable_destination_id.id if self.responsable_destination_id else False,
        })
        
        return True
    
    def action_cancel(self):
        """Annule le transfert."""
        self.ensure_one()
        self.state = 'cancelled'
        return True
