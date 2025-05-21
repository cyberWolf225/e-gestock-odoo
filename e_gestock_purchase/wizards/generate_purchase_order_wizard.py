from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GeneratePurchaseOrderWizard(models.TransientModel):
    _name = 'e_gestock.generate_purchase_order_wizard'
    _description = 'Assistant de génération de bon de commande'

    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation', required=True,
                                domain=[('state', '=', 'selected'), ('is_best_offer', '=', True)])
    date_order = fields.Datetime(string='Date de commande', default=fields.Datetime.now, required=True)
    note = fields.Text(string='Notes pour le fournisseur')
    signataire_ids = fields.Many2many('res.users', string='Signataires', required=True)

    @api.model
    def default_get(self, fields):
        """Récupération des valeurs par défaut"""
        res = super(GeneratePurchaseOrderWizard, self).default_get(fields)

        # Prendre la cotation du contexte
        cotation_id = self.env.context.get('default_cotation_id')
        if cotation_id:
            cotation = self.env['e_gestock.cotation'].browse(cotation_id)
            if cotation.exists():
                res['cotation_id'] = cotation.id

                # Récupérer les signataires disponibles (utilisateurs avec des droits de responsable)
                signataires = self.env['res.users'].search([
                    ('groups_id', 'in', [
                        self.env.ref('e_gestock_base.group_e_gestock_resp_achats').id,
                        self.env.ref('e_gestock_base.group_e_gestock_resp_dmp').id,
                        self.env.ref('e_gestock_base.group_e_gestock_budget_controller').id
                    ])
                ])

                if signataires:
                    res['signataire_ids'] = [(6, 0, signataires.ids[:3])]  # Limiter à 3 signataires par défaut

        return res

    def action_generate_po(self):
        """Génère le bon de commande à partir de la cotation sélectionnée"""
        self.ensure_one()
        cotation = self.cotation_id

        if not cotation.is_best_offer or cotation.state != 'selected':
            raise UserError(_("Seule une cotation sélectionnée peut être utilisée pour générer un bon de commande."))

        if cotation.purchase_order_id:
            raise UserError(_("Un bon de commande a déjà été généré pour cette cotation."))

        # Création du bon de commande E-GESTOCK
        purchase_order = self.env['e_gestock.purchase_order'].create({
            'partner_id': cotation.supplier_id.id,
            'date_order': self.date_order,
            'currency_id': cotation.currency_id.id,
            'company_id': cotation.company_id.id,
            'state': 'draft',
            'state_approbation': 'draft',
            'notes': self.note,
            'signataire_ids': [(6, 0, self.signataire_ids.ids)],
            'demande_cotation_id': cotation.demande_id.id,
            'cotation_id': cotation.id,
            'origin': cotation.reference,
        })

        # Création des lignes de commande
        for line in cotation.line_ids:
            if line.article_id and line.quantite_a_servir > 0:
                # Conversion en produit Odoo
                product = self.env['product.product'].search([
                    ('default_code', '=', line.article_id.ref_article)
                ], limit=1)

                if not product:
                    # Création du produit s'il n'existe pas
                    product = self.env['product.product'].create({
                        'name': line.designation,
                        'default_code': line.article_id.ref_article,
                        'type': 'consu',  # 'consu' est la valeur correcte pour les biens dans Odoo 18
                        'uom_id': line.unite_id.id,
                        'uom_po_id': line.unite_id.id,
                        'purchase_ok': True,
                        'standard_price': line.prix_unitaire,
                    })

                # Création de la ligne de commande E-GESTOCK
                self.env['e_gestock.purchase_order_line'].create({
                    'order_id': purchase_order.id,
                    'product_id': product.id,
                    'name': line.description or line.designation,
                    'date_planned': self.date_order,
                    'product_qty': line.quantite_a_servir,
                    'product_uom': line.unite_id.id,
                    'price_unit': line.prix_unitaire,
                    'taxes_id': [(6, 0, product.supplier_taxes_id.ids)],
                    'cotation_line_id': line.id,
                    'e_gestock_article_id': line.article_id.id,
                })

        # Mise à jour des informations du bon de commande
        purchase_order._compute_amount()

        # Lier le bon de commande à la cotation et à la demande
        cotation.write({
            'purchase_order_id': purchase_order.id,
            'state': 'po_generated'
        })

        cotation.demande_id.write({
            'purchase_order_id': purchase_order.id,
            'state': 'po_generated'
        })

        # Rediriger vers le bon de commande E-GESTOCK généré
        return {
            'name': _('Bon de commande'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'e_gestock.purchase_order',
            'res_id': purchase_order.id,
            'target': 'current',
        }