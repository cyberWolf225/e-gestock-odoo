# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetDisposalWizard(models.TransientModel):
    _name = 'e_gestock.asset.disposal.wizard'
    _description = 'Assistant de cession d\'immobilisation'
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True)
    date = fields.Date(string='Date de cession', required=True, default=fields.Date.today)
    
    # Type de cession
    type = fields.Selection([
        ('sale', 'Vente'),
        ('scrapping', 'Mise au rebut'),
        ('donation', 'Don'),
        ('theft', 'Vol/Perte'),
        ('other', 'Autre')
    ], string='Type de cession', required=True, default='sale')
    
    # Informations financières
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    valeur_comptable = fields.Monetary(string='Valeur comptable', readonly=True)
    prix_cession = fields.Monetary(string='Prix de cession')
    
    # Informations complémentaires
    motif = fields.Text(string='Motif de la cession')
    
    # Destinataire (en cas de vente ou don)
    partner_id = fields.Many2one('res.partner', string='Destinataire')
    
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        """Met à jour les champs en fonction de l'immobilisation sélectionnée."""
        if self.asset_id:
            self.valeur_comptable = self.asset_id.valeur_acquisition  # À remplacer par la valeur nette comptable réelle
    
    @api.onchange('type')
    def _onchange_type(self):
        """Met à jour les champs en fonction du type de cession."""
        if self.type in ['scrapping', 'theft']:
            self.prix_cession = 0.0
    
    def action_dispose(self):
        """Crée une cession d'immobilisation."""
        self.ensure_one()
        
        # Création de la cession
        disposal_vals = {
            'asset_id': self.asset_id.id,
            'date': self.date,
            'type': self.type,
            'valeur_comptable': self.valeur_comptable,
            'prix_cession': self.prix_cession,
            'motif': self.motif,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'state': 'draft',
        }
        
        disposal = self.env['e_gestock.asset_disposal'].create(disposal_vals)
        
        # Confirmation automatique de la cession
        disposal.action_confirm()
        
        # Ouverture du formulaire de cession créé
        return {
            'name': _('Cession d\'immobilisation'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_disposal',
            'res_id': disposal.id,
            'view_mode': 'form',
            'target': 'current',
        }
