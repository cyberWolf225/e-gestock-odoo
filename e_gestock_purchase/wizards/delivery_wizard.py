from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DeliveryWizard(models.TransientModel):
    _name = 'e_gestock.delivery_wizard'
    _description = 'Assistant de livraison'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande',
                                       related='workflow_id.purchase_order_id', readonly=True)
    
    date_livraison = fields.Date(string='Date de livraison', required=True, default=fields.Date.context_today)
    bl_attachment = fields.Binary(string='Bon de livraison', required=True)
    bl_filename = fields.Char(string='Nom du fichier BL')
    
    def action_deliver(self):
        """Enregistre la livraison de la commande"""
        self.ensure_one()
        
        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande n'est associé à ce workflow."))
        
        if not self.bl_attachment:
            raise UserError(_("Veuillez joindre un bon de livraison."))
        
        # Mettre à jour le bon de commande
        self.purchase_order_id.write({
            'date_livraison_reelle': self.date_livraison,
            'bl_attachment': self.bl_attachment,
            'bl_filename': self.bl_filename or 'bon_livraison.pdf',
            'state_approbation': 'delivered'
        })
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': 'delivered'
        })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 