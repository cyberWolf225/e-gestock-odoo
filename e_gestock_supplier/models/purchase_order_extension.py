# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    supplier_article_id = fields.Many2one(
        'e_gestock.supplier_article',
        string='Article fournisseur E-GESTOCK',
        domain="[('supplier_id', '=', parent.partner_id), ('active', '=', True)]"
    )
    
    @api.onchange('supplier_article_id')
    def _onchange_supplier_article_id(self):
        """Met à jour les informations de la ligne de commande en fonction de l'article fournisseur sélectionné"""
        if self.supplier_article_id:
            self.product_id = self.supplier_article_id.product_id
            self.price_unit = self.supplier_article_id.prix_ht
            self.date_planned = fields.Datetime.now() + fields.Timedelta(days=self.supplier_article_id.delai_livraison or 0)
