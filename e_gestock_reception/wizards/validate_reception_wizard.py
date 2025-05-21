from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ValidateReceptionWizard(models.TransientModel):
    _name = 'e_gestock.reception.validate_reception_wizard'
    _description = 'Assistant de validation de réception'
    
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', 
                                      required=True, readonly=True)
    date_reception = fields.Date(string='Date de réception', 
                               default=fields.Date.context_today, required=True)
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception',
                                 required=True)
    notes = fields.Text(string='Notes de réception')
    
    line_ids = fields.One2many('e_gestock.reception.validate_reception_line_wizard', 'wizard_id', 
                             string='Lignes de réception')
    
    @api.model
    def default_get(self, fields):
        res = super(ValidateReceptionWizard, self).default_get(fields)
        
        if 'purchase_order_id' in res and res['purchase_order_id']:
            purchase_order = self.env['e_gestock.purchase_order'].browse(res['purchase_order_id'])
            
            # Récupérer le comité de réception
            if purchase_order.committee_id:
                res['committee_id'] = purchase_order.committee_id.id
            
            # Créer les lignes de réception
            lines = []
            for line in purchase_order.order_line:
                if line.product_qty > line.qty_received:
                    lines.append((0, 0, {
                        'purchase_line_id': line.id,
                        'product_id': line.product_id.id,
                        'description': line.name,
                        'product_qty': line.product_qty,
                        'qty_received': line.qty_received,
                        'qty_to_receive': line.product_qty - line.qty_received,
                        'uom_id': line.product_uom.id,
                    }))
            
            if lines:
                res['line_ids'] = lines
        
        return res
    
    def action_validate(self):
        """Valide la réception"""
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Aucune ligne à réceptionner."))
        
        # Vérifier que les quantités sont valides
        for line in self.line_ids:
            if line.qty_to_receive <= 0:
                raise UserError(_("La quantité à réceptionner doit être supérieure à zéro."))
            
            if line.qty_to_receive > (line.product_qty - line.qty_received):
                raise UserError(_("La quantité à réceptionner ne peut pas dépasser la quantité restante."))
        
        # Créer une réception
        reception_vals = {
            'purchase_order_id': self.purchase_order_id.id,
            'date': self.date_reception,
            'committee_id': self.committee_id.id,
            'notes': self.notes,
            'depot_id': self.env['e_gestock.depot'].search([], limit=1).id,  # À adapter selon les besoins
        }
        
        reception = self.env['e_gestock.reception'].create(reception_vals)
        
        # Créer les lignes de réception
        for line in self.line_ids:
            reception_line_vals = {
                'reception_id': reception.id,
                'purchase_line_id': line.purchase_line_id.id,
                'article_id': line.product_id.e_gestock_article_id.id if hasattr(line.product_id, 'e_gestock_article_id') else False,
                'designation': line.description,
                'quantite_commandee': line.product_qty,
                'quantite_deja_recue': line.qty_received,
                'quantite_recue': line.qty_to_receive,
                'quantite_restante': 0,
                'uom_id': line.uom_id.id,
            }
            
            self.env['e_gestock.reception_line'].create(reception_line_vals)
            
            # Mettre à jour la quantité reçue dans la ligne de commande
            line.purchase_line_id.qty_received += line.qty_to_receive
        
        # Confirmer la réception
        reception.action_confirm()
        
        # Ouvrir la réception créée
        return {
            'name': _('Réception'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception',
            'res_id': reception.id,
            'view_mode': 'form',
            'target': 'current',
        }


class ValidateReceptionLineWizard(models.TransientModel):
    _name = 'e_gestock.reception.validate_reception_line_wizard'
    _description = 'Ligne d\'assistant de validation de réception'
    
    wizard_id = fields.Many2one('e_gestock.reception.validate_reception_wizard', 
                              string='Assistant', required=True, ondelete='cascade')
    purchase_line_id = fields.Many2one('e_gestock.purchase_order_line', 
                                     string='Ligne de commande', required=True)
    product_id = fields.Many2one('product.product', string='Produit', required=True)
    description = fields.Text(string='Description')
    product_qty = fields.Float(string='Quantité commandée', digits='Product Unit of Measure')
    qty_received = fields.Float(string='Quantité déjà reçue', digits='Product Unit of Measure')
    qty_to_receive = fields.Float(string='Quantité à réceptionner', digits='Product Unit of Measure')
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure')
    notes = fields.Text(string='Notes')
