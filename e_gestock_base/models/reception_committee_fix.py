from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReceptionCommittee(models.Model):
    _name = 'e_gestock.reception_committee'
    _description = 'Comité de réception E-GESTOCK'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom du comité', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    active = fields.Boolean(string='Actif', default=True, tracking=True)
    
    # Responsable et membres du comité
    responsible_id = fields.Many2one(
        'res.users', string='Responsable/Président', 
        required=True, tracking=True,
        domain=[('groups_id', 'in', [
            lambda self: self.env.ref('e_gestock_base.group_e_gestock_reception_manager').id
        ])]
    )
    secretary_id = fields.Many2one(
        'res.users', string='Secrétaire', 
        tracking=True
    )
    member_ids = fields.Many2many(
        'res.users', string='Membres', 
        tracking=True,
        domain=[('groups_id', 'in', [
            lambda self: self.env.ref('e_gestock_base.group_e_gestock_reception_user').id
        ])]
    )
    
    # Structure associée
    structure_id = fields.Many2one(
        'e_gestock.structure', string='Structure', 
        required=True, tracking=True
    )
    
    # Paramètres de validation
    quorum = fields.Integer(
        string='Quorum requis', 
        default=3, tracking=True,
        help='Nombre minimum de signatures requises pour valider un PV'
    )
    
    # Relations avec d'autres modèles - SUPPRIMÉ POUR ÉVITER LA DÉPENDANCE CIRCULAIRE
    # Ces champs seront ajoutés par les modules qui définissent les modèles correspondants
    
    # Statistiques
    purchase_order_count = fields.Integer(
        string='Nombre de BC', 
        compute='_compute_purchase_order_count'
    )
    reception_count = fields.Integer(
        string='Nombre de réceptions', 
        compute='_compute_reception_count'
    )
    pv_count = fields.Integer(
        string='Nombre de PV', 
        compute='_compute_pv_count'
    )
    receptions_pending_count = fields.Integer(
        string='Réceptions en attente', 
        compute='_compute_reception_count'
    )
    
    # Traçabilité
    date_creation = fields.Date(
        string='Date de création', 
        default=fields.Date.context_today, 
        readonly=True
    )
    notes = fields.Text(string='Notes')
    
    # Champs liés à la société
    company_id = fields.Many2one(
        'res.company', string='Société',
        default=lambda self: self.env.company,
        required=True
    )
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code du comité de réception doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('e_gestock.reception_committee') or 'NOUVEAU'
        return super(ReceptionCommittee, self).create(vals_list)
    
    def _compute_purchase_order_count(self):
        for committee in self:
            committee.purchase_order_count = 0
    
    def _compute_reception_count(self):
        for committee in self:
            committee.reception_count = 0
            committee.receptions_pending_count = 0
    
    def _compute_pv_count(self):
        for committee in self:
            committee.pv_count = 0
    
    @api.constrains('quorum', 'member_ids', 'responsible_id', 'secretary_id')
    def _check_quorum(self):
        for committee in self:
            # Compter tous les membres potentiels (responsable + secrétaire + membres)
            all_members = committee.member_ids.ids + [committee.responsible_id.id]
            if committee.secretary_id:
                all_members.append(committee.secretary_id.id)

            # Enlever les doublons
            unique_members = list(set(all_members))

            if committee.quorum > len(unique_members):
                raise ValidationError(_(
                    "Le quorum requis (%s) ne peut pas être supérieur au nombre total de membres du comité (%s)"
                ) % (committee.quorum, len(unique_members)))
