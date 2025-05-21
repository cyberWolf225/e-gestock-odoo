# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AssetMaintenance(models.Model):
    _name = 'e_gestock.asset_maintenance'
    _description = 'Maintenance d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc'
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True, default=fields.Date.today)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    
    type = fields.Selection([
        ('preventive', 'Préventive'),
        ('corrective', 'Corrective'),
        ('regulatory', 'Réglementaire')
    ], string='Type de maintenance', required=True, tracking=True, default='preventive')
    
    description = fields.Text(string='Description des travaux', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable interne', tracking=True, default=lambda self: self.env.user)
    prestataire_id = fields.Many2one('res.partner', string='Prestataire externe', tracking=True, domain=[('supplier_rank', '>', 0)])
    
    # Informations financières
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    cout = fields.Monetary(string='Coût', tracking=True)
    
    # État
    state = fields.Selection([
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string='État', default='planned', tracking=True)
    
    # Pièces jointes
    rapport_intervention = fields.Binary(string='Rapport d\'intervention', attachment=True)
    rapport_filename = fields.Char(string='Nom du fichier rapport')
    
    # Informations techniques
    piece_ids = fields.Many2many('e_gestock.article', string='Pièces détachées utilisées')
    duree_intervention = fields.Float(string='Durée d\'intervention (heures)', tracking=True)
    
    # Contraintes SQL
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de maintenance doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour générer automatiquement la référence."""
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.asset_maintenance') or 'Nouveau'
        
        return super(AssetMaintenance, self).create(vals_list)
    
    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        """Vérifie que la date de fin est postérieure à la date de début."""
        for maintenance in self:
            if maintenance.date_fin and maintenance.date_fin < maintenance.date_debut:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début!"))
    
    def action_start(self):
        """Démarre la maintenance."""
        self.ensure_one()
        self.state = 'in_progress'
        if self.asset_id.state != 'in_maintenance':
            self.asset_id.state = 'in_maintenance'
        return True
    
    def action_done(self):
        """Termine la maintenance."""
        self.ensure_one()
        if not self.date_fin:
            self.date_fin = fields.Date.today()
        self.state = 'done'
        
        # Vérifier si d'autres maintenances sont en cours pour cet actif
        other_maintenances = self.search([
            ('asset_id', '=', self.asset_id.id),
            ('state', '=', 'in_progress'),
            ('id', '!=', self.id)
        ])
        
        # Si aucune autre maintenance en cours, remettre l'actif en service
        if not other_maintenances and self.asset_id.state == 'in_maintenance':
            self.asset_id.state = 'in_service'
        
        return True
    
    def action_cancel(self):
        """Annule la maintenance."""
        self.ensure_one()
        self.state = 'cancelled'
        
        # Vérifier si d'autres maintenances sont en cours pour cet actif
        other_maintenances = self.search([
            ('asset_id', '=', self.asset_id.id),
            ('state', '=', 'in_progress'),
            ('id', '!=', self.id)
        ])
        
        # Si aucune autre maintenance en cours, remettre l'actif en service
        if not other_maintenances and self.asset_id.state == 'in_maintenance':
            self.asset_id.state = 'in_service'
        
        return True
