from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EgestockPurchaseOrderReception(models.Model):
    _inherit = 'e_gestock.purchase_order'

    # Champs pour la réception
    reception_ids = fields.One2many('e_gestock.reception', 'purchase_order_id', string='Réceptions')
    reception_count = fields.Integer(string='Nombre de réceptions', compute='_compute_reception_count', store=True)

    # Comité de réception
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception assigné',
                                  tracking=True, domain=[('active', '=', True)])

    # Statut de réception
    is_fully_received = fields.Boolean(string='Entièrement réceptionné', compute='_compute_is_fully_received', store=True)

    @api.depends('reception_ids')
    def _compute_reception_count(self):
        """Calcule le nombre de réceptions liées à ce bon de commande"""
        for order in self:
            order.reception_count = len(order.reception_ids)

    @api.depends('order_line.qty_received', 'order_line.product_qty')
    def _compute_is_fully_received(self):
        """Détermine si toutes les lignes ont été entièrement réceptionnées"""
        for order in self:
            if not order.order_line:
                order.is_fully_received = False
                continue

            order.is_fully_received = all(
                line.qty_received >= line.product_qty
                for line in order.order_line
            )

            # Mettre à jour l'état du bon de commande si toutes les lignes sont réceptionnées
            if order.is_fully_received and order.state_approbation == 'delivered':
                order.write({'state_approbation': 'received'})

                # Message dans le chatter
                order.message_post(
                    body=_("Toutes les lignes de la commande ont été réceptionnées."),
                    subtype_id=self.env.ref('mail.mt_note').id
                )

    def action_view_receptions(self):
        """Affiche les réceptions liées à ce bon de commande"""
        self.ensure_one()

        action = {
            'name': _('Réceptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception',
            'view_mode': 'list,form',
            'domain': [('purchase_order_id', '=', self.id)],
            'context': {'default_purchase_order_id': self.id},
        }

        if len(self.reception_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.reception_ids[0].id,
            })

        return action

    def action_create_reception(self):
        """Crée une nouvelle réception pour ce bon de commande"""
        self.ensure_one()

        if self.state_approbation != 'delivered':
            raise UserError(_("Vous ne pouvez créer une réception que pour un bon de commande livré."))

        # Vérifier si toutes les lignes ont déjà été réceptionnées
        if self.is_fully_received:
            raise UserError(_("Toutes les lignes de ce bon de commande ont déjà été réceptionnées."))

        # Créer une nouvelle réception
        reception = self.env['e_gestock.reception'].create({
            'purchase_order_id': self.id,
            'date_reception': fields.Date.today(),
            'committee_id': self.committee_id.id,
        })

        # Ouvrir la réception nouvellement créée
        return {
            'name': _('Nouvelle réception'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.reception',
            'view_mode': 'form',
            'res_id': reception.id,
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_open_reception_wizard(self):
        """Ouvre l'assistant de réception"""
        self.ensure_one()

        if self.state_approbation != 'delivered':
            raise UserError(_("Seuls les bons de commande livrés peuvent être réceptionnés."))

        return {
            'name': _('Valider la réception'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.validate_reception_wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'default_committee_id': self.committee_id.id,
            }
        }


class EgestockPurchaseOrderLineReception(models.Model):
    _inherit = 'e_gestock.purchase_order_line'

    # Champs pour la réception
    qty_received = fields.Float(string='Quantité reçue', digits='Product Unit of Measure', default=0.0)
    qty_to_receive = fields.Float(string='Quantité à recevoir', compute='_compute_qty_to_receive', store=True)

    @api.depends('product_qty', 'qty_received')
    def _compute_qty_to_receive(self):
        """Calcule la quantité restant à recevoir"""
        for line in self:
            line.qty_to_receive = line.product_qty - line.qty_received
