# -*- coding: utf-8 -*-
{
    'name': 'E-GESTOCK Perdiem',
    'version': '1.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Gestion des perdiems et indemnités journalières',
    'description': """
Module de gestion des perdiems pour E-GESTOCK
=============================================

Ce module permet la gestion des demandes de perdiem (indemnités journalières) :
- Création et suivi des demandes de perdiem
- Workflow de validation configurable
- Intégration avec le module budgétaire
- Contrôle des disponibilités budgétaires
- Suivi des bénéficiaires et montants
- Reporting et statistiques
""",
    'author': 'E-GESTOCK',
    'website': 'https://www.e-gestock.com',
    'depends': [
        'base',
        'mail',
        'e_gestock_base',
        'e_gestock_budget',
    ],
    'data': [
        # Sécurité
        'security/e_gestock_perdiem_security.xml',
        'security/ir.model.access.csv',
        
        # Données
        'data/e_gestock_perdiem_sequence_data.xml',
        'data/e_gestock_perdiem_status_data.xml',
        'data/e_gestock_perdiem_mail_template_data.xml',
        
        # Assistants
        'wizards/perdiem_validation_wizard_views.xml',
        'wizards/perdiem_reject_wizard_views.xml',
        
        # Vues
        'views/perdiem_views.xml',
        'views/perdiem_beneficiary_views.xml',
        'views/perdiem_status_type_views.xml',
        'views/menu_views.xml',
        
        # Rapports
        'report/perdiem_report.xml',
        'report/perdiem_templates.xml',
    ],
    'demo': [
        'demo/perdiem_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
