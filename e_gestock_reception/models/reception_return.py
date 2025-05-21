# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class ReceptionReturn(models.Model):
    _name = 'e_gestock.reception.return'
    _description = 'Retour fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    
    # Relations avec la réception
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, tracking=True)
    purchase_order_id = fields.Many2one(related='reception_id.purchase_order_id', 
                                      string='Bon de commande', store=True, tracking=True)
    fournisseur_id = fields.Many2one(related='reception_id.fournisseur_id', 
                                   string='Fournisseur', store=True, tracking=True)
    
    # Informations sur le retour
    motif = fields.Selection([
        ('qualite', 'Problème de qualité'),
        ('quantite', 'Quantité incorrecte'),
        ('reference', 'Référence incorrecte'),
        ('delai', 'Hors délai'),
        ('autre', 'Autre motif')
    ], string='Motif principal', required=True, tracking=True)
    
    description = fields.Text(string='Description', required=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', 
                                   default=lambda self: self.env.user, required=True, tracking=True)
    
    # Informations de transport
    transporteur_id = fields.Many2one('res.partner', string='Transporteur', 
                                    domain=[('is_company', '=', True)])
    date_expedition = fields.Date(string='Date d\'expédition')
    numero_tracking = fields.Char(string='Numéro de tracking')
    
    # Documents
    bon_retour = fields.Binary(string='Bon de retour')
    bon_retour_nom = fields.Char(string='Nom du fichier')
    
    # Lignes de retour
    line_ids = fields.One2many('e_gestock.reception.return.line', 'return_id', string='Lignes')
    
    # Suivi financier
    montant_total = fields.Monetary(string='Montant total', compute='_compute_montant_total', store=True)
    currency_id = fields.Many2one(related='purchase_order_id.currency_id', 
                                string='Devise', readonly=True)
    avoir_attendu = fields.Boolean(string='Avoir attendu', default=True, tracking=True)
    avoir_recu = fields.Boolean(string='Avoir reçu', default=False, tracking=True)
    reference_avoir = fields.Char(string='Référence avoir', tracking=True)
    date_avoir = fields.Date(string='Date avoir', tracking=True)
    montant_avoir = fields.Monetary(string='Montant avoir', tracking=True)
    
    # Statut et suivi
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('shipped', 'Expédié'),
        ('received', 'Reçu par fournisseur'),
        ('closed', 'Clôturé')
    ], string='État', default='draft', tracking=True)
    
    # Champs techniques
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    stock_picking_id = fields.Many2one('stock.picking', string='Transfert de stock')
    
    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence du retour fournisseur doit être unique!')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception.return') or 'Nouveau'
        return super().create(vals_list)
    
    @api.depends('line_ids.montant')
    def _compute_montant_total(self):
        for record in self:
            record.montant_total = sum(record.line_ids.mapped('montant'))
    
    def action_confirm(self):
        """Confirme le retour fournisseur"""
        for record in self:
            if not record.line_ids:
                raise UserError(_("Vous ne pouvez pas confirmer un retour sans lignes."))
            
            # Création du transfert de stock
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('warehouse_id.company_id', '=', record.company_id.id)
            ], limit=1)
            
            if not picking_type:
                raise UserError(_("Aucun type d'opération de sortie trouvé."))
            
            # Trouver l'emplacement source
            location_src = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('e_gestock_depot_id', '=', record.reception_id.depot_id.id)
            ], limit=1)
            
            if not location_src:
                raise UserError(_("Impossible de trouver un emplacement source valide."))
            
            # Trouver l'emplacement de destination (fournisseur)
            location_dest = self.env['stock.location'].search([
                ('usage', '=', 'supplier')
            ], limit=1)
            
            if not location_dest:
                raise UserError(_("Impossible de trouver un emplacement de destination pour les fournisseurs."))
            
            # Création du transfert
            picking_vals = {
                'picking_type_id': picking_type.id,
                'partner_id': record.fournisseur_id.id,
                'origin': record.reference,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'scheduled_date': fields.Datetime.now(),
                'e_gestock_return_id': record.id,
            }
            
            picking = self.env['stock.picking'].create(picking_vals)
            
            # Création des mouvements de stock
            for line in record.line_ids:
                product = line.article_id.product_id
                if not product:
                    raise UserError(_("L'article %s n'a pas de produit Odoo associé.") % line.article_id.name)
                
                move_vals = {
                    'name': line.designation,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': line.quantite,
                    'picking_id': picking.id,
                    'location_id': location_src.id,
                    'location_dest_id': location_dest.id,
                }
                
                self.env['stock.move'].create(move_vals)
            
            # Confirmation du transfert
            picking.action_confirm()
            
            record.write({
                'state': 'confirmed',
                'stock_picking_id': picking.id,
            })
            
            # Notification au fournisseur
            template = self.env.ref('e_gestock_reception.email_template_reception_return')
            if template:
                template.send_mail(record.id, force_send=True)
        
        return True
    
    def action_ship(self):
        """Marque le retour comme expédié"""
        for record in self:
            if not record.date_expedition:
                record.date_expedition = fields.Date.today()
            
            if record.stock_picking_id and record.stock_picking_id.state not in ['done', 'cancel']:
                # Validation du transfert de stock
                for move in record.stock_picking_id.move_ids_without_package:
                    if move.state not in ['done', 'cancel']:
                        move.quantity_done = move.product_uom_qty
                
                record.stock_picking_id.button_validate()
            
            record.write({'state': 'shipped'})
        return True
    
    def action_received_by_supplier(self):
        """Marque le retour comme reçu par le fournisseur"""
        for record in self:
            record.write({'state': 'received'})
        return True
    
    def action_register_credit_note(self):
        """Enregistre l'avoir du fournisseur"""
        self.ensure_one()
        return {
            'name': _('Enregistrer un avoir'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.return.credit.note.wizard',
            'type': 'ir.actions.act_window',
            'context': {
                'default_return_id': self.id,
                'default_montant_attendu': self.montant_total,
            },
            'target': 'new',
        }
    
    def action_close(self):
        """Clôture le retour fournisseur"""
        for record in self:
            if record.avoir_attendu and not record.avoir_recu:
                raise UserError(_("Vous devez d'abord enregistrer l'avoir du fournisseur avant de clôturer ce retour."))
            
            record.write({'state': 'closed'})
        return True
    
    def action_print_return_form(self):
        """Imprime le bon de retour"""
        self.ensure_one()
        return self.env.ref('e_gestock_reception.action_report_reception_return').report_action(self)


class ReceptionReturnLine(models.Model):
    _name = 'e_gestock.reception.return.line'
    _description = 'Ligne de retour fournisseur'
    _order = 'id'
    
    return_id = fields.Many2one('e_gestock.reception.return', string='Retour', required=True, ondelete='cascade')
    reception_line_id = fields.Many2one('e_gestock.reception_line', string='Ligne de réception')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    
    prix_unitaire = fields.Float(string='Prix unitaire', digits='Product Price')
    montant = fields.Monetary(string='Montant', compute='_compute_montant', store=True)
    currency_id = fields.Many2one(related='return_id.currency_id', string='Devise', readonly=True)
    
    motif_detail = fields.Text(string='Motif détaillé')
    photo = fields.Binary(string='Photo')
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_montant(self):
        for record in self:
            record.montant = record.quantite * record.prix_unitaire
    
    @api.onchange('reception_line_id')
    def _onchange_reception_line(self):
        if self.reception_line_id:
            self.article_id = self.reception_line_id.article_id
            self.designation = self.reception_line_id.designation
            self.prix_unitaire = self.reception_line_id.prix_unitaire


class ReceptionReturnCreditNoteWizard(models.TransientModel):
    _name = 'e_gestock.reception.return.credit.note.wizard'
    _description = 'Assistant d\'enregistrement d\'avoir'
    
    return_id = fields.Many2one('e_gestock.reception.return', string='Retour', required=True)
    reference_avoir = fields.Char(string='Référence avoir', required=True)
    date_avoir = fields.Date(string='Date avoir', required=True, default=fields.Date.context_today)
    montant_attendu = fields.Monetary(string='Montant attendu', readonly=True)
    montant_avoir = fields.Monetary(string='Montant avoir', required=True)
    currency_id = fields.Many2one(related='return_id.currency_id', string='Devise', readonly=True)
    commentaire = fields.Text(string='Commentaire')
    
    def action_validate(self):
        """Valide l'avoir"""
        self.ensure_one()
        
        if self.montant_avoir <= 0:
            raise UserError(_("Le montant de l'avoir doit être positif."))
        
        self.return_id.write({
            'avoir_recu': True,
            'reference_avoir': self.reference_avoir,
            'date_avoir': self.date_avoir,
            'montant_avoir': self.montant_avoir,
        })
        
        # Création d'une note dans le chatter
        self.return_id.message_post(
            body=_("Avoir fournisseur enregistré: %s pour un montant de %s %s") % 
                 (self.reference_avoir, self.montant_avoir, self.currency_id.name),
            subtype_id=self.env.ref('mail.mt_note').id
        )
        
        return {'type': 'ir.actions.act_window_close'}
