from odoo import api, fields, models, _

class ContractClause(models.Model):
    _name = 'e_gestock.contract_clause'
    _description = 'Clause de contrat fournisseur'
    _order = 'sequence, id'

    contract_id = fields.Many2one(
        'e_gestock.supplier_contract',
        string='Contrat',
        required=True,
        ondelete='cascade')
    sequence = fields.Integer(
        string='Séquence',
        default=10)
    name = fields.Char(
        string='Titre',
        required=True)
    type = fields.Selection([
        ('general', 'Clause générale'),
        ('financial', 'Clause financière'),
        ('delivery', 'Clause de livraison'),
        ('warranty', 'Clause de garantie'),
        ('confidentiality', 'Clause de confidentialité'),
        ('quality', 'Clause de qualité'),
        ('termination', 'Clause de résiliation'),
        ('other', 'Autre')
    ], string='Type de clause', default='general', required=True)
    content = fields.Text(
        string='Contenu',
        required=True)
    is_mandatory = fields.Boolean(
        string='Obligatoire',
        default=True,
        help="Indique si cette clause est obligatoire pour la validité du contrat")
    is_standard = fields.Boolean(
        string='Clause standard',
        default=False,
        help="Indique si cette clause est une clause standard pour ce type de contrat")
    notes = fields.Text(
        string='Notes')

    def name_get(self):
        return [(clause.id, f"{clause.name} ({dict(self._fields['type'].selection).get(clause.type)})")
                for clause in self]

    @api.model
    def get_standard_clauses(self, contract_type):
        """Retourne les clauses standards pour un type de contrat donné"""
        clauses = self.env['e_gestock.contract_clause_template'].search([
            ('contract_type', '=', contract_type),
            ('active', '=', True)
        ])
        return clauses

class ContractClauseTemplate(models.Model):
    _name = 'e_gestock.contract_clause_template'
    _description = 'Modèle de clause de contrat'
    _order = 'sequence, id'

    name = fields.Char(string='Titre', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    type = fields.Selection([
        ('general', 'Clause générale'),
        ('financial', 'Clause financière'),
        ('delivery', 'Clause de livraison'),
        ('warranty', 'Clause de garantie'),
        ('confidentiality', 'Clause de confidentialité'),
        ('quality', 'Clause de qualité'),
        ('termination', 'Clause de résiliation'),
        ('other', 'Autre')
    ], string='Type de clause', default='general', required=True)
    contract_type = fields.Selection([
        ('framework', 'Contrat cadre'),
        ('punctual', 'Contrat ponctuel'),
        ('service', 'Contrat de service'),
        ('maintenance', 'Contrat de maintenance'),
        ('all', 'Tous types')
    ], string='Type de contrat', default='all', required=True)
    content = fields.Text(string='Contenu', required=True)
    is_mandatory = fields.Boolean(string='Obligatoire', default=True)
    active = fields.Boolean(string='Active', default=True)
    note = fields.Text(string='Note')
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)