from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EgestockPurchaseOrderBudget(models.Model):
    _inherit = 'e_gestock.purchase_order'
    
    # Champs pour le suivi budgétaire
    budget_control_id = fields.Many2one('e_gestock_budget.budget_control', string='Contrôle budgétaire')
    budget_state = fields.Selection([
        ('not_checked', 'Non vérifié'),
        ('checked', 'Vérifié'),
        ('insufficient', 'Insuffisant'),
        ('pending_derogation', 'Dérogation en attente'),
        ('derogation_approved', 'Dérogation approuvée'),
        ('rejected', 'Rejeté')
    ], string='Statut budget', compute='_compute_budget_state', store=True)
    budget_operation_id = fields.Many2one('e_gestock_budget.operation_budget', string='Opération budget')
    
    # Champs pour le contrôle budgétaire
    credit_id = fields.Many2one('e_gestock_budget.credit_budget', string='Crédit budgétaire', compute='_compute_credit_budget')
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
                credit = self.env['e_gestock_budget.credit_budget'].search([
                    ('structure_id', '=', order.structure_id.id),
                    ('famille_id', '=', order.famille_id.id),
                    ('exercice_id.is_active', '=', True)
                ], limit=1)
                
                if not credit and hasattr(order, 'section_id'):
                    # Rechercher un crédit budgétaire avec section
                    credit = self.env['e_gestock_budget.credit_budget'].search([
                        ('structure_id', '=', order.structure_id.id),
                        ('section_id', '=', order.section_id.id),
                        ('famille_id', '=', order.famille_id.id),
                        ('exercice_id.is_active', '=', True)
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
    
    def action_check_budget(self):
        """Vérifier la disponibilité budgétaire"""
        self.ensure_one()
        
        # Vérifier si un contrôle existe déjà
        if self.budget_control_id:
            # Ouvrir le contrôle existant
            action = {
                'name': _('Contrôle budgétaire'),
                'type': 'ir.actions.act_window',
                'res_model': 'e_gestock_budget.budget_control',
                'view_mode': 'form',
                'res_id': self.budget_control_id.id,
                'target': 'current',
            }
            return action
        
        # Créer un nouveau contrôle budgétaire
        if not hasattr(self, 'credit_id') or not self.credit_id:
            raise UserError(_("Impossible de créer un contrôle budgétaire. Aucun crédit budgétaire n'est associé à cette commande."))
        
        control = self.env['e_gestock_budget.budget_control'].create({
            'purchase_order_id': self.id,
            'credit_id': self.credit_id.id,
            'montant': self.amount_total,
            'date_controle': fields.Date.today(),
            'state': 'draft',
        })
        
        self.budget_control_id = control.id
        
        # Ouvrir le contrôle budgétaire
        action = {
            'name': _('Contrôle budgétaire'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock_budget.budget_control',
            'view_mode': 'form',
            'res_id': control.id,
            'target': 'current',
        }
        return action
    
    def button_confirm(self):
        """Surcharge de la confirmation pour enregistrer la consommation budgétaire"""
        res = super(EgestockPurchaseOrderBudget, self).button_confirm()
        
        for order in self:
            # Si la commande est liée à un contrôle budgétaire
            if order.budget_control_id and order.budget_control_id.state == 'approved':
                # Créer une opération de consommation budgétaire
                operation = self.env['e_gestock_budget.operation_budget'].create({
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
