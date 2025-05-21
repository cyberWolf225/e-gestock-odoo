from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SupplierSelectionWizard(models.TransientModel):
    _name = 'e_gestock.supplier_selection_wizard'
    _description = 'Assistant de sélection du fournisseur'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    demande_cotation_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation',
                                        related='workflow_id.demande_cotation_id', readonly=True)
    
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation sélectionnée',
                                domain="[('demande_id', '=', demande_cotation_id), ('state', '=', 'confirmed')]",
                                required=True)
    
    @api.onchange('workflow_id')
    def _onchange_workflow(self):
        """Pré-remplit la cotation si une seule est disponible"""
        if self.workflow_id and self.demande_cotation_id:
            cotations = self.env['e_gestock.cotation'].search([
                ('demande_id', '=', self.demande_cotation_id.id),
                ('state', '=', 'confirmed')
            ])
            if len(cotations) == 1:
                self.cotation_id = cotations.id
    
    def action_select_supplier(self):
        """Sélectionne le fournisseur"""
        self.ensure_one()
        
        if not self.cotation_id:
            raise UserError(_("Veuillez sélectionner une cotation."))
        
        # Marquer la cotation comme sélectionnée
        self.cotation_id.action_select()
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': 'supplier_selected',
            'cotation_id': self.cotation_id.id
        })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 