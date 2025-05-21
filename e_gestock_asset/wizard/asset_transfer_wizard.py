# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetTransferWizard(models.TransientModel):
    _name = 'e_gestock.asset.transfer.wizard'
    _description = 'Assistant de transfert d\'immobilisation'
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True)
    date = fields.Date(string='Date du transfert', required=True, default=fields.Date.today)
    
    # Informations de transfert
    structure_origine_id = fields.Many2one('e_gestock.structure', string='Structure d\'origine', readonly=True)
    section_origine_id = fields.Many2one('e_gestock.section', string='Section d\'origine', readonly=True)
    localisation_origine = fields.Char(string='Localisation d\'origine', readonly=True)
    
    structure_destination_id = fields.Many2one('e_gestock.structure', string='Structure de destination', required=True)
    section_destination_id = fields.Many2one('e_gestock.section', string='Section de destination')
    localisation_destination = fields.Char(string='Localisation de destination')
    
    # Responsables
    responsable_origine_id = fields.Many2one('res.users', string='Responsable d\'origine', readonly=True)
    responsable_destination_id = fields.Many2one('res.users', string='Responsable de destination')
    
    # Informations complémentaires
    motif = fields.Text(string='Motif du transfert')
    
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        """Met à jour les champs en fonction de l'immobilisation sélectionnée."""
        if self.asset_id:
            self.structure_origine_id = self.asset_id.structure_id
            self.section_origine_id = self.asset_id.section_id
            self.localisation_origine = self.asset_id.localisation
            self.responsable_origine_id = self.asset_id.responsable_id
    
    def action_transfer(self):
        """Crée un transfert d'immobilisation."""
        self.ensure_one()
        
        # Création du transfert
        transfer_vals = {
            'asset_id': self.asset_id.id,
            'date': self.date,
            'structure_origine_id': self.structure_origine_id.id if self.structure_origine_id else False,
            'section_origine_id': self.section_origine_id.id if self.section_origine_id else False,
            'localisation_origine': self.localisation_origine,
            'responsable_origine_id': self.responsable_origine_id.id if self.responsable_origine_id else False,
            'structure_destination_id': self.structure_destination_id.id,
            'section_destination_id': self.section_destination_id.id if self.section_destination_id else False,
            'localisation_destination': self.localisation_destination,
            'responsable_destination_id': self.responsable_destination_id.id if self.responsable_destination_id else False,
            'motif': self.motif,
            'state': 'draft',
        }
        
        transfer = self.env['e_gestock.asset_transfer'].create(transfer_vals)
        
        # Confirmation automatique du transfert
        transfer.action_confirm()
        
        # Ouverture du formulaire de transfert créé
        return {
            'name': _('Transfert d\'immobilisation'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset_transfer',
            'res_id': transfer.id,
            'view_mode': 'form',
            'target': 'current',
        }
