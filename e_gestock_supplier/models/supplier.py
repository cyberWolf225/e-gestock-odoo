from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Champs de catégorisation
    e_gestock_supplier_category_id = fields.Many2one(
        'e_gestock.supplier_category',
        string='Catégorie fournisseur',
        tracking=True)
    e_gestock_is_approved = fields.Boolean(
        string='Fournisseur approuvé',
        default=False,
        tracking=True,
        help="Indique si ce fournisseur a été validé par le processus d'approbation")
    e_gestock_approval_date = fields.Date(
        string='Date d\'approbation',
        tracking=True)
    e_gestock_approval_user_id = fields.Many2one(
        'res.users',
        string='Approuvé par',
        tracking=True)

    # Informations financières et commerciales
    e_gestock_remise_generale = fields.Float(
        string='Remise générale (%)',
        default=0.0,
        digits='Discount',
        tracking=True)
    e_gestock_condition_reglement = fields.Many2one(
        'account.payment.term',
        string='Conditions de règlement',
        tracking=True)
    e_gestock_code_bancaire = fields.Char(
        string='Code bancaire',
        tracking=True)
    e_gestock_ref_externe = fields.Char(
        string='Référence externe',
        tracking=True,
        help="Référence du fournisseur dans un système externe")

    # Relations avec d'autres modèles
    e_gestock_article_ids = fields.One2many(
        'e_gestock.supplier_article',
        'supplier_id',
        string='Articles fournis')
    e_gestock_contract_ids = fields.One2many(
        'e_gestock.supplier_contract',
        'supplier_id',
        string='Contrats')
    e_gestock_evaluation_ids = fields.One2many(
        'e_gestock.supplier_evaluation',
        'supplier_id',
        string='Évaluations')

    # Compteurs pour les vues
    e_gestock_article_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_e_gestock_counts')
    e_gestock_contract_count = fields.Integer(
        string='Nombre de contrats',
        compute='_compute_e_gestock_counts')
    e_gestock_evaluation_count = fields.Integer(
        string='Nombre d\'évaluations',
        compute='_compute_e_gestock_counts')
    e_gestock_purchase_count = fields.Integer(
        string='Nombre d\'achats',
        compute='_compute_e_gestock_counts')

    # Notation et performance
    e_gestock_note_globale = fields.Float(
        string='Note globale',
        compute='_compute_e_gestock_note_globale',
        store=True,
        tracking=True,
        help="Note globale calculée sur les dernières évaluations")
    e_gestock_delai_moyen = fields.Float(
        string='Délai moyen (jours)',
        compute='_compute_e_gestock_performance',
        store=True,
        help="Délai moyen de livraison en jours")
    e_gestock_taux_conformite = fields.Float(
        string='Taux de conformité (%)',
        compute='_compute_e_gestock_performance',
        store=True,
        help="Pourcentage de livraisons conformes")

    # Documents et certifications
    e_gestock_certifications = fields.Text(
        string='Certifications',
        help="Certifications détenues par le fournisseur (ISO, etc.)")
    e_gestock_attachment_ids = fields.Many2many(
        'ir.attachment',
        'e_gestock_supplier_attachment_rel',
        'partner_id',
        'attachment_id',
        string='Documents')

    def _compute_e_gestock_counts(self):
        """Calcule les compteurs pour les smart buttons"""
        for partner in self:
            partner.e_gestock_article_count = self.env['e_gestock.supplier_article'].search_count([
                ('supplier_id', '=', partner.id)
            ])
            partner.e_gestock_contract_count = self.env['e_gestock.supplier_contract'].search_count([
                ('supplier_id', '=', partner.id)
            ])
            partner.e_gestock_evaluation_count = self.env['e_gestock.supplier_evaluation'].search_count([
                ('supplier_id', '=', partner.id)
            ])
            partner.e_gestock_purchase_count = self.env['e_gestock.purchase_order'].search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['approved', 'withdrawn', 'delivered', 'received'])
            ])

    @api.depends('e_gestock_evaluation_ids', 'e_gestock_evaluation_ids.note_globale')
    def _compute_e_gestock_note_globale(self):
        """Calcule la note globale du fournisseur en fonction des évaluations"""
        for partner in self:
            evaluations = self.env['e_gestock.supplier_evaluation'].search([
                ('supplier_id', '=', partner.id),
                ('state', '=', 'validated')
            ], order='date desc', limit=5)  # Prendre les 5 dernières évaluations validées

            if evaluations:
                partner.e_gestock_note_globale = sum(eval.note_globale for eval in evaluations) / len(evaluations)
            else:
                partner.e_gestock_note_globale = 0

    def _compute_e_gestock_performance(self):
        """Calcule les indicateurs de performance du fournisseur"""
        for partner in self:
            # Récupérer les commandes récentes
            orders = self.env['e_gestock.purchase_order'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'received')
            ], order='date_order desc', limit=20)  # Limiter aux 20 dernières commandes

            # Délai moyen de livraison
            delays = []
            conformites = []

            for order in orders:
                if order.date_order and order.date_planned:
                    promised_date = order.date_planned.date()
                    effective_date = None
                    reception = self.env['e_gestock.reception'].search([
                        ('purchase_order_id', '=', order.id),
                        ('state', '=', 'validated')
                    ], limit=1)

                    if reception and reception.date_validation:
                        effective_date = reception.date_validation.date()
                        delays.append((effective_date - promised_date).days)

                # Conformité
                if order.e_gestock_is_conform is not None:  # Champ à ajouter dans le module purchase
                    conformites.append(1 if order.e_gestock_is_conform else 0)

            # Calcul final
            partner.e_gestock_delai_moyen = sum(delays) / len(delays) if delays else 0
            partner.e_gestock_taux_conformite = (sum(conformites) / len(conformites) * 100) if conformites else 0

    def action_view_e_gestock_articles(self):
        """Affiche les articles fournis par ce fournisseur"""
        self.ensure_one()
        return {
            'name': _('Articles fournis'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_article',
            'view_mode': 'list,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id}
        }

    def action_view_e_gestock_contracts(self):
        """Affiche les contrats de ce fournisseur"""
        self.ensure_one()
        return {
            'name': _('Contrats'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_contract',
            'view_mode': 'list,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id}
        }

    def action_view_e_gestock_evaluations(self):
        """Affiche les évaluations de ce fournisseur"""
        self.ensure_one()
        return {
            'name': _('Évaluations'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_evaluation',
            'view_mode': 'list,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id}
        }

    def action_approve_supplier(self):
        """Approuve le fournisseur"""
        self.ensure_one()
        if not self.e_gestock_is_approved:
            self.write({
                'e_gestock_is_approved': True,
                'e_gestock_approval_date': fields.Date.today(),
                'e_gestock_approval_user_id': self.env.user.id
            })

    def action_disapprove_supplier(self):
        """Retire l'approbation du fournisseur"""
        self.ensure_one()
        if self.e_gestock_is_approved:
            self.write({
                'e_gestock_is_approved': False,
                'e_gestock_approval_date': False,
                'e_gestock_approval_user_id': False
            })