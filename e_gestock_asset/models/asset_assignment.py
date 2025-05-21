# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetAssignment(models.Model):
    _name = 'e_gestock.asset_assignment'
    _description = 'Affectation d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc'
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    
    # Dates
    date_debut = fields.Date(string='Date de début', required=True, tracking=True, default=fields.Date.today)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    
    # Affectation
    user_id = fields.Many2one('res.users', string='Utilisateur', tracking=True)
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', tracking=True)
    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True)
    
    # Informations complémentaires
    motif = fields.Text(string='Motif de l\'affectation', tracking=True)
    note = fields.Text(string='Notes', tracking=True)
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('terminated', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    
    # Documents
    contrat = fields.Binary(string='Contrat d\'affectation', attachment=True)
    contrat_filename = fields.Char(string='Nom du fichier contrat')
    
    # Contraintes SQL
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence d\'affectation doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer automatiquement la référence."""
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset_assignment') or 'Nouveau'
        
        return super(AssetAssignment, self).create(vals_list)
    
    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        """Vérifie que la date de fin est postérieure à la date de début."""
        for assignment in self:
            if assignment.date_fin and assignment.date_fin < assignment.date_debut:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début!"))
    
    def action_confirm(self):
        """Confirme l'affectation."""
        self.ensure_one()
        self.state = 'confirmed'
        
        # Mise à jour des informations de l'immobilisation
        if self.user_id:
            self.asset_id.responsable_id = self.user_id
        if self.structure_id:
            self.asset_id.structure_id = self.structure_id
        if self.section_id:
            self.asset_id.section_id = self.section_id
        
        return True
    
    def action_terminate(self):
        """Termine l'affectation."""
        self.ensure_one()
        if not self.date_fin:
            self.date_fin = fields.Date.today()
        self.state = 'terminated'
        return True
    
    def action_cancel(self):
        """Annule l'affectation."""
        self.ensure_one()
        self.state = 'cancelled'
        return True
