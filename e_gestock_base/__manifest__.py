# -*- coding: utf-8 -*-
{
    'name': 'E-GESTOCK Base',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Module de base pour la solution E-GESTOCK',
    'description': """
Module de base pour E-GESTOCK
=============================

Ce module constitue le socle fondamental de la solution E-GESTOCK pour Odoo 18 Community.
Il définit la structure organisationnelle, les articles et les fonctionnalités communes utilisées
par tous les autres modules.

Fonctionnalités principales:
---------------------------
* Gestion des structures organisationnelles
* Gestion des sections
* Gestion des dépôts
* Gestion des familles d'articles
* Gestion des articles
* Gestion des types de gestion
* Droits d'accès et sécurité
    """,
    'author': 'E-GESTOCK Team',
    'depends': [
        'base',
        'mail',
        'product',
        'uom',
        'web',
    ],
    'data': [
        # Configuration des données de base
        'data/e_gestock_type_gestion_data.xml',
        'data/categorie_data.xml',
        'data/depot_data.xml',
        'data/famille_data.xml',
        'data/structure_data.xml',
        'data/section_data.xml',  # Fichier combiné de toutes les sections
        # 'data/test_sections.xml',  # Sections de test - temporairement désactivé

        # Security
        'security/e_gestock_security_optimized.xml',
        'security/group_compatibility_minimal.xml',
        'security/ir.model.access.csv',

        # Views
        'views/structure_views.xml',
        'views/section_views.xml',
        'views/famille_views.xml',
        'views/depot_views.xml',
        'views/categorie_views.xml',
        'views/article_views.xml',
        'views/type_gestion_views.xml',

        # Menu principal (consolidé)
        'views/menu_views.xml',

        # Vues qui dépendent des menus
        'views/res_users_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}