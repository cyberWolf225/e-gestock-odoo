from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SupplierCategory(models.Model):
    _name = 'e_gestock.supplier_category'
    _description = 'Catégorie de fournisseur'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Nom', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    complete_name = fields.Char(
        string='Nom complet',
        compute='_compute_complete_name',
        recursive=True,
        store=True)
    parent_id = fields.Many2one(
        'e_gestock.supplier_category',
        string='Catégorie parente',
        index=True,
        ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'e_gestock.supplier_category',
        'parent_id',
        string='Sous-catégories')
    note = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    partner_ids = fields.One2many(
        'res.partner',
        'e_gestock_supplier_category_id',
        string='Fournisseurs')
    partner_count = fields.Integer(
        string='Nombre de fournisseurs',
        compute='_compute_partner_count',
        store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('code_uniq', 'unique (code, company_id)', 'Le code doit être unique par société !')
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for category in self:
            category.partner_count = len(category.partner_ids)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_('Vous ne pouvez pas créer de catégories récursives.'))

    def name_get(self):
        return [(category.id, category.complete_name) for category in self]