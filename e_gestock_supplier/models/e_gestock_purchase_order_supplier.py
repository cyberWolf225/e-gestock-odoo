from odoo import api, fields, models, _


class EgestockPurchaseOrderSupplier(models.Model):
    _inherit = 'e_gestock.purchase_order'

    e_gestock_contract_id = fields.Many2one(
        'e_gestock.supplier_contract',
        string='Contrat fournisseur',
        help="Contrat fournisseur associé à cette commande"
    )

    e_gestock_supplier_article_ids = fields.One2many(
        'e_gestock.supplier_article',
        compute='_compute_supplier_articles',
        string='Articles fournisseur'
    )

    has_preferred_supplier = fields.Boolean(
        string='Contient un fournisseur préféré',
        compute='_compute_has_preferred_supplier',
        store=True
    )

    @api.depends('partner_id')
    def _compute_supplier_articles(self):
        """Calcule les articles disponibles pour ce fournisseur"""
        for order in self:
            if order.partner_id:
                order.e_gestock_supplier_article_ids = self.env['e_gestock.supplier_article'].search([
                    ('supplier_id', '=', order.partner_id.id),
                    ('active', '=', True)
                ])
            else:
                order.e_gestock_supplier_article_ids = False

    @api.depends('order_line.supplier_article_id', 'order_line.is_preferred_supplier')
    def _compute_has_preferred_supplier(self):
        """Calcule si la commande contient des articles de fournisseurs préférés"""
        for order in self:
            order.has_preferred_supplier = False
            if hasattr(order.order_line, 'is_preferred_supplier'):
                order.has_preferred_supplier = any(line.is_preferred_supplier for line in order.order_line)

    def button_confirm(self):
        """Surcharge de la confirmation pour mettre à jour les statistiques d'achat"""
        res = super(EgestockPurchaseOrderSupplier, self).button_confirm()

        for order in self:
            # Mise à jour des statistiques d'achat pour les articles fournisseurs
            for line in order.order_line:
                if hasattr(line, 'supplier_article_id') and line.supplier_article_id:
                    line.supplier_article_id.write({
                        'last_purchase_date': fields.Date.today(),
                        'last_purchase_price': line.price_unit,
                        'total_purchased_quantity': line.supplier_article_id.total_purchased_quantity + line.product_qty,
                        'total_purchase_amount': line.supplier_article_id.total_purchase_amount + line.price_subtotal
                    })

            # Mise à jour des statistiques du fournisseur
            if order.partner_id:
                # Calculer le nombre total de commandes
                purchase_count = self.env['e_gestock.purchase_order'].search_count([
                    ('partner_id', '=', order.partner_id.id),
                    ('state', 'in', ['approved', 'withdrawn', 'delivered', 'received'])
                ])

                # Calculer le montant total des achats
                purchase_orders = self.env['e_gestock.purchase_order'].search([
                    ('partner_id', '=', order.partner_id.id),
                    ('state', 'in', ['approved', 'withdrawn', 'delivered', 'received'])
                ])
                total_amount = sum(po.amount_total for po in purchase_orders)

                # Mettre à jour les statistiques du fournisseur
                if hasattr(order.partner_id, 'e_gestock_purchase_count'):
                    order.partner_id.write({
                        'e_gestock_purchase_count': purchase_count,
                        'e_gestock_purchase_amount': total_amount,
                        'e_gestock_last_purchase_date': fields.Date.today()
                    })

        return res


class EgestockPurchaseOrderLineSupplier(models.Model):
    _inherit = 'e_gestock.purchase_order_line'

    supplier_article_id = fields.Many2one(
        'e_gestock.supplier_article',
        string='Article fournisseur',
        domain="[('supplier_id', '=', parent.partner_id), ('active', '=', True)]"
    )

    is_preferred_supplier = fields.Boolean(
        string='Fournisseur préféré',
        related='supplier_article_id.is_preferred',
        store=True,
        readonly=True
    )

    @api.onchange('supplier_article_id')
    def _onchange_supplier_article_id(self):
        """Met à jour les informations de l'article lorsque l'article fournisseur change"""
        if self.supplier_article_id:
            self.product_id = self.supplier_article_id.product_id
            self.name = self.supplier_article_id.name or self.product_id.name
            self.price_unit = self.supplier_article_id.list_price
            self.product_uom = self.supplier_article_id.product_id.uom_po_id or self.supplier_article_id.product_id.uom_id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Met à jour l'article fournisseur lorsque le produit change"""
        res = super(EgestockPurchaseOrderLineSupplier, self)._onchange_product_id() if hasattr(super(), '_onchange_product_id') else None

        if self.product_id and self.order_id.partner_id:
            # Rechercher un article fournisseur correspondant
            supplier_article = self.env['e_gestock.supplier_article'].search([
                ('supplier_id', '=', self.order_id.partner_id.id),
                ('product_id', '=', self.product_id.id),
                ('active', '=', True)
            ], limit=1)

            if supplier_article:
                self.supplier_article_id = supplier_article.id
                self.price_unit = supplier_article.list_price

        return res
