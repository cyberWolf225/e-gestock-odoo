from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Depot(models.Model):
    _inherit = 'e_gestock.depot'

    warehouse_id = fields.Many2one('stock.warehouse', string='Entrepôt Odoo', ondelete='restrict')
    location_id = fields.Many2one('stock.location', string='Emplacement principal', ondelete='restrict')
    input_location_id = fields.Many2one('stock.location', string='Emplacement d\'entrée')
    output_location_id = fields.Many2one('stock.location', string='Emplacement de sortie')
    quality_location_id = fields.Many2one('stock.location', string='Emplacement de contrôle qualité')
    stock_rule_ids = fields.One2many('stock.rule', 'warehouse_id', string='Règles de stock', compute='_compute_stock_rules')
    stock_item_ids = fields.One2many('e_gestock.stock_item', 'depot_id', string='Articles en stock')
    total_stock_value = fields.Monetary(string='Valeur totale du stock', compute='_compute_total_stock_value')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    stock_movement_count = fields.Integer(string='Nombre de mouvements', compute='_compute_movement_count')
    inventory_count = fields.Integer(string='Nombre d\'inventaires', compute='_compute_inventory_count')

    @api.model_create_multi
    def create(self, vals_list):
        # Création automatique de l'entrepôt Odoo correspondant
        depots = super(Depot, self).create(vals_list)
        for depot in depots:
            if not depot.warehouse_id:
                warehouse_vals = {
                    'name': depot.design_dep,
                    'code': depot.ref_depot,
                    'partner_id': self.env.company.partner_id.id,
                }
                warehouse = self.env['stock.warehouse'].create(warehouse_vals)
                depot.write({
                    'warehouse_id': warehouse.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'input_location_id': warehouse.wh_input_stock_loc_id.id,
                    'output_location_id': warehouse.wh_output_stock_loc_id.id
                })

                # Création d'un emplacement de contrôle qualité
                quality_location = self.env['stock.location'].create({
                    'name': _('Contrôle qualité'),
                    'location_id': warehouse.view_location_id.id,
                    'usage': 'internal',
                    'company_id': self.env.company.id
                })
                depot.quality_location_id = quality_location.id
        return depots

    def _compute_stock_rules(self):
        for depot in self:
            if depot.warehouse_id:
                depot.stock_rule_ids = self.env['stock.rule'].search([('warehouse_id', '=', depot.warehouse_id.id)])
            else:
                depot.stock_rule_ids = False

    def _compute_total_stock_value(self):
        for depot in self:
            total = sum(item.value for item in depot.stock_item_ids)
            depot.total_stock_value = total

    def _compute_movement_count(self):
        for depot in self:
            source_count = self.env['e_gestock.stock_movement'].search_count([
                ('depot_source_id', '=', depot.id)
            ])
            dest_count = self.env['e_gestock.stock_movement'].search_count([
                ('depot_destination_id', '=', depot.id)
            ])
            depot.stock_movement_count = source_count + dest_count

    def _compute_inventory_count(self):
        for depot in self:
            depot.inventory_count = self.env['e_gestock.inventory'].search_count([
                ('depot_id', '=', depot.id)
            ])

    def action_view_warehouse(self):
        self.ensure_one()
        if not self.warehouse_id:
            return

        return {
            'name': _('Entrepôt'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse',
            'view_mode': 'form',
            'res_id': self.warehouse_id.id,
        }

    def action_view_stock_items(self):
        self.ensure_one()
        return {
            'name': _('Articles en stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.stock_item',
            'view_mode': 'tree,form',
            'domain': [('depot_id', '=', self.id)],
            'context': {'default_depot_id': self.id},
        }

    def action_view_movements(self):
        self.ensure_one()
        return {
            'name': _('Mouvements de stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.stock_movement',
            'view_mode': 'tree,form',
            'domain': ['|', ('depot_source_id', '=', self.id), ('depot_destination_id', '=', self.id)],
            'context': {'default_depot_source_id': self.id}
        }

    def action_view_inventories(self):
        self.ensure_one()
        return {
            'name': _('Inventaires'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.inventory',
            'view_mode': 'tree,form',
            'domain': [('depot_id', '=', self.id)],
            'context': {'default_depot_id': self.id}
        }