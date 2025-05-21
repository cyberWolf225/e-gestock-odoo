from odoo import api, fields, models, _


class EgestockPurchaseOrderFields(models.Model):
    """
    Ajoute des champs supplémentaires au modèle e_gestock.purchase_order
    pour la compatibilité avec le module e_gestock_budget_purchase_bridge.
    """
    _inherit = 'e_gestock.purchase_order'

    # Champs pour la compatibilité avec le module budget
    structure_id = fields.Many2one('e_gestock.structure', string='Structure',
                                 related='demande_cotation_id.structure_id', store=True, readonly=True)
    # Le champ section_id n'existe pas dans demande_cotation, nous le définissons directement
    section_id = fields.Many2one('e_gestock.section', string='Section', store=True, readonly=True)
    famille_id = fields.Many2one('e_gestock.famille', string='Famille',
                               related='demande_cotation_id.compte_budg_id', store=True, readonly=True)
    type_gestion_id = fields.Many2one('e_gestock.type_gestion', string='Type de gestion',
                                    related='demande_cotation_id.gestion_id', store=True, readonly=True)
