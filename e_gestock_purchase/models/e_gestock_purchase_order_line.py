from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class EgestockPurchaseOrderLine(models.Model):
    _name = 'e_gestock.purchase_order_line'
    _description = 'Ligne de bon de commande E-GESTOCK'
    _order = 'order_id, sequence, id'

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    
    order_id = fields.Many2one('e_gestock.purchase_order', string='Commande', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Article', domain=[('purchase_ok', '=', True)])
    product_qty = fields.Float(string='Quantité', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unité de mesure', required=True)
    
    price_unit = fields.Float(string='Prix unitaire', required=True, digits='Product Price')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    price_subtotal = fields.Monetary(string='Sous-total', compute='_compute_amount', store=True)
    price_tax = fields.Monetary(string='Taxes', compute='_compute_amount', store=True)
    price_total = fields.Monetary(string='Total', compute='_compute_amount', store=True)
    
    currency_id = fields.Many2one(related='order_id.currency_id', string='Devise', store=True, readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Société', store=True, readonly=True)
    
    date_planned = fields.Datetime(string='Date prévue', index=True)
    
    # Champs spécifiques à E-GESTOCK
    cotation_line_id = fields.Many2one('e_gestock.cotation_line', string='Ligne de cotation d\'origine', readonly=True)
    e_gestock_article_id = fields.Many2one('e_gestock.article', string='Article E-GESTOCK')
    
    # Champs pour la réception
    qty_received = fields.Float(string='Quantité reçue', digits='Product Unit of Measure', default=0.0)
    qty_to_receive = fields.Float(string='Quantité à recevoir', compute='_compute_qty_to_receive', store=True)
    
    @api.depends('product_qty', 'qty_received')
    def _compute_qty_to_receive(self):
        for line in self:
            line.qty_to_receive = line.product_qty - line.qty_received
    
    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        """Calcule les montants de la ligne"""
        for line in self:
            taxes = line.taxes_id.compute_all(
                line.price_unit,
                line.order_id.currency_id,
                line.product_qty,
                product=line.product_id,
                partner=line.order_id.partner_id
            )
            line.price_subtotal = taxes['total_excluded']
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
            line.price_total = taxes['total_included']
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        """Met à jour les informations en fonction du produit sélectionné"""
        if not self.product_id:
            return
        
        self.product_uom = self.product_id.uom_po_id.id or self.product_id.uom_id.id
        self.name = self.product_id.name
        
        # Récupérer le prix fournisseur si disponible
        seller = self.product_id._select_seller(
            partner_id=self.order_id.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order,
            uom_id=self.product_uom
        )
        
        if seller:
            self.price_unit = seller.price
        else:
            self.price_unit = self.product_id.standard_price
        
        # Récupérer les taxes
        self.taxes_id = self.product_id.supplier_taxes_id
        
        # Lier à l'article E-GESTOCK si disponible
        e_gestock_article = self.env['e_gestock.article'].search([
            ('product_id', '=', self.product_id.id)
        ], limit=1)
        
        if e_gestock_article:
            self.e_gestock_article_id = e_gestock_article.id
    
    def _prepare_stock_move_vals(self):
        """Prépare les valeurs pour créer un mouvement de stock"""
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.product_qty,
            'date': self.order_id.date_planned or fields.Datetime.now(),
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.order_id.picking_type_id.default_location_dest_id.id or self.env.ref('stock.stock_location_stock').id,
            'partner_id': self.order_id.partner_id.id,
            'state': 'draft',
            'purchase_line_id': self.id,
            'origin': self.order_id.name,
            'company_id': self.order_id.company_id.id,
        }
