from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SupplierArticle(models.Model):
    _name = 'e_gestock.supplier_article'
    _description = 'Article fourni par un fournisseur'
    _rec_name = 'display_name'

    supplier_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        required=True,
        ondelete='cascade',
        domain=[('supplier_rank', '>', 0)])
    article_id = fields.Many2one(
        'e_gestock.article',
        string='Article',
        required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Produit Odoo',
        related='article_id.product_id',
        store=True)
    display_name = fields.Char(
        string='Référence',
        compute='_compute_display_name',
        store=True)
    prix_unitaire = fields.Float(
        string='Prix unitaire',
        digits='Product Price')
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id.id)
    date_debut = fields.Date(
        string='Date début validité',
        default=fields.Date.context_today)
    date_fin = fields.Date(
        string='Date fin validité')
    delai_livraison = fields.Integer(
        string='Délai de livraison (jours)',
        default=1)
    quantite_min = fields.Float(
        string='Quantité minimale',
        digits='Product Unit of Measure',
        default=1.0)
    remise = fields.Float(
        string='Remise (%)',
        digits='Discount',
        default=0.0)
    remise_generale = fields.Float(
        string='Remise générale (%)',
        digits='Discount',
        related='supplier_id.e_gestock_remise_generale',
        readonly=True,
        store=True)
    tva = fields.Float(
        string='TVA (%)',
        digits='Product Price',
        default=lambda self: self.env.company.account_sale_tax_id.amount if self.env.company.account_sale_tax_id else 18.0)
    notes = fields.Text(string='Notes')
    is_preferred = fields.Boolean(
        string='Fournisseur préféré',
        default=False,
        help="Indique si ce fournisseur est le fournisseur préféré pour cet article")
    prix_ht = fields.Monetary(
        string='Prix HT',
        compute='_compute_prix_ht',
        store=True,
        currency_field='currency_id')
    prix_ttc = fields.Monetary(
        string='Prix TTC',
        compute='_compute_prix_ttc',
        store=True,
        currency_field='currency_id')
    last_purchase_date = fields.Date(
        string='Dernière date d\'achat',
        compute='_compute_purchase_info',
        store=True)
    last_purchase_price = fields.Monetary(
        string='Dernier prix d\'achat',
        compute='_compute_purchase_info',
        store=True,
        currency_field='currency_id')
    purchase_count = fields.Integer(
        string='Nombre d\'achats',
        compute='_compute_purchase_info',
        store=True)
    active = fields.Boolean(
        string='Actif',
        default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('supplier_article_uniq', 'unique(supplier_id, article_id, company_id)',
         'Un article ne peut être associé qu\'une seule fois à un fournisseur par société!')
    ]

    @api.depends('supplier_id', 'article_id')
    def _compute_display_name(self):
        for record in self:
            supplier_name = record.supplier_id.name or ''
            article_name = record.article_id.design_article or ''
            record.display_name = f"{supplier_name} - {article_name}" if supplier_name and article_name else ''

    @api.depends('prix_unitaire', 'remise', 'remise_generale')
    def _compute_prix_ht(self):
        for record in self:
            prix = record.prix_unitaire
            if record.remise:
                prix = prix * (1 - record.remise / 100)
            if record.remise_generale:
                prix = prix * (1 - record.remise_generale / 100)
            record.prix_ht = prix

    @api.depends('prix_ht', 'tva')
    def _compute_prix_ttc(self):
        for record in self:
            record.prix_ttc = record.prix_ht * (1 + record.tva / 100)

    def _compute_purchase_info(self):
        """Calcule les informations d'achat depuis l'historique"""
        PurchaseLine = self.env['purchase.order.line']
        for record in self:
            # Chercher les lignes d'achat pour ce fournisseur et cet article
            domain = [
                ('partner_id', '=', record.supplier_id.id),
                ('product_id', '=', record.product_id.id),
                ('state', 'in', ['purchase', 'done'])
            ]
            lines = PurchaseLine.search(domain, order='date_order desc')
            record.purchase_count = len(lines)

            if lines:
                record.last_purchase_date = lines[0].order_id.date_order.date()
                record.last_purchase_price = lines[0].price_unit
            else:
                record.last_purchase_date = False
                record.last_purchase_price = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('is_preferred'):
                # Désactiver le statut préféré des autres fournisseurs pour cet article
                self.search([
                    ('article_id', '=', vals.get('article_id')),
                    ('is_preferred', '=', True)
                ]).write({'is_preferred': False})
        return super(SupplierArticle, self).create(vals_list)

    def write(self, vals):
        res = super(SupplierArticle, self).write(vals)
        if 'is_preferred' in vals and vals['is_preferred']:
            # Désactiver le statut préféré des autres fournisseurs pour le même article
            for record in self:
                self.search([
                    ('article_id', '=', record.article_id.id),
                    ('id', '!=', record.id),
                    ('is_preferred', '=', True)
                ]).write({'is_preferred': False})
        return res