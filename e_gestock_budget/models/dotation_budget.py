from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DotationBudget(models.Model):
    _name = 'e_gestock.dotation_budget'
    _description = 'Dotation budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reference = fields.Char(string='Référence', readonly=True, default='Nouveau')
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, tracking=True)
    famille_id = fields.Many2one('e_gestock.famille', string='Famille', required=True, tracking=True)
    exercise_id = fields.Many2one('e_gestock.exercise', string='Exercice budgétaire', required=True, tracking=True)
    montant_dotation = fields.Monetary(string='Montant dotation', required=True, tracking=True)
    montant_consomme = fields.Monetary(string='Montant consommé', default=0.0, tracking=True)
    montant_disponible = fields.Monetary(string='Montant disponible', compute='_compute_montant_disponible', store=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    date_creation = fields.Date(string='Date de création', default=fields.Date.context_today, readonly=True)
    active = fields.Boolean(string='Archivé', default=True)

    _sql_constraints = [
        ('depot_famille_exercise_uniq', 'unique(depot_id, famille_id, exercise_id)',
         'Une dotation budgétaire doit être unique par dépôt, famille et exercice!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.dotation_budget') or 'Nouveau'
        return super(DotationBudget, self).create(vals_list)

    @api.depends('montant_dotation', 'montant_consomme')
    def _compute_montant_disponible(self):
        for dotation in self:
            dotation.montant_disponible = dotation.montant_dotation - dotation.montant_consomme

    @api.constrains('montant_consomme', 'montant_dotation')
    def _check_montant_consomme(self):
        for dotation in self:
            if dotation.montant_consomme > dotation.montant_dotation:
                raise ValidationError(_("Le montant consommé ne peut pas dépasser le montant de la dotation!"))

    def name_get(self):
        result = []
        for dotation in self:
            name = dotation.reference or ""
            if dotation.famille_id and dotation.depot_id:
                name = f"{name} - {dotation.famille_id.design_fam} ({dotation.depot_id.design_dep})"
            result.append((dotation.id, name))
        return result