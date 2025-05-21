# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AssetType(models.Model):
    _name = 'e_gestock.asset_type'
    _description = 'Type d\'immobilisation'
    _order = 'code'
    
    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Nom', required=True)
    
    # Comptes comptables
    account_asset_id = fields.Many2one('account.account', string='Compte d\'actif', 
                                      domain=[('deprecated', '=', False)])
    account_depreciation_id = fields.Many2one('account.account', string='Compte d\'amortissement', 
                                             domain=[('deprecated', '=', False)])
    account_expense_id = fields.Many2one('account.account', string='Compte de charge', 
                                        domain=[('deprecated', '=', False)])
    
    # Paramètres d'amortissement par défaut
    duree_amortissement = fields.Integer(string='Durée amortissement par défaut (années)', default=5)
    methode_amortissement = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressive')
    ], string='Méthode amortissement par défaut', default='linear')
    
    # Autres informations
    note = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    # Relations
    asset_ids = fields.One2many('e_gestock.asset', 'type_id', string='Immobilisations')
    asset_count = fields.Integer(compute='_compute_asset_count', string='Nombre d\'immobilisations')
    
    # Contraintes SQL
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code du type d\'immobilisation doit être unique!')
    ]
    
    @api.depends('asset_ids')
    def _compute_asset_count(self):
        """Calcule le nombre d'immobilisations pour ce type."""
        for record in self:
            record.asset_count = len(record.asset_ids)
    
    def action_view_assets(self):
        """Affiche les immobilisations de ce type."""
        self.ensure_one()
        return {
            'name': _('Immobilisations'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.asset',
            'view_mode': 'tree,form',
            'domain': [('type_id', '=', self.id)],
            'context': {'default_type_id': self.id},
        }
