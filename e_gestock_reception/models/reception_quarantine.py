# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class ReceptionQuarantine(models.Model):
    _name = 'e_gestock.reception.quarantine'
    _description = 'Quarantaine de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    
    # Dates
    date_debut = fields.Date(string='Date de début', default=fields.Date.context_today, 
                           required=True, tracking=True)
    date_echeance = fields.Date(string='Date d\'échéance', required=True, tracking=True,
                              default=lambda self: fields.Date.context_today(self) + timedelta(days=14))
    date_fin = fields.Date(string='Date de fin', tracking=True)
    duree = fields.Integer(string='Durée (jours)', compute='_compute_duree', store=True)
    
    # Relations avec la réception
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, tracking=True)
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', 
                                      string='Bon de commande', store=True, tracking=True)
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', 
                                   string='Fournisseur', store=True, tracking=True)
    
    # Informations sur l'article
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    
    # Emplacement de quarantaine
    zone_id = fields.Many2one('e_gestock.reception.quarantine.zone', string='Zone de quarantaine', 
                            required=True, tracking=True)
    emplacement = fields.Char(string='Emplacement', tracking=True)
    
    # Motif et description
    motif = fields.Selection([
        ('qualite', 'Qualité non conforme'),
        ('quantite', 'Quantité non conforme'),
        ('reference', 'Référence non conforme'),
        ('emballage', 'Emballage endommagé'),
        ('documentation', 'Documentation manquante'),
        ('inspection', 'Inspection complémentaire requise'),
        ('autre', 'Autre motif')
    ], string='Motif', required=True, tracking=True)
    
    description = fields.Text(string='Description', required=True)
    
    # Responsable et suivi
    responsable_id = fields.Many2one('res.users', string='Responsable', 
                                   default=lambda self: self.env.user, required=True, tracking=True)
    
    # Statut et décision
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('in_progress', 'En cours'),
        ('inspection', 'En inspection'),
        ('decision', 'Décision requise'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('closed', 'Clôturé')
    ], string='État', default='draft', tracking=True)
    
    decision = fields.Selection([
        ('accept', 'Accepter et mettre en stock'),
        ('accept_degrade', 'Accepter avec déclassement'),
        ('return', 'Retourner au fournisseur'),
        ('destroy', 'Détruire'),
        ('other', 'Autre décision')
    ], string='Décision finale', tracking=True)
    
    decision_commentaire = fields.Text(string='Commentaire sur la décision', tracking=True)
    decision_date = fields.Date(string='Date de décision', tracking=True)
    decision_user_id = fields.Many2one('res.users', string='Décideur', tracking=True)
    
    # Inspections complémentaires
    inspection_ids = fields.One2many('e_gestock.reception.quarantine.inspection', 'quarantine_id', 
                                   string='Inspections complémentaires')
    inspection_count = fields.Integer(string='Nombre d\'inspections', compute='_compute_inspection_count')
    
    # Champs techniques
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    nonconformity_id = fields.Many2one('e_gestock.reception.nonconformity', string='Non-conformité associée')
    return_id = fields.Many2one('e_gestock.reception.return', string='Retour fournisseur')
    stock_move_id = fields.Many2one('stock.move', string='Mouvement de stock')
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de quarantaine doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception.quarantine') or 'Nouveau'
        return super().create(vals_list)
    
    @api.depends('date_debut', 'date_fin')
    def _compute_duree(self):
        for record in self:
            if record.date_debut and record.date_fin:
                delta = fields.Date.from_string(record.date_fin) - fields.Date.from_string(record.date_debut)
                record.duree = delta.days
            elif record.date_debut:
                delta = fields.Date.today() - fields.Date.from_string(record.date_debut)
                record.duree = delta.days
            else:
                record.duree = 0
    
    def _compute_inspection_count(self):
        for record in self:
            record.inspection_count = len(record.inspection_ids)
    
    def action_confirm(self):
        """Confirme la mise en quarantaine"""
        for record in self:
            if not record.zone_id:
                raise UserError(_("Vous devez spécifier une zone de quarantaine."))
            
            record.write({'state': 'confirmed'})
            
            # Notification au responsable
            activity = self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'note': _('Nouvel article en quarantaine à traiter: %s') % record.designation,
                'user_id': record.responsable_id.id,
                'res_id': record.id,
                'res_model_id': self.env['ir.model']._get('e_gestock.reception.quarantine').id,
                'date_deadline': fields.Date.today() + timedelta(days=1),
            })
        return True
    
    def action_start(self):
        """Démarre la période de quarantaine"""
        for record in self:
            record.write({'state': 'in_progress'})
        return True
    
    def action_inspection(self):
        """Marque comme en inspection"""
        for record in self:
            record.write({'state': 'inspection'})
        return True
    
    def action_request_decision(self):
        """Demande une décision finale"""
        for record in self:
            record.write({'state': 'decision'})
            
            # Notification au responsable qualité
            quality_manager = self.env.ref('e_gestock_reception.group_reception_quality_manager')
            if quality_manager:
                for user in quality_manager.users:
                    activity = self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': _('Décision requise pour l\'article en quarantaine: %s') % record.designation,
                        'user_id': user.id,
                        'res_id': record.id,
                        'res_model_id': self.env['ir.model']._get('e_gestock.reception.quarantine').id,
                        'date_deadline': fields.Date.today() + timedelta(days=1),
                    })
        return True
    
    def action_accept(self):
        """Accepte l'article et le met en stock"""
        self.ensure_one()
        if self.state != 'decision':
            raise UserError(_("Vous ne pouvez prendre une décision que lorsque l'état est 'Décision requise'."))
        
        # Création du mouvement de stock
        stock_move = self._create_stock_move('accept')
        
        self.write({
            'state': 'accepted',
            'decision': 'accept',
            'decision_date': fields.Date.today(),
            'decision_user_id': self.env.user.id,
            'date_fin': fields.Date.today(),
            'stock_move_id': stock_move.id if stock_move else False,
        })
        return True
    
    def action_reject(self):
        """Rejette l'article et crée un retour fournisseur"""
        self.ensure_one()
        if self.state != 'decision':
            raise UserError(_("Vous ne pouvez prendre une décision que lorsque l'état est 'Décision requise'."))
        
        # Création du retour fournisseur
        return_wizard = self.env['e_gestock.reception.return.wizard'].create({
            'reception_id': self.reception_id.id,
            'motif': 'qualite',
            'commentaire': _("Retour suite à quarantaine: %s") % self.description,
        })
        
        # Ajout de la ligne pour l'article en quarantaine
        self.env['e_gestock.reception.return.wizard.line'].create({
            'wizard_id': return_wizard.id,
            'article_id': self.article_id.id,
            'designation': self.designation,
            'quantite': self.quantite,
        })
        
        # Création du retour
        action = return_wizard.action_create_return()
        return_id = action.get('res_id', False)
        
        if return_id:
            self.write({
                'state': 'rejected',
                'decision': 'return',
                'decision_date': fields.Date.today(),
                'decision_user_id': self.env.user.id,
                'date_fin': fields.Date.today(),
                'return_id': return_id,
            })
        
        return action
    
    def action_close(self):
        """Clôture la quarantaine"""
        for record in self:
            if record.state not in ['accepted', 'rejected']:
                raise UserError(_("Vous ne pouvez clôturer que des quarantaines acceptées ou rejetées."))
            
            record.write({
                'state': 'closed',
                'date_fin': fields.Date.today() if not record.date_fin else record.date_fin,
            })
        return True
    
    def action_add_inspection(self):
        """Ajoute une inspection complémentaire"""
        self.ensure_one()
        return {
            'name': _('Ajouter une inspection'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.quarantine.inspection',
            'type': 'ir.actions.act_window',
            'context': {
                'default_quarantine_id': self.id,
                'default_article_id': self.article_id.id,
                'default_designation': self.designation,
                'default_quantite': self.quantite,
            },
            'target': 'new',
        }
    
    def action_view_inspections(self):
        """Affiche les inspections complémentaires"""
        self.ensure_one()
        return {
            'name': _('Inspections complémentaires'),
            'view_mode': 'list,form',
            'res_model': 'e_gestock.reception.quarantine.inspection',
            'domain': [('quarantine_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_quarantine_id': self.id},
        }
    
    def _create_stock_move(self, action_type):
        """Crée un mouvement de stock en fonction de la décision"""
        self.ensure_one()
        
        if action_type == 'accept':
            # Trouver l'emplacement de destination
            location_dest = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('e_gestock_depot_id', '=', self.reception_id.depot_id.id)
            ], limit=1)
            
            if not location_dest:
                raise UserError(_("Impossible de trouver un emplacement de destination valide."))
            
            # Trouver l'emplacement source (quarantaine)
            location_src = self.zone_id.location_id
            if not location_src:
                raise UserError(_("La zone de quarantaine n'a pas d'emplacement défini."))
            
            # Créer le mouvement de stock
            product = self.article_id.product_id
            if not product:
                raise UserError(_("L'article n'a pas de produit Odoo associé."))
            
            vals = {
                'name': _('Sortie de quarantaine: %s') % self.reference,
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': self.quantite,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'company_id': self.company_id.id,
                'origin': self.reference,
                'e_gestock_quarantine_id': self.id,
            }
            
            move = self.env['stock.move'].create(vals)
            move._action_confirm()
            move._action_assign()
            move._action_done()
            
            return move
        
        return False


