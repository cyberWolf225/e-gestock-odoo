from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ValidateReceptionWizard(models.TransientModel):
    _name = 'e_gestock.validate_reception_wizard'
    _description = 'Assistant de validation de réception'

    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande',
                                      required=True, readonly=True)
    date_reception = fields.Date(string='Date de réception',
                               default=fields.Date.context_today, required=True)
    notes = fields.Text(string='Notes de réception')

    line_ids = fields.One2many('e_gestock.validate_reception_line_wizard', 'wizard_id',
                             string='Lignes de réception')

    @api.model
    def default_get(self, fields):
        res = super(ValidateReceptionWizard, self).default_get(fields)

        # Récupérer l'ID du bon de commande depuis le contexte
        purchase_id = self.env.context.get('default_purchase_order_id')
        if purchase_id:
            purchase = self.env['e_gestock.purchase_order'].browse(purchase_id)
            if purchase.exists():
                res['purchase_order_id'] = purchase.id

                # Préparer les lignes de réception
                lines = []
                for po_line in purchase.order_line:
                    # Calcul de la quantité restante à réceptionner
                    received_qty = sum(move.quantity_done for move in po_line.move_ids
                                     if move.state == 'done')
                    remaining_qty = po_line.product_qty - received_qty

                    if remaining_qty > 0:
                        lines.append((0, 0, {
                            'purchase_line_id': po_line.id,
                            'product_id': po_line.product_id.id,
                            'product_qty': po_line.product_qty,
                            'received_qty': received_qty,
                            'quantity_to_receive': remaining_qty,
                            'uom_id': po_line.product_uom.id,
                        }))

                res['line_ids'] = lines

        return res

    def action_validate_reception(self):
        """Valide la réception de la commande"""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("Aucune ligne à réceptionner."))

        # Vérifier que des quantités à réceptionner sont spécifiées
        invalid_lines = self.line_ids.filtered(lambda l: l.quantity_to_receive <= 0)
        if invalid_lines:
            raise UserError(_("Toutes les lignes doivent avoir une quantité à réceptionner supérieure à zéro."))

        # Vérifier que toutes les quantités sont inférieures ou égales aux quantités restantes
        invalid_qty = self.line_ids.filtered(lambda l: l.quantity_to_receive > (l.product_qty - l.received_qty))
        if invalid_qty:
            raise UserError(_("La quantité à réceptionner ne peut pas dépasser la quantité restante."))

        # Création du mouvement de stock pour chaque ligne
        for line in self.line_ids:
            # Créer un picking de réception
            if not line.quantity_to_receive:
                continue

            # Pour chaque ligne de commande, mettre à jour le mouvement de stock
            for move in line.purchase_line_id.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                move.quantity_done = line.quantity_to_receive
                move.date = self.date_reception

        # Mettre à jour l'état de la commande
        self.purchase_order_id.write({
            'state_approbation': 'received',
            'date_livraison_reelle': self.date_reception,
            'reception_comment': self.notes,
            'reception_validator_id': self.env.user.id,
            'reception_validation_date': fields.Datetime.now(),
        })

        # Si une demande de cotation est liée, mettre à jour son état
        if self.purchase_order_id.demande_cotation_id:
            self.purchase_order_id.demande_cotation_id.write({
                'state': 'received'
            })

        # Créer un message dans le chatter
        body = _("""
            <p>Commande réceptionnée le %s</p>
            <ul>
                %s
            </ul>
            <p>Notes: %s</p>
        """) % (
            self.date_reception,
            ''.join(['<li>%s: %s %s</li>' % (
                line.product_id.name,
                line.quantity_to_receive,
                line.uom_id.name
            ) for line in self.line_ids]),
            self.notes or _('Aucune note')
        )

        self.purchase_order_id.message_post(body=body)

        # Envoyer une notification au demandeur
        self.purchase_order_id.action_notify_reception_complete()

        return {
            'type': 'ir.actions.act_window_close'
        }


class ValidateReceptionLineWizard(models.TransientModel):
    _name = 'e_gestock.validate_reception_line_wizard'
    _description = 'Ligne d\'assistant de validation de réception'

    wizard_id = fields.Many2one('e_gestock.validate_reception_wizard', string='Assistant',
                              ondelete='cascade')
    purchase_line_id = fields.Many2one('e_gestock.purchase_order_line', string='Ligne de commande',
                                     required=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Produit', required=True, readonly=True)
    product_qty = fields.Float(string='Quantité commandée', readonly=True)
    received_qty = fields.Float(string='Quantité déjà reçue', readonly=True)
    quantity_to_receive = fields.Float(string='Quantité à réceptionner', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité', readonly=True)