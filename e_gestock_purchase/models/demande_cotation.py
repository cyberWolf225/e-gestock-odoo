from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DemandeCotation(models.Model):
    _name = 'e_gestock.demande_cotation'
    _description = 'Demande de cotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'reference'

    reference = fields.Char(string='N° Demande', required=True, readonly=True, default='Nouveau', tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    demandeur_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user, required=True, tracking=True)
    exercice_id = fields.Many2one('e_gestock.exercise', string='Exercice', required=True, tracking=True)

    # Structure et budget
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    compte_budg_id = fields.Many2one('e_gestock.famille', string='Compte budg.', required=True, tracking=True)
    designation_compte = fields.Char(related='compte_budg_id.design_fam', string='Désignation compte', readonly=True)
    gestion_id = fields.Many2one('e_gestock.type_gestion', string='Gestion', required=True, tracking=True)
    designation_gestion = fields.Char(related='gestion_id.libelle_gestion', string='Désignation gestion', readonly=True)

    # Caractéristiques de la demande
    intitule = fields.Char(string='Intitulé', required=True, tracking=True)
    is_stockable = fields.Boolean(string='Commande stockable', default=True, tracking=True,
                                 help="Indique si les articles de la demande sont des articles stockables")
    solde_disponible = fields.Monetary(string='Solde disponible', compute='_compute_solde_disponible', store=False)
    montant_total = fields.Monetary(string='Montant Total', compute='_compute_montant_total', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)

    # Notes et commentaires
    note = fields.Text(string='Commentaire')
    urgence_signalee = fields.Boolean(string='Urgence signalée', default=False, tracking=True)
    memo_motivation = fields.Binary(string='Mémo de motivation')
    memo_filename = fields.Char(string='Nom du fichier mémo')

    # Validation et workflow
    validation_comment = fields.Text(string='Commentaire de validation')

    # Lignes et état
    line_ids = fields.One2many('e_gestock.demande_cotation_line', 'demande_id', string='Lignes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('validated', 'Validée'),
        ('budget_checked', 'Budget vérifié'),
        ('approved', 'Approuvée'),
        ('engaged', 'Engagée'),
        ('quotation', 'En attente cotation'),
        ('quoted', 'Cotations reçues'),
        ('selected', 'Fournisseur sélectionné'),
        ('po_generated', 'BC généré'),
        ('delivered', 'Livrée'),
        ('received', 'Réceptionnée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True)

    # Relations
    cotation_ids = fields.One2many('e_gestock.cotation', 'demande_id', string='Cotations')
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande')
    supplier_ids = fields.Many2many('res.partner', string='Fournisseurs présélectionnés',
                                   domain=[('supplier_rank', '>', 0)])
    demande_cotation_fournisseur_ids = fields.One2many('e_gestock.demande_cotation_fournisseur', 'demande_id',
                                                     string='Demandes fournisseurs')

    # Compteurs pour les boutons statistiques
    cotation_count = fields.Integer(string='Nombre de cotations', compute='_compute_cotation_count')
    fournisseur_count = fields.Integer(string='Nombre de fournisseurs', compute='_compute_fournisseur_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                # Format: Année/Structure/DC/Séquence
                structure = self.env['e_gestock.structure'].browse(vals.get('structure_id'))
                year = fields.Date.context_today(self).year
                seq = self.env['ir.sequence'].next_by_code('e_gestock.demande_cotation')
                vals['reference'] = f"{year}/{structure.code_structure or 'XXX'}/DC/{seq}"
        return super(DemandeCotation, self).create(vals_list)

    @api.depends('line_ids.quantite', 'line_ids.article_id', 'line_ids.prix_unitaire')
    def _compute_montant_total(self):
        for record in self:
            record.montant_total = sum(line.quantite * (line.prix_unitaire or 0) for line in record.line_ids)

    def _compute_solde_disponible(self):
        for record in self:
            solde = 0.0
            if record.exercice_id and record.structure_id and record.compte_budg_id:
                # Recherche du crédit budgétaire correspondant
                credit = self.env['e_gestock.credit_budget'].search([
                    ('exercise_id', '=', record.exercice_id.id),
                    ('structure_id', '=', record.structure_id.id),
                    ('famille_id', '=', record.compte_budg_id.id)
                ], limit=1)

                if credit:
                    solde = credit.montant_disponible

            record.solde_disponible = solde

    def _compute_cotation_count(self):
        for record in self:
            record.cotation_count = len(record.cotation_ids)

    def _compute_fournisseur_count(self):
        for record in self:
            record.fournisseur_count = len(record.demande_cotation_fournisseur_ids)

    def action_submit(self):
        """Soumet la demande pour validation"""
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("Cette demande ne peut pas être soumise car elle n'est pas en état brouillon."))

        return self.write({'state': 'submitted'})

    def action_validate(self):
        """Valide la demande par le responsable achats"""
        self.ensure_one()

        if self.state != 'submitted':
            raise UserError(_("Cette demande ne peut pas être validée car elle n'est pas en état soumis."))

        # Mettre à jour l'état
        self.write({'state': 'validated'})

        # Envoyer email au responsable achats
        template = self.env.ref('e_gestock_purchase.email_template_purchase_request_validated')
        if template:
            template.send_mail(self.id, force_send=True)

        # Envoyer email au contrôleur budgétaire
        template_budget = self.env.ref('e_gestock_purchase.email_template_budget_check_request')
        if template_budget:
            # Rechercher un utilisateur avec le rôle de contrôleur budgétaire
            budget_controller = self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('e_gestock_base.group_e_gestock_budget_controller').id)
            ], limit=1)

            if budget_controller and budget_controller.email:
                # Envoyer l'email avec l'adresse du contrôleur dans le contexte
                template_budget.with_context(controller_email=budget_controller.email).send_mail(self.id, force_send=True)
            else:
                # Log un message si aucun contrôleur budgétaire n'est trouvé
                self.message_post(
                    body=_("⚠️ Impossible d'envoyer l'email de notification au contrôleur budgétaire: aucun utilisateur avec ce rôle n'a été trouvé."),
                    subtype_id=self.env.ref('mail.mt_note').id
                )

        # Message dans le chatter
        self.message_post(
            body=_("Demande validée et transmise au contrôle budgétaire."),
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_check_budget(self):
        """Vérifie la disponibilité budgétaire"""
        self.ensure_one()

        if self.state != 'validated':
            raise UserError(_("Cette demande ne peut pas être vérifiée car elle n'est pas en état validé."))

        # Vérifier le budget
        if self.montant_total > self.solde_disponible:
            # Si le solde est insuffisant, on peut créer une alerte mais laisser continuer
            self.message_post(
                body=_("⚠️ Attention: Le montant de la demande (%s) dépasse le solde disponible (%s).") %
                     (self.montant_total, self.solde_disponible),
                subtype_id=self.env.ref('mail.mt_note').id
            )

        self.write({'state': 'budget_checked'})

        # Message dans le chatter
        self.message_post(
            body=_("Budget vérifié. Solde disponible: %s") % self.solde_disponible,
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return True

    def action_approve(self):
        """Approbation de la demande"""
        self.write({'state': 'approved'})
        return True

    def action_send_quotation(self):
        """Initialise le processus de demande de cotation"""
        if not self.supplier_ids:
            raise UserError(_("Veuillez sélectionner au moins un fournisseur pour la demande de cotation."))

        self.write({'state': 'quotation'})

        # Ouvrir l'assistant de sélection des fournisseurs
        return {
            'name': _('Sélection des fournisseurs'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'e_gestock.select_suppliers_wizard',
            'target': 'new',
            'context': {
                'default_demande_id': self.id,
                'default_supplier_ids': [(6, 0, self.supplier_ids.ids)],
            }
        }

    def action_cancel(self):
        """Annulation de la demande"""
        self.write({'state': 'cancelled'})
        return True

    def action_view_cotations(self):
        """Affiche les cotations liées à cette demande"""
        self.ensure_one()
        return {
            'name': _('Cotations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'e_gestock.cotation',
            'domain': [('demande_id', '=', self.id)],
            'context': {'default_demande_id': self.id},
        }

    def action_view_fournisseurs(self):
        """Affiche les demandes de cotation aux fournisseurs"""
        self.ensure_one()
        return {
            'name': _('Demandes fournisseurs'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'e_gestock.demande_cotation_fournisseur',
            'domain': [('demande_id', '=', self.id)],
            'context': {'default_demande_id': self.id},
        }

    def name_get(self):
        """Personnalisation de l'affichage du nom des demandes de cotation"""
        result = []
        for record in self:
            name = f"{record.reference or ''} - {record.intitule or ''}"
            result.append((record.id, name))
        return result