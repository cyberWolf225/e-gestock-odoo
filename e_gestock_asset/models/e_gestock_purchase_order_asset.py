from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EgestockPurchaseOrderAsset(models.Model):
    _inherit = 'e_gestock.purchase_order'

    # Champs pour les immobilisations
    is_asset_purchase = fields.Boolean(
        string='Achat d\'immobilisations',
        help="Cochez cette case si cette commande concerne des immobilisations"
    )

    asset_ids = fields.One2many(
        'e_gestock.asset',
        'purchase_order_id',
        string='Immobilisations',
        help="Immobilisations créées à partir de cette commande"
    )

    asset_count = fields.Integer(
        string='Nombre d\'immobilisations',
        compute='_compute_asset_count'
    )

    @api.depends('asset_ids')
    def _compute_asset_count(self):
        """Calcule le nombre d'immobilisations liées à cette commande"""
        for order in self:
            order.asset_count = len(order.asset_ids)

    def action_view_assets(self):
        """Affiche les immobilisations liées à cette commande"""
        self.ensure_one()

        action = {
            'name': _('Immobilisations'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset',
            'view_mode': 'list,form',
            'domain': [('purchase_order_id', '=', self.id)],
            'context': {'default_purchase_order_id': self.id},
        }

        if len(self.asset_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.asset_ids[0].id,
            })

        return action

    def action_create_assets(self):
        """Crée des immobilisations à partir des lignes de commande"""
        self.ensure_one()

        if not self.is_asset_purchase:
            raise UserError(_("Cette commande n'est pas marquée comme un achat d'immobilisations."))

        if self.state_approbation != 'received':
            raise UserError(_("Vous ne pouvez créer des immobilisations qu'à partir d'une commande réceptionnée."))

        # Vérifier si des immobilisations existent déjà
        if self.asset_ids:
            return self.action_view_assets()

        # Créer les immobilisations pour chaque ligne de commande
        assets_created = False
        for line in self.order_line:
            if line.product_id and line.product_id.type == 'product' and line.qty_received > 0:
                # Vérifier si le produit est une immobilisation
                asset_type = self.env['e_gestock.asset_type'].search([
                    ('product_id', '=', line.product_id.id)
                ], limit=1)

                if not asset_type:
                    continue

                # Créer une immobilisation pour chaque unité reçue
                for i in range(int(line.qty_received)):
                    asset_vals = {
                        'name': f"{line.product_id.name} ({self.name})",
                        'code': self.env['ir.sequence'].next_by_code('e_gestock.asset'),
                        'purchase_order_id': self.id,
                        'purchase_date': self.date_order,
                        'acquisition_date': fields.Date.today(),
                        'acquisition_value': line.price_unit,
                        'asset_type_id': asset_type.id,
                        'product_id': line.product_id.id,
                        'structure_id': self.structure_id.id if hasattr(self, 'structure_id') else False,
                        'section_id': self.section_id.id if hasattr(self, 'section_id') else False,
                        'state': 'draft',
                    }

                    self.env['e_gestock.asset'].create(asset_vals)
                    assets_created = True

        if not assets_created:
            raise UserError(_("Aucune immobilisation n'a pu être créée. Vérifiez que les produits sont bien définis comme des immobilisations."))

        # Marquer la commande comme un achat d'immobilisations
        self.is_asset_purchase = True

        return self.action_view_assets()


class EgestockPurchaseOrderLineAsset(models.Model):
    _inherit = 'e_gestock.purchase_order_line'

    is_asset = fields.Boolean(
        string='Est une immobilisation',
        compute='_compute_is_asset',
        store=True
    )

    @api.depends('product_id')
    def _compute_is_asset(self):
        """Détermine si le produit est une immobilisation"""
        for line in self:
            if line.product_id:
                asset_type = self.env['e_gestock.asset_type'].search([
                    ('product_id', '=', line.product_id.id)
                ], limit=1)

                line.is_asset = bool(asset_type)

                # Si c'est une immobilisation, suggérer de marquer la commande comme achat d'immobilisations
                if line.is_asset and line.order_id and not line.order_id.is_asset_purchase:
                    line.order_id.is_asset_purchase = True
            else:
                line.is_asset = False
