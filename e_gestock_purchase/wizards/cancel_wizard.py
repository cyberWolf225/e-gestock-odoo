from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CancelWizard(models.TransientModel):
    _name = 'e_gestock.cancel_wizard'
    _description = 'Assistant d\'annulation du processus d\'achat'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    reason = fields.Text(string='Motif d\'annulation', required=True)
    
    def action_cancel(self):
        """Annule le processus d'achat"""
        self.ensure_one()
        
        # Vérifier si on peut annuler
        if self.workflow_id.state in ['received']:
            raise UserError(_("Impossible d'annuler un processus déjà terminé."))
        
        # Annuler la demande de cotation si elle existe
        if self.workflow_id.demande_cotation_id:
            self.workflow_id.demande_cotation_id.write({
                'state': 'cancelled'
            })
        
        # Annuler le bon de commande s'il existe
        if self.workflow_id.purchase_order_id:
            self.workflow_id.purchase_order_id.write({
                'state': 'cancel',
                'state_approbation': 'cancelled'
            })
        
        # Annuler la cotation sélectionnée si elle existe
        if self.workflow_id.cotation_id:
            self.workflow_id.cotation_id.write({
                'state': 'rejected',
                'is_best_offer': False
            })
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': 'cancelled',
            'notes': (self.workflow_id.notes or '') + '\n\nAnnulé le ' + fields.Date.today().strftime('%d/%m/%Y') + 
                    ' pour le motif suivant: ' + self.reason
        })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 