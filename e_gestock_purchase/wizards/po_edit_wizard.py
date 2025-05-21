from odoo import api, fields, models, _
from odoo.exceptions import UserError


class POEditWizard(models.TransientModel):
    _name = 'e_gestock.po_edit_wizard'
    _description = 'Assistant d\'édition du bon de commande'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation sélectionnée',
                                related='workflow_id.cotation_id', readonly=True)
    
    # Signataires sélectionnés
    signataire_ids = fields.Many2many('res.users', string='Signataires',
                                    domain=[('groups_id', 'in', [
                                        lambda self: self.env.ref('e_gestock_base.group_e_gestock_manager').id
                                    ])])
    
    @api.model
    def default_get(self, fields_list):
        """Pré-remplit certains champs"""
        res = super(POEditWizard, self).default_get(fields_list)
        
        # Proposer des signataires par défaut
        signataires = self.env['res.users'].search([
            ('groups_id', 'in', [self.env.ref('e_gestock_base.group_e_gestock_manager').id])
        ], limit=3)
        
        if signataires:
            res['signataire_ids'] = [(6, 0, signataires.ids)]
        
        return res
    
    def action_edit_po(self):
        """Édite le bon de commande"""
        self.ensure_one()
        
        if not self.cotation_id:
            raise UserError(_("Aucune cotation sélectionnée pour ce workflow."))
        
        # Créer le bon de commande s'il n'existe pas déjà
        if not self.workflow_id.purchase_order_id:
            # Création du bon de commande
            purchase_order = self.env['e_gestock.purchase_order'].create({
                'partner_id': self.cotation_id.supplier_id.id,
                'date_order': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'currency_id': self.cotation_id.currency_id.id,
                'demande_cotation_id': self.cotation_id.demande_id.id,
                'cotation_id': self.cotation_id.id,
                'signataire_ids': [(6, 0, self.signataire_ids.ids)],
                'state': 'approved',
                'state_approbation': 'approved',
            })
            
            # Création des lignes
            for line in self.cotation_id.line_ids:
                self.env['e_gestock.purchase_order_line'].create({
                    'order_id': purchase_order.id,
                    'article_id': line.demande_line_id.article_id.id,
                    'description': line.demande_line_id.article_id.description,
                    'product_qty': line.quantite_a_servir,
                    'price_unit': line.prix_unitaire,
                    'product_uom': line.demande_line_id.article_id.uom_id.id,
                })
            
            # Lier le bon de commande au workflow
            self.workflow_id.write({
                'purchase_order_id': purchase_order.id,
                'state': 'po_edited'
            })
            
            # Lier le bon de commande à la cotation
            self.cotation_id.write({
                'purchase_order_id': purchase_order.id,
                'state': 'po_generated'
            })
        else:
            # Mettre à jour le bon de commande existant
            self.workflow_id.purchase_order_id.write({
                'signataire_ids': [(6, 0, self.signataire_ids.ids)],
            })
            
            # Mettre à jour l'état du workflow
            self.workflow_id.write({
                'state': 'po_edited'
            })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 