from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class EgestockPurchaseOrder(models.Model):
    _name = 'e_gestock.purchase_order'
    _description = 'Bon de commande E-GESTOCK'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_order desc, id desc'

    name = fields.Char('Référence', required=True, copy=False, default='Nouveau', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Fournisseur', required=True, tracking=True)
    date_order = fields.Datetime(string='Date de commande', required=True, default=fields.Datetime.now, tracking=True)
    date_planned = fields.Datetime(string='Date de livraison prévue', tracking=True)
    user_id = fields.Many2one('res.users', string='Acheteur', default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', string='Société', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Devise', required=True,
                                default=lambda self: self.env.company.currency_id.id)

    # Champs financiers
    amount_untaxed = fields.Monetary(string='Montant HT', store=True, compute='_compute_amount', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, compute='_compute_amount', tracking=True)
    amount_total = fields.Monetary(string='Total', store=True, compute='_compute_amount', tracking=True)

    # Lignes de commande
    order_line = fields.One2many('e_gestock.purchase_order_line', 'order_id', string='Lignes de commande')

    # État de la commande
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('to_approve', 'À approuver'),
        ('approved', 'Approuvé'),
        ('done', 'Terminé'),
        ('cancel', 'Annulé')
    ], string='État', default='draft', tracking=True, copy=False)

    # Circuit de validation E-GESTOCK
    state_approbation = fields.Selection([
        ('draft', 'Brouillon'),
        ('cmp_validated', 'Validé par CMP'),
        ('budget_validated', 'Validé par contrôle budgétaire'),
        ('dcg_dept_validated', 'Validé par Chef Département DCG'),
        ('dcg_validated', 'Validé par Responsable DCG'),
        ('dgaaf_validated', 'Validé par DGAAF'),
        ('dg_validated', 'Validé par DG'),
        ('approved', 'Approuvé'),
        ('withdrawn', 'Retiré par le fournisseur'),
        ('delivered', 'Livré'),
        ('received', 'Réceptionné'),
        ('cancelled', 'Annulé')
    ], string='État d\'approbation', default='draft', tracking=True, copy=False)

    # Liens avec E-GESTOCK
    demande_cotation_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation d\'origine',
                                        readonly=True, copy=False, tracking=True)
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation sélectionnée',
                                readonly=True, copy=False, tracking=True)

    # Signataires
    signataire_ids = fields.Many2many('res.users', string='Signataires sélectionnés')

    # Commentaires des validateurs
    cmp_comment = fields.Text(string='Commentaire CMP')
    budget_comment = fields.Text(string='Commentaire contrôle budgétaire')
    dcg_dept_comment = fields.Text(string='Commentaire Chef Département DCG')
    dcg_comment = fields.Text(string='Commentaire Responsable DCG')
    dgaaf_comment = fields.Text(string='Commentaire DGAAF')
    dg_comment = fields.Text(string='Commentaire DG')
    reception_comment = fields.Text(string='Commentaire comité de réception')

    # Utilisateurs qui ont validé chaque étape
    cmp_validator_id = fields.Many2one('res.users', string='Validé par (CMP)', readonly=True)
    budget_validator_id = fields.Many2one('res.users', string='Validé par (Budget)', readonly=True)
    dcg_dept_validator_id = fields.Many2one('res.users', string='Validé par (Chef Dép. DCG)', readonly=True)
    dcg_validator_id = fields.Many2one('res.users', string='Validé par (Resp. DCG)', readonly=True)
    dgaaf_validator_id = fields.Many2one('res.users', string='Validé par (DGAAF)', readonly=True)
    dg_validator_id = fields.Many2one('res.users', string='Validé par (DG)', readonly=True)
    reception_validator_id = fields.Many2one('res.users', string='Validé par (Réception)', readonly=True)

    # Dates de validation
    cmp_validation_date = fields.Datetime(string='Date validation CMP', readonly=True)
    budget_validation_date = fields.Datetime(string='Date validation Budget', readonly=True)
    dcg_dept_validation_date = fields.Datetime(string='Date validation Chef Dép. DCG', readonly=True)
    dcg_validation_date = fields.Datetime(string='Date validation Resp. DCG', readonly=True)
    dgaaf_validation_date = fields.Datetime(string='Date validation DGAAF', readonly=True)
    dg_validation_date = fields.Datetime(string='Date validation DG', readonly=True)
    reception_validation_date = fields.Datetime(string='Date validation Réception', readonly=True)

    # Dates supplémentaires
    date_approval = fields.Date(string='Date d\'approbation')
    date_retrait = fields.Date(string='Date de retrait')
    date_livraison_prevue = fields.Date(string='Date de livraison prévue')
    date_livraison_reelle = fields.Date(string='Date de livraison réelle')

    # Comité de réception
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception assigné',
                                  tracking=True, domain=[('active', '=', True)])
    reception_committee_id = fields.Many2one('e_gestock.reception_committee', string='Ancien comité de réception',
                                           tracking=True)
    committee_responsible_id = fields.Many2one('res.users', string='Responsable du comité',
                                             related='committee_id.responsible_id', readonly=True)
    committee_members = fields.Many2many('res.users', string='Membres du comité',
                                       related='committee_id.member_ids', readonly=True)

    # Bon de livraison
    bl_attachment = fields.Binary(string='Bon de livraison')
    bl_filename = fields.Char(string='Nom du fichier BL')

    # Seuil pour validation DG ou DGAAF
    seuil_validation_dg = fields.Float(string='Seuil de validation DG',
                                     default=lambda self: self.env['ir.config_parameter'].sudo().get_param('e_gestock_purchase.seuil_validation_dg', 5000000.0),
                                     readonly=True)

    # Champs supplémentaires
    notes = fields.Text(string='Notes')
    origin = fields.Char(string='Document d\'origine')

    @api.depends('order_line.price_subtotal')
    def _compute_amount(self):
        """Calcule les montants totaux de la commande"""
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_untaxed + amount_tax

    @api.depends('amount_total')
    def _compute_validation_level(self):
        """Détermine si le bon de commande doit être validé par le DG ou le DGAAF"""
        for po in self:
            if po.amount_total >= po.seuil_validation_dg:
                po.needs_dg_validation = True
            else:
                po.needs_dg_validation = False

    needs_dg_validation = fields.Boolean(string='Nécessite validation DG', compute='_compute_validation_level', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode de création pour générer la séquence"""
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('e_gestock.purchase_order') or 'Nouveau'
        return super(EgestockPurchaseOrder, self).create(vals_list)

    def action_validate_cmp(self):
        """Validation par le responsable CMP"""
        self.ensure_one()

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation CMP'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'cmp',
                'default_next_state': 'cmp_validated',
            }
        }

    def action_validate_budget(self):
        """Validation par le contrôle budgétaire"""
        self.ensure_one()

        # Vérifier si le contrôle budgétaire a été effectué
        if hasattr(self, 'budget_control_id') and not self.budget_control_id:
            # Essayer de créer un contrôle budgétaire automatiquement
            try:
                self.action_check_budget()
            except Exception as e:
                # Si la création échoue, afficher un avertissement
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Attention'),
                        'message': _("Le contrôle budgétaire n'a pas été effectué. Veuillez le faire avant de valider."),
                        'sticky': True,
                        'type': 'warning',
                    }
                }

        # Si le contrôle budgétaire existe mais n'est pas approuvé
        if hasattr(self, 'budget_control_id') and self.budget_control_id and hasattr(self.budget_control_id, 'state'):
            if self.budget_control_id.state != 'approved':
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Attention'),
                        'message': _("Le contrôle budgétaire n'a pas été approuvé. Veuillez l'approuver avant de valider."),
                        'sticky': True,
                        'type': 'warning',
                    }
                }

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation Contrôle Budgétaire'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'budget',
                'default_next_state': 'budget_validated',
            }
        }

    def action_validate_dcg_dept(self):
        """Validation par le chef département DCG"""
        self.ensure_one()

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation Chef Département DCG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'dcg_dept',
                'default_next_state': 'dcg_dept_validated',
            }
        }

    def action_validate_dcg(self):
        """Validation par le responsable DCG"""
        self.ensure_one()

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation Responsable DCG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'dcg',
                'default_next_state': 'dcg_validated',
            }
        }

    def action_validate_dgaaf(self):
        """Validation par le DGAAF"""
        self.ensure_one()

        if self.needs_dg_validation:
            raise UserError(_("Ce bon de commande doit être validé par le DG car son montant dépasse le seuil de %s.") % self.seuil_validation_dg)

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation DGAAF'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'dgaaf',
                'default_next_state': 'dgaaf_validated',
            }
        }

    def action_validate_dg(self):
        """Validation par le DG"""
        self.ensure_one()

        if not self.needs_dg_validation:
            raise UserError(_("Ce bon de commande doit être validé par le DGAAF car son montant est inférieur au seuil de %s.") % self.seuil_validation_dg)

        # Ouvrir l'assistant de validation avec commentaire
        return {
            'name': _('Validation DG'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validation_comment_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_validation_type': 'dg',
                'default_next_state': 'dg_validated',
            }
        }

    def action_approve_final(self):
        """Approuve le bon de commande après les validations"""
        self.ensure_one()

        if self.state_approbation not in ['dgaaf_validated', 'dg_validated']:
            raise UserError(_("Le bon de commande n'a pas encore été validé par toutes les parties."))

        self.write({
            'state': 'approved',
            'state_approbation': 'approved',
            'date_approval': fields.Date.today(),
        })

        # Envoyer l'email au fournisseur avec le BC en pièce jointe
        template = self.env.ref('e_gestock_purchase.email_template_purchase_order_created', False)
        if template:
            template.send_mail(self.id, force_send=True)

        # Message dans le chatter
        self.message_post(
            body=_("Bon de commande approuvé et envoyé au fournisseur."),
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_withdraw(self):
        """Marquer le bon de commande comme retiré"""
        self.ensure_one()

        if self.state_approbation != 'approved':
            raise UserError(_("Le bon de commande doit être approuvé avant d'être retiré."))

        self.write({
            'state_approbation': 'withdrawn',
            'date_retrait': fields.Date.today(),
        })

        # Message dans le chatter
        self.message_post(
            body=_("Bon de commande retiré par le fournisseur."),
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_set_delivered(self):
        """Marquer le bon de commande comme livré"""
        self.ensure_one()

        if self.state_approbation != 'withdrawn':
            raise UserError(_("Le bon de commande doit être retiré avant d'être livré."))

        self.write({
            'state_approbation': 'delivered',
            'date_livraison_reelle': fields.Date.today(),
        })

        # Envoyer une notification au comité de réception
        if self.committee_id:
            template = self.env.ref('e_gestock_purchase.email_template_delivery_notification', False)
            if template:
                # Envoyer au responsable du comité
                if self.committee_responsible_id:
                    template.send_mail(self.id, force_send=True, email_values={'email_to': self.committee_responsible_id.email})

                # Envoyer aux membres du comité
                for member in self.committee_members:
                    if member.email:
                        template.send_mail(self.id, force_send=True, email_values={'email_to': member.email})

        # Message dans le chatter
        self.message_post(
            body=_("Commande livrée. En attente de réception par le comité."),
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_reception(self):
        """Ouvre l'assistant de réception"""
        self.ensure_one()

        if self.state_approbation != 'delivered':
            raise UserError(_("Le bon de commande doit être livré avant d'être réceptionné."))

        # Ouvrir l'assistant de validation de réception
        return {
            'name': _('Valider la réception'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validate_reception_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
            }
        }

    def action_cancel(self):
        """Annuler le bon de commande"""
        self.write({
            'state': 'cancel',
            'state_approbation': 'cancelled',
        })
        return True

    def action_draft(self):
        """Remettre en brouillon"""
        self.write({
            'state': 'draft',
            'state_approbation': 'draft',
        })
        return True

    def action_send_rfq(self):
        """Envoyer la demande de prix au fournisseur"""
        self.ensure_one()

        # Marquer comme envoyé
        self.write({
            'state': 'sent',
        })

        # Envoyer l'email
        template = self.env.ref('e_gestock_purchase.email_template_purchase_order_sent', False)
        if template:
            template.send_mail(self.id, force_send=True)

        return True
