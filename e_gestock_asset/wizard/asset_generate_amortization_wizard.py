# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class AssetGenerateAmortizationWizard(models.TransientModel):
    _name = 'e_gestock.asset.generate.amortization.wizard'
    _description = 'Assistant de génération des amortissements'
    
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True)
    date_debut = fields.Date(string='Date de début', required=True, default=fields.Date.today)
    duree_amortissement = fields.Integer(string='Durée amortissement (années)', required=True)
    methode_amortissement = fields.Selection([
        ('linear', 'Linéaire'),
        ('degressive', 'Dégressive')
    ], string='Méthode amortissement', default='linear', required=True)
    valeur_acquisition = fields.Monetary(string='Valeur d\'acquisition', required=True)
    valeur_residuelle = fields.Monetary(string='Valeur résiduelle')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        """Met à jour les champs en fonction de l'immobilisation sélectionnée."""
        if self.asset_id:
            self.date_debut = self.asset_id.date_mise_service or fields.Date.today()
            self.duree_amortissement = self.asset_id.duree_amortissement or 5
            self.methode_amortissement = self.asset_id.methode_amortissement or 'linear'
            self.valeur_acquisition = self.asset_id.valeur_acquisition or 0.0
            self.valeur_residuelle = self.asset_id.valeur_residuelle or 0.0
    
    def action_generate_amortization(self):
        """Génère les lignes d'amortissement pour l'immobilisation."""
        self.ensure_one()
        
        if not self.asset_id.date_mise_service:
            self.asset_id.date_mise_service = self.date_debut
        
        self.asset_id.write({
            'duree_amortissement': self.duree_amortissement,
            'methode_amortissement': self.methode_amortissement,
            'valeur_acquisition': self.valeur_acquisition,
            'valeur_residuelle': self.valeur_residuelle,
        })
        
        # Ici, vous pouvez ajouter le code pour générer les lignes d'amortissement
        # selon la méthode choisie (linéaire ou dégressive)
        
        # Exemple simplifié pour la méthode linéaire
        if self.methode_amortissement == 'linear':
            montant_amortissable = self.valeur_acquisition - self.valeur_residuelle
            annuite = montant_amortissable / self.duree_amortissement
            
            # Création d'un actif dans le module account_asset
            asset_vals = {
                'name': self.asset_id.name,
                'original_value': self.valeur_acquisition,
                'method': 'linear',
                'method_number': self.duree_amortissement * 12,  # En mois
                'method_period': '1',  # Mensuel
                'prorata': True,
                'date_start': self.date_debut,
                'salvage_value': self.valeur_residuelle,
                'asset_type': 'purchase',
                'state': 'open',
            }
            
            # Création de l'actif dans le module account_asset
            account_asset = self.env['account.asset'].create(asset_vals)
            
            # Lien entre l'immobilisation E-GESTOCK et l'actif Odoo
            self.asset_id.write({
                'account_asset_id': account_asset.id,
            })
        
        return {'type': 'ir.actions.act_window_close'}
