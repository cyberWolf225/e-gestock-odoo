{
    'name': 'E-GESTOCK Supplier Management',
    'version': '1.0',
    'category': 'Inventory/Purchase',
    'sequence': 20,
    'summary': 'Gestion avancée des fournisseurs pour E-GESTOCK',
    'description': """
Module de gestion des fournisseurs
==================================
Ce module étend les fonctionnalités de gestion des fournisseurs dans Odoo pour la solution E-GESTOCK:
- Catégorisation des fournisseurs
- Gestion des contrats fournisseurs
- Système d'évaluation des performances
- Portail fournisseur enrichi
- Gestion des articles par fournisseur
    """,
    'author': 'E-GESTOCK Team',
    'website': 'https://www.e-gestock.com',
    'depends': [
        'base',
        'mail',
        'portal',
        'product',
        'e_gestock_base',
        'e_gestock_purchase',
    ],
    'data': [
        'security/supplier_security.xml',
        'security/ir.model.access.csv',
        'views/supplier_views.xml',
        'views/supplier_category_views.xml',
        'views/supplier_article_views.xml',
        'views/contract_views.xml',
        'views/evaluation_views.xml',
        'views/e_gestock_purchase_order_supplier_views.xml',
        'views/menu_views.xml',
        'data/supplier_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}