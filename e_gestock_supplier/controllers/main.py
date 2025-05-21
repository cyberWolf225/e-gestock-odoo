from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.tools import consteq
from collections import OrderedDict
import json


class EGestockSupplierPortal(CustomerPortal):
    """Portail fournisseur pour E-GESTOCK"""

    def _prepare_home_portal_values(self, counters):
        """Ajoute des compteurs supplémentaires pour le portail fournisseur"""
        values = super()._prepare_home_portal_values(counters)
        
        if 'supplier_contract_count' in counters:
            # Compter les contrats fournisseur si l'utilisateur est un fournisseur
            partner = request.env.user.partner_id
            contract_count = 0
            if partner and partner.supplier_rank > 0:
                contract_model = request.env['e_gestock.supplier_contract']
                contract_count = contract_model.search_count([
                    ('supplier_id', '=', partner.id),
                    ('state', 'in', ['active', 'validated'])
                ])
            values['supplier_contract_count'] = contract_count
            
        if 'supplier_evaluation_count' in counters:
            # Compter les évaluations fournisseur
            partner = request.env.user.partner_id
            evaluation_count = 0
            if partner and partner.supplier_rank > 0:
                evaluation_model = request.env['e_gestock.supplier_evaluation']
                evaluation_count = evaluation_model.search_count([
                    ('supplier_id', '=', partner.id),
                    ('state', '=', 'validated')
                ])
            values['supplier_evaluation_count'] = evaluation_count
        
        return values

    # ========== Contrats Fournisseur ============
    @http.route(['/my/supplier/contracts', '/my/supplier/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_supplier_contracts(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Page listant les contrats fournisseur"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SupplierContract = request.env['e_gestock.supplier_contract']
        
        domain = [
            ('supplier_id', '=', partner.id),
            ('state', 'in', ['active', 'validated', 'expired'])
        ]
        
        # Filtres
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('state', '=', 'active')]},
            'expired': {'label': _('Expired'), 'domain': [('state', '=', 'expired')]},
        }
        
        # Tri
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date_debut desc'},
            'name': {'label': _('Title'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        
        # Valeurs par défaut
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # Compteur
        contract_count = SupplierContract.search_count(domain)
        
        # Paginateur
        pager = portal_pager(
            url="/my/supplier/contracts",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=contract_count,
            page=page,
            step=self._items_per_page
        )
        
        # Récupérer les contrats
        contracts = SupplierContract.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        values.update({
            'date': date_begin,
            'contracts': contracts,
            'page_name': 'supplier_contracts',
            'pager': pager,
            'default_url': '/my/supplier/contracts',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        
        return request.render("e_gestock_supplier.portal_my_supplier_contracts", values)

    @http.route(['/my/supplier/contract/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_my_supplier_contract(self, contract_id=None, **kw):
        """Détail d'un contrat fournisseur"""
        try:
            contract_sudo = self._document_check_access('e_gestock.supplier_contract', contract_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'page_name': 'supplier_contract',
            'contract': contract_sudo,
        }
        
        return request.render("e_gestock_supplier.portal_my_supplier_contract", values)
    
    # ========== Évaluations Fournisseur ============
    @http.route(['/my/supplier/evaluations', '/my/supplier/evaluations/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_supplier_evaluations(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Page listant les évaluations fournisseur"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SupplierEvaluation = request.env['e_gestock.supplier_evaluation']
        
        domain = [
            ('supplier_id', '=', partner.id),
            ('state', '=', 'validated')
        ]
        
        # Tri
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'rating': {'label': _('Rating'), 'order': 'note_globale desc'},
        }
        
        # Valeurs par défaut
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
        # Compteur
        evaluation_count = SupplierEvaluation.search_count(domain)
        
        # Paginateur
        pager = portal_pager(
            url="/my/supplier/evaluations",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=evaluation_count,
            page=page,
            step=self._items_per_page
        )
        
        # Récupérer les évaluations
        evaluations = SupplierEvaluation.search(
            domain,
            order=sort_order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        values.update({
            'date': date_begin,
            'evaluations': evaluations,
            'page_name': 'supplier_evaluations',
            'pager': pager,
            'default_url': '/my/supplier/evaluations',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        
        return request.render("e_gestock_supplier.portal_my_supplier_evaluations", values)

    @http.route(['/my/supplier/evaluation/<int:evaluation_id>'], type='http', auth="user", website=True)
    def portal_my_supplier_evaluation(self, evaluation_id=None, **kw):
        """Détail d'une évaluation fournisseur"""
        try:
            evaluation_sudo = self._document_check_access('e_gestock.supplier_evaluation', evaluation_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
            
        values = {
            'page_name': 'supplier_evaluation',
            'evaluation': evaluation_sudo,
        }
        
        return request.render("e_gestock_supplier.portal_my_supplier_evaluation", values)
    
    # ========== API RESTful pour le portail fournisseur ============
    @http.route('/api/supplier/contracts', type='json', auth='user')
    def api_supplier_contracts(self, **kwargs):
        """API pour récupérer les contrats fournisseur"""
        partner = request.env.user.partner_id
        if not partner or partner.supplier_rank <= 0:
            return {'error': 'Not a supplier'}
            
        SupplierContract = request.env['e_gestock.supplier_contract']
        domain = [
            ('supplier_id', '=', partner.id),
            ('state', 'in', ['active', 'validated', 'expired'])
        ]
        
        contracts = SupplierContract.search(domain)
        result = []
        
        for contract in contracts:
            result.append({
                'id': contract.id,
                'reference': contract.reference,
                'name': contract.name,
                'date_debut': contract.date_debut,
                'date_fin': contract.date_fin,
                'state': contract.state,
                'montant': contract.montant,
                'currency': contract.currency_id.name,
                'currency_symbol': contract.currency_id.symbol,
            })
            
        return result

    @http.route('/api/supplier/evaluations', type='json', auth='user')
    def api_supplier_evaluations(self, **kwargs):
        """API pour récupérer les évaluations fournisseur"""
        partner = request.env.user.partner_id
        if not partner or partner.supplier_rank <= 0:
            return {'error': 'Not a supplier'}
            
        SupplierEvaluation = request.env['e_gestock.supplier_evaluation']
        domain = [
            ('supplier_id', '=', partner.id),
            ('state', '=', 'validated')
        ]
        
        evaluations = SupplierEvaluation.search(domain)
        result = []
        
        for evaluation in evaluations:
            result.append({
                'id': evaluation.id,
                'name': evaluation.name,
                'date': evaluation.date,
                'note_globale': evaluation.note_globale,
                'period_start': evaluation.period_start,
                'period_end': evaluation.period_end,
                'remarks': evaluation.remarks,
            })
            
        return result 