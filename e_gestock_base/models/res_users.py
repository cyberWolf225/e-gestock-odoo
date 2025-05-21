from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    structure_id = fields.Many2one(
        'e_gestock.structure',
        string='Structure principale',
        help="Structure à laquelle l'utilisateur est principalement rattaché"
    )

    section_id = fields.Many2one(
        'e_gestock.section',
        string='Section principale',
        domain="[('code_structure', '=', structure_id)]",
        help="Section à laquelle l'utilisateur est principalement rattaché"
    )

    structure_ids = fields.Many2many(
        'e_gestock.structure',
        'e_gestock_user_structure_rel',
        'user_id',
        'structure_id',
        string='Structures autorisées'
    )

    e_gestock_groups_id = fields.Many2many(
        'res.groups',
        'res_groups_users_rel',
        'uid',
        'gid',
        string='Rôles E-GESTOCK',
        domain="[('category_id.name', 'ilike', 'E-GESTOCK')]",
        compute='_compute_e_gestock_groups_id',
        inverse='_inverse_e_gestock_groups_id',
        readonly=False
    )

    @api.depends('groups_id')
    def _compute_e_gestock_groups_id(self):
        """Calcule les groupes E-GESTOCK de l'utilisateur"""
        for user in self:
            user.e_gestock_groups_id = user.groups_id.filtered(lambda g: g.category_id.name == 'E-GESTOCK')

    def _inverse_e_gestock_groups_id(self):
        """Met à jour les groupes de l'utilisateur lorsque les groupes E-GESTOCK sont modifiés"""
        for user in self:
            # Supprimer tous les groupes E-GESTOCK actuels
            groups_to_remove = user.groups_id.filtered(lambda g: g.category_id.name == 'E-GESTOCK')
            for group in groups_to_remove:
                user.write({'groups_id': [(3, group.id)]})

            # Ajouter les nouveaux groupes E-GESTOCK
            for group in user.e_gestock_groups_id:
                user.write({'groups_id': [(4, group.id)]})

    @api.onchange('structure_id')
    def _onchange_structure_id(self):
        """Vide la section si la structure change"""
        if self.structure_id and self.section_id and self.section_id.code_structure != self.structure_id:
            self.section_id = False