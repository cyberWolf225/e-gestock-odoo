from odoo import models, fields, api, _

class InventoryLine(models.Model):
    _name = 'e_gestock.inventory_line'
    _description = 'Ligne d\'inventaire'
    _rec_name = 'article_id'
    
    inventory_id = fields.Many2one('e_gestock.inventory', string='Inventaire', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    product_id = fields.Many2one('product.product', string='Produit Odoo', related='article_id.product_id', store=True)
    quantite_theorique = fields.Float(string='Quantité théorique', digits='Product Unit of Measure', readonly=True)
    quantite_reelle = fields.Float(string='Quantité réelle', digits='Product Unit of Measure')
    ecart = fields.Float(string='Écart', compute='_compute_ecart', store=True)
    ecart_ratio = fields.Float(string='Écart %', compute='_compute_ecart_ratio', store=True)
    is_counted = fields.Boolean(string='Compté', default=False)
    notes = fields.Text(string='Notes')
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.code_unite', store=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', related='inventory_id.depot_id', store=True)
    state = fields.Selection(related='inventory_id.state', string='État', store=True)
    date = fields.Datetime(related='inventory_id.date', string='Date', store=True)
    
    @api.depends('quantite_theorique', 'quantite_reelle', 'is_counted')
    def _compute_ecart(self):
        for line in self:
            if line.is_counted:
                line.ecart = line.quantite_reelle - line.quantite_theorique
            else:
                line.ecart = 0
    
    @api.depends('ecart', 'quantite_theorique')
    def _compute_ecart_ratio(self):
        for line in self:
            if line.quantite_theorique > 0:
                line.ecart_ratio = (line.ecart / line.quantite_theorique) * 100
            elif line.ecart != 0:
                # Si la quantité théorique est 0 mais qu'il y a un écart
                line.ecart_ratio = 100
            else:
                line.ecart_ratio = 0
    
    @api.onchange('quantite_reelle')
    def _onchange_quantite_reelle(self):
        if self.quantite_reelle != self.quantite_theorique:
            self.is_counted = True
        
    def action_set_counted(self):
        """Marquer comme compté avec la quantité théorique"""
        self.ensure_one()
        if self.inventory_id.state != 'in_progress':
            return
            
        self.write({
            'quantite_reelle': self.quantite_theorique,
            'is_counted': True
        })
        
        return True
    
    def action_set_zero(self):
        """Marquer comme compté avec une quantité nulle"""
        self.ensure_one()
        if self.inventory_id.state != 'in_progress':
            return
            
        self.write({
            'quantite_reelle': 0,
            'is_counted': True
        })
        
        return True 