{
    'name': 'E-GESTOCK Budget-Purchase Bridge',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Budget',
    'summary': 'Module pont entre E-GESTOCK Budget et E-GESTOCK Purchase',
    'description': """
        Module pont entre E-GESTOCK Budget et E-GESTOCK Purchase
        ========================================================

        Ce module ajoute les fonctionnalités qui dépendent à la fois du module budget et du module achat.
    """,
    'author': 'E-GESTOCK Team',
    'website': 'https://www.e-gestock.com',
    'depends': [
        'e_gestock_base',
        'e_gestock_budget',
        'e_gestock_purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/e_gestock_purchase_order_budget_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
