from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BudgetControl(models.Model):
    _name = 'e_gestock.budget_control'
    _description = 'Contrôle budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande d\'achat')
    # Le champ purchase_order_id est défini dans le module e_gestock_budget_purchase_bridge
    credit_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', required=True)
    montant = fields.Monetary(string='Montant', compute='_compute_montant', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    controleur_id = fields.Many2one('res.users', string='Contrôleur budgétaire',
                                   domain=[('groups_id', 'in', [lambda self: self.env.ref('e_gestock_base.group_budget_controller').id])])
    state = fields.Selection([
        ('draft', 'À contrôler'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('derogation', 'Dérogation')
    ], string='État', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    operation_id = fields.Many2one('e_gestock.operation_budget', string='Opération budgétaire')

    @api.depends('demande_id')
    def _compute_montant(self):
        for record in self:
            if record.demande_id:
                record.montant = record.demande_id.montant_total
            else:
                record.montant = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.budget_control') or 'Nouveau'
        return super(BudgetControl, self).create(vals_list)

    def action_approve(self):
        self.ensure_one()
        # Vérifier la disponibilité budgétaire
        if self.credit_id.montant_disponible < self.montant:
            raise ValidationError(_("Budget insuffisant! Le montant disponible est de %s %s.") %
                                (self.credit_id.montant_disponible, self.currency_id.symbol))

        self.state = 'approved'

        # Déterminer l'origine et la référence
        origine = 'demande_achat'
        ref_origine = self.demande_id.reference if self.demande_id else ''

        # Création de l'opération budgétaire d'engagement
        operation = self.env['e_gestock.operation_budget'].create({
            'credit_id': self.credit_id.id,
            'date': fields.Datetime.now(),
            'montant': self.montant,
            'type': 'engagement',
            'origine': origine,
            'ref_origine': ref_origine,
            'user_id': self.env.user.id,
            'validateur_id': self.controleur_id.id,
            'etape_validation': 'budget',
            'notes': self.notes
        })
        self.operation_id = operation.id

        # Mise à jour de l'état de la demande
        if self.demande_id and hasattr(self.demande_id, 'state'):
            self.demande_id.write({'state': 'budget_checked'})

    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'

        # Mise à jour de l'état de la demande
        if self.demande_id and hasattr(self.demande_id, 'state'):
            self.demande_id.write({'state': 'budget_rejected'})

        # La mise à jour de l'état du bon de commande est gérée dans le module e_gestock_budget_purchase_bridge

    def action_derogation(self):
        self.ensure_one()
        self.state = 'derogation'

        # Mise à jour de l'état de la demande
        if self.demande_id and hasattr(self.demande_id, 'state'):
            self.demande_id.write({'state': 'budget_derogation'})

        # La mise à jour de l'état du bon de commande est gérée dans le module e_gestock_budget_purchase_bridge

        # Workflow de dérogation spécifique
        # À implémenter selon les besoins