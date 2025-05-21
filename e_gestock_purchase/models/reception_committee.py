from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReceptionCommittee(models.Model):
    _name = 'e_gestock.reception_committee'
    _description = 'Comité de réception E-GESTOCK'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom du comité', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    active = fields.Boolean(string='Actif', default=True, tracking=True)
    
    # Responsable du comité
    responsible_id = fields.Many2one('res.users', string='Responsable', 
                                    required=True, tracking=True,
                                    domain=[('groups_id', 'in', [
                                        lambda self: self.env.ref('e_gestock_base.group_e_gestock_reception_manager').id
                                    ])])
    
    # Membres du comité
    member_ids = fields.Many2many('res.users', string='Membres', 
                                 tracking=True,
                                 domain=[('groups_id', 'in', [
                                     lambda self: self.env.ref('e_gestock_base.group_e_gestock_reception_user').id
                                 ])])
    
    # Structure associée
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', 
                                  required=True, tracking=True)
    
    # Bons de commande assignés à ce comité
    purchase_order_ids = fields.One2many('e_gestock.purchase_order', 'committee_id', 
                                        string='Bons de commande assignés')
    
    # Statistiques
    purchase_order_count = fields.Integer(string='Nombre de BC', compute='_compute_purchase_order_count')
    reception_count = fields.Integer(string='Nombre de réceptions', compute='_compute_reception_count')
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for committee in self:
            committee.purchase_order_count = len(committee.purchase_order_ids)
    
    @api.depends('purchase_order_ids')
    def _compute_reception_count(self):
        for committee in self:
            reception_count = self.env['e_gestock.purchase_order'].search_count([
                ('committee_id', '=', committee.id),
                ('state_approbation', '=', 'received')
            ])
            committee.reception_count = reception_count
    
    @api.constrains('responsible_id')
    def _check_responsible_is_reception_manager(self):
        """Vérifie que le responsable a bien le rôle de gestionnaire de réception"""
        for committee in self:
            if not committee.responsible_id.has_group('e_gestock_base.group_e_gestock_reception_manager'):
                raise UserError(_("Le responsable du comité doit avoir le rôle 'Gestionnaire de réception'."))
    
    @api.constrains('member_ids')
    def _check_members_are_reception_users(self):
        """Vérifie que les membres ont bien le rôle d'utilisateur de réception"""
        for committee in self:
            for member in committee.member_ids:
                if not member.has_group('e_gestock_base.group_e_gestock_reception_user'):
                    raise UserError(_("Les membres du comité doivent avoir le rôle 'Utilisateur de réception'."))
    
    def action_view_purchase_orders(self):
        """Affiche les bons de commande assignés à ce comité"""
        self.ensure_one()
        return {
            'name': _('Bons de commande'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.purchase_order',
            'view_mode': 'list,form',
            'domain': [('committee_id', '=', self.id)],
            'context': {'default_committee_id': self.id},
        }
    
    def action_view_receptions(self):
        """Affiche les réceptions effectuées par ce comité"""
        self.ensure_one()
        return {
            'name': _('Réceptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.purchase_order',
            'view_mode': 'list,form',
            'domain': [
                ('committee_id', '=', self.id),
                ('state_approbation', '=', 'received')
            ],
        }
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code du comité de réception doit être unique !'),
    ]
