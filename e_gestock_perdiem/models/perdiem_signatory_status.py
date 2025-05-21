# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PerdiemSignatoryStatus(models.Model):
    _name = 'e_gestock.perdiem.signatory.status'
    _description = 'Statut du signataire de Perdiem'
    _order = 'date_debut desc'
    
    signatory_id = fields.Many2one('e_gestock.perdiem.signatory', string='Signataire', required=True, ondelete='cascade')
    status = fields.Selection([
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='Statut', required=True, default='pending')
    date_debut = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, default=lambda self: self.env.user)
    commentaire = fields.Text(string='Commentaire')
    
    # Champs calculés
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', related='signatory_id.perdiem_id', store=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour fermer le statut précédent."""
        for vals in vals_list:
            # Fermer le statut précédent
            if vals.get('signatory_id'):
                previous_status = self.search([
                    ('signatory_id', '=', vals.get('signatory_id')),
                    ('status', '=', 'pending')
                ], order='date_debut desc', limit=1)
                
                if previous_status:
                    previous_status.write({'status': vals.get('status')})
        
        return super(PerdiemSignatoryStatus, self).create(vals_list)
