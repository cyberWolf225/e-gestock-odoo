{
    'name': 'E-GESTOCK Inventory',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Gestion des stocks pour E-GESTOCK',
    'description': """
        Module de gestion des stocks pour E-GESTOCK
        ==========================================
        
        Ce module permet de gérer les stocks dans E-GESTOCK:
        * Suivi des articles en stock
        * Mouvements de stock (entrées, sorties, transferts)
        * Inventaires physiques
        * Intégration avec le système de stock Odoo
    """,
    'author': 'E-GESTOCK Team',
    'website': 'https://www.e-gestock.com',
    'depends': [
        'base',
        'product',
        'stock',
        'uom',
        'mail',
        'e_gestock_base',
    ],
    'data': [
        # Sécurité
        'security/e_gestock_inventory_security.xml',
        'security/ir.model.access.csv',
        
        # Données
        'data/e_gestock_sequence_data.xml',
        
        # Assistants - chargés avant les vues pour que les références existent
        'wizards/stock_transfer_wizard_views.xml',
        'wizards/inventory_import_wizard_views.xml',
        
        # Vues
        'views/depot_views.xml',
        'views/stock_item_views.xml',
        'views/stock_movement_views.xml',
        'views/inventory_views.xml',
        'views/menu_views.xml',
        
        # Rapports
        'report/inventory_report.xml',
        'report/stock_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 