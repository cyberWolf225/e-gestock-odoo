from odoo import models, fields, api, _

class StockMovementLine(models.Model):
    _name = 'e_gestock.stock_movement_line'
    _description = 'Ligne de mouvement de stock'
    _rec_name = 'article_id'
    
    movement_id = fields.Many2one('e_gestock.stock_movement', string='Mouvement', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.code_unite', store=True)
    prix_unitaire = fields.Float(string='Prix unitaire')
    montant_total = fields.Monetary(string='Montant total', compute='_compute_montant_total', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', related='movement_id.currency_id', store=True)
    stock_move_id = fields.Many2one('stock.move', string='Mouvement Odoo')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Numéro de série')
    date_peremption = fields.Date(string='Date de péremption')
    product_id = fields.Many2one('product.product', string='Produit Odoo', related='article_id.product_id', store=True)
    depot_source_id = fields.Many2one('e_gestock.depot', string='Dépôt source', related='movement_id.depot_source_id', store=True)
    depot_destination_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', related='movement_id.depot_destination_id', store=True)
    movement_type = fields.Selection(related='movement_id.type', string='Type de mouvement', store=True)
    state = fields.Selection(related='movement_id.state', string='État', store=True)
    date = fields.Datetime(related='movement_id.date', string='Date', store=True)
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant_total(self):
        for line in self:
            line.montant_total = line.quantite * line.prix_unitaire
    
    @api.onchange('article_id')
    def _onchange_article_id(self):
        if self.article_id and self.movement_id.type in ('out', 'transfer'):
            # Récupérer le prix moyen de l'article dans le dépôt source
            stock_item = self.env['e_gestock.stock_item'].search([
                ('article_id', '=', self.article_id.id),
                ('depot_id', '=', self.movement_id.depot_source_id.id)
            ], limit=1)
            if stock_item and stock_item.quantite_disponible > 0 and stock_item.prix_unitaire > 0:
                self.prix_unitaire = stock_item.prix_unitaire
            else:
                # Si pas d'information de prix dans le stock, utiliser le prix standard du produit
                self.prix_unitaire = self.article_id.product_id.standard_price
        elif self.article_id and self.movement_id.type == 'in':
            # Pour les entrées, utiliser le prix standard du produit comme prix par défaut
            self.prix_unitaire = self.article_id.product_id.standard_price 