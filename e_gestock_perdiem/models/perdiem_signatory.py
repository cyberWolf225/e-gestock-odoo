# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PerdiemSignatory(models.Model):
    _name = 'e_gestock.perdiem.signatory'
    _description = 'Signataire de Perdiem'
    _order = 'sequence'
    
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Utilisateur', required=True)
    function = fields.Char(string='Fonction', required=True)
    sequence = fields.Integer(string='Séquence', default=10, 
                             help="Ordre de validation des signataires")
    is_active = fields.Boolean(string='Actif', default=True)
    
    # Relations
    status_ids = fields.One2many('e_gestock.perdiem.signatory.status', 'signatory_id', string='Statuts')
    
    # Champs calculés
    current_status = fields.Selection([
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='Statut actuel', compute='_compute_current_status', store=True)
    
    @api.depends('status_ids.status', 'status_ids.date_debut')
    def _compute_current_status(self):
        """Calcule le statut actuel du signataire en fonction de son dernier statut."""
        for record in self:
            if not record.status_ids:
                record.current_status = 'pending'
            else:
                last_status = record.status_ids.sorted('date_debut', reverse=True)[0]
                record.current_status = last_status.status
    
    def action_approve(self):
        """Approuve la demande par le signataire."""
        self.ensure_one()
        
        # Vérification que l'utilisateur actuel est bien le signataire
        if self.user_id != self.env.user:
            raise UserError(_("Vous n'êtes pas autorisé à approuver cette demande."))
        
        # Création du statut de signataire
        self.env['e_gestock.perdiem.signatory.status'].create({
            'signatory_id': self.id,
            'status': 'approved',
            'date_debut': fields.Datetime.now(),
            'user_id': self.env.user.id,
        })
        
        # Mise à jour du statut de la demande si tous les signataires ont approuvé
        perdiem = self.perdiem_id
        all_signatories = perdiem.signatory_ids.filtered(lambda s: s.is_active)
        all_approved = all(s.current_status == 'approved' for s in all_signatories)
        
        if all_approved:
            # Tous les signataires ont approuvé, on passe au statut suivant
            if perdiem.state == 'submitted':
                perdiem.write({'state': 'section_validated'})
            elif perdiem.state == 'section_validated':
                perdiem.write({'state': 'structure_validated'})
            elif perdiem.state == 'structure_validated':
                perdiem.write({'state': 'budget_validated'})
            elif perdiem.state == 'budget_validated':
                perdiem.write({'state': 'finance_validated'})
            elif perdiem.state == 'finance_validated':
                perdiem.write({'state': 'dg_validated'})
            elif perdiem.state == 'dg_validated':
                perdiem.write({'state': 'approved'})
    
    def action_reject(self):
        """Rejette la demande par le signataire."""
        self.ensure_one()
        
        # Vérification que l'utilisateur actuel est bien le signataire
        if self.user_id != self.env.user:
            raise UserError(_("Vous n'êtes pas autorisé à rejeter cette demande."))
        
        return {
            'name': _('Rejeter la demande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.perdiem.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_perdiem_id': self.perdiem_id.id,
                'default_signatory_id': self.id,
            },
        }
