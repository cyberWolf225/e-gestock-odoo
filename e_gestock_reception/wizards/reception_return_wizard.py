# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ReceptionReturnWizard(models.TransientModel):
    _name = 'e_gestock.reception.return.wizard'
    _description = 'Assistant de création de retour fournisseur'
    
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True)
    inspection_id = fields.Many2one('e_gestock.reception.inspection', string='Inspection')
    
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', string='Fournisseur', readonly=True)
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', string='Bon de commande', readonly=True)
    
    motif = fields.Selection([
        ('qualite', 'Problème de qualité'),
        ('quantite', 'Quantité incorrecte'),
        ('reference', 'Référence incorrecte'),
        ('delai', 'Hors délai'),
        ('autre', 'Autre motif')
    ], string='Motif principal', required=True, default='qualite')
    
    commentaire = fields.Text(string='Commentaire', required=True)
    
    line_ids = fields.One2many('e_gestock.reception.return.wizard.line', 'wizard_id', string='Lignes')
    
    @api.onchange('reception_id')
    def _onchange_reception_id(self):
        if self.reception_id:
            lines = []
            for reception_line in self.reception_id.line_ids:
                if reception_line.quantite_recue > 0:
                    # Récupérer le prix unitaire depuis la ligne de commande
                    prix_unitaire = 0.0
                    if reception_line.purchase_line_id:
                        prix_unitaire = reception_line.purchase_line_id.price_unit
                    
                    lines.append((0, 0, {
                        'reception_line_id': reception_line.id,
                        'article_id': reception_line.article_id.id,
                        'designation': reception_line.designation,
                        'quantite_recue': reception_line.quantite_recue,
                        'quantite': 0.0,
                        'prix_unitaire': prix_unitaire,
                    }))
            self.line_ids = lines
    
    @api.onchange('inspection_id')
    def _onchange_inspection_id(self):
        if self.inspection_id:
            # Mettre à jour les quantités en fonction des résultats de l'inspection
            for wizard_line in self.line_ids:
                inspection_line = self.inspection_id.line_ids.filtered(
                    lambda l: l.reception_line_id.id == wizard_line.reception_line_id.id
                )
                if inspection_line and inspection_line.resultat != 'conforme':
                    wizard_line.quantite = inspection_line.quantite_non_conforme
                    wizard_line.motif_detail = inspection_line.commentaire
    
    def action_create_return(self):
        """Crée un retour fournisseur à partir des données de l'assistant"""
        self.ensure_one()
        
        # Vérifier qu'au moins une ligne a une quantité positive
        if not any(line.quantite > 0 for line in self.line_ids):
            raise UserError(_("Vous devez spécifier au moins une ligne avec une quantité positive."))
        
        # Créer le retour
        return_vals = {
            'reception_id': self.reception_id.id,
            'motif': self.motif,
            'description': self.commentaire,
            'responsable_id': self.env.user.id,
        }
        
        return_id = self.env['e_gestock.reception.return'].create(return_vals)
        
        # Créer les lignes de retour
        for line in self.line_ids.filtered(lambda l: l.quantite > 0):
            return_line_vals = {
                'return_id': return_id.id,
                'reception_line_id': line.reception_line_id.id,
                'article_id': line.article_id.id,
                'designation': line.designation,
                'quantite': line.quantite,
                'prix_unitaire': line.prix_unitaire,
                'motif_detail': line.motif_detail,
            }
            self.env['e_gestock.reception.return.line'].create(return_line_vals)
        
        # Redirection vers le retour créé
        return {
            'name': _('Retour fournisseur'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.return',
            'res_id': return_id.id,
            'type': 'ir.actions.act_window',
        }


class ReceptionReturnWizardLine(models.TransientModel):
    _name = 'e_gestock.reception.return.wizard.line'
    _description = 'Ligne d\'assistant de retour fournisseur'
    
    wizard_id = fields.Many2one('e_gestock.reception.return.wizard', string='Assistant', required=True, ondelete='cascade')
    reception_line_id = fields.Many2one('e_gestock.reception_line', string='Ligne de réception', required=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    
    quantite_recue = fields.Float(string='Quantité reçue', digits='Product Unit of Measure', readonly=True)
    quantite = fields.Float(string='Quantité à retourner', digits='Product Unit of Measure')
    prix_unitaire = fields.Float(string='Prix unitaire', digits='Product Price')
    montant = fields.Float(string='Montant', compute='_compute_montant')
    
    motif_detail = fields.Text(string='Motif détaillé')
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant(self):
        for record in self:
            record.montant = record.quantite * record.prix_unitaire
    
    @api.onchange('quantite')
    def _onchange_quantite(self):
        if self.quantite > self.quantite_recue:
            return {'warning': {
                'title': _('Attention'),
                'message': _('La quantité à retourner ne peut pas dépasser la quantité reçue.')
            }}
