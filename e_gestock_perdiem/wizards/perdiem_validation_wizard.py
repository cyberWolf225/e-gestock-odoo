# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PerdiemValidationWizard(models.TransientModel):
    _name = 'e_gestock.perdiem.validation.wizard'
    _description = 'Assistant de validation de Perdiem'
    
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', required=True)
    commentaire = fields.Text(string='Commentaire')
    
    def action_validate(self):
        """Valide la demande de perdiem."""
        self.ensure_one()
        perdiem = self.perdiem_id
        
        # Déterminer le statut suivant en fonction du statut actuel
        next_state = False
        status_type_id = False
        
        if perdiem.state == 'draft':
            next_state = 'submitted'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_submitted').id
        elif perdiem.state == 'submitted':
            next_state = 'section_validated'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_section_validated').id
        elif perdiem.state == 'section_validated':
            next_state = 'structure_validated'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_structure_validated').id
        elif perdiem.state == 'structure_validated':
            next_state = 'budget_validated'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_budget_validated').id
        elif perdiem.state == 'budget_validated':
            next_state = 'finance_validated'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_finance_validated').id
        elif perdiem.state == 'finance_validated':
            next_state = 'dg_validated'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_dg_validated').id
        elif perdiem.state == 'dg_validated':
            next_state = 'approved'
            status_type_id = self.env.ref('e_gestock_perdiem.perdiem_status_type_approved').id
        
        if not next_state or not status_type_id:
            raise UserError(_("Impossible de déterminer le statut suivant."))
        
        # Création du statut
        self.env['e_gestock.perdiem.status'].create({
            'perdiem_id': perdiem.id,
            'status_type_id': status_type_id,
            'user_id': self.env.user.id,
            'date_debut': fields.Datetime.now(),
            'commentaire': self.commentaire,
        })
        
        # Mise à jour du statut de la demande
        perdiem.write({'state': next_state})
        
        # Si la demande est approuvée, engager le budget
        if next_state == 'approved':
            # Logique d'engagement budgétaire
            credit = perdiem.credit_budgetaire_id
            if credit:
                # Mise à jour du crédit budgétaire
                credit.write({
                    'montant_consomme': credit.montant_consomme + perdiem.montant_total
                })
                
                # Marquer la demande comme engagée
                perdiem.write({'flag_engagement': True})
        
        return {'type': 'ir.actions.act_window_close'}
