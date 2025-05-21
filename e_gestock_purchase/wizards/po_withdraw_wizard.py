from odoo import api, fields, models, _
from odoo.exceptions import UserError


class POWithdrawWizard(models.TransientModel):
    _name = 'e_gestock.po_withdraw_wizard'
    _description = 'Assistant de retrait du bon de commande'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande',
                                       related='workflow_id.purchase_order_id', readonly=True)
    
    date_retrait = fields.Date(string='Date de retrait', required=True, default=fields.Date.context_today)
    date_livraison_prevue = fields.Date(string='Date de livraison prévue', required=True)
    
    @api.model
    def default_get(self, fields_list):
        """Pré-remplit certains champs"""
        res = super(POWithdrawWizard, self).default_get(fields_list)
        
        # Proposer une date de livraison par défaut (date de retrait + 15 jours)
        if 'date_livraison_prevue' in fields_list and not res.get('date_livraison_prevue'):
            date_retrait = res.get('date_retrait') or fields.Date.context_today(self)
            res['date_livraison_prevue'] = fields.Date.add(date_retrait, days=15)
        
        return res
    
    def action_withdraw_po(self):
        """Enregistre le retrait du bon de commande"""
        self.ensure_one()
        
        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande n'est associé à ce workflow."))
        
        # Mettre à jour le bon de commande
        self.purchase_order_id.write({
            'date_retrait': self.date_retrait,
            'date_livraison_prevue': self.date_livraison_prevue,
            'state_approbation': 'withdrawn'
        })
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': 'po_withdrawn'
        })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 