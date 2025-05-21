from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SupplierEvaluation(models.Model):
    _name = 'e_gestock.supplier_evaluation'
    _description = 'Évaluation fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Référence',
        required=True,
        readonly=True,
        default='Nouveau',
        tracking=True)
    supplier_id = fields.Many2one(
        'res.partner',
        string='Fournisseur',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        tracking=True)
    date = fields.Date(
        string='Date d\'évaluation',
        default=fields.Date.context_today,
        required=True,
        tracking=True)
    evaluator_id = fields.Many2one(
        'res.users',
        string='Évaluateur',
        required=True,
        default=lambda self: self.env.user,
        tracking=True)
    validator_id = fields.Many2one(
        'res.users',
        string='Validateur',
        tracking=True)
    validation_date = fields.Date(
        string='Date de validation',
        tracking=True)
    period_start = fields.Date(
        string='Début période',
        required=True)
    period_end = fields.Date(
        string='Fin période',
        required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('validated', 'Validée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)
    note_ids = fields.One2many(
        'e_gestock.evaluation_note',
        'evaluation_id',
        string='Notes par critère')
    note_globale = fields.Float(
        string='Note globale',
        compute='_compute_note_globale',
        store=True,
        tracking=True)
    remarks = fields.Text(
        string='Remarques générales',
        tracking=True)
    purchase_ids = fields.Many2many(
        'e_gestock.purchase_order',
        string='Commandes concernées',
        domain="[('partner_id', '=', supplier_id), ('state', 'in', ['approved', 'withdrawn', 'delivered', 'received'])]")
    purchase_count = fields.Integer(
        string='Nombre de commandes',
        compute='_compute_purchase_count')
    active = fields.Boolean(
        string='Active',
        default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'La référence de l\'évaluation doit être unique !')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('e_gestock.supplier_evaluation') or 'Nouveau'
        return super(SupplierEvaluation, self).create(vals_list)

    @api.depends('note_ids', 'note_ids.note', 'note_ids.weight')
    def _compute_note_globale(self):
        for evaluation in self:
            if not evaluation.note_ids:
                evaluation.note_globale = 0
                continue

            total_weight = sum(note.weight for note in evaluation.note_ids)
            if total_weight:
                # Calcul de la moyenne pondérée
                weighted_sum = sum(note.note * note.weight for note in evaluation.note_ids)
                evaluation.note_globale = weighted_sum / total_weight
            else:
                evaluation.note_globale = 0

    def _compute_purchase_count(self):
        for evaluation in self:
            evaluation.purchase_count = len(evaluation.purchase_ids)

    def action_submit(self):
        """Soumet l'évaluation pour validation"""
        self.ensure_one()
        # Vérifier que tous les critères ont été notés
        criteria_count = self.env['e_gestock.evaluation_criteria'].search_count([
            ('active', '=', True)
        ])

        if len(self.note_ids) < criteria_count:
            missing_count = criteria_count - len(self.note_ids)
            raise UserError(_('Vous devez évaluer tous les critères avant de soumettre. Il manque %s critères.') % missing_count)

        self.state = 'submitted'

        # Créer une activité pour le validateur
        user_id = self.env.ref('e_gestock_base.group_supplier_manager').users[0].id if self.env.ref('e_gestock_base.group_supplier_manager').users else self.env.user.id

        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=_('Évaluation à valider'),
            note=_('L\'évaluation %s du fournisseur %s a été soumise pour validation.') % (self.name, self.supplier_id.name),
            user_id=user_id,
            date_deadline=fields.Date.today()
        )

    def action_validate(self):
        """Valide l'évaluation"""
        self.ensure_one()
        if self.state == 'submitted':
            self.write({
                'state': 'validated',
                'validator_id': self.env.user.id,
                'validation_date': fields.Date.today()
            })

    def action_cancel(self):
        """Annule l'évaluation"""
        self.ensure_one()
        if self.state in ['draft', 'submitted']:
            self.state = 'cancelled'

    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.ensure_one()
        if self.state in ['submitted', 'cancelled']:
            self.state = 'draft'

    def action_view_purchases(self):
        """Affiche les commandes liées à cette évaluation"""
        self.ensure_one()
        action = {
            'name': _('Commandes évaluées'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.purchase_order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_ids.ids)],
        }
        return action

    @api.onchange('supplier_id', 'period_start', 'period_end')
    def _onchange_supplier_period(self):
        """Affiche les commandes dans la période pour sélection"""
        if self.supplier_id and self.period_start and self.period_end:
            domain = [
                ('partner_id', '=', self.supplier_id.id),
                ('state', 'in', ['approved', 'withdrawn', 'delivered', 'received']),
                ('date_order', '>=', self.period_start),
                ('date_order', '<=', self.period_end)
            ]
            orders = self.env['e_gestock.purchase_order'].search(domain)
            self.purchase_ids = orders

    @api.onchange('supplier_id')
    def _onchange_supplier(self):
        """Ajoute automatiquement les critères d'évaluation"""
        if self.supplier_id and not self.note_ids:
            criteria = self.env['e_gestock.evaluation_criteria'].search([
                ('active', '=', True)
            ], order='sequence')

            notes = [(0, 0, {
                'criteria_id': criteria.id,
                'name': criteria.name,
                'weight': criteria.weight,
            }) for criteria in criteria]

            self.note_ids = notes