from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import uuid


class DemandeCotationFournisseur(models.Model):
    _name = 'e_gestock.demande_cotation_fournisseur'
    _description = 'Demande de cotation fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date_envoi desc, id desc'

    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation',
                               required=True, ondelete='cascade', tracking=True)
    reference = fields.Char(string='Référence', required=True, readonly=True, default='/',
                          tracking=True, copy=False)

    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True,
                                domain=[('supplier_rank', '>', 0)], tracking=True)

    date_envoi = fields.Date(string='Date d\'envoi', default=fields.Date.context_today,
                           required=True, tracking=True)
    date_echeance = fields.Date(string='Date d\'échéance', required=True, tracking=True)
    code_echeance = fields.Selection([
        ('standard', 'Standard (7 jours)'),
        ('urgent', 'Urgent (3 jours)'),
        ('tres_urgent', 'Très urgent (1 jour)'),
    ], string='Code d\'échéance', default='standard', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('received', 'Reçue'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)

    type_achat = fields.Selection([
        ('direct', 'Achat direct'),
        ('appel_offre', 'Appel d\'offres'),
        ('consultation', 'Consultation restreinte')
    ], string='Type d\'achat', default='direct', required=True, tracking=True)

    taux_acompte = fields.Float(string='Taux d\'acompte (%)', default=0.0, tracking=True)

    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation reçue')

    company_id = fields.Many2one('res.company', string='Société', related='demande_id.company_id',
                              store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Devise', related='demande_id.currency_id',
                               store=True, readonly=True)

    # Fields for portal access
    access_token = fields.Char('Token d\'accès', copy=False)
    access_url = fields.Char('URL d\'accès', compute='_compute_access_url')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', '/') == '/':
                demande = self.env['e_gestock.demande_cotation'].browse(vals.get('demande_id'))
                supplier = self.env['res.partner'].browse(vals.get('supplier_id'))
                vals['reference'] = f"{demande.reference}/F/{supplier.name[:3].upper()}"

            # Calculer la date d'échéance en fonction du code
            if vals.get('code_echeance') and not vals.get('date_echeance'):
                date_envoi = vals.get('date_envoi') or fields.Date.context_today(self)
                if isinstance(date_envoi, str):
                    date_envoi = fields.Date.from_string(date_envoi)

                days = 7  # Standard
                if vals['code_echeance'] == 'urgent':
                    days = 3
                elif vals['code_echeance'] == 'tres_urgent':
                    days = 1

                vals['date_echeance'] = date_envoi + timedelta(days=days)

        return super(DemandeCotationFournisseur, self).create(vals_list)

    @api.onchange('code_echeance', 'date_envoi')
    def _onchange_code_echeance(self):
        if self.code_echeance and self.date_envoi:
            days = 7  # Standard
            if self.code_echeance == 'urgent':
                days = 3
            elif self.code_echeance == 'tres_urgent':
                days = 1

            self.date_echeance = self.date_envoi + timedelta(days=days)

    @api.onchange('demande_id')
    def _onchange_demande_id(self):
        """Affiche un message pour indiquer que les articles seront automatiquement ajoutés lors de la création de la cotation"""
        if self.demande_id:
            return {
                'warning': {
                    'title': _('Information'),
                    'message': _('Les articles de la demande seront automatiquement ajoutés lors de la création de la cotation.')
                }
            }

    def _compute_access_url(self):
        for record in self:
            record.access_url = f'/my/quotation_requests/{record.id}?access_token={record.access_token}'

    def _generate_access_token(self):
        for record in self:
            if not record.access_token:
                record.access_token = self.env['ir.config_parameter'].sudo().get_param('database.uuid') + str(record.id)
        return True

    def action_send(self):
        """Envoie la demande de cotation au fournisseur"""
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("Cette demande ne peut pas être envoyée car elle n'est pas en état brouillon."))

        if not self.supplier_id.email:
            raise UserError(_("Le fournisseur %s n'a pas d'adresse email. Veuillez en ajouter une.") % self.supplier_id.name)

        # Générer un token d'accès au portail s'il n'existe pas déjà
        if not self.access_token:
            self.access_token = uuid.uuid4().hex

        # Préparer l'URL d'accès au portail
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.access_url = '%s/my/demandes/%s?access_token=%s' % (base_url, self.id, self.access_token)

        # Mise à jour de l'état
        self.write({
            'state': 'sent',
        })

        # Envoyer l'email au fournisseur
        template = self.env.ref('e_gestock_purchase.email_template_new_supplier_quotation_request')
        if template:
            template.send_mail(self.id, force_send=True)

        # Mettre à jour l'état de la demande principale si nécessaire
        if self.demande_id.state == 'approved':
            self.demande_id.write({
                'state': 'quotation'
            })

        # Message dans le chatter
        self.message_post(
            body=_("Demande de cotation envoyée à %s") % self.supplier_id.name,
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_cancel(self):
        """Annule la demande de cotation"""
        self.write({'state': 'cancelled'})
        return True

    def action_reset_to_draft(self):
        """Remet la demande en brouillon"""
        if self.state != 'cancelled':
            raise UserError(_("Seules les demandes annulées peuvent être remises en brouillon."))

        self.write({'state': 'draft'})
        return True

    def action_set_received(self):
        """Marque la demande comme reçue (cotation soumise par le fournisseur)"""
        self.write({'state': 'received'})
        return True

    def name_get(self):
        """Personnalisation de l'affichage du nom des demandes de cotation fournisseur"""
        result = []
        for record in self:
            name = f"{record.reference or ''} - {record.supplier_id.name or ''}"
            result.append((record.id, name))
        return result