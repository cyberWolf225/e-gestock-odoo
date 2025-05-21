from odoo import models, fields, api, _

class OperationBudget(models.Model):
    _name = 'e_gestock.operation_budget'
    _description = 'Opération budgétaire'
    _order = 'date desc, id desc'
    
    credit_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', required=True, ondelete='cascade')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    montant = fields.Monetary(string='Montant', required=True)
    type = fields.Selection([
        ('allocation', 'Allocation'),
        ('engagement', 'Engagement'),
        ('consommation', 'Consommation'),
        ('ajustement', 'Ajustement')
    ], string='Type d\'opération', required=True)
    origine = fields.Selection([
        ('demande_achat', 'Demande d\'achat'),
        ('bon_commande', 'Bon de commande'),
        ('manuel', 'Manuel'),
        ('init', 'Initialisation')
    ], string='Origine', required=True, default='manuel')
    ref_origine = fields.Char(string='Référence origine')
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, required=True)
    validateur_id = fields.Many2one('res.users', string='Validateur')
    etape_validation = fields.Selection([
        ('cmp', 'Validation CMP'),
        ('budget', 'Contrôle Budgétaire'),
        ('dcg_dept', 'Chef Département DCG'),
        ('dcg', 'Responsable DCG'),
        ('dgaaf', 'DGAAF'),
        ('dg', 'DG')
    ], string='Étape de validation')
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Devise', related='credit_id.currency_id')
    structure_id = fields.Many2one(related='credit_id.structure_id', store=True, string='Structure')
    famille_id = fields.Many2one(related='credit_id.famille_id', store=True, string='Famille')
    exercise_id = fields.Many2one(related='credit_id.exercise_id', store=True, string='Exercice')
    
    @api.model_create_multi
    def create(self, vals_list):
        operations = super(OperationBudget, self).create(vals_list)
        # Mettre à jour les montants sur le crédit budgétaire
        for operation in operations:
            credit = operation.credit_id
            if operation.type == 'allocation':
                # déjà géré dans le create du crédit budgétaire
                pass
            elif operation.type == 'engagement':
                credit.montant_engage += operation.montant
            elif operation.type == 'consommation':
                credit.montant_consomme += operation.montant
            elif operation.type == 'ajustement':
                # déjà géré dans le write du crédit budgétaire
                pass
        return operations 