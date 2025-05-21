from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Reception(models.Model):
    _name = 'e_gestock.reception'
    _description = 'Réception de commande'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau',
                          tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)

    # Relations avec les commandes et bons de commande
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation',
                              tracking=True, readonly=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', required=True,
                                     tracking=True, domain=[('cotation_id', '!=', False)])

    # Informations de réception
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', required=True,
                             tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user,
                                   tracking=True)
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', related='purchase_order_id.partner_id',
                                   store=True, readonly=True)
    bl_number = fields.Char(string='N° Bon de livraison fournisseur', tracking=True)
    bl_date = fields.Date(string='Date BL fournisseur', tracking=True)

    # État et flux de travail
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('comite_validation', 'En attente validation comité'),
        ('done', 'Terminée'),
        ('cancel', 'Annulée')
    ], string='État', default='draft', tracking=True)

    # Informations complémentaires
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('e_gestock.reception_line', 'reception_id', string='Lignes')
    stock_picking_id = fields.Many2one('stock.picking', string='Réception Odoo', readonly=True)
    is_partial = fields.Boolean(string='Livraison partielle', compute='_compute_is_partial', store=True)

    # Validation par comité
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception',
                                tracking=True)
    comite_reception_id = fields.Many2one('e_gestock.comite_reception', string='Ancien comité de réception',
                                       tracking=True)
    pv_validation = fields.Boolean(string='PV validé', default=False, tracking=True)
    pv_count = fields.Integer(string='Nombre de PV', compute='_compute_pv_count')

    # Champs liés à la société
    company_id = fields.Many2one('res.company', string='Société',
                               default=lambda self: self.env.company,
                               required=True)
    currency_id = fields.Many2one('res.currency', string='Devise',
                                related='company_id.currency_id',
                                readonly=True)

    # Compteurs pour les documents liés
    notice_count = fields.Integer(string='Nombre d\'avis préalables', compute='_compute_notice_count')
    inspection_count = fields.Integer(string='Nombre d\'inspections', compute='_compute_inspection_count')
    nonconformity_count = fields.Integer(string='Nombre de non-conformités', compute='_compute_nonconformity_count')
    quarantine_count = fields.Integer(string='Nombre de quarantaines', compute='_compute_quarantine_count')
    return_count = fields.Integer(string='Nombre de retours', compute='_compute_return_count')

    # Compute fields
    @api.depends('line_ids.quantite_restante')
    def _compute_is_partial(self):
        for record in self:
            record.is_partial = any(line.quantite_restante > 0 for line in record.line_ids)

    def _compute_pv_count(self):
        for record in self:
            record.pv_count = self.env['e_gestock.pv_reception'].search_count([
                ('reception_id', '=', record.id)
            ])

    def _compute_notice_count(self):
        for record in self:
            record.notice_count = self.env['e_gestock.reception.notice'].search_count([
                ('reception_id', '=', record.id)
            ])

    def _compute_inspection_count(self):
        for record in self:
            record.inspection_count = self.env['e_gestock.reception.inspection'].search_count([
                ('reception_id', '=', record.id)
            ])

    def _compute_nonconformity_count(self):
        for record in self:
            record.nonconformity_count = self.env['e_gestock.reception.nonconformity'].search_count([
                ('reception_id', '=', record.id)
            ])

    def _compute_quarantine_count(self):
        for record in self:
            record.quarantine_count = self.env['e_gestock.reception.quarantine'].search_count([
                ('reception_id', '=', record.id)
            ])

    def _compute_return_count(self):
        for record in self:
            record.return_count = self.env['e_gestock.reception.return'].search_count([
                ('reception_id', '=', record.id)
            ])

    # Onchange et contraintes
    @api.onchange('purchase_order_id')
    def _onchange_purchase_order(self):
        if self.purchase_order_id:
            # Récupération de la demande d'achat liée
            self.demande_id = self.purchase_order_id.demande_cotation_id

            # Récupérer le comité de réception du bon de commande
            if hasattr(self.purchase_order_id, 'committee_id') and self.purchase_order_id.committee_id:
                self.committee_id = self.purchase_order_id.committee_id
            elif hasattr(self.purchase_order_id, 'reception_committee_id') and self.purchase_order_id.reception_committee_id:
                self.committee_id = self.purchase_order_id.reception_committee_id

            # Pour la compatibilité avec l'ancien modèle
            if hasattr(self.purchase_order_id, 'comite_reception_id') and self.purchase_order_id.comite_reception_id:
                self.comite_reception_id = self.purchase_order_id.comite_reception_id

            # Générer les lignes de réception
            lines = []
            for po_line in self.purchase_order_id.order_line:
                # Calcul des quantités déjà reçues
                already_received = self._get_already_received_qty(po_line)

                remaining_qty = po_line.product_qty - already_received
                if remaining_qty <= 0:
                    continue

                # Création de la ligne de réception
                line_vals = {
                    'purchase_line_id': po_line.id,
                    'article_id': self._find_article_from_product(po_line.product_id),
                    'designation': po_line.name,
                    'quantite_commandee': po_line.product_qty,
                    'quantite_deja_recue': already_received,
                    'quantite_recue': remaining_qty,
                    'quantite_restante': 0,
                    'uom_id': po_line.product_uom.id,
                }
                lines.append((0, 0, line_vals))

            self.line_ids = lines

    def _get_already_received_qty(self, po_line):
        """Calcule la quantité déjà reçue pour une ligne de commande d'achat"""
        # Recherche des mouvements de stock déjà réalisés
        moves = self.env['stock.move'].search([
            ('purchase_line_id', '=', po_line.id),
            ('state', '=', 'done')
        ])

        return sum(move.quantity_done for move in moves)

    def _find_article_from_product(self, product):
        """Trouve l'article e_gestock correspondant au produit Odoo"""
        article = self.env['e_gestock.article'].search([
            ('product_id', '=', product.id)
        ], limit=1)

        return article.id if article else False

    # CRUD overrides
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.reception') or 'Nouveau'

        return super(Reception, self).create(vals_list)

    # Business methods
    def action_confirm(self):
        """Confirme la réception"""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Vous ne pouvez pas confirmer une réception sans lignes."))

        # Vérifier que toutes les lignes ont une quantité reçue
        invalid_lines = self.line_ids.filtered(lambda l: l.quantite_recue <= 0)
        if invalid_lines:
            raise UserError(_("Toutes les lignes doivent avoir une quantité reçue supérieure à zéro."))

        # Créer le transfert de stock
        self._create_stock_picking()

        self.write({'state': 'confirmed'})

        return True

    def action_submit_comite(self):
        """Soumet la réception au comité"""
        self.ensure_one()

        if not self.committee_id and not self.comite_reception_id:
            raise UserError(_("Veuillez sélectionner un comité de réception avant de soumettre."))

        # Vérifier que toutes les lignes ont une conformité renseignée
        lines_without_conformity = self.line_ids.filtered(lambda l: not l.est_conforme)
        if lines_without_conformity:
            raise UserError(_("Veuillez renseigner la conformité pour toutes les lignes avant de soumettre au comité."))

        self.write({'state': 'comite_validation'})

        # Notification au comité de réception
        self._notify_comite_reception()

        return True

    def action_done(self):
        """Termine la réception après validation du comité"""
        self.ensure_one()

        if not self.pv_validation:
            raise UserError(_("Un procès-verbal de réception validé est requis pour terminer la réception."))

        self.write({'state': 'done'})

        # Mettre à jour l'état de la demande liée
        if self.demande_id:
            self.demande_id.write({'state': 'received'})

        # Mettre à jour l'état du bon de commande lié
        if self.purchase_order_id and self.purchase_order_id.state_approbation == 'delivered':
            self.purchase_order_id.write({'state_approbation': 'received'})

            # Mettre à jour les quantités reçues dans les lignes de commande
            for line in self.line_ids:
                if line.purchase_line_id and line.quantite_recue > 0:
                    line.purchase_line_id.qty_received += line.quantite_recue

        return True

    def action_cancel(self):
        """Annule la réception"""
        self.ensure_one()

        if self.state in ['done']:
            raise UserError(_("Vous ne pouvez pas annuler une réception terminée."))

        # Annuler le mouvement de stock si existant
        if self.stock_picking_id and self.stock_picking_id.state != 'cancel':
            self.stock_picking_id.action_cancel()

        self.write({'state': 'cancel'})

        return True

    def action_view_pv(self):
        """Affiche les PV liés à cette réception"""
        self.ensure_one()

        pvs = self.env['e_gestock.pv_reception'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Procès-verbaux de réception'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.pv_reception',
            'view_mode': 'list,form',
        }

        if len(pvs) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': pvs.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', pvs.ids)],
            })

        return action

    def action_create_pv(self):
        """Ouvre l'assistant de création de PV"""
        self.ensure_one()

        if self.state != 'comite_validation':
            raise UserError(_("Vous ne pouvez créer un PV que pour une réception en attente de validation par le comité."))

        # Vérifier si un PV existe déjà
        existing_pv = self.env['e_gestock.pv_reception'].search([
            ('reception_id', '=', self.id),
            ('state', '!=', 'cancelled')
        ], limit=1)

        if existing_pv:
            return {
                'name': _('Procès-verbal existant'),
                'type': 'ir.actions.act_window',
                'res_model': 'e_gestock.pv_reception',
                'res_id': existing_pv.id,
                'view_mode': 'form',
            }

        return {
            'name': _('Créer un procès-verbal'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.create_pv_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }

    def _create_stock_picking(self):
        """Crée le transfert de stock correspondant à la réception"""
        self.ensure_one()

        if self.stock_picking_id:
            raise UserError(_("Un transfert de stock existe déjà pour cette réception."))

        # Déterminer la destination
        location_dest = self.depot_id.location_id
        if not location_dest:
            raise UserError(_("Le dépôt sélectionné n'a pas d'emplacement de stock défini."))

        # Créer le picking
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.env.company.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_("Aucun type d'opération trouvé pour les réceptions."))

        picking_vals = {
            'partner_id': self.fournisseur_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': location_dest.id,
            'scheduled_date': self.date,
            'origin': self.reference,
            'company_id': self.env.company.id,
        }

        picking = self.env['stock.picking'].create(picking_vals)

        # Créer les moves
        for line in self.line_ids:
            if line.quantite_recue <= 0:
                continue

            if not line.purchase_line_id.product_id:
                raise UserError(_("La ligne %s n'a pas de produit défini.") % line.designation)

            move_vals = {
                'name': line.designation,
                'product_id': line.purchase_line_id.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantite_recue,
                'quantity_done': line.quantite_recue,  # Pré-remplir la quantité fait
                'picking_id': picking.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': location_dest.id,
                'purchase_line_id': line.purchase_line_id.id,
            }

            move = self.env['stock.move'].create(move_vals)
            line.stock_move_id = move.id

        # Associer le picking à la réception
        self.stock_picking_id = picking.id

        # Valider le picking
        picking.action_confirm()
        picking.action_assign()

        return picking

    def _notify_comite_reception(self):
        """Notifie les membres du comité de réception"""
        self.ensure_one()

        members = []

        # Utiliser le nouveau modèle de comité si disponible
        if self.committee_id:
            # Trouver tous les membres du comité
            if self.committee_id.responsible_id:
                members.append(self.committee_id.responsible_id)
            if self.committee_id.secretary_id:
                members.append(self.committee_id.secretary_id)
            members.extend(self.committee_id.member_ids)
        # Sinon, utiliser l'ancien modèle de comité
        elif self.comite_reception_id:
            # Trouver tous les membres du comité
            if self.comite_reception_id.president_id:
                members.append(self.comite_reception_id.president_id)
            if self.comite_reception_id.secretaire_id:
                members.append(self.comite_reception_id.secretaire_id)
            members.extend(self.comite_reception_id.membre_ids)

        if not members:
            return

        # Envoyer une notification à chaque membre
        template = self.env.ref('e_gestock_reception.mail_template_reception_comite_notification')
        if template:
            for member in members:
                if member.email:
                    template.send_mail(self.id, force_send=True, email_values={
                        'email_to': member.email,
                        'subject': _('Réception en attente de validation - %s') % self.reference,
                    })

    # Actions pour les documents liés
    def action_view_notices(self):
        """Affiche les avis préalables liés à cette réception"""
        self.ensure_one()

        notices = self.env['e_gestock.reception.notice'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Avis préalables'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception.notice',
            'view_mode': 'list,form',
        }

        if len(notices) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': notices.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', notices.ids)],
            })

        return action

    def action_view_inspections(self):
        """Affiche les inspections liées à cette réception"""
        self.ensure_one()

        inspections = self.env['e_gestock.reception.inspection'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Inspections'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception.inspection',
            'view_mode': 'list,form',
        }

        if len(inspections) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': inspections.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', inspections.ids)],
            })

        return action

    def action_view_nonconformities(self):
        """Affiche les non-conformités liées à cette réception"""
        self.ensure_one()

        nonconformities = self.env['e_gestock.reception.nonconformity'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Non-conformités'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception.nonconformity',
            'view_mode': 'list,form',
        }

        if len(nonconformities) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': nonconformities.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', nonconformities.ids)],
            })

        return action

    def action_view_quarantines(self):
        """Affiche les quarantaines liées à cette réception"""
        self.ensure_one()

        quarantines = self.env['e_gestock.reception.quarantine'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Quarantaines'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception.quarantine',
            'view_mode': 'list,form',
        }

        if len(quarantines) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': quarantines.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', quarantines.ids)],
            })

        return action

    def action_view_returns(self):
        """Affiche les retours liés à cette réception"""
        self.ensure_one()

        returns = self.env['e_gestock.reception.return'].search([
            ('reception_id', '=', self.id)
        ])

        action = {
            'name': _('Retours fournisseurs'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception.return',
            'view_mode': 'list,form',
        }

        if len(returns) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': returns.id,
            })
        else:
            action.update({
                'domain': [('id', 'in', returns.ids)],
            })

        return action

    def action_create_inspection(self):
        """Crée une inspection pour cette réception"""
        self.ensure_one()

        if self.state not in ['confirmed', 'comite_validation', 'done']:
            raise UserError(_("Vous ne pouvez créer une inspection que pour une réception confirmée ou validée."))

        # Créer l'inspection
        inspection_vals = {
            'reception_id': self.id,
            'date': fields.Date.context_today(self),
            'inspecteur_id': self.env.user.id,
        }

        inspection = self.env['e_gestock.reception.inspection'].create(inspection_vals)

        # Redirection vers l'inspection créée
        return {
            'name': _('Inspection'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.inspection',
            'res_id': inspection.id,
            'type': 'ir.actions.act_window',
        }

    def action_create_return(self):
        """Ouvre l'assistant de création de retour fournisseur"""
        self.ensure_one()

        if self.state not in ['confirmed', 'comite_validation', 'done']:
            raise UserError(_("Vous ne pouvez créer un retour que pour une réception confirmée ou validée."))

        return {
            'name': _('Créer un retour fournisseur'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.return.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }

    def action_create_quarantine(self):
        """Ouvre l'assistant de mise en quarantaine"""
        self.ensure_one()

        if self.state not in ['confirmed', 'comite_validation', 'done']:
            raise UserError(_("Vous ne pouvez créer une quarantaine que pour une réception confirmée ou validée."))

        return {
            'name': _('Mise en quarantaine'),
            'view_mode': 'form',
            'res_model': 'e_gestock.reception.quarantine.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_reception_id': self.id},
        }

    def action_view_stock_picking(self):
        """Affiche l'opération de stock liée à cette réception"""
        self.ensure_one()

        if not self.stock_picking_id:
            return

        action = {
            'name': _('Opération de stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.stock_picking_id.id,
        }

        return action