# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ReceptionQuai(models.Model):
    _name = 'e_gestock.reception.quai'
    _description = 'Quai de réception'
    _order = 'sequence, name'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    
    capacite = fields.Integer(string='Capacité (véhicules)', default=1)
    type_vehicule = fields.Selection([
        ('all', 'Tous types'),
        ('small', 'Petits véhicules'),
        ('medium', 'Véhicules moyens'),
        ('large', 'Grands véhicules')
    ], string='Type de véhicule', default='all', required=True)
    
    equipement_ids = fields.Many2many('e_gestock.reception.equipement', string='Équipements disponibles')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Actif', default=True)
    
    # Planification
    planning_ids = fields.One2many('e_gestock.reception.quai.planning', 'quai_id', string='Planning')
    
    _sql_constraints = [
        ('code_depot_uniq', 'unique(code, depot_id)', 'Le code du quai doit être unique par dépôt!')
    ]
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.depot_id.name} - {record.name}"
            result.append((record.id, name))
        return result
    
    @api.model
    def get_available_quais(self, depot_id, date, creneau):
        """Retourne les quais disponibles pour un dépôt, une date et un créneau donnés"""
        domain = [
            ('depot_id', '=', depot_id),
            ('active', '=', True)
        ]
        
        quais = self.search(domain)
        available_quais = self.env['e_gestock.reception.quai']
        
        for quai in quais:
            # Vérifier si le quai est déjà réservé pour cette date et ce créneau
            planning = self.env['e_gestock.reception.quai.planning'].search([
                ('quai_id', '=', quai.id),
                ('date', '=', date),
                ('creneau', '=', creneau)
            ], limit=1)
            
            if not planning:
                available_quais += quai
        
        return available_quais


class ReceptionEquipement(models.Model):
    _name = 'e_gestock.reception.equipement'
    _description = 'Équipement de réception'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    type = fields.Selection([
        ('manutention', 'Équipement de manutention'),
        ('pesage', 'Équipement de pesage'),
        ('controle', 'Équipement de contrôle'),
        ('autre', 'Autre')
    ], string='Type', required=True)
    
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code de l\'équipement doit être unique!')
    ]


class ReceptionQuaiPlanning(models.Model):
    _name = 'e_gestock.reception.quai.planning'
    _description = 'Planning des quais de réception'
    _order = 'date, creneau'
    
    quai_id = fields.Many2one('e_gestock.reception.quai', string='Quai', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    creneau = fields.Selection([
        ('matin', 'Matin (8h-12h)'),
        ('apres_midi', 'Après-midi (14h-18h)'),
        ('journee', 'Journée entière')
    ], string='Créneau horaire', required=True)
    
    notice_id = fields.Many2one('e_gestock.reception.notice', string='Avis préalable')
    fournisseur_id = fields.Many2one(related='notice_id.fournisseur_id', string='Fournisseur', store=True)
    reception_id = fields.Many2one(related='notice_id.reception_id', string='Réception', store=True)
    
    notes = fields.Text(string='Notes')
    
    _sql_constraints = [
        ('quai_date_creneau_uniq', 'unique(quai_id, date, creneau)', 
         'Un quai ne peut avoir qu\'une seule réservation par créneau horaire!')
    ]
    
    @api.constrains('notice_id')
    def _check_notice_id(self):
        for record in self:
            if not record.notice_id:
                continue
            
            # Vérifier qu'il n'y a pas d'autre planning pour cet avis préalable
            other_planning = self.search([
                ('notice_id', '=', record.notice_id.id),
                ('id', '!=', record.id)
            ], limit=1)
            
            if other_planning:
                raise ValidationError(_("Cet avis préalable est déjà associé à un autre planning de quai."))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.quai_id.name} - {record.date} - {dict(record._fields['creneau'].selection).get(record.creneau)}"
            result.append((record.id, name))
        return result
