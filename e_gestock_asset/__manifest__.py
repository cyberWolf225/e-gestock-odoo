# -*- coding: utf-8 -*-
{
    'name': "E-GESTOCK Gestion des Immobilisations",
    'summary': """
        Module de gestion des immobilisations pour E-GESTOCK
    """,
    'description': """
        Ce module permet la gestion complète des immobilisations dans E-GESTOCK:
        - Enregistrement et suivi des immobilisations
        - Calcul des amortissements
        - Gestion des affectations et transferts
        - Suivi des maintenances
        - Gestion des sorties d'immobilisations
        - Gestion documentaire
    """,
    'author': "E-GESTOCK",
    'website': "https://www.e-gestock.com",
    'category': 'Accounting/Assets',
    'version': '1.0',
    'depends': [
        'base',
        'mail',
        'web',
        'e_gestock_base',
        'e_gestock_inventory',
        'e_gestock_purchase',
        'account_asset',
        'stock',
        'maintenance',
    ],
    'data': [
        'security/e_gestock_asset_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/asset_type_data.xml',
        'views/asset_views.xml',
        'views/asset_type_views.xml',
        'views/asset_assignment_views.xml',
        'views/asset_maintenance_views.xml',
        'views/asset_document_views.xml',
        'views/asset_transfer_views.xml',
        'views/asset_disposal_views.xml',
        'views/e_gestock_purchase_order_asset_views.xml',
        'views/menu_views.xml',
        'wizard/asset_generate_amortization_wizard_views.xml',
        'wizard/asset_transfer_wizard_views.xml',
        'wizard/asset_disposal_wizard_views.xml',
        'report/asset_report.xml',
        'report/maintenance_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
