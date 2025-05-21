from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BudgetControl(models.Model):
    _inherit = 'e_gestock.budget_control'
    
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande')
    
    @api.depends('demande_id', 'purchase_order_id')
    def _compute_montant(self):
        for record in self:
            if record.demande_id:
                record.montant = record.demande_id.montant_total
            elif record.purchase_order_id:
                record.montant = record.purchase_order_id.amount_total
            else:
                record.montant = 0.0
    
    def action_approve(self):
        res = super(BudgetControl, self).action_approve()
        
        # Mise à jour du bon de commande
        if self.purchase_order_id:
            self.purchase_order_id.write({'budget_operation_id': self.operation_id.id})
        
        return res
    
    def action_reject(self):
        res = super(BudgetControl, self).action_reject()
        
        # Mise à jour de l'état du bon de commande
        if self.purchase_order_id:
            self.purchase_order_id.write({'budget_state': 'rejected'})
        
        return res
    
    def action_derogation(self):
        res = super(BudgetControl, self).action_derogation()
        
        # Mise à jour de l'état du bon de commande
        if self.purchase_order_id:
            self.purchase_order_id.write({'budget_state': 'pending_derogation'})
        
        return res
