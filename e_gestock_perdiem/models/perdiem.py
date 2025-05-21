# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class Perdiem(models.Model):
    _name = 'e_gestock.perdiem'
    _description = 'Demande de Perdiem'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, tracking=True)
    exercice_id = fields.Many2one('e_gestock.exercise', string='Exercice', required=True, tracking=True,
        default=lambda self: self.env['e_gestock.exercise'].search([('is_active', '=', True)], limit=1))
    requester_id = fields.Many2one('res.users', string='Demandeur', required=True, default=lambda self: self.env.user, tracking=True)
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    motive = fields.Text(string='Motif', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('validated_section', 'Validé par la section'),
        ('validated_direction', 'Validé par la direction'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté')
    ], string='État', default='draft', tracking=True)
    beneficiary_ids = fields.One2many('e_gestock.perdiem.beneficiary', 'perdiem_id', string='Bénéficiaires')
    total_amount = fields.Float(string='Montant total', compute='_compute_montant_total', store=True)
    credit_budget_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', tracking=True)
    budget_available = fields.Float(string='Disponible budgétaire', compute='_compute_budget_available')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    status_ids = fields.One2many('e_gestock.perdiem.status', 'perdiem_id', string='Historique des statuts')

    @api.depends('beneficiary_ids.montant')
    def _compute_montant_total(self):
        for perdiem in self:
            perdiem.total_amount = sum(perdiem.beneficiary_ids.mapped('montant'))

    @api.depends('credit_budget_id', 'credit_budget_id.montant_disponible')
    def _compute_budget_available(self):
        for perdiem in self:
            perdiem.budget_available = perdiem.credit_budget_id.montant_disponible if perdiem.credit_budget_id else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('e_gestock.perdiem') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        if not self.beneficiary_ids:
            raise UserError(_("Veuillez ajouter au moins un bénéficiaire avant de soumettre la demande."))
            
        # Création d'un statut 'submitted'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_submitted', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande soumise par %s") % self.env.user.name
            })
            
        self.write({'state': 'submitted'})

    def action_validate_section(self):
        self.ensure_one()
        
        # Création d'un statut 'validated_section'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_validated_section', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande validée par la section par %s") % self.env.user.name
            })
            
        self.write({'state': 'validated_section'})

    def action_validate_direction(self):
        self.ensure_one()
        
        # Création d'un statut 'validated_direction'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_validated_direction', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande validée par la direction par %s") % self.env.user.name
            })
            
        self.write({'state': 'validated_direction'})

    def action_approve(self):
        self.ensure_one()
        if self.total_amount > self.budget_available:
            raise UserError(_("Le montant total dépasse le budget disponible!"))
            
        # Création d'un engagement budgétaire si un crédit est défini
        if self.credit_budget_id:
            # Créer l'opération budgétaire d'engagement
            self.env['e_gestock.operation_budget'].create({
                'credit_id': self.credit_budget_id.id,
                'montant': self.total_amount,
                'type': 'engagement',
                'origine': 'manuel',
                'ref_origine': self.name,
                'notes': _("Engagement pour perdiem %s") % self.name
            })
            
        # Création d'un statut 'approved'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_approved', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande approuvée par %s") % self.env.user.name
            })
            
        self.write({'state': 'approved'})

    def action_reject(self):
        self.ensure_one()
        
        # Création d'un statut 'rejected'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_rejected', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande rejetée par %s") % self.env.user.name
            })
            
        self.write({'state': 'rejected'})

    def action_reset_to_draft(self):
        self.ensure_one()
        
        # Création d'un statut 'draft'
        status_type = self.env.ref('e_gestock_perdiem.perdiem_status_type_draft', raise_if_not_found=False)
        if status_type:
            self.env['e_gestock.perdiem.status'].create({
                'perdiem_id': self.id,
                'status_type_id': status_type.id,
                'user_id': self.env.user.id,
                'date_debut': fields.Datetime.now(),
                'commentaire': _("Demande remise en brouillon par %s") % self.env.user.name
            })
            
        self.write({'state': 'draft'})

    @api.onchange('structure_id', 'exercice_id')
    def _onchange_budget_fields(self):
        if self.structure_id and self.exercice_id:
            # Recherche du crédit budgétaire correspondant
            credit = self.env['e_gestock.credit_budget'].search([
                ('structure_id', '=', self.structure_id.id),
                ('exercice_id', '=', self.exercice_id.id),
                ('type', '=', 'perdiem')
            ], limit=1)
            
            # Si aucun crédit budgétaire de type 'perdiem' n'est trouvé, essayer sans filtre de type
            if not credit:
                credit = self.env['e_gestock.credit_budget'].search([
                    ('structure_id', '=', self.structure_id.id),
                    ('exercice_id', '=', self.exercice_id.id),
                ], limit=1)
                
            self.credit_budget_id = credit
