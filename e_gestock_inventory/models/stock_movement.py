from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class StockMovement(models.Model):
    _name = 'e_gestock.stock_movement'
    _description = 'Mouvement de stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    type = fields.Selection([
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('transfer', 'Transfert'),
        ('adjustment', 'Ajustement')
    ], string='Type', required=True, default='in', tracking=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, tracking=True)
    depot_source_id = fields.Many2one('e_gestock.depot', string='Dépôt source',
                                    domain="[('id', '!=', depot_destination_id)]",
                                    tracking=True)
    depot_destination_id = fields.Many2one('e_gestock.depot', string='Dépôt destination',
                                         domain="[('id', '!=', depot_source_id)]",
                                         tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user,
                                   tracking=True)
    validateur_id = fields.Many2one('res.users', string='Validateur', tracking=True, readonly=True)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('done', 'Terminé'),
        ('cancel', 'Annulé')
    ], string='État', default='draft', tracking=True)
    line_ids = fields.One2many('e_gestock.stock_movement_line', 'movement_id', string='Lignes')

    # Champs calculés pour la lecture seule
    depot_source_readonly = fields.Boolean(compute='_compute_readonly_fields')
    depot_destination_readonly = fields.Boolean(compute='_compute_readonly_fields')
    responsable_readonly = fields.Boolean(compute='_compute_readonly_fields')
    notes_readonly = fields.Boolean(compute='_compute_readonly_fields')
    lines_readonly = fields.Boolean(compute='_compute_readonly_fields')

    @api.depends('state')
    def _compute_readonly_fields(self):
        for record in self:
            record.depot_source_readonly = record.state in ['done', 'cancel']
            record.depot_destination_readonly = record.state in ['done', 'cancel']
            record.responsable_readonly = record.state in ['done', 'cancel']
            record.notes_readonly = record.state in ['done', 'cancel']
            record.lines_readonly = record.state in ['done', 'cancel']
            record.origine_readonly = record.state in ['done', 'cancel']
            record.reference_origine_readonly = record.state in ['done', 'cancel']
    stock_picking_id = fields.Many2one('stock.picking', string='Opération de stock Odoo', readonly=True)
    origine = fields.Selection([
        ('purchase', 'Achat'),
        ('internal', 'Demande interne'),
        ('return', 'Retour'),
        ('inventory', 'Inventaire'),
        ('other', 'Autre')
    ], string='Type d\'origine', default='other', tracking=True)
    reference_origine = fields.Char(string='Référence d\'origine')

    # Champs calculés pour la lecture seule
    origine_readonly = fields.Boolean(compute='_compute_readonly_fields')
    reference_origine_readonly = fields.Boolean(compute='_compute_readonly_fields')
    total_amount = fields.Monetary(string='Montant total', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                # Générer une référence basée sur le type de mouvement
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.stock_movement.' + vals.get('type', 'in')) or 'Nouveau'
        return super(StockMovement, self).create(vals_list)

    @api.depends('line_ids.montant_total')
    def _compute_total_amount(self):
        for movement in self:
            movement.total_amount = sum(line.montant_total for line in movement.line_ids)

    @api.constrains('type', 'depot_source_id', 'depot_destination_id')
    def _check_depots(self):
        for record in self:
            if record.type == 'in' and not record.depot_destination_id:
                raise ValidationError(_("Un dépôt de destination est requis pour une entrée de stock."))
            if record.type == 'out' and not record.depot_source_id:
                raise ValidationError(_("Un dépôt source est requis pour une sortie de stock."))
            if record.type == 'transfer' and (not record.depot_source_id or not record.depot_destination_id):
                raise ValidationError(_("Les dépôts source et destination sont requis pour un transfert."))

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'in':
            self.depot_source_id = False
        elif self.type == 'out':
            self.depot_destination_id = False

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            return

        # Vérifier la disponibilité des articles pour les sorties et transferts
        if self.type in ('out', 'transfer'):
            self._check_availability()

        # Créer l'opération de stock dans Odoo
        picking_type = self._get_picking_type()
        if not picking_type:
            raise UserError(_("Impossible de trouver un type d'opération pour ce mouvement."))

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self._get_source_location().id,
            'location_dest_id': self._get_destination_location().id,
            'origin': self.reference,
            'move_type': 'direct',
            'scheduled_date': self.date,
            'company_id': self.company_id.id,
        }
        picking = self.env['stock.picking'].create(picking_vals)

        # Créer les mouvements de stock
        for line in self.line_ids:
            if not line.article_id.product_id:
                raise UserError(_("L'article %s n'est pas lié à un produit Odoo.") % line.article_id.design_article)

            move_vals = {
                'name': line.article_id.design_article,
                'product_id': line.article_id.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantite,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'date': self.date,
                'company_id': self.company_id.id,
            }
            move = self.env['stock.move'].create(move_vals)
            line.stock_move_id = move.id

        # Lier l'opération au mouvement
        self.stock_picking_id = picking.id

        # Confirmer l'opération
        picking.action_confirm()

        # Mettre à jour l'état
        self.write({
            'state': 'confirmed',
        })

        return True

    def action_validate(self):
        self.ensure_one()
        if self.state != 'confirmed':
            return

        picking = self.stock_picking_id
        if not picking:
            raise UserError(_("Aucune opération de stock associée à ce mouvement."))

        # Forcer la disponibilité si nécessaire
        if picking.state not in ['assigned', 'done']:
            picking.action_assign()
            if picking.state != 'assigned':
                picking.action_force_assign()

        # Créer les mouvements de déstockage et remplir les quantités
        for move in picking.move_ids_without_package:
            if move.state not in ['assigned', 'done']:
                continue

            line = self.line_ids.filtered(lambda l: l.stock_move_id.id == move.id)
            if not line:
                continue

            # Créer les mouvements de lot si nécessaire
            if line.lot_id:
                move_line_vals = {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'qty_done': line.quantite,
                    'lot_id': line.lot_id.id,
                }
                self.env['stock.move.line'].create(move_line_vals)
            else:
                # Sinon, simplement mettre la quantité fait
                move.quantity_done = line.quantite

        # Valider l'opération
        picking.button_validate()

        # Mettre à jour les niveaux de stock dans notre modèle
        self._update_stock_levels()

        # Mettre à jour l'état
        self.write({
            'state': 'done',
            'validateur_id': self.env.user.id
        })

        return True

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("Impossible d'annuler un mouvement déjà terminé."))

        if self.stock_picking_id:
            # Annuler l'opération de stock Odoo
            if self.stock_picking_id.state != 'cancel':
                self.stock_picking_id.action_cancel()

        # Mettre à jour l'état
        self.write({
            'state': 'cancel'
        })

        return True

    def _check_availability(self):
        """Vérifier la disponibilité des articles dans le dépôt source"""
        self.ensure_one()

        if self.type not in ('out', 'transfer'):
            return True

        for line in self.line_ids:
            stock_item = self.env['e_gestock.stock_item'].search([
                ('depot_id', '=', self.depot_source_id.id),
                ('article_id', '=', line.article_id.id)
            ], limit=1)

            if not stock_item or stock_item.quantite_disponible < line.quantite:
                raise UserError(_("Quantité insuffisante pour l'article '%s' dans le dépôt source. "
                               "Disponible: %s %s, Demandé: %s %s") %
                               (line.article_id.design_article,
                                stock_item and stock_item.quantite_disponible or 0.0,
                                line.uom_id.name,
                                line.quantite,
                                line.uom_id.name))

        return True

    def _get_picking_type(self):
        """Récupérer le type d'opération en fonction du type de mouvement"""
        self.ensure_one()

        if self.type == 'in':
            return self.depot_destination_id.warehouse_id.in_type_id
        elif self.type == 'out':
            return self.depot_source_id.warehouse_id.out_type_id
        elif self.type == 'transfer':
            # Pour les transferts entre dépôts, utiliser le type de transfert interne
            return self.depot_source_id.warehouse_id.int_type_id
        else:
            # Pour les ajustements
            return self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', self.depot_source_id.warehouse_id.id or self.depot_destination_id.warehouse_id.id)
            ], limit=1)

    def _get_source_location(self):
        """Récupérer l'emplacement source"""
        self.ensure_one()

        if self.type == 'in':
            # Pour les entrées, l'emplacement source est l'emplacement fournisseur
            return self.env.ref('stock.stock_location_suppliers')
        elif self.type in ('out', 'transfer'):
            # Pour les sorties et transferts, c'est l'emplacement du dépôt source
            return self.depot_source_id.location_id
        else:
            # Pour les ajustements
            return self.depot_source_id.location_id if self.depot_source_id else self.env.ref('stock.stock_location_inventory')

    def _get_destination_location(self):
        """Récupérer l'emplacement destination"""
        self.ensure_one()

        if self.type == 'out':
            # Pour les sorties, l'emplacement destination est l'emplacement client
            return self.env.ref('stock.stock_location_customers')
        elif self.type in ('in', 'transfer'):
            # Pour les entrées et transferts, c'est l'emplacement du dépôt destination
            return self.depot_destination_id.location_id
        else:
            # Pour les ajustements
            return self.depot_destination_id.location_id if self.depot_destination_id else self.env.ref('stock.stock_location_inventory')

    def _update_stock_levels(self):
        """Mettre à jour les niveaux de stock dans notre modèle"""
        self.ensure_one()

        if self.type == 'in':
            # Entrée de stock: ajouter à la destination
            for line in self.line_ids:
                stock_item = self.env['e_gestock.stock_item'].search([
                    ('depot_id', '=', self.depot_destination_id.id),
                    ('article_id', '=', line.article_id.id)
                ], limit=1)

                if stock_item:
                    # Mettre à jour la quantité
                    stock_item.write({
                        'quantite_disponible': stock_item.quantite_disponible + line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })
                else:
                    # Créer un nouvel élément de stock
                    self.env['e_gestock.stock_item'].create({
                        'depot_id': self.depot_destination_id.id,
                        'article_id': line.article_id.id,
                        'quantite_disponible': line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })

        elif self.type == 'out':
            # Sortie de stock: retirer de la source
            for line in self.line_ids:
                stock_item = self.env['e_gestock.stock_item'].search([
                    ('depot_id', '=', self.depot_source_id.id),
                    ('article_id', '=', line.article_id.id)
                ], limit=1)

                if stock_item:
                    # Mettre à jour la quantité
                    stock_item.write({
                        'quantite_disponible': stock_item.quantite_disponible - line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })

        elif self.type == 'transfer':
            # Transfert: retirer de la source et ajouter à la destination
            for line in self.line_ids:
                # Source
                source_item = self.env['e_gestock.stock_item'].search([
                    ('depot_id', '=', self.depot_source_id.id),
                    ('article_id', '=', line.article_id.id)
                ], limit=1)

                if source_item:
                    source_item.write({
                        'quantite_disponible': source_item.quantite_disponible - line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })

                # Destination
                dest_item = self.env['e_gestock.stock_item'].search([
                    ('depot_id', '=', self.depot_destination_id.id),
                    ('article_id', '=', line.article_id.id)
                ], limit=1)

                if dest_item:
                    dest_item.write({
                        'quantite_disponible': dest_item.quantite_disponible + line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })
                else:
                    # Créer un nouvel élément de stock
                    self.env['e_gestock.stock_item'].create({
                        'depot_id': self.depot_destination_id.id,
                        'article_id': line.article_id.id,
                        'quantite_disponible': line.quantite,
                        'last_inventory_date': fields.Datetime.now()
                    })

        # Pour les ajustements, c'est géré directement dans la validation de l'inventaire
        return True