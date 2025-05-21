# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Categorie(models.Model):
    _name = 'e_gestock.categorie'
    _description = 'Catégorie d\'articles'
    _order = 'code'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
        help="Nom de la catégorie"
    )

    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        index=True,
        help="Code unique de la catégorie"
    )

    description = fields.Text(
        string='Description',
        tracking=True,
        help="Description détaillée de la catégorie"
    )

    article_ids = fields.One2many(
        'e_gestock.article',
        'categorie_id',
        string='Articles',
        help="Articles appartenant à cette catégorie"
    )

    article_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_article_count',
        store=True,
        help="Nombre d'articles dans cette catégorie"
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si cette catégorie est actuellement utilisable"
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Le code de catégorie doit être unique!')
    ]

    @api.depends('article_ids')
    def _compute_article_count(self):
        """Calcule le nombre d'articles dans cette catégorie"""
        for record in self:
            record.article_count = len(record.article_ids)

    @api.constrains('code')
    def _check_code_length(self):
        """Vérifie que le code a une longueur raisonnable"""
        for record in self:
            if record.code and len(record.code) > 10:
                raise ValidationError(_("Le code de catégorie ne doit pas dépasser 10 caractères!"))

    def name_get(self):
        """Affiche le code et le nom dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.code} - {record.name}" if record.code else record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par code ou par nom"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def action_view_articles(self):
        """Ouvre la vue des articles de cette catégorie"""
        self.ensure_one()
        return {
            'name': _('Articles'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.article',
            'view_mode': 'tree,form',
            'domain': [('categorie_id', '=', self.id)],
            'context': {'default_categorie_id': self.id},
        }