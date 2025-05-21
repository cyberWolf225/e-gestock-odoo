# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ReceptionNonconformity(models.Model):
    _name = 'e_gestock.reception.nonconformity'
    _description = 'Non-conformité de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    
    # Relations avec l'inspection et la réception
    inspection_id = fields.Many2one('e_gestock.reception.inspection', string='Inspection', tracking=True)
    inspection_line_id = fields.Many2one('e_gestock.reception.inspection.line', string='Ligne d\'inspection')
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, tracking=True)
    reception_line_id = fields.Many2one('e_gestock.reception_line', string='Ligne de réception')
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', 
                                      string='Bon de commande', store=True, tracking=True)
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', 
                                   string='Fournisseur', store=True, tracking=True)
    
    # Informations sur l'article
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    quantite = fields.Float(string='Quantité concernée', digits='Product Unit of Measure', required=True)
    
    # Détails de la non-conformité
    type = fields.Selection([
        ('qualite', 'Qualité non conforme'),
        ('quantite', 'Quantité non conforme'),
        ('reference', 'Référence non conforme'),
        ('emballage', 'Emballage endommagé'),
        ('documentation', 'Documentation manquante'),
        ('autre', 'Autre problème')
    ], string='Type', required=True, tracking=True)
    
    gravite = fields.Selection([
        ('mineure', 'Mineure'),
        ('majeure', 'Majeure'),
        ('critique', 'Critique')
    ], string='Gravité', required=True, tracking=True, default='majeure')
    
    description = fields.Text(string='Description', required=True)
    photo = fields.Binary(string='Photo')
    
    # Actions et suivi
    action_requise = fields.Selection([
        ('retour', 'Retour au fournisseur'),
        ('acceptation', 'Acceptation avec réserve'),
        ('remise', 'Demande de remise'),
        ('remplacement', 'Demande de remplacement'),
        ('quarantaine', 'Mise en quarantaine'),
        ('derogation', 'Demande de dérogation'),
        ('autre', 'Autre action')
    ], string='Action requise', required=True, tracking=True)
    
    responsable_id = fields.Many2one('res.users', string='Responsable', 
                                   default=lambda self: self.env.user, required=True, tracking=True)
    date_echeance = fields.Date(string='Date d\'échéance', 
                              default=lambda self: fields.Date.context_today(self) + timedelta(days=7), 
                              required=True, tracking=True)
    
    # Statut et suivi
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('in_progress', 'En cours de traitement'),
        ('resolved', 'Résolu'),
        ('closed', 'Clôturé')
    ], string='État', default='draft', tracking=True)
    
    # Résolution
    resolution = fields.Text(string='Résolution', tracking=True)
    date_resolution = fields.Date(string='Date de résolution', tracking=True)
    cout_resolution = fields.Float(string='Coût de résolution', tracking=True)
    
    # Champs techniques
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    quarantine_id = fields.Many2one('e_gestock.reception.quarantine', string='Quarantaine')
    return_id = fields.Many2one('e_gestock.reception.return', string='Retour fournisseur')
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de la non-conformité doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception.nonconformity') or 'Nouveau'
        return super().create(vals_list)
    
    def action_confirm(self):
        """Confirme la non-conformité"""
        for record in self:
            record.write({'state': 'confirmed'})
            
            # Notification au fournisseur si critique
            if record.gravite == 'critique':
                template = self.env.ref('e_gestock_reception.email_template_nonconformity_critical')
                if template:
                    template.send_mail(record.id, force_send=True)
        return True
    
    def action_start_processing(self):
        """Démarre le traitement de la non-conformité"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_("Vous ne pouvez démarrer le traitement que pour des non-conformités confirmées."))
            
            # Création automatique d'une quarantaine si nécessaire
            if record.action_requise == 'quarantaine' and not record.quarantine_id:
                quarantine = self.env['e_gestock.reception.quarantine'].create({
                    'reception_id': record.reception_id.id,
                    'article_id': record.article_id.id,
                    'designation': record.designation,
                    'quantite': record.quantite,
                    'motif': record.type,
                    'description': record.description,
                    'responsable_id': record.responsable_id.id,
                    'date_echeance': record.date_echeance,
                })
                record.write({'quarantine_id': quarantine.id})
            
            # Création automatique d'un retour fournisseur si nécessaire
            if record.action_requise == 'retour' and not record.return_id:
                return_vals = {
                    'reception_id': record.reception_id.id,
                    'fournisseur_id': record.fournisseur_id.id,
                    'motif': 'qualite',
                    'description': record.description,
                    'responsable_id': record.responsable_id.id,
                }
                return_id = self.env['e_gestock.reception.return'].create(return_vals)
                
                # Création de la ligne de retour
                self.env['e_gestock.reception.return.line'].create({
                    'return_id': return_id.id,
                    'article_id': record.article_id.id,
                    'designation': record.designation,
                    'quantite': record.quantite,
                    'motif_detail': record.description,
                })
                
                record.write({'return_id': return_id.id})
            
            record.write({'state': 'in_progress'})
        return True
    
    def action_resolve(self):
        """Marque la non-conformité comme résolue"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_("Vous ne pouvez résoudre que des non-conformités en cours de traitement."))
            
            if not record.resolution:
                raise UserError(_("Veuillez saisir la résolution avant de marquer comme résolu."))
            
            record.write({
                'state': 'resolved',
                'date_resolution': fields.Date.context_today(record)
            })
        return True
    
    def action_close(self):
        """Clôture la non-conformité"""
        for record in self:
            if record.state != 'resolved':
                raise UserError(_("Vous ne pouvez clôturer que des non-conformités résolues."))
            
            record.write({'state': 'closed'})
            
            # Mise à jour des statistiques fournisseur
            if record.fournisseur_id:
                supplier_stats = self.env['e_gestock.supplier.quality'].search([
                    ('partner_id', '=', record.fournisseur_id.id)
                ], limit=1)
                
                if supplier_stats:
                    supplier_stats.nonconformity_count += 1
                    if record.gravite == 'critique':
                        supplier_stats.critical_nonconformity_count += 1
                else:
                    self.env['e_gestock.supplier.quality'].create({
                        'partner_id': record.fournisseur_id.id,
                        'nonconformity_count': 1,
                        'critical_nonconformity_count': 1 if record.gravite == 'critique' else 0,
                    })
        return True
    
    def action_view_quarantine(self):
        """Affiche la quarantaine liée à cette non-conformité"""
        self.ensure_one()
        if not self.quarantine_id:
            raise UserError(_("Aucune quarantaine n'est associée à cette non-conformité."))
        
        return {
            'name': _('Quarantaine'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.quarantine',
            'res_id': self.quarantine_id.id,
            'type': 'ir.actions.act_window',
        }
    
    def action_view_return(self):
        """Affiche le retour fournisseur lié à cette non-conformité"""
        self.ensure_one()
        if not self.return_id:
            raise UserError(_("Aucun retour fournisseur n'est associé à cette non-conformité."))
        
        return {
            'name': _('Retour fournisseur'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.return',
            'res_id': self.return_id.id,
            'type': 'ir.actions.act_window',
        }
