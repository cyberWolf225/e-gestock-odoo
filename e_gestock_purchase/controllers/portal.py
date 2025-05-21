# -*- coding: utf-8 -*-

import base64
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR


class EGestockPurchasePortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'demande_count' in counters:
            # Récupérer les demandes de cotation pour ce fournisseur
            DemandeCotationFournisseur = request.env['e_gestock.demande_cotation_fournisseur']

            domain = [
                ('supplier_id', '=', partner.id),
                ('state', 'in', ['sent', 'received'])
            ]

            values['demande_count'] = DemandeCotationFournisseur.search_count(domain)

        if 'purchase_order_count' in counters:
            # Récupérer les bons de commande pour ce fournisseur
            EgestockPurchaseOrder = request.env['e_gestock.purchase_order']

            domain = [
                ('partner_id', '=', partner.id),
                ('state_approbation', 'in', ['approved', 'withdrawn', 'delivered'])
            ]

            values['purchase_order_count'] = EgestockPurchaseOrder.search_count(domain)

        return values

    @http.route(['/my/demandes', '/my/demandes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_demandes(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        DemandeCotationFournisseur = request.env['e_gestock.demande_cotation_fournisseur']

        domain = [
            ('supplier_id', '=', partner.id),
            ('state', 'in', ['sent', 'received'])
        ]

        # Comptage pour pagination
        demande_count = DemandeCotationFournisseur.search_count(domain)

        # Pager
        pager = portal_pager(
            url="/my/demandes",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=demande_count,
            page=page,
            step=self._items_per_page
        )

        # Contenu
        demandes = DemandeCotationFournisseur.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'demandes': demandes,
            'page_name': 'demande',
            'pager': pager,
            'default_url': '/my/demandes',
        })

        return request.render("e_gestock_purchase.portal_my_demandes", values)

    @http.route(['/my/demandes/<int:demande_id>'], type='http', auth="user", website=True)
    def portal_my_demande_detail(self, demande_id, **kw):
        try:
            demande_sudo = self._document_check_access('e_gestock.demande_cotation_fournisseur', demande_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Vérifier que la demande appartient bien au fournisseur
        if demande_sudo.supplier_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')

        values = {
            'page_name': 'demande',
            'demande': demande_sudo,
        }

        # Si une cotation existe déjà pour cette demande
        cotation = request.env['e_gestock.cotation'].sudo().search([
            ('demande_cotation_fournisseur_id', '=', demande_sudo.id)
        ], limit=1)

        if cotation:
            values['cotation'] = cotation

        return request.render("e_gestock_purchase.portal_my_demande_detail", values)

    @http.route(['/my/demandes/<int:demande_id>/submit'], type='http', auth="user", website=True)
    def portal_submit_cotation(self, demande_id, **post):
        try:
            demande_sudo = self._document_check_access('e_gestock.demande_cotation_fournisseur', demande_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Vérifier que la demande appartient bien au fournisseur
        if demande_sudo.supplier_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')

        # Vérifier si une cotation existe déjà
        existing_cotation = request.env['e_gestock.cotation'].sudo().search([
            ('demande_cotation_fournisseur_id', '=', demande_sudo.id)
        ], limit=1)

        if existing_cotation:
            return request.redirect('/my/demandes/%s' % demande_id)

        # Afficher le formulaire de soumission
        values = {
            'page_name': 'submit_cotation',
            'demande': demande_sudo,
        }

        # Récupérer les lignes de la demande originale
        original_lines = demande_sudo.demande_id.line_ids
        values['original_lines'] = original_lines

        return request.render("e_gestock_purchase.portal_submit_cotation", values)

    @http.route(['/my/demandes/<int:demande_id>/submit/confirm'], type='http', auth="user", website=True)
    def portal_submit_cotation_confirm(self, demande_id, **post):
        try:
            demande_sudo = self._document_check_access('e_gestock.demande_cotation_fournisseur', demande_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Traitement du formulaire soumis
        values = {}
        error = {}

        # Création de la cotation
        cotation_vals = {
            'demande_id': demande_sudo.demande_id.id,
            'supplier_id': demande_sudo.supplier_id.id,
            'demande_cotation_fournisseur_id': demande_sudo.id,
            'date': post.get('date'),
            'delai_livraison': int(post.get('delai_livraison', 0)),
            'conditions_paiement': post.get('conditions_paiement', ''),
            'notes': post.get('notes', ''),
            'state': 'draft',
        }

        # Création de la cotation
        cotation = request.env['e_gestock.cotation'].sudo().create(cotation_vals)

        # Traitement des lignes
        for line in demande_sudo.demande_id.line_ids:
            line_qty = float(post.get('qty_%s' % line.id, 0))
            line_price = float(post.get('price_%s' % line.id, 0))

            if line_qty > 0 and line_price > 0:
                line_vals = {
                    'cotation_id': cotation.id,
                    'demande_line_id': line.id,
                    'article_id': line.article_id.id if line.article_id else False,
                    'designation': line.designation,
                    'quantite': line.quantite,
                    'quantite_a_servir': line_qty,
                    'unite_id': line.unite_id.id if line.unite_id else False,
                    'prix_unitaire': line_price,
                    'remise_ligne': float(post.get('remise_%s' % line.id, 0)),
                }
                request.env['e_gestock.cotation_line'].sudo().create(line_vals)

        # Recalculer les montants totaux
        cotation.sudo()._compute_montants()

        # Marquer la demande comme reçue
        demande_sudo.sudo().write({
            'state': 'received',
            'cotation_id': cotation.id,
        })

        return request.redirect('/my/demandes/%s' % demande_id)

    # Routes pour les bons de commande
    @http.route(['/my/purchase_orders', '/my/purchase_orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        EgestockPurchaseOrder = request.env['e_gestock.purchase_order']

        domain = [
            ('partner_id', '=', partner.id),
            ('state_approbation', 'in', ['approved', 'withdrawn', 'delivered'])
        ]

        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state_approbation'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        # count for pager
        purchase_count = EgestockPurchaseOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/purchase_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        purchase_orders = EgestockPurchaseOrder.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchase_orders_history'] = purchase_orders.ids[:100]

        values.update({
            'date': date_begin,
            'purchase_orders': purchase_orders.sudo(),
            'page_name': 'purchase_order',
            'pager': pager,
            'default_url': '/my/purchase_orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("e_gestock_purchase.portal_my_purchase_orders", values)

    @http.route(['/my/purchase_order/<int:purchase_order_id>'], type='http', auth="user", website=True)
    def portal_my_purchase_order(self, purchase_order_id=None, access_token=None, **kw):
        try:
            purchase_order_sudo = self._document_check_access('e_gestock.purchase_order', purchase_order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._purchase_order_get_page_view_values(purchase_order_sudo, access_token, **kw)
        return request.render("e_gestock_purchase.portal_my_purchase_order", values)

    def _purchase_order_get_page_view_values(self, purchase_order, access_token, **kwargs):
        values = {
            'page_name': 'purchase_order',
            'purchase_order': purchase_order,
        }
        return self._get_page_view_values(purchase_order, access_token, values, 'my_purchase_orders_history', False, **kwargs)

    # Actions
    @http.route(['/my/purchase_order/<int:purchase_order_id>/withdraw'], type='http', auth="user", website=True)
    def portal_purchase_order_withdraw(self, purchase_order_id=None, access_token=None, **kw):
        try:
            purchase_order_sudo = self._document_check_access('e_gestock.purchase_order', purchase_order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if purchase_order_sudo.state_approbation != 'approved':
            return request.redirect('/my/purchase_order/%s' % purchase_order_id)

        purchase_order_sudo.action_withdraw()
        return request.redirect('/my/purchase_order/%s' % purchase_order_id)

    @http.route(['/my/purchase_order/<int:purchase_order_id>/deliver'], type='http', auth="user", website=True)
    def portal_purchase_order_deliver(self, purchase_order_id=None, access_token=None, **kw):
        try:
            purchase_order_sudo = self._document_check_access('e_gestock.purchase_order', purchase_order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if purchase_order_sudo.state_approbation != 'withdrawn':
            return request.redirect('/my/purchase_order/%s' % purchase_order_id)

        if 'delivery_date' in kw and kw.get('delivery_date'):
            purchase_order_sudo.date_livraison_prevue = kw.get('delivery_date')

        if request.httprequest.method == 'POST' and 'delivery_note' in request.httprequest.files:
            file = request.httprequest.files['delivery_note']
            if file:
                data = file.read()
                purchase_order_sudo.write({
                    'bl_attachment': base64.b64encode(data),
                    'bl_filename': file.filename,
                })

        if 'confirm_delivery' in kw:
            purchase_order_sudo.action_set_delivered()
            return request.redirect('/my/purchase_order/%s' % purchase_order_id)

        values = self._purchase_order_get_page_view_values(purchase_order_sudo, access_token, **kw)
        values['delivery_form'] = True
        return request.render("e_gestock_purchase.portal_my_purchase_order", values)