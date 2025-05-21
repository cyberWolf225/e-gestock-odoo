{
    'name': 'E-GESTOCK Budget',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Budget',
    'summary': 'Gestion budgétaire pour E-GESTOCK',
    'description': """
        Module de gestion budgétaire pour E-GESTOCK
        ==========================================

        Ce module permet de gérer les budgets dans E-GESTOCK:
        * Exercices budgétaires
        * Crédits budgétaires
        * Dotations budgétaires
        * Opérations budgétaires
        * Contrôles budgétaires
    """,
    'author': 'E-GESTOCK Team',
    'website': 'https://www.e-gestock.com',
    'depends': [
        'base',
        'mail',
        'web',
        'e_gestock_base',
    ],
    'data': [
        # Sécurité
        'security/e_gestock_budget_security.xml',
        'security/ir.model.access.csv',

        # Données
        'data/e_gestock_sequence_budget_data.xml',

        # Vues
        'views/exercise_views.xml',
        'views/credit_budget_views.xml',
        'views/operation_budget_views.xml',
        'views/dotation_budget_views.xml',
        'views/budget_control_views.xml',
        # La vue e_gestock_purchase_order_budget_views.xml a été déplacée dans le module e_gestock_budget_purchase_bridge
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}