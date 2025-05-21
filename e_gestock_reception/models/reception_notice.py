# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class ReceptionNotice(models.Model):
    _name = 'e_gestock.reception.notice'
    _description = 'Avis préalable de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_prevue desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    date_creation = fields.Date(string='Date de création', default=fields.Date.context_today,
                              readonly=True, tracking=True)
    date_prevue = fields.Date(string='Date prévue', required=True, tracking=True)
    creneau_horaire = fields.Selection([
        ('matin', 'Matin (8h-12h)'),
        ('apres_midi', 'Après-midi (14h-18h)'),
        ('journee', 'Journée entière')
    ], string='Créneau horaire', default='matin', tracking=True)

    # Relations avec les commandes et bons de commande
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', required=True,
                                     tracking=True, domain=[('state_approbation', '=', 'approved')])
    fournisseur_id = fields.Many2one(related='purchase_order_id.partner_id',
                                   string='Fournisseur', store=True, tracking=True)
    demande_id = fields.Many2one(related='purchase_order_id.demande_cotation_id',
                               string='Demande de cotation', store=True, tracking=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', required=True, tracking=True)

    # Informations sur la réception
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user,
                                   tracking=True)
    quai_id = fields.Many2one('e_gestock.reception.quai', string='Quai de réception', tracking=True)
    instructions = fields.Text(string='Instructions spécifiques', tracking=True)
    documents_requis = fields.Text(string='Documents requis', tracking=True)

    # Lignes de l'avis préalable
    line_ids = fields.One2many('e_gestock.reception.notice.line', 'notice_id', string='Lignes')

    # Statut et suivi
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('notified', 'Fournisseur notifié'),
        ('received', 'Réceptionné'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    # Champs techniques
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    reception_id = fields.Many2one('e_gestock.reception', string='Réception associée', tracking=True)

    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence de l\'avis préalable doit être unique!')
    ]

    @api.depends('reference', 'fournisseur_id', 'date_prevue')
    def _compute_name(self):
        for record in self:
            if record.reference and record.fournisseur_id and record.date_prevue:
                record.name = f"{record.reference} - {record.fournisseur_id.name} - {record.date_prevue}"
            else:
                record.name = record.reference or 'Nouveau'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception.notice') or 'Nouveau'
        return super().create(vals_list)

    def action_confirm(self):
        """Confirme l'avis préalable de réception"""
        for record in self:
            if not record.line_ids:
                raise UserError(_("Vous ne pouvez pas confirmer un avis préalable sans lignes."))
            record.write({'state': 'confirmed'})
        return True

    def action_notify_supplier(self):
        """Notifie le fournisseur de l'avis préalable"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Vous ne pouvez notifier le fournisseur que pour un avis préalable confirmé."))

        # Envoi d'email au fournisseur
        template = self.env.ref('e_gestock_reception.email_template_reception_notice')
        if template:
            template.send_mail(self.id, force_send=True)

        self.write({'state': 'notified'})
        return True

    def action_cancel(self):
        """Annule l'avis préalable de réception"""
        for record in self:
            if record.state == 'received':
                raise UserError(_("Vous ne pouvez pas annuler un avis préalable déjà réceptionné."))
            record.write({'state': 'cancelled'})
        return True

    def action_create_reception(self):
        """Crée une réception à partir de l'avis préalable"""
        self.ensure_one()
        if self.state not in ['confirmed', 'notified']:
            raise UserError(_("Vous ne pouvez créer une réception que pour un avis préalable confirmé ou notifié."))

        if self.reception_id:
            raise UserError(_("Une réception a déjà été créée pour cet avis préalable."))

        # Création de la réception
        reception_vals = {
            'purchase_order_id': self.purchase_order_id.id,
            'depot_id': self.depot_id.id,
            'date': fields.Date.context_today(self),
            'responsable_id': self.env.user.id,
            'comite_reception_id': self.purchase_order_id.comite_reception_id.id,
            'notes': _("Créé depuis l'avis préalable %s") % self.reference,
        }

        reception = self.env['e_gestock.reception'].create(reception_vals)

        # Création des lignes de réception
        for line in self.line_ids:
            reception_line_vals = {
                'reception_id': reception.id,
                'purchase_line_id': line.purchase_line_id.id,
                'article_id': line.article_id.id,
                'designation': line.designation,
                'quantite_commandee': line.quantite_attendue,
                'quantite_deja_recue': line.purchase_line_id.qty_received,
                'quantite_recue': 0.0,
            }
            self.env['e_gestock.reception_line'].create(reception_line_vals)

        # Mise à jour de l'avis préalable
        self.write({
            'reception_id': reception.id,
            'state': 'received'
        })

        # Redirection vers la réception créée
        return {
            'name': _('Réception'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception',
            'res_id': reception.id,
            'type': 'ir.actions.act_window',
        }

    def action_view_reception(self):
        """Affiche la réception associée à cet avis préalable"""
        self.ensure_one()

        if not self.reception_id:
            return

        return {
            'name': _('Réception'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception',
            'res_id': self.reception_id.id,
            'type': 'ir.actions.act_window',
        }


class ReceptionNoticeLine(models.Model):
    _name = 'e_gestock.reception.notice.line'
    _description = 'Ligne d\'avis préalable de réception'
    _order = 'id'

    notice_id = fields.Many2one('e_gestock.reception.notice', string='Avis préalable', required=True, ondelete='cascade')
    purchase_line_id = fields.Many2one('e_gestock.purchase_order_line', string='Ligne de commande', required=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    designation = fields.Char(string='Désignation', required=True)
    quantite_attendue = fields.Float(string='Quantité attendue', required=True, digits='Product Unit of Measure')
    quantite_deja_recue = fields.Float(string='Quantité déjà reçue', digits='Product Unit of Measure')
    emplacement_id = fields.Many2one('e_gestock.emplacement', string='Emplacement de destination')
    instructions_specifiques = fields.Text(string='Instructions spécifiques')

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line(self):
        if self.purchase_line_id:
            product = self.purchase_line_id.product_id
            article = self.env['e_gestock.article'].search([('product_id', '=', product.id)], limit=1)

            self.article_id = article.id if article else False
            self.designation = self.purchase_line_id.name
            self.quantite_attendue = self.purchase_line_id.product_qty - self.purchase_line_id.qty_received
            self.quantite_deja_recue = self.purchase_line_id.qty_received
