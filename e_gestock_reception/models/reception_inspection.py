# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class ReceptionInspection(models.Model):
    _name = 'e_gestock.reception.inspection'
    _description = 'Inspection de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    
    # Relations avec la réception
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, tracking=True,
                                 domain=[('state', 'in', ['confirmed', 'comite_validation'])])
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', 
                                      string='Bon de commande', store=True, tracking=True)
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', 
                                   string='Fournisseur', store=True, tracking=True)
    
    # Informations sur l'inspection
    inspecteur_id = fields.Many2one('res.users', string='Inspecteur', default=lambda self: self.env.user, 
                                  required=True, tracking=True)
    methode_echantillonnage = fields.Selection([
        ('complet', 'Contrôle complet'),
        ('aleatoire', 'Échantillonnage aléatoire'),
        ('statistique', 'Échantillonnage statistique'),
        ('visuel', 'Contrôle visuel')
    ], string='Méthode d\'échantillonnage', default='complet', required=True, tracking=True)
    taux_echantillonnage = fields.Float(string='Taux d\'échantillonnage (%)', default=100.0, tracking=True)
    
    # Lignes d'inspection
    line_ids = fields.One2many('e_gestock.reception.inspection.line', 'inspection_id', string='Lignes')
    
    # Résultats et décisions
    decision = fields.Selection([
        ('accepte', 'Accepté'),
        ('accepte_reserve', 'Accepté avec réserves'),
        ('quarantaine', 'Mise en quarantaine'),
        ('rejete', 'Rejeté')
    ], string='Décision', tracking=True)
    taux_conformite = fields.Float(string='Taux de conformité (%)', compute='_compute_taux_conformite', store=True)
    commentaire = fields.Text(string='Commentaire', tracking=True)
    
    # Statut et suivi
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    
    # Champs techniques
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    nonconformity_count = fields.Integer(string='Nombre de non-conformités', compute='_compute_nonconformity_count')
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de l\'inspection doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception.inspection') or 'Nouveau'
        return super().create(vals_list)
    
    @api.depends('line_ids', 'line_ids.resultat')
    def _compute_taux_conformite(self):
        for record in self:
            total_lines = len(record.line_ids)
            if total_lines > 0:
                conformes = len(record.line_ids.filtered(lambda l: l.resultat == 'conforme'))
                record.taux_conformite = (conformes / total_lines) * 100
            else:
                record.taux_conformite = 0
    
    def _compute_nonconformity_count(self):
        for record in self:
            record.nonconformity_count = self.env['e_gestock.reception.nonconformity'].search_count([
                ('inspection_id', '=', record.id)
            ])
    
    @api.onchange('reception_id')
    def _onchange_reception_id(self):
        if self.reception_id:
            # Création automatique des lignes d'inspection basées sur les lignes de réception
            lines = []
            for reception_line in self.reception_id.line_ids:
                lines.append((0, 0, {
                    'reception_line_id': reception_line.id,
                    'article_id': reception_line.article_id.id,
                    'designation': reception_line.designation,
                    'quantite_recue': reception_line.quantite_recue,
                    'quantite_inspectee': reception_line.quantite_recue,
                }))
            self.line_ids = lines
    
    def action_confirm(self):
        """Confirme l'inspection"""
        for record in self:
            if not record.line_ids:
                raise UserError(_("Vous ne pouvez pas confirmer une inspection sans lignes."))
            
            # Vérifier que toutes les lignes ont un résultat
            if any(not line.resultat for line in record.line_ids):
                raise UserError(_("Toutes les lignes d'inspection doivent avoir un résultat."))
            
            record.write({'state': 'confirmed'})
            
            # Création automatique des non-conformités pour les lignes non conformes
            for line in record.line_ids.filtered(lambda l: l.resultat != 'conforme'):
                self.env['e_gestock.reception.nonconformity'].create({
                    'inspection_id': record.id,
                    'inspection_line_id': line.id,
                    'reception_id': record.reception_id.id,
                    'reception_line_id': line.reception_line_id.id,
                    'article_id': line.article_id.id,
                    'designation': line.designation,
                    'type': line.type_non_conformite,
                    'description': line.commentaire,
                    'gravite': line.gravite,
                    'quantite': line.quantite_non_conforme,
                })
        return True
    
    def action_done(self):
        """Termine l'inspection et applique la décision"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_("Vous ne pouvez terminer que des inspections confirmées."))
            
            if not record.decision:
                raise UserError(_("Vous devez prendre une décision avant de terminer l'inspection."))
            
            # Application de la décision sur la réception
            if record.decision == 'rejete':
                # Création d'un retour fournisseur
                return_wizard = self.env['e_gestock.reception.return.wizard'].create({
                    'reception_id': record.reception_id.id,
                    'inspection_id': record.id,
                    'motif': 'qualite',
                    'commentaire': record.commentaire or _("Rejeté suite à l'inspection %s") % record.reference,
                })
                return return_wizard.action_create_return()
            
            elif record.decision == 'quarantaine':
                # Mise en quarantaine des articles non conformes
                quarantine_wizard = self.env['e_gestock.reception.quarantine.wizard'].create({
                    'reception_id': record.reception_id.id,
                    'inspection_id': record.id,
                    'commentaire': record.commentaire or _("Mise en quarantaine suite à l'inspection %s") % record.reference,
                })
                return quarantine_wizard.action_create_quarantine()
            
            else:
                # Acceptation (avec ou sans réserves)
                record.write({'state': 'done'})
                
                # Mise à jour des lignes de réception
                for line in record.line_ids:
                    line.reception_line_id.write({
                        'est_conforme': 'oui' if line.resultat == 'conforme' else 'non',
                        'motif_non_conformite': line.type_non_conformite if line.resultat != 'conforme' else False,
                        'action_corrective': line.action_corrective if line.resultat != 'conforme' else False,
                    })
        
        return True
    
    def action_cancel(self):
        """Annule l'inspection"""
        for record in self:
            if record.state == 'done':
                raise UserError(_("Vous ne pouvez pas annuler une inspection terminée."))
            record.write({'state': 'cancelled'})
        return True
    
    def action_view_nonconformities(self):
        """Affiche les non-conformités liées à cette inspection"""
        self.ensure_one()
        return {
            'name': _('Non-conformités'),
            'view_mode': 'list,form',
            'res_model': 'e_gestock.reception.nonconformity',
            'domain': [('inspection_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_inspection_id': self.id},
        }


class ReceptionInspectionLine(models.Model):
    _name = 'e_gestock.reception.inspection.line'
    _description = 'Ligne d\'inspection de réception'
    _order = 'id'
    
    inspection_id = fields.Many2one('e_gestock.reception.inspection', string='Inspection', required=True, ondelete='cascade')
    reception_line_id = fields.Many2one('e_gestock.reception_line', string='Ligne de réception', required=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    
    # Quantités
    quantite_recue = fields.Float(string='Quantité reçue', digits='Product Unit of Measure', required=True)
    quantite_inspectee = fields.Float(string='Quantité inspectée', digits='Product Unit of Measure', required=True)
    quantite_conforme = fields.Float(string='Quantité conforme', digits='Product Unit of Measure')
    quantite_non_conforme = fields.Float(string='Quantité non conforme', digits='Product Unit of Measure')
    
    # Résultats
    resultat = fields.Selection([
        ('conforme', 'Conforme'),
        ('non_conforme', 'Non conforme'),
        ('partiellement_conforme', 'Partiellement conforme')
    ], string='Résultat')
    
    type_non_conformite = fields.Selection([
        ('qualite', 'Qualité non conforme'),
        ('quantite', 'Quantité non conforme'),
        ('reference', 'Référence non conforme'),
        ('emballage', 'Emballage endommagé'),
        ('documentation', 'Documentation manquante'),
        ('autre', 'Autre problème')
    ], string='Type de non-conformité')
    
    gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique')
    ], string='Gravité')
    
    action_corrective = fields.Selection([
        ('retour', 'Retour au fournisseur'),
        ('acceptation', 'Acceptation avec réserve'),
        ('remise', 'Demande de remise'),
        ('remplacement', 'Demande de remplacement'),
        ('quarantaine', 'Mise en quarantaine'),
        ('autre', 'Autre action')
    ], string='Action corrective')
    
    commentaire = fields.Text(string='Commentaire')
    photo = fields.Binary(string='Photo')
    
    @api.onchange('quantite_conforme', 'quantite_non_conforme')
    def _onchange_quantites(self):
        total = self.quantite_conforme + self.quantite_non_conforme
        if total > self.quantite_inspectee:
            return {'warning': {
                'title': _('Attention'),
                'message': _('La somme des quantités conformes et non conformes ne peut pas dépasser la quantité inspectée.')
            }}
        
        # Détermination automatique du résultat
        if self.quantite_non_conforme == 0:
            self.resultat = 'conforme'
        elif self.quantite_conforme == 0:
            self.resultat = 'non_conforme'
        else:
            self.resultat = 'partiellement_conforme'
    
    @api.onchange('resultat')
    def _onchange_resultat(self):
        if self.resultat == 'conforme':
            self.type_non_conformite = False
            self.gravite = False
            self.action_corrective = False
            self.quantite_conforme = self.quantite_inspectee
            self.quantite_non_conforme = 0
        elif self.resultat == 'non_conforme':
            if not self.type_non_conformite:
                self.type_non_conformite = 'qualite'
            if not self.gravite:
                self.gravite = 'majeure'
            self.quantite_conforme = 0
            self.quantite_non_conforme = self.quantite_inspectee
