# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class ReceptionQuarantineWizard(models.TransientModel):
    _name = 'e_gestock.reception.quarantine.wizard'
    _description = 'Assistant de mise en quarantaine'
    
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True)
    inspection_id = fields.Many2one('e_gestock.reception.inspection', string='Inspection')
    
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', string='Fournisseur', readonly=True)
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', string='Bon de commande', readonly=True)
    
    zone_id = fields.Many2one('e_gestock.reception.quarantine.zone', string='Zone de quarantaine', required=True,
                            domain="[('depot_id', '=', depot_id)]")
    depot_id = fields.Many2one(related='reception_id.depot_id', string='Dépôt', readonly=True)
    
    date_echeance = fields.Date(string='Date d\'échéance', required=True,
                              default=lambda self: fields.Date.today() + timedelta(days=14))
    
    commentaire = fields.Text(string='Commentaire', required=True)
    
    line_ids = fields.One2many('e_gestock.reception.quarantine.wizard.line', 'wizard_id', string='Lignes')
    
    @api.onchange('reception_id')
    def _onchange_reception_id(self):
        if self.reception_id:
            lines = []
            for reception_line in self.reception_id.line_ids:
                if reception_line.quantite_recue > 0:
                    lines.append((0, 0, {
                        'reception_line_id': reception_line.id,
                        'article_id': reception_line.article_id.id,
                        'designation': reception_line.designation,
                        'quantite_recue': reception_line.quantite_recue,
                        'quantite': 0.0,
                        'motif': 'qualite',
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
                    wizard_line.motif = inspection_line.type_non_conformite or 'qualite'
                    wizard_line.description = inspection_line.commentaire
    
    def action_create_quarantine(self):
        """Crée des quarantaines à partir des données de l'assistant"""
        self.ensure_one()
        
        # Vérifier qu'au moins une ligne a une quantité positive
        if not any(line.quantite > 0 for line in self.line_ids):
            raise UserError(_("Vous devez spécifier au moins une ligne avec une quantité positive."))
        
        # Créer une quarantaine pour chaque ligne avec une quantité positive
        quarantine_ids = []
        for line in self.line_ids.filtered(lambda l: l.quantite > 0):
            quarantine_vals = {
                'reception_id': self.reception_id.id,
                'article_id': line.article_id.id,
                'designation': line.designation,
                'quantite': line.quantite,
                'zone_id': self.zone_id.id,
                'motif': line.motif,
                'description': line.description or self.commentaire,
                'responsable_id': self.env.user.id,
                'date_echeance': self.date_echeance,
            }
            
            quarantine = self.env['e_gestock.reception.quarantine'].create(quarantine_vals)
            quarantine_ids.append(quarantine.id)
        
        # Si une seule quarantaine a été créée, rediriger vers celle-ci
        if len(quarantine_ids) == 1:
            return {
                'name': _('Quarantaine'),
                'view_mode': 'form',
                'res_model': 'e_gestock.reception.quarantine',
                'res_id': quarantine_ids[0],
                'type': 'ir.actions.act_window',
            }
        
        # Sinon, rediriger vers la liste des quarantaines créées
        return {
            'name': _('Quarantaines'),
            'view_mode': 'list,form',
            'res_model': 'e_gestock.reception.quarantine',
            'domain': [('id', 'in', quarantine_ids)],
            'type': 'ir.actions.act_window',
        }


class ReceptionQuarantineWizardLine(models.TransientModel):
    _name = 'e_gestock.reception.quarantine.wizard.line'
    _description = 'Ligne d\'assistant de mise en quarantaine'
    
    wizard_id = fields.Many2one('e_gestock.reception.quarantine.wizard', string='Assistant', required=True, ondelete='cascade')
    reception_line_id = fields.Many2one('e_gestock.reception_line', string='Ligne de réception', required=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    
    quantite_recue = fields.Float(string='Quantité reçue', digits='Product Unit of Measure', readonly=True)
    quantite = fields.Float(string='Quantité en quarantaine', digits='Product Unit of Measure')
    
    motif = fields.Selection([
        ('qualite', 'Qualité non conforme'),
        ('quantite', 'Quantité non conforme'),
        ('reference', 'Référence non conforme'),
        ('emballage', 'Emballage endommagé'),
        ('documentation', 'Documentation manquante'),
        ('inspection', 'Inspection complémentaire requise'),
        ('autre', 'Autre motif')
    ], string='Motif', required=True, default='qualite')
    
    description = fields.Text(string='Description')
    
    @api.onchange('quantite')
    def _onchange_quantite(self):
        if self.quantite > self.quantite_recue:
            return {'warning': {
                'title': _('Attention'),
                'message': _('La quantité en quarantaine ne peut pas dépasser la quantité reçue.')
            }}
