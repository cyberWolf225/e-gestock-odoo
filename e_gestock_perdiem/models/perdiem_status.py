# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PerdiemStatus(models.Model):
    _name = 'e_gestock.perdiem.status'
    _description = 'Statut de Perdiem'
    _order = 'date_debut desc'
    
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', required=True, ondelete='cascade')
    status_type_id = fields.Many2one('e_gestock.perdiem.status.type', string='Type de statut', required=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True, default=lambda self: self.env.user)
    date_debut = fields.Datetime(string='Date de début', required=True, default=fields.Datetime.now)
    date_fin = fields.Datetime(string='Date de fin')
    commentaire = fields.Text(string='Commentaire')
    
    # Champs calculés
    duration = fields.Float(string='Durée (heures)', compute='_compute_duration', store=True)
    
    @api.depends('date_debut', 'date_fin')
    def _compute_duration(self):
        """Calcule la durée entre la date de début et la date de fin en heures."""
        for record in self:
            if record.date_debut and record.date_fin:
                duration = (record.date_fin - record.date_debut).total_seconds() / 3600
                record.duration = round(duration, 2)
            else:
                record.duration = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour fermer le statut précédent."""
        for vals in vals_list:
            # Fermer le statut précédent
            if vals.get('perdiem_id'):
                previous_status = self.search([
                    ('perdiem_id', '=', vals.get('perdiem_id')),
                    ('date_fin', '=', False)
                ], order='date_debut desc', limit=1)
                
                if previous_status:
                    previous_status.write({'date_fin': vals.get('date_debut')})
        
        return super(PerdiemStatus, self).create(vals_list)
