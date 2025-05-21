from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class EvaluationCriteria(models.Model):
    _name = 'e_gestock.evaluation_criteria'
    _description = 'Critère d\'évaluation fournisseur'
    _order = 'sequence, id'

    name = fields.Char(
        string='Nom du critère',
        required=True)
    description = fields.Text(
        string='Description')
    category = fields.Selection([
        ('quality', 'Qualité'),
        ('price', 'Prix'),
        ('delivery', 'Livraison'),
        ('service', 'Service'),
        ('communication', 'Communication'),
        ('other', 'Autre')
    ], string='Catégorie', required=True, default='quality')
    sequence = fields.Integer(
        string='Séquence',
        default=10)
    weight = fields.Float(
        string='Pondération (%)',
        default=10.0,
        help="Pondération du critère dans l'évaluation globale (en pourcentage)")
    active = fields.Boolean(
        string='Actif',
        default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)
    note_ids = fields.One2many(
        'e_gestock.evaluation_note',
        'criteria_id',
        string='Notes')

    @api.constrains('weight')
    def _check_weight(self):
        for criteria in self:
            if criteria.weight <= 0 or criteria.weight > 100:
                raise ValidationError(_("La pondération doit être comprise entre 0 et 100 %."))

    @api.model
    def _get_default_criteria(self):
        """Crée les critères par défaut lors de l'installation du module"""
        criteria = [
            {
                'name': 'Qualité des produits/services',
                'description': 'Évaluation de la qualité des produits ou services fournis',
                'category': 'quality',
                'sequence': 10,
                'weight': 25.0,
            },
            {
                'name': 'Respect des délais',
                'description': 'Évaluation du respect des délais de livraison',
                'category': 'delivery',
                'sequence': 20,
                'weight': 20.0,
            },
            {
                'name': 'Rapport qualité-prix',
                'description': 'Évaluation du rapport qualité-prix des produits/services',
                'category': 'price',
                'sequence': 30,
                'weight': 20.0,
            },
            {
                'name': 'Service client',
                'description': 'Évaluation du service client et du suivi',
                'category': 'service',
                'sequence': 40,
                'weight': 15.0,
            },
            {
                'name': 'Réactivité',
                'description': 'Évaluation de la réactivité face aux demandes urgentes',
                'category': 'communication',
                'sequence': 50,
                'weight': 10.0,
            },
            {
                'name': 'Conformité administrative',
                'description': 'Évaluation de la conformité des documents administratifs',
                'category': 'other',
                'sequence': 60,
                'weight': 10.0,
            },
        ]

        for criterium in criteria:
            if not self.search([('name', '=', criterium['name'])]):
                self.create(criterium)

        return True