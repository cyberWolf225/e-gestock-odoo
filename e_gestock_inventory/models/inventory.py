from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class Inventory(models.Model):
    _name = 'e_gestock.inventory'
    _description = 'Inventaire physique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, tracking=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user,
                                   tracking=True)
    validateur_id = fields.Many2one('res.users', string='Validateur', tracking=True, readonly=True)
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('in_progress', 'En cours'),
        ('validated', 'Validé'),
        ('cancel', 'Annulé')
    ], string='État', default='draft', tracking=True)
    line_ids = fields.One2many('e_gestock.inventory_line', 'inventory_id', string='Lignes')

    # Champs calculés pour la lecture seule
    depot_readonly = fields.Boolean(compute='_compute_readonly_fields')
    responsable_readonly = fields.Boolean(compute='_compute_readonly_fields')
    notes_readonly = fields.Boolean(compute='_compute_readonly_fields')
    lines_readonly = fields.Boolean(compute='_compute_readonly_fields')

    @api.depends('state')
    def _compute_readonly_fields(self):
        for record in self:
            record.depot_readonly = record.state in ['in_progress', 'validated', 'cancel']
            record.responsable_readonly = record.state in ['validated', 'cancel']
            record.notes_readonly = record.state in ['validated', 'cancel']
            record.lines_readonly = record.state in ['validated', 'cancel']

    # Dans Odoo 18, le modèle stock.inventory n'existe plus, les ajustements se font directement sur les quants
    # inventory_id = fields.Many2one('stock.inventory', string='Inventaire Odoo', readonly=True)
    adjustment_movement_id = fields.Many2one('e_gestock.stock_movement', string='Mouvement d\'ajustement', readonly=True)
    total_lines = fields.Integer(string='Total des lignes', compute='_compute_total_lines')
    total_counted = fields.Integer(string='Lignes comptées', compute='_compute_total_counted')
    count_progress = fields.Float(string='Progression', compute='_compute_count_progress')
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.inventory') or 'Nouveau'
        return super(Inventory, self).create(vals_list)

    @api.depends('line_ids')
    def _compute_total_lines(self):
        for inventory in self:
            inventory.total_lines = len(inventory.line_ids)

    @api.depends('line_ids.is_counted')
    def _compute_total_counted(self):
        for inventory in self:
            inventory.total_counted = len(inventory.line_ids.filtered(lambda l: l.is_counted))

    @api.depends('total_lines', 'total_counted')
    def _compute_count_progress(self):
        for inventory in self:
            if inventory.total_lines > 0:
                inventory.count_progress = (inventory.total_counted / inventory.total_lines) * 100
            else:
                inventory.count_progress = 0

    def action_start(self):
        self.ensure_one()
        if self.state != 'draft':
            return

        # Vérifier qu'il n'y a pas d'autre inventaire en cours sur ce dépôt
        other_inventories = self.search([
            ('depot_id', '=', self.depot_id.id),
            ('state', 'in', ['in_progress']),
            ('id', '!=', self.id)
        ])
        if other_inventories:
            raise UserError(_("Il existe déjà un inventaire en cours pour ce dépôt."))

        # Générer les lignes d'inventaire
        self._generate_inventory_lines()

        # Dans Odoo 18, il n'y a plus de modèle stock.inventory
        # Les ajustements se font directement sur les quants lors de la validation

        # Mettre à jour l'état
        self.write({'state': 'in_progress'})

        return True

    def action_validate(self):
        self.ensure_one()
        if self.state != 'in_progress':
            return

        # Vérifier que toutes les lignes ont été comptées
        uncounted_lines = self.line_ids.filtered(lambda l: not l.is_counted)
        if uncounted_lines:
            raise UserError(_("Toutes les lignes d'inventaire doivent être comptées avant validation."))

        # Dans Odoo 18, les ajustements d'inventaire se font directement sur les quants
        for line in self.line_ids:
            # Ajuster les quants pour les articles avec une différence
            if line.ecart != 0 and line.article_id.product_id:
                # Rechercher le quant existant
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', line.article_id.product_id.id),
                    ('location_id', '=', self.depot_id.location_id.id)
                ], limit=1)

                if quant:
                    # Mettre à jour le quant existant
                    quant.inventory_quantity = line.quantite_reelle
                    quant.inventory_diff_quantity = line.ecart
                    quant.inventory_date = self.date
                    quant.user_id = self.env.user.id
                    quant.inventory_quantity_set = True
                    # Appliquer l'ajustement
                    quant.action_apply_inventory()
                else:
                    # Créer un nouveau quant
                    quant = self.env['stock.quant'].create({
                        'product_id': line.article_id.product_id.id,
                        'location_id': self.depot_id.location_id.id,
                        'inventory_quantity': line.quantite_reelle,
                        'inventory_date': self.date,
                        'user_id': self.env.user.id,
                        'inventory_quantity_set': True
                    })
                    # Appliquer l'ajustement
                    quant.action_apply_inventory()

        # Créer un mouvement d'ajustement dans notre modèle
        lines_with_ecart = self.line_ids.filtered(lambda l: l.ecart != 0)
        if lines_with_ecart:
            adjustment = self.env['e_gestock.stock_movement'].create({
                'type': 'adjustment',
                'date': self.date,
                'depot_source_id': self.depot_id.id,
                'depot_destination_id': self.depot_id.id,
                'responsable_id': self.responsable_id.id,
                'validateur_id': self.env.user.id,
                'notes': _("Ajustement d'inventaire: %s") % self.reference,
                'origine': 'inventory',
                'reference_origine': self.reference,
                'state': 'done',
            })

            # Ajouter les lignes d'ajustement
            for line in self.line_ids.filtered(lambda l: l.ecart != 0):
                self.env['e_gestock.stock_movement_line'].create({
                    'movement_id': adjustment.id,
                    'article_id': line.article_id.id,
                    'quantite': abs(line.ecart),
                    'prix_unitaire': line.article_id.product_id.standard_price,
                })

            self.adjustment_movement_id = adjustment.id

        # Mettre à jour les quantités dans notre modèle stock_item
        for line in self.line_ids:
            stock_item = self.env['e_gestock.stock_item'].search([
                ('depot_id', '=', self.depot_id.id),
                ('article_id', '=', line.article_id.id)
            ], limit=1)

            if stock_item:
                # Mettre à jour la quantité
                stock_item.write({
                    'quantite_disponible': line.quantite_reelle,
                    'last_inventory_date': self.date
                })
            elif line.quantite_reelle > 0:
                # Créer un nouvel élément de stock
                self.env['e_gestock.stock_item'].create({
                    'depot_id': self.depot_id.id,
                    'article_id': line.article_id.id,
                    'quantite_disponible': line.quantite_reelle,
                    'last_inventory_date': self.date
                })

        # Mettre à jour l'état
        self.write({
            'state': 'validated',
            'validateur_id': self.env.user.id
        })

        return True

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'validated':
            raise UserError(_("Impossible d'annuler un inventaire déjà validé."))

        # Dans Odoo 18, il n'y a plus de modèle stock.inventory
        # Aucune action à effectuer sur les inventaires Odoo

        # Mettre à jour l'état
        self.write({'state': 'cancel'})

        return True

    def _generate_inventory_lines(self):
        """Générer les lignes d'inventaire pour tous les articles du dépôt"""
        self.ensure_one()

        # Supprimer les lignes existantes
        self.line_ids.unlink()

        # Récupérer les articles en stock dans ce dépôt
        stock_items = self.env['e_gestock.stock_item'].search([('depot_id', '=', self.depot_id.id)])

        # Créer une ligne pour chaque article
        for item in stock_items:
            self.env['e_gestock.inventory_line'].create({
                'inventory_id': self.id,
                'article_id': item.article_id.id,
                'quantite_theorique': item.quantite_disponible,
                'quantite_reelle': 0,
                'is_counted': False
            })

    def action_add_article(self):
        """Ouvrir un assistant pour ajouter un article à l'inventaire"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Vous ne pouvez ajouter d'articles qu'à un inventaire en cours."))

        return {
            'name': _('Ajouter un article'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.inventory.add.article.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_inventory_id': self.id, 'default_depot_id': self.depot_id.id},
        }