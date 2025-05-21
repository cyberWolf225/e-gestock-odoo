# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PerdiemRejectWizard(models.TransientModel):
    _name = 'e_gestock.perdiem.reject.wizard'
    _description = 'Assistant de rejet de Perdiem'
    
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', required=True)
    signatory_id = fields.Many2one('e_gestock.perdiem.signatory', string='Signataire')
    commentaire = fields.Text(string='Motif du rejet', required=True)
    
    def action_reject(self):
        """Rejette la demande de perdiem."""
        self.ensure_one()
        perdiem = self.perdiem_id
        
        # Si le rejet vient d'un signataire spécifique
        if self.signatory_id:
            # Création du statut de signataire
            self.env['e_gestock.perdiem.signatory.status'].create({
                'signatory_id': self.signatory_id.id,
                'status': 'rejected',
                'date_debut': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'commentaire': self.commentaire,
            })
        
        # Création du statut de la demande
        self.env['e_gestock.perdiem.status'].create({
            'perdiem_id': perdiem.id,
            'status_type_id': self.env.ref('e_gestock_perdiem.perdiem_status_type_rejected').id,
            'user_id': self.env.user.id,
            'date_debut': fields.Datetime.now(),
            'commentaire': self.commentaire,
        })
        
        # Mise à jour du statut de la demande
        perdiem.write({'state': 'rejected'})
        
        return {'type': 'ir.actions.act_window_close'}
