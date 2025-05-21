# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PerdiemStatusType(models.Model):
    _name = 'e_gestock.perdiem.status.type'
    _description = 'Type de statut de Perdiem'
    _order = 'sequence, id'
    
    name = fields.Char(string='Libellé', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    # Champs techniques
    is_system = fields.Boolean(string='Système', default=False, 
                              help="Indique si ce type de statut est utilisé par le système et ne doit pas être modifié")
    
    # Contraintes SQL
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code du type de statut doit être unique!')
    ]
