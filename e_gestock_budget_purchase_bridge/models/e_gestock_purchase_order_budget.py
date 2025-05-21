from odoo import models, fields, api, _


class EgestockPurchaseOrderBudget(models.Model):
    _inherit = 'e_gestock.purchase_order'

    # Champs pour le suivi budgétaire
    budget_control_id = fields.Many2one('e_gestock.budget_control', string='Contrôle budgétaire')
    budget_state = fields.Selection([
        ('not_checked', 'Non vérifié'),
        ('checked', 'Vérifié'),
        ('insufficient', 'Insuffisant'),
        ('pending_derogation', 'Dérogation en attente'),
        ('derogation_approved', 'Dérogation approuvée'),
        ('rejected', 'Rejeté')
    ], string='Statut budget', compute='_compute_budget_state', store=True)
    budget_operation_id = fields.Many2one('e_gestock.operation_budget', string='Opération budget')

    # Champs pour le contrôle budgétaire
    credit_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', compute='_compute_credit_budget')
    montant_budget_disponible = fields.Monetary(string='Budget disponible', compute='_compute_credit_budget')
    est_budget_suffisant = fields.Boolean(string='Budget suffisant', compute='_compute_credit_budget')

    @api.depends('budget_control_id', 'budget_control_id.state')
    def _compute_budget_state(self):
        """Calcule l'état du budget en fonction du contrôle budgétaire"""
        for order in self:
            if not order.budget_control_id:
                order.budget_state = 'not_checked'
            elif order.budget_control_id.state == 'approved':
                order.budget_state = 'checked'
            elif order.budget_control_id.state == 'rejected':
                order.budget_state = 'rejected'
            elif order.budget_control_id.state == 'derogation':
                if order.budget_control_id.derogation_approuvee:
                    order.budget_state = 'derogation_approved'
                else:
                    order.budget_state = 'pending_derogation'
            else:
                order.budget_state = 'not_checked'

    @api.depends('structure_id', 'famille_id', 'amount_total')
    def _compute_credit_budget(self):
        """Calcule le crédit budgétaire associé et la disponibilité"""
        for order in self:
            # Rechercher un crédit budgétaire pour la structure, la section et la famille
            if hasattr(order, 'structure_id') and hasattr(order, 'famille_id'):
                credit = self.env['e_gestock.credit_budget'].search([
                    ('structure_id', '=', order.structure_id.id),
                    ('famille_id', '=', order.famille_id.id),
                    ('exercise_id.is_active', '=', True)
                ], limit=1)

                if not credit and hasattr(order, 'section_id'):
                    # Rechercher un crédit budgétaire avec section
                    credit = self.env['e_gestock.credit_budget'].search([
                        ('structure_id', '=', order.structure_id.id),
                        ('section_id', '=', order.section_id.id),
                        ('famille_id', '=', order.famille_id.id),
                        ('exercise_id.is_active', '=', True)
                    ], limit=1)

                if credit:
                    order.credit_id = credit.id
                    order.montant_budget_disponible = credit.montant_disponible
                    order.est_budget_suffisant = credit.montant_disponible >= order.amount_total
                else:
                    order.credit_id = False
                    order.montant_budget_disponible = 0
                    order.est_budget_suffisant = False
            else:
                order.credit_id = False
                order.montant_budget_disponible = 0
                order.est_budget_suffisant = False

    def button_confirm(self):
        """Surcharge de la confirmation pour enregistrer la consommation budgétaire"""
        res = super(EgestockPurchaseOrderBudget, self).button_confirm()

        for order in self:
            # Si la commande est liée à un contrôle budgétaire
            if order.budget_control_id and order.budget_control_id.state == 'approved':
                # Créer une opération de consommation budgétaire
                operation = self.env['e_gestock.operation_budget'].create({
                    'credit_id': order.budget_control_id.credit_id.id,
                    'type': 'engagement',
                    'montant': order.amount_total,
                    'date_operation': fields.Date.today(),
                    'purchase_order_id': order.id,
                    'description': _('Engagement pour bon de commande %s') % order.name,
                })

                if operation:
                    order.budget_operation_id = operation.id

        return res
