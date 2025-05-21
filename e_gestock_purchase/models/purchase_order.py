from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    demande_cotation_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation d\'origine',
                                        readonly=True)
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation sélectionnée', readonly=True)

    # Circuit de validation
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

    # Signataires
    signataire_ids = fields.Many2many('res.users', string='Signataires sélectionnés')

    # Commentaires des validateurs
    cmp_comment = fields.Text(string='Commentaire CMP')
    budget_comment = fields.Text(string='Commentaire contrôle budgétaire')
    dcg_dept_comment = fields.Text(string='Commentaire Chef Département DCG')
    dcg_comment = fields.Text(string='Commentaire Responsable DCG')
    dgaaf_comment = fields.Text(string='Commentaire DGAAF')
    dg_comment = fields.Text(string='Commentaire DG')

    # Dates supplémentaires
    date_retrait = fields.Date(string='Date de retrait')
    date_livraison_prevue = fields.Date(string='Date de livraison prévue')
    date_livraison_reelle = fields.Date(string='Date de livraison réelle')

    # Comité de réception
    comite_reception_id = fields.Many2one('res.users', string='Comité de réception assigné')

    # Bon de livraison
    bl_attachment = fields.Binary(string='Bon de livraison')
    bl_filename = fields.Char(string='Nom du fichier BL')

    # Seuil pour validation DG ou DGAAF
    seuil_validation_dg = fields.Float(string='Seuil de validation DG',
                                     default=lambda self: self.env['ir.config_parameter'].sudo().get_param('e_gestock_purchase.seuil_validation_dg', 5000000.0),
                                     readonly=True)

    @api.depends('amount_total')
    def _compute_validation_level(self):
        """Détermine si le bon de commande doit être validé par le DG ou le DGAAF"""
        for po in self:
            if po.amount_total >= po.seuil_validation_dg:
                po.needs_dg_validation = True
            else:
                po.needs_dg_validation = False

    needs_dg_validation = fields.Boolean(string='Nécessite validation DG', compute='_compute_validation_level', store=True)

    def action_validate_cmp(self):
        """Validation par le responsable CMP"""
        self.write({
            'state_approbation': 'cmp_validated'
        })
        return True

    def action_validate_budget(self):
        """Validation par le contrôle budgétaire"""
        self.write({
            'state_approbation': 'budget_validated'
        })
        return True

    def action_validate_dcg_dept(self):
        """Validation par le chef département DCG"""
        self.write({
            'state_approbation': 'dcg_dept_validated'
        })
        return True

    def action_validate_dcg(self):
        """Validation par le responsable DCG"""
        self.write({
            'state_approbation': 'dcg_validated'
        })
        return True

    def action_validate_dgaaf(self):
        """Validation par le DGAAF"""
        if self.needs_dg_validation:
            raise UserError(_("Ce bon de commande doit être validé par le DG car son montant dépasse le seuil de %s.") % self.seuil_validation_dg)

        self.write({
            'state_approbation': 'dgaaf_validated'
        })
        return True

    def action_validate_dg(self):
        """Validation par le DG"""
        if not self.needs_dg_validation:
            raise UserError(_("Ce bon de commande doit être validé par le DGAAF car son montant est inférieur au seuil de %s.") % self.seuil_validation_dg)

        self.write({
            'state_approbation': 'dg_validated'
        })
        return True

    def action_approve_final(self):
        """Approuve le bon de commande après les validations"""
        self.ensure_one()

        if self.state_approbation not in ['dgaaf_validated', 'dg_validated']:
            raise UserError(_("Le bon de commande n'a pas encore été validé par toutes les parties."))

        self.write({
            'state_approbation': 'approved',
            'date_approval': fields.Date.today(),
        })

        # Envoyer l'email au fournisseur avec le BC en pièce jointe
        template = self.env.ref('e_gestock_purchase.email_template_purchase_order_created')
        if template:
            template.send_mail(self.id, force_send=True)

        # Message dans le chatter
        self.message_post(
            body=_("Bon de commande approuvé et envoyé au fournisseur."),
            subtype_id=self.env.ref('mail.mt_note').id
        )

        # Confirmer le bon de commande standard
        self.button_confirm()

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
        if self.comite_reception_id:
            template = self.env.ref('e_gestock_purchase.email_template_delivery_notification')
            if template:
                template.send_mail(self.id, force_send=True)

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

    # Ajout d'une méthode pour notification après la réception
    def action_notify_reception_complete(self):
        """Envoie une notification au demandeur après la réception"""
        self.ensure_one()

        if self.state_approbation != 'received':
            return False

        # Envoyer l'email au demandeur
        if self.demande_cotation_id and self.demande_cotation_id.demandeur_id:
            template = self.env.ref('e_gestock_purchase.email_template_reception_completed')
            if template:
                template.send_mail(self.id, force_send=True)

                # Message dans le chatter
                self.message_post(
                    body=_("Notification de réception envoyée au demandeur %s.") %
                        self.demande_cotation_id.demandeur_id.name,
                    subtype_id=self.env.ref('mail.mt_note').id
                )

        return True

    def button_confirm(self):
        """Surcharge de la méthode de confirmation pour intégrer le circuit E-GESTOCK"""
        # Si le bon de commande provient d'une cotation E-GESTOCK, le circuit spécifique est requis
        if self.cotation_id or self.demande_cotation_id:
            raise UserError(_("Ce bon de commande doit suivre le circuit de validation E-GESTOCK."))

        # Vérifier si l'utilisateur a les droits E-GESTOCK appropriés
        if self.amount_total >= 5000000 and not self.env.user.has_group('e_gestock_base.group_dg_validator'):
            raise UserError(_("Seul le DG peut valider les commandes de plus de 5 000 000."))
        elif self.amount_total >= 1000000 and not self.env.user.has_group('e_gestock_base.group_dgaa_validator'):
            raise UserError(_("Seul le DGAA peut valider les commandes de plus de 1 000 000."))

        # Sinon, on utilise le comportement standard
        return super(PurchaseOrder, self).button_confirm()

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        """Surcharge de la méthode de vérification des droits d'accès pour prendre en compte les groupes E-GESTOCK"""
        # Si l'utilisateur a un rôle E-GESTOCK, on lui accorde les droits
        if (self.env.user.has_group('e_gestock_base.group_e_gestock_purchase_user') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_purchase_manager') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_resp_dmp') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_budget_controller') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_resp_dfc') or
            self.env.user.has_group('e_gestock_base.group_dfc_validator') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_direction') or
            self.env.user.has_group('e_gestock_base.group_e_gestock_admin')):
            return True

        # Sinon, on utilise le comportement standard
        return super(PurchaseOrder, self).check_access_rights(operation, raise_exception)