from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ComiteReception(models.Model):
    _name = 'e_gestock.comite_reception'
    _description = 'Comité de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nom', required=True, tracking=True)
    president_id = fields.Many2one('res.users', string='Président', required=True, tracking=True,
                                  domain=[('groups_id', 'in', [lambda self: self.env.ref('purchase.group_purchase_manager').id])])
    secretaire_id = fields.Many2one('res.users', string='Secrétaire', tracking=True)
    membre_ids = fields.Many2many('res.users', string='Membres', tracking=True)
    active = fields.Boolean(string='Actif', default=True, tracking=True)
    quorum = fields.Integer(string='Quorum requis', default=3, tracking=True,
                          help='Nombre minimum de signatures requises pour valider un PV')
    reception_ids = fields.One2many('e_gestock.reception', 'comite_reception_id', string='Réceptions')
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', tracking=True)
    notes = fields.Text(string='Notes')

    # Champs liés à la société
    company_id = fields.Many2one('res.company', string='Société',
                               default=lambda self: self.env.company,
                               required=True)

    @api.constrains('quorum', 'membre_ids', 'president_id', 'secretaire_id')
    def _check_quorum(self):
        for comite in self:
            # Compter tous les membres potentiels (président + secrétaire + membres)
            all_members = comite.membre_ids.ids + [comite.president_id.id]
            if comite.secretaire_id:
                all_members.append(comite.secretaire_id.id)

            # Enlever les doublons
            unique_members = list(set(all_members))

            if comite.quorum > len(unique_members):
                raise ValidationError(_("Le quorum requis (%s) ne peut pas être supérieur au nombre total de membres du comité (%s)")
                                     % (comite.quorum, len(unique_members)))

    def action_review_receptions(self):
        self.ensure_one()
        action = {
            'name': _('Réceptions à valider'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception',
            'domain': [('comite_reception_id', '=', self.id), ('state', '=', 'comite_validation')],
            'view_mode': 'list,form',
            'context': {'default_comite_reception_id': self.id}
        }
        return action

    def action_view_pvs(self):
        self.ensure_one()
        action = {
            'name': _('Procès-verbaux'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.pv_reception',
            'domain': [('comite_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'default_comite_id': self.id}
        }
        return action