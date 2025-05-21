from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta


class Cotation(models.Model):
    _name = 'e_gestock.cotation'
    _description = 'Cotation fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation',
                               required=True, tracking=True,
                               domain=[('state', 'in', ['quotation', 'quoted'])])
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True,
                                domain=[('supplier_rank', '>', 0)], tracking=True)

    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    date_expiration = fields.Date(string='Date d\'expiration', tracking=True)

    montant_ht = fields.Monetary(string='Montant HT', compute='_compute_montants', store=True, tracking=True)
    montant_tva = fields.Monetary(string='Montant TVA', compute='_compute_montants', store=True, tracking=True)
    montant_total = fields.Monetary(string='Montant total TTC', compute='_compute_montants', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id,
                               tracking=True)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company,
                              tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('submitted', 'Soumise'),
        ('confirmed', 'Confirmée'),
        ('selected', 'Sélectionnée'),
        ('rejected', 'Rejetée'),
        ('po_generated', 'BC généré')
    ], string='État', default='draft', tracking=True)

    is_best_offer = fields.Boolean(string='Meilleure offre', default=False, tracking=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande')

    line_ids = fields.One2many('e_gestock.cotation_line', 'cotation_id', string='Lignes')

    delai_livraison = fields.Integer(string='Délai de livraison (jours)', tracking=True)
    conditions_paiement = fields.Char(string='Conditions de paiement', tracking=True)

    remise_generale = fields.Float(string='Remise générale (%)', tracking=True, default=0.0)
    tva = fields.Float(string='TVA (%)', tracking=True, default=18.0)  # Taux par défaut à 18%

    bl_attachment = fields.Binary(string='Bon de livraison')
    bl_filename = fields.Char(string='Nom du fichier BL')
    date_livraison = fields.Date(string='Date de livraison')

    # Champs pour le circuit de validation
    notes = fields.Text(string='Notes')
    cmp_comment = fields.Text(string='Commentaire CMP')

    # Lien vers la demande de cotation fournisseur
    demande_cotation_fournisseur_id = fields.Many2one('e_gestock.demande_cotation_fournisseur',
                                                   string='Demande de cotation fournisseur',
                                                   tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Surchargée pour assigner la séquence et envoyer notifications"""
        for vals in vals_list:
            if not vals.get('reference'):
                sequence_obj = self.env['ir.sequence']
                vals['reference'] = sequence_obj.next_by_code('e_gestock.cotation')
                # Si la séquence n'existe pas ou ne génère pas de référence, créer une référence par défaut
                if not vals.get('reference'):
                    vals['reference'] = f"COT/{fields.Date.today().year}/{self.env['ir.sequence'].next_by_id(self.env.ref('e_gestock_purchase.seq_e_gestock_cotation').id) or '0001'}"

        # Créer les cotations
        cotations = super(Cotation, self).create(vals_list)

        for cotation in cotations:
            # Mettre à jour l'état de la demande fournisseur si elle existe
            if cotation.demande_cotation_fournisseur_id:
                cotation.demande_cotation_fournisseur_id.state = 'received'
                cotation.demande_cotation_fournisseur_id.cotation_id = cotation.id

            # Notifier le demandeur
            if cotation.demande_id and cotation.demande_id.demandeur_id and cotation.demande_id.demandeur_id.email:
                template = self.env.ref('e_gestock_purchase.email_template_quotation_received')
                if template:
                    template.send_mail(cotation.id, force_send=True)

            # Mettre à jour le statut de la demande principale si nécessaire
            if cotation.demande_id and cotation.demande_id.state == 'quotation':
                cotation_count = self.search_count([('demande_id', '=', cotation.demande_id.id)])
                if cotation_count == 1:  # Si c'est la première cotation reçue
                    cotation.demande_id.write({'state': 'quoted'})

            # Message dans le chatter
            cotation.message_post(
                body=_("Cotation reçue du fournisseur %s pour un montant de %s") %
                     (cotation.supplier_id.name, cotation.montant_total),
                subtype_id=self.env.ref('mail.mt_note').id
            )

            # Créer automatiquement les lignes de cotation à partir des lignes de demande
            if cotation.demande_id and not cotation.line_ids:
                cotation._create_lines_from_demande()

        return cotations

    def _create_lines_from_demande(self):
        """Crée automatiquement les lignes de cotation à partir des lignes de demande"""
        self.ensure_one()

        if not self.demande_id:
            return

        # Récupérer les lignes de demande
        demande_lines = self.demande_id.line_ids

        # Créer les lignes de cotation
        cotation_line_vals = []
        for line in demande_lines:
            cotation_line_vals.append({
                'cotation_id': self.id,
                'demande_line_id': line.id,
                'quantite_a_servir': line.quantite_accordee or line.quantite,
                'prix_unitaire': line.prix_unitaire or 0.0,
            })

        if cotation_line_vals:
            self.env['e_gestock.cotation_line'].create(cotation_line_vals)

    @api.onchange('demande_id')
    def _onchange_demande_id(self):
        """Charge automatiquement les articles liés à la demande sélectionnée"""
        if self.demande_id and not self.line_ids:
            # Supprimer les lignes existantes si nécessaire
            self.line_ids = [(5, 0, 0)]

            # Créer les nouvelles lignes
            lines = []
            for line in self.demande_id.line_ids:
                lines.append((0, 0, {
                    'demande_line_id': line.id,
                    'quantite_a_servir': line.quantite_accordee or line.quantite,
                    'prix_unitaire': line.prix_unitaire or 0.0,
                }))

            if lines:
                self.line_ids = lines

    @api.depends('line_ids.montant', 'remise_generale', 'tva')
    def _compute_montants(self):
        for record in self:
            # Total HT avant remise
            total_ht_avant_remise = sum(line.montant for line in record.line_ids)

            # Application de la remise générale
            remise = total_ht_avant_remise * (record.remise_generale / 100.0)
            record.montant_ht = total_ht_avant_remise - remise

            # Calcul de la TVA
            record.montant_tva = record.montant_ht * (record.tva / 100.0)

            # Total TTC
            record.montant_total = record.montant_ht + record.montant_tva

    def action_submit(self):
        """Soumet la cotation (par le fournisseur)"""
        if not self.line_ids:
            raise UserError(_("Vous ne pouvez pas soumettre une cotation sans lignes."))

        # Vérification que toutes les lignes ont un prix
        lines_without_price = self.line_ids.filtered(lambda l: l.prix_unitaire <= 0)
        if lines_without_price:
            raise UserError(_("Toutes les lignes doivent avoir un prix unitaire supérieur à zéro."))

        self.write({'state': 'submitted'})

        # Mettre à jour la demande de cotation fournisseur si présente
        if self.demande_cotation_fournisseur_id:
            self.demande_cotation_fournisseur_id.write({
                'state': 'received',
                'cotation_id': self.id
            })

        # Vérifier si toutes les demandes de cotation fournisseur ont été reçues
        demandes_fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].search([
            ('demande_id', '=', self.demande_id.id)
        ])

        all_received = all(demande.state == 'received' for demande in demandes_fournisseur)
        if all_received and demandes_fournisseur:
            self.demande_id.write({'state': 'quoted'})

        return True

    def action_confirm(self):
        """Confirme la cotation par le responsable des achats"""
        self.write({'state': 'confirmed'})
        return True

    def action_select(self):
        """Sélectionne cette cotation comme la meilleure offre"""
        # Vérifier qu'aucune autre cotation n'est déjà sélectionnée
        other_selected = self.env['e_gestock.cotation'].search([
            ('demande_id', '=', self.demande_id.id),
            ('is_best_offer', '=', True),
            ('id', '!=', self.id)
        ])

        if other_selected:
            # Désélectionner les autres cotations
            other_selected.write({'is_best_offer': False, 'state': 'rejected'})

        # Sélectionner celle-ci
        self.write({
            'is_best_offer': True,
            'state': 'selected'
        })

        # Mettre à jour l'état de la demande
        self.demande_id.write({'state': 'selected'})

        return True

    def action_revert_selection(self):
        """Annule la sélection de cette cotation"""
        if self.state == 'po_generated':
            raise UserError(_("Impossible d'annuler la sélection car un bon de commande a déjà été généré."))

        self.write({
            'is_best_offer': False,
            'state': 'confirmed'
        })

        # Mettre à jour l'état de la demande
        self.demande_id.write({'state': 'quoted'})

        return True

    def action_generate_po(self):
        """Ouvre l'assistant de génération du bon de commande"""
        self.ensure_one()

        if not self.is_best_offer:
            raise UserError(_("Vous ne pouvez générer un bon de commande que pour la cotation sélectionnée."))

        return {
            'name': _('Générer un bon de commande'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'e_gestock.generate_purchase_order_wizard',
            'target': 'new',
            'context': {
                'default_cotation_id': self.id,
            }
        }

    def action_view_purchase_order(self):
        """Affiche le bon de commande généré"""
        self.ensure_one()

        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande n'a encore été généré pour cette cotation."))

        return {
            'name': _('Bon de commande'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'e_gestock.purchase_order',
            'res_id': self.purchase_order_id.id,
        }