from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    # Champs spécifiques à E-GESTOCK
    cotation_line_id = fields.Many2one('e_gestock.cotation_line', string='Ligne de cotation d\'origine', readonly=True)
    
    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Surcharge de la méthode de vérification des droits d'accès pour prendre en compte les groupes E-GESTOCK"""
        # Si l'utilisateur a un rôle E-GESTOCK, on lui accorde les droits
        if (self.env.user.has_group('e_gestock_base.group_e_gestock_purchase_user') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_purchase_manager') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_resp_dmp') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_budget_controller') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_resp_dfc') or
            self.env.user.has_group('e_gestock_base.group_dfc_validator') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_direction') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_admin')):
            return True
        
        # Sinon, on utilise le comportement standard
        return super(PurchaseOrderLine, self).check_access_rights(operation, raise_exception)
