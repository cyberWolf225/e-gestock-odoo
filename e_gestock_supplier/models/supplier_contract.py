from odoo import api, fields, models, _
from datetime import timedelta

class SupplierContract(models.Model):
    _name = 'e_gestock.supplier_contract'
    _description = 'Contrat fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_debut desc, id desc'

    # Informations générales
    reference = fields.Char(
        string='Référence',
        required=True,
        readonly=True,
        default='Nouveau',
        tracking=True)
    name = fields.Char(
        string='Titre',
        required=True,
        tracking=True)
    supplier_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        tracking=True)
    type = fields.Selection([
        ('framework', 'Contrat cadre'),
        ('punctual', 'Contrat ponctuel'),
        ('service', 'Contrat de service'),
        ('maintenance', 'Contrat de maintenance')
    ], string='Type de contrat', required=True, tracking=True)
    date_debut = fields.Date(
        string='Date de début',
        required=True,
        tracking=True)
    date_fin = fields.Date(
        string='Date de fin',
        tracking=True)
    date_signature = fields.Date(
        string='Date de signature',
        tracking=True)

    # Informations financières
    montant = fields.Monetary(
        string='Montant',
        tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id.id)
    conditions_paiement = fields.Char(
        string='Conditions de paiement',
        tracking=True)
    remise = fields.Float(
        string='Remise (%)',
        digits='Discount',
        tracking=True)

    # Responsables et validations
    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        default=lambda self: self.env.user)
    validateur_id = fields.Many2one(
        'res.users',
        string='Validateur',
        tracking=True)
    date_validation = fields.Date(
        string='Date de validation',
        tracking=True)

    # Statut et suivi
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('validated', 'Validé'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('terminated', 'Résilié'),
        ('renewed', 'Renouvelé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    active = fields.Boolean(
        string='Actif',
        default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)

    # Renouvellement
    renew_auto = fields.Boolean(
        string='Renouvellement automatique',
        default=False,
        tracking=True)
    renewal_reminder = fields.Integer(
        string='Rappel renouvellement (jours)',
        default=30)
    renewal_count = fields.Integer(
        string='Nombre de renouvellements',
        default=0,
        tracking=True)
    renewal_date = fields.Date(
        string='Prochaine date de renouvellement',
        compute='_compute_renewal_date',
        store=True)
    parent_id = fields.Many2one(
        'e_gestock.supplier_contract',
        string='Contrat d\'origine',
        readonly=True)
    renewal_ids = fields.One2many(
        'e_gestock.supplier_contract',
        'parent_id',
        string='Renouvellements')

    # Caractéristiques
    is_exclusive = fields.Boolean(
        string='Exclusivité',
        default=False,
        tracking=True,
        help="Le fournisseur est le seul autorisé pour ces articles ou familles")
    famille_ids = fields.Many2many(
        'e_gestock.famille',
        string='Familles d\'articles concernées')
    note = fields.Text(
        string='Notes')

    # Relations
    clause_ids = fields.One2many(
        'e_gestock.contract_clause',
        'contract_id',
        string='Clauses')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes')
    purchase_order_ids = fields.One2many(
        'e_gestock.purchase_order',
        'e_gestock_contract_id',
        string='Commandes liées')

    # Statistiques
    purchase_count = fields.Integer(
        string='Nombre de commandes',
        compute='_compute_purchase_count')
    total_purchase_amount = fields.Monetary(
        string='Montant total des achats',
        compute='_compute_purchase_count',
        currency_field='currency_id')

    _sql_constraints = [
        ('reference_uniq', 'unique(reference)', 'La référence du contrat doit être unique !')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.supplier_contract') or 'Nouveau'
        return super(SupplierContract, self).create(vals_list)

    @api.depends('date_fin', 'renewal_reminder')
    def _compute_renewal_date(self):
        for contract in self:
            if contract.date_fin:
                contract.renewal_date = contract.date_fin - timedelta(days=contract.renewal_reminder)
            else:
                contract.renewal_date = False

    def _compute_purchase_count(self):
        for contract in self:
            purchases = contract.purchase_order_ids.filtered(lambda o: o.state in ['purchase', 'done'])
            contract.purchase_count = len(purchases)
            contract.total_purchase_amount = sum(p.amount_total for p in purchases)

    def action_submit(self):
        """Soumet le contrat pour validation"""
        self.ensure_one()
        if self.state == 'draft':
            self.state = 'submitted'

            # Créer une activité pour le responsable des achats
            user_id = self.env.ref('e_gestock_base.group_purchase_manager').users[0].id if self.env.ref('e_gestock_base.group_purchase_manager').users else self.env.user.id

            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Contrat à valider'),
                note=_('Le contrat %s a été soumis pour validation.') % self.reference,
                user_id=user_id,
                date_deadline=fields.Date.today() + timedelta(days=3)
            )

        return True

    def action_validate(self):
        """Valide le contrat"""
        self.ensure_one()
        if self.state in ['draft', 'submitted']:
            self.write({
                'state': 'validated',
                'validateur_id': self.env.user.id,
                'date_validation': fields.Date.today()
            })

            # Si la date de début est aujourd'hui ou dans le passé, activer le contrat
            if self.date_debut <= fields.Date.today():
                self.action_activate()

        return True

    def action_activate(self):
        """Active le contrat"""
        self.ensure_one()
        if self.state == 'validated':
            if not self.date_signature:
                self.date_signature = fields.Date.today()
            self.state = 'active'
        return True

    def action_terminate(self):
        """Résilie le contrat"""
        self.ensure_one()
        if self.state == 'active':
            self.state = 'terminated'
        return True

    def action_cancel(self):
        """Annule le contrat"""
        self.ensure_one()
        if self.state in ['draft', 'submitted', 'validated']:
            self.state = 'cancelled'
        return True

    def action_renew(self):
        """Renouvelle le contrat"""
        self.ensure_one()
        if self.state in ['active', 'expired']:
            # Calculer les nouvelles dates
            old_date_debut = self.date_debut
            old_date_fin = self.date_fin
            duration = (old_date_fin - old_date_debut).days if old_date_fin else 365

            new_date_debut = fields.Date.today()
            new_date_fin = new_date_debut + timedelta(days=duration)

            # Créer le nouveau contrat
            new_contract = self.copy({
                'reference': 'Nouveau',
                'name': f"{self.name} (Renouvellement {self.renewal_count + 1})",
                'date_debut': new_date_debut,
                'date_fin': new_date_fin,
                'date_signature': False,
                'date_validation': False,
                'state': 'draft',
                'parent_id': self.id,
                'renewal_count': 0,
                'validateur_id': False,
            })

            # Mettre à jour le contrat actuel
            self.write({
                'state': 'renewed',
                'renewal_count': self.renewal_count + 1,
                'active': False
            })

            # Ouvrir le nouveau contrat
            return {
                'name': _('Contrat renouvelé'),
                'type': 'ir.actions.act_window',
                'res_model': 'e_gestock.supplier_contract',
                'res_id': new_contract.id,
                'view_mode': 'form',
                'target': 'current',
            }

        return True

    def action_view_purchases(self):
        """Affiche les commandes liées au contrat"""
        self.ensure_one()
        action = {
            'name': _('Commandes'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.purchase_order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'default_e_gestock_contract_id': self.id}
        }
        return action

    @api.model
    def _cron_check_expiring_contracts(self):
        """Vérifie les contrats qui vont expirer bientôt"""
        today = fields.Date.today()

        # Trouver les contrats actifs qui arrivent à expiration
        contracts = self.search([
            ('state', '=', 'active'),
            ('date_fin', '!=', False),
            ('renewal_date', '<=', today)
        ])

        for contract in contracts:
            # Si le contrat arrive à expiration, créer une activité
            if contract.date_fin <= today:
                contract.state = 'expired'

                # Renouveler automatiquement si configuré
                if contract.renew_auto:
                    contract.action_renew()

            # Sinon, notifier pour le renouvellement
            else:
                days_before_expiry = (contract.date_fin - today).days

                contract.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Contrat à renouveler'),
                    note=_('Le contrat %s expire dans %s jours.') % (contract.reference, days_before_expiry),
                    user_id=contract.responsable_id.id,
                    date_deadline=contract.date_fin
                )