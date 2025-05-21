from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class EvaluationNote(models.Model):
    _name = 'e_gestock.evaluation_note'
    _description = 'Note d\'évaluation fournisseur'
    _rec_name = 'criteria_id'
    
    evaluation_id = fields.Many2one(
        'e_gestock.supplier_evaluation',
        string='Évaluation',
        required=True,
        ondelete='cascade')
    criteria_id = fields.Many2one(
        'e_gestock.evaluation_criteria',
        string='Critère',
        required=True,
        ondelete='restrict')
    name = fields.Char(
        string='Critère',
        related='criteria_id.name',
        store=True)
    category = fields.Selection(
        related='criteria_id.category',
        string='Catégorie',
        store=True)
    note = fields.Float(
        string='Note',
        default=0.0,
        required=True,
        help="Note de 0 à 5 (0: Très insatisfaisant, 5: Excellent)")
    weight = fields.Float(
        string='Poids',
        default=lambda self: self._default_weight(),
        required=True)
    comments = fields.Text(
        string='Commentaires')
    
    @api.model
    def _default_weight(self):
        """Retourne la pondération par défaut depuis le critère"""
        if self.env.context.get('default_criteria_id'):
            criteria = self.env['e_gestock.evaluation_criteria'].browse(self.env.context.get('default_criteria_id'))
            return criteria.weight
        return 10.0
    
    @api.constrains('note')
    def _check_note(self):
        for record in self:
            if record.note < 0 or record.note > 5:
                raise ValidationError(_("La note doit être comprise entre 0 et 5."))
    
    @api.constrains('criteria_id', 'evaluation_id')
    def _check_unique_criteria(self):
        for record in self:
            duplicates = self.search([
                ('evaluation_id', '=', record.evaluation_id.id),
                ('criteria_id', '=', record.criteria_id.id),
                ('id', '!=', record.id)
            ])
            if duplicates:
                raise ValidationError(_("Un critère ne peut être évalué qu'une seule fois par évaluation.")) 