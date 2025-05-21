from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockItem(models.Model):
    _name = 'e_gestock.stock_item'
    _description = 'Article en stock'
    _rec_name = 'article_id'

    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite_disponible = fields.Float(string='Quantité disponible', digits='Product Unit of Measure')
    quantite_reservee = fields.Float(string='Quantité réservée', digits='Product Unit of Measure')
    quantite_virtuelle = fields.Float(string='Quantité virtuelle', compute='_compute_virtual_quantity', store=True)
    emplacement_id = fields.Many2one('stock.location', string='Emplacement',
                                    related='depot_id.location_id', store=True, readonly=True)
    last_inventory_date = fields.Datetime(string='Date du dernier inventaire')
    value = fields.Monetary(string='Valeur', compute='_compute_value', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    prix_unitaire = fields.Float(string='Prix unitaire moyen', compute='_compute_prix_unitaire', store=True)
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.code_unite')
    min_quantity = fields.Float(string='Quantité minimale', digits='Product Unit of Measure', default=0.0)
    max_quantity = fields.Float(string='Quantité maximale', digits='Product Unit of Measure', default=0.0)
    # Relation calculée pour les mouvements
    movement_ids = fields.Many2many('e_gestock.stock_movement_line', compute='_compute_movement_ids', string='Mouvements')
    product_id = fields.Many2one('product.product', string='Produit Odoo', related='article_id.product_id')

    _sql_constraints = [
        ('article_depot_uniq', 'unique(article_id, depot_id)', 'Un article ne peut être présent qu\'une fois par dépôt!')
    ]

    @api.depends('quantite_disponible', 'quantite_reservee')
    def _compute_virtual_quantity(self):
        for record in self:
            record.quantite_virtuelle = record.quantite_disponible - record.quantite_reservee

    @api.depends('quantite_disponible', 'prix_unitaire')
    def _compute_value(self):
        for record in self:
            record.value = record.quantite_disponible * record.prix_unitaire

    @api.depends('value', 'quantite_disponible')
    def _compute_prix_unitaire(self):
        for record in self:
            if record.quantite_disponible > 0:
                # Le prix unitaire pourrait être calculé à partir des mouvements passés ou des quants Odoo
                # Pour une implémentation simple, on utilise un champ calculé
                # Dans une implémentation réelle, ce prix serait mis à jour par les mouvements de stock
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', record.article_id.product_id.id),
                    ('location_id', '=', record.depot_id.location_id.id)
                ])
                total_value = sum(quant.value for quant in quants)
                total_quantity = sum(quant.quantity for quant in quants)

                if total_quantity > 0:
                    record.prix_unitaire = total_value / total_quantity
                else:
                    # Chercher le dernier prix connu pour cet article
                    last_move = self.env['e_gestock.stock_movement_line'].search([
                        ('article_id', '=', record.article_id.id),
                        ('prix_unitaire', '>', 0)
                    ], order='create_date desc', limit=1)

                    if last_move:
                        record.prix_unitaire = last_move.prix_unitaire
                    else:
                        # Si pas de mouvement antérieur, utiliser le prix standard du produit
                        record.prix_unitaire = record.article_id.product_id.standard_price
            else:
                record.prix_unitaire = 0.0

    @api.model
    def get_stock_quantity(self, article_id, depot_id):
        """Méthode utilisée par d'autres modules pour vérifier la disponibilité"""
        stock_item = self.search([('article_id', '=', article_id), ('depot_id', '=', depot_id)], limit=1)
        if stock_item:
            return stock_item.quantite_disponible
        return 0.0

    def action_view_movements(self):
        self.ensure_one()
        return {
            'name': _('Mouvements de stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.stock_movement_line',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.article_id.id),
                       '|',
                       ('movement_id.depot_source_id', '=', self.depot_id.id),
                       ('movement_id.depot_destination_id', '=', self.depot_id.id)],
        }

    def _compute_movement_ids(self):
        """Calcule les mouvements associés à cet article dans ce dépôt"""
        for record in self:
            # Rechercher les mouvements où cet article est impliqué dans ce dépôt
            movement_lines = self.env['e_gestock.stock_movement_line'].search([
                ('article_id', '=', record.article_id.id),
                '|',
                ('depot_source_id', '=', record.depot_id.id),
                ('depot_destination_id', '=', record.depot_id.id)
            ])
            record.movement_ids = movement_lines

    def action_update_from_odoo(self):
        """Mettre à jour les quantités depuis les quants Odoo"""
        for record in self:
            if not record.article_id.product_id or not record.depot_id.location_id:
                continue

            # Récupérer les quants Odoo
            quants = self.env['stock.quant'].search([
                ('product_id', '=', record.article_id.product_id.id),
                ('location_id', '=', record.depot_id.location_id.id)
            ])

            # Calculer la quantité totale
            quantity = sum(quant.quantity for quant in quants)

            # Mettre à jour la quantité
            record.quantite_disponible = quantity