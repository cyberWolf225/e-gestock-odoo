from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Exercise(models.Model):
    _name = 'e_gestock.exercise'
    _description = 'Exercice budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', required=True, tracking=True)
    name = fields.Char(string='Nom', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', required=True, tracking=True)
    state = fields.Selection([
        ('open', 'Ouvert'),
        ('closed', 'Fermé')
    ], string='État', default='open', tracking=True)
    is_active = fields.Boolean(string='Actif', default=False, tracking=True)
    active = fields.Boolean(string='Archivé', default=True)
    notes = fields.Text(string='Notes')
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    credit_ids = fields.One2many('e_gestock.credit_budget', 'exercise_id', string='Crédits budgétaires')
    dotation_ids = fields.One2many('e_gestock.dotation_budget', 'exercise_id', string='Dotations')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code de l\'exercice doit être unique!')
    ]

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for exercise in self:
            if exercise.date_fin <= exercise.date_debut:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début!"))

    @api.constrains('is_active')
    def _check_active_unique(self):
        for exercise in self:
            if exercise.is_active:
                other_active = self.search([('is_active', '=', True), ('id', '!=', exercise.id)])
                if other_active:
                    raise ValidationError(_("Un seul exercice peut être actif à la fois!"))

    def action_close(self):
        self.ensure_one()
        return self.write({'state': 'closed'})

    def action_open(self):
        self.ensure_one()
        return self.write({'state': 'open'})

    def action_activate(self):
        self.ensure_one()
        if self.state == 'closed':
            raise ValidationError(_("Impossible d'activer un exercice fermé!"))
        # Désactiver les autres exercices actifs
        other_active = self.search([('is_active', '=', True), ('id', '!=', self.id)])
        other_active.write({'is_active': False})
        # Activer cet exercice
        return self.write({'is_active': True})

    def name_get(self):
        result = []
        for exercise in self:
            name = exercise.code
            if exercise.name:
                name = f'{name} - {exercise.name}'
            result.append((exercise.id, name))
        return result