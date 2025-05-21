from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class PVReception(models.Model):
    _name = 'e_gestock.pv_reception'
    _description = 'Procès-verbal de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, tracking=True,
                                 domain=[('state', '=', 'comite_validation')])
    comite_id = fields.Many2one('e_gestock.comite_reception', string='Ancien Comité',
                             related='reception_id.comite_reception_id', store=True, readonly=True)
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité',
                                related='reception_id.committee_id', store=True, readonly=True)

    # Signatures
    president_signature = fields.Boolean(string='Signature président', default=False, tracking=True)
    secretaire_signature = fields.Boolean(string='Signature secrétaire', default=False, tracking=True)
    membre_signature_ids = fields.One2many('e_gestock.pv_signature', 'pv_id', string='Signatures membres')

    quorum_atteint = fields.Boolean(string='Quorum atteint', compute='_compute_quorum_atteint', store=True)
    observation = fields.Text(string='Observations', tracking=True)

    decision = fields.Selection([
        ('accepted', 'Accepté'),
        ('accepted_reserve', 'Accepté avec réserves'),
        ('rejected', 'Rejeté')
    ], string='Décision', required=True, default='accepted', tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)

    reserve_ids = fields.One2many('e_gestock.pv_reserve', 'pv_id', string='Réserves')

    # Documents
    pv_attachment = fields.Binary(string='Document PV signé', attachment=True)
    pv_filename = fields.Char(string='Nom du fichier PV')

    # Pour suivi et auditing
    created_by_id = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user, readonly=True)
    date_validation = fields.Datetime(string='Date de validation', readonly=True)

    # Champs liés à la société
    company_id = fields.Many2one('res.company', string='Société',
                               default=lambda self: self.env.company,
                               required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.pv_reception') or 'Nouveau'
        return super(PVReception, self).create(vals_list)

    @api.depends('president_signature', 'secretaire_signature', 'membre_signature_ids.signed')
    def _compute_quorum_atteint(self):
        for pv in self:
            # Compter les signatures
            signatures_count = (1 if pv.president_signature else 0) + (1 if pv.secretaire_signature else 0)
            signatures_count += len(pv.membre_signature_ids.filtered(lambda s: s.signed))

            # Vérifier si le quorum est atteint
            if pv.committee_id:
                quorum_required = pv.committee_id.quorum
            elif pv.comite_id:
                quorum_required = pv.comite_id.quorum
            else:
                quorum_required = 3

            pv.quorum_atteint = signatures_count >= quorum_required

    @api.onchange('reception_id')
    def _onchange_reception_id(self):
        if self.reception_id:
            # Créer les lignes de signature pour les membres du comité
            if not self.membre_signature_ids:
                signatures = []

                # Utiliser le nouveau modèle de comité si disponible
                if self.reception_id.committee_id and self.reception_id.committee_id.member_ids:
                    for membre in self.reception_id.committee_id.member_ids:
                        signatures.append((0, 0, {
                            'user_id': membre.id,
                            'signed': False,
                        }))
                # Sinon, utiliser l'ancien modèle de comité
                elif self.reception_id.comite_reception_id and self.reception_id.comite_reception_id.membre_ids:
                    for membre in self.reception_id.comite_reception_id.membre_ids:
                        signatures.append((0, 0, {
                            'user_id': membre.id,
                            'signed': False,
                        }))

                if signatures:
                    self.membre_signature_ids = signatures

    def action_validate(self):
        """Valider le PV de réception"""
        self.ensure_one()

        if not self.quorum_atteint:
            raise UserError(_("Le quorum n'est pas atteint. Il manque des signatures pour valider ce PV."))

        if self.decision == 'accepted_reserve' and not self.reserve_ids:
            raise UserError(_("Veuillez spécifier au moins une réserve lorsque la décision est 'Accepté avec réserves'."))

        # Vérifier que la réception est en attente de validation
        if self.reception_id.state != 'comite_validation':
            raise UserError(_("La réception n'est pas en attente de validation par le comité."))

        # Mettre à jour l'état du PV
        self.write({
            'state': 'validated',
            'date_validation': fields.Datetime.now(),
        })

        # Mettre à jour la réception
        self.reception_id.write({
            'pv_validation': True,
        })

        # Selon la décision, mettre à jour l'état de la réception
        if self.decision in ['accepted', 'accepted_reserve']:
            self.reception_id.action_done()
        elif self.decision == 'rejected':
            self.reception_id.write({
                'state': 'confirmed',  # Retour à l'état confirmé pour correction
            })
            # Notifier le responsable de la réception
            self._notify_reception_rejected()

        return True

    def action_cancel(self):
        """Annuler le PV"""
        self.ensure_one()

        if self.state == 'validated':
            raise UserError(_("Vous ne pouvez pas annuler un PV validé."))

        self.write({
            'state': 'cancelled'
        })

        return True

    def _notify_reception_rejected(self):
        """Notifier le responsable que la réception a été rejetée"""
        self.ensure_one()

        if not self.reception_id.responsable_id:
            return

        template = self.env.ref('e_gestock_reception.mail_template_reception_rejected')
        if template:
            template.send_mail(self.id, force_send=True)

    def action_sign_president(self):
        """Signer le PV en tant que président"""
        self.ensure_one()

        # Vérifier si l'utilisateur est le président du comité
        is_president = False

        if self.committee_id and self.env.user == self.committee_id.responsible_id:
            is_president = True
        elif self.comite_id and self.env.user == self.comite_id.president_id:
            is_president = True

        if not is_president:
            raise UserError(_("Seul le président du comité peut signer ici."))

        self.write({
            'president_signature': True
        })

        return True

    def action_sign_secretaire(self):
        """Signer le PV en tant que secrétaire"""
        self.ensure_one()

        # Vérifier si l'utilisateur est le secrétaire du comité
        is_secretary = False

        if self.committee_id and self.env.user == self.committee_id.secretary_id:
            is_secretary = True
        elif self.comite_id and self.env.user == self.comite_id.secretaire_id:
            is_secretary = True

        if not is_secretary:
            raise UserError(_("Seul le secrétaire du comité peut signer ici."))

        self.write({
            'secretaire_signature': True
        })

        return True