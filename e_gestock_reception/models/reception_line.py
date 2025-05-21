from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ReceptionLine(models.Model):
    _name = 'e_gestock.reception_line'
    _description = 'Ligne de réception'

    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, ondelete='cascade')
    purchase_line_id = fields.Many2one('e_gestock.purchase_order_line', string='Ligne de commande')
    article_id = fields.Many2one('e_gestock.article', string='Article')
    designation = fields.Char(string='Désignation')
    quantite_commandee = fields.Float(string='Quantité commandée', digits='Product Unit of Measure')
    quantite_deja_recue = fields.Float(string='Quantité déjà reçue', digits='Product Unit of Measure')
    quantite_recue = fields.Float(string='Quantité reçue', digits='Product Unit of Measure')
    quantite_restante = fields.Float(string='Quantité restante', compute='_compute_quantite_restante', store=True)
    est_conforme = fields.Selection([
        ('oui', 'Conforme'),
        ('non', 'Non conforme'),
        ('partiel', 'Partiellement conforme')
    ], string='Conformité', default='oui')
    notes = fields.Text(string='Notes')
    stock_move_id = fields.Many2one('stock.move', string='Mouvement de stock')
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure')

    @api.depends('quantite_commandee', 'quantite_deja_recue', 'quantite_recue')
    def _compute_quantite_restante(self):
        for line in self:
            line.quantite_restante = line.quantite_commandee - line.quantite_deja_recue - line.quantite_recue

    @api.onchange('quantite_recue')
    def _onchange_quantite_recue(self):
        if self.quantite_recue < 0:
            return {'warning': {
                'title': _('Quantité invalide'),
                'message': _('La quantité reçue ne peut pas être négative.')
            }}

        if self.quantite_recue > (self.quantite_commandee - self.quantite_deja_recue):
            return {'warning': {
                'title': _('Quantité excessive'),
                'message': _('La quantité reçue dépasse la quantité restant à recevoir.')
            }}

    @api.constrains('quantite_recue')
    def _check_quantite_recue(self):
        for line in self:
            if line.quantite_recue < 0:
                raise ValidationError(_("La quantité reçue ne peut pas être négative."))