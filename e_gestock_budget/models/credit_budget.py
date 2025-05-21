from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CreditBudget(models.Model):
    _name = 'e_gestock.credit_budget'
    _description = 'Crédit budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reference = fields.Char(string='Référence', readonly=True, default='Nouveau')
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    structure_display = fields.Char(string='Structure', compute='_compute_display_names', store=True)

    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True,
                                domain="[('code_structure', '=', structure_id)]")
    section_display = fields.Char(string='Section', compute='_compute_display_names', store=True)

    famille_id = fields.Many2one('e_gestock.famille', string='Famille (Compte budgétaire)', required=True, tracking=True,
                                domain="[('budgetary_account', '=', True)]")
    famille_display = fields.Char(string='Famille', compute='_compute_display_names', store=True)

    type_gestion_id = fields.Many2one('e_gestock.type_gestion', string='Type de gestion', tracking=True)
    type_gestion_display = fields.Char(string='Type de gestion', compute='_compute_display_names', store=True)
    exercise_id = fields.Many2one('e_gestock.exercise', string='Exercice budgétaire', required=True, tracking=True,
                                 domain=[('state', '=', 'open')])
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, tracking=True)
    montant_alloue = fields.Monetary(string='Montant alloué', required=True, tracking=True)
    montant_engage = fields.Monetary(string='Montant engagé', default=0.0, tracking=True)
    montant_consomme = fields.Monetary(string='Montant consommé', default=0.0, tracking=True)
    montant_disponible = fields.Monetary(string='Montant disponible', compute='_compute_montant_disponible', store=True)
    threshold_percentage = fields.Float(string='Seuil d\'alerte (%)', default=80.0)
    is_below_threshold = fields.Boolean(string='Sous le seuil', compute='_compute_is_below_threshold', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    operation_ids = fields.One2many('e_gestock.operation_budget', 'credit_id', string='Opérations')
    date_creation = fields.Date(string='Date de création', default=fields.Date.context_today, readonly=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user, readonly=True)
    active = fields.Boolean(string='Archivé', default=True)

    _sql_constraints = [
        ('struct_fam_exer_depot_uniq', 'unique(structure_id, famille_id, exercise_id, type_gestion_id, depot_id)',
         'Un crédit budgétaire doit être unique par structure, famille, exercice, type de gestion et dépôt!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.credit_budget') or 'Nouveau'
        records = super(CreditBudget, self).create(vals_list)
        # Créer l'opération budgétaire d'allocation initiale
        for record in records:
            self.env['e_gestock.operation_budget'].create({
                'credit_id': record.id,
                'date': fields.Datetime.now(),
                'montant': record.montant_alloue,
                'type': 'allocation',
                'origine': 'init',
                'user_id': self.env.user.id,
                'notes': 'Allocation initiale'
            })
        return records

    def write(self, vals):
        if 'montant_alloue' in vals:
            old_montant = self.montant_alloue
            new_montant = vals['montant_alloue']
            result = super(CreditBudget, self).write(vals)
            # Créer une opération d'ajustement
            if old_montant != new_montant:
                for record in self:
                    self.env['e_gestock.operation_budget'].create({
                        'credit_id': record.id,
                        'date': fields.Datetime.now(),
                        'montant': new_montant - old_montant,
                        'type': 'ajustement',
                        'origine': 'manuel',
                        'user_id': self.env.user.id,
                        'notes': 'Ajustement du montant alloué'
                    })
            return result
        return super(CreditBudget, self).write(vals)

    @api.depends('montant_alloue', 'montant_engage', 'montant_consomme')
    def _compute_montant_disponible(self):
        for credit in self:
            credit.montant_disponible = credit.montant_alloue - credit.montant_engage

    @api.depends('montant_disponible', 'montant_alloue', 'threshold_percentage')
    def _compute_is_below_threshold(self):
        for credit in self:
            if credit.montant_alloue > 0:
                ratio = (credit.montant_disponible / credit.montant_alloue) * 100
                credit.is_below_threshold = ratio < (100 - credit.threshold_percentage)
            else:
                credit.is_below_threshold = True

    @api.onchange('structure_id')
    def _onchange_structure_id(self):
        self.section_id = False
        # Mettre à jour le domaine du champ section_id
        if self.structure_id:
            return {'domain': {'section_id': [('code_structure', '=', self.structure_id.id)]}}

    @api.depends('structure_id', 'section_id', 'famille_id', 'type_gestion_id')
    def _compute_display_names(self):
        for record in self:
            # Structure
            if record.structure_id:
                record.structure_display = f"{record.structure_id.code_structure} - {record.structure_id.nom_structure}"
            else:
                record.structure_display = False

            # Section
            if record.section_id:
                record.section_display = f"{record.section_id.code_section} - {record.section_id.nom_section}"
            else:
                record.section_display = False

            # Famille
            if record.famille_id:
                record.famille_display = f"{record.famille_id.ref_fam} - {record.famille_id.design_fam}"
            else:
                record.famille_display = False

            # Type de gestion
            if record.type_gestion_id:
                record.type_gestion_display = f"{record.type_gestion_id.code_gestion} - {record.type_gestion_id.libelle_gestion}"
            else:
                record.type_gestion_display = False

    def name_get(self):
        result = []
        for credit in self:
            name = credit.reference or ""
            if credit.famille_id and credit.exercise_id:
                name = f"{name} - {credit.famille_id.design_fam} ({credit.exercise_id.code})"
            result.append((credit.id, name))
        return result