class ReceptionQuarantineZone(models.Model):
    _name = 'e_gestock.reception.quarantine.zone'
    _description = 'Zone de quarantaine'
    _order = 'name'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True)
    location_id = fields.Many2one('stock.location', string='Emplacement Odoo', 
                                domain=[('usage', '=', 'inventory')])
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code de la zone de quarantaine doit être unique!')
    ]


class ReceptionQuarantineInspection(models.Model):
    _name = 'e_gestock.reception.quarantine.inspection'
    _description = 'Inspection complémentaire de quarantaine'
    _order = 'date desc, id desc'
    
    quarantine_id = fields.Many2one('e_gestock.reception.quarantine', string='Quarantaine', 
                                  required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    inspecteur_id = fields.Many2one('res.users', string='Inspecteur', 
                                  default=lambda self: self.env.user, required=True)
    
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    
    type_inspection = fields.Selection([
        ('visuel', 'Inspection visuelle'),
        ('mesure', 'Mesures et tests'),
        ('labo', 'Analyse laboratoire'),
        ('autre', 'Autre type')
    ], string='Type d\'inspection', required=True)
    
    description = fields.Text(string='Description de l\'inspection', required=True)
    resultat = fields.Selection([
        ('conforme', 'Conforme'),
        ('non_conforme', 'Non conforme'),
        ('partiellement', 'Partiellement conforme')
    ], string='Résultat', required=True)
    
    commentaire = fields.Text(string='Commentaire')
    recommandation = fields.Selection([
        ('accept', 'Accepter et mettre en stock'),
        ('accept_degrade', 'Accepter avec déclassement'),
        ('return', 'Retourner au fournisseur'),
        ('destroy', 'Détruire'),
        ('other', 'Autre recommandation')
    ], string='Recommandation')
    
    piece_jointe = fields.Binary(string='Rapport d\'inspection')
    piece_jointe_nom = fields.Char(string='Nom du fichier')
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super(ReceptionQuarantineInspection, self).create(vals_list)
        
        # Mise à jour de l'état de la quarantaine
        for record in res:
            if record.quarantine_id.state not in ['inspection', 'decision']:
                record.quarantine_id.write({'state': 'inspection'})
        
        return res
