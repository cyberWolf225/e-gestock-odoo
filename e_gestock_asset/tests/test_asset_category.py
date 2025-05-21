# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestAssetCategory(TransactionCase):
    """Tests pour le modèle asset_category du module e_gestock_asset"""

    def setUp(self):
        super(TestAssetCategory, self).setUp()
        # Créer des catégories d'actifs
        self.category1 = self.env['e_gestock.asset_category'].create({
            'name': 'Catégorie Asset 1',
            'code': 'CAT_AST1',
            'depreciation_method': 'linear',
            'depreciation_rate': 20.0,  # 5 ans
            'active': True,
        })
        
        self.category2 = self.env['e_gestock.asset_category'].create({
            'name': 'Catégorie Asset 2',
            'code': 'CAT_AST2',
            'depreciation_method': 'degressive',
            'depreciation_rate': 30.0,  # 3.33 ans
            'active': True,
        })
        
        self.category3 = self.env['e_gestock.asset_category'].create({
            'name': 'Catégorie Asset 3',
            'code': 'CAT_AST3',
            'depreciation_method': 'linear',
            'depreciation_rate': 10.0,  # 10 ans
            'active': False,  # Catégorie inactive
        })

    def test_category_creation(self):
        """Test de la création d'une catégorie d'actif"""
        self.assertEqual(self.category1.name, 'Catégorie Asset 1')
        self.assertEqual(self.category1.code, 'CAT_AST1')
        self.assertEqual(self.category1.depreciation_method, 'linear')
        self.assertEqual(self.category1.depreciation_rate, 20.0)
        self.assertTrue(self.category1.active)
        
        self.assertEqual(self.category2.name, 'Catégorie Asset 2')
        self.assertEqual(self.category2.code, 'CAT_AST2')
        self.assertEqual(self.category2.depreciation_method, 'degressive')
        self.assertEqual(self.category2.depreciation_rate, 30.0)
        self.assertTrue(self.category2.active)
        
        self.assertEqual(self.category3.name, 'Catégorie Asset 3')
        self.assertEqual(self.category3.code, 'CAT_AST3')
        self.assertEqual(self.category3.depreciation_method, 'linear')
        self.assertEqual(self.category3.depreciation_rate, 10.0)
        self.assertFalse(self.category3.active)

    def test_category_search(self):
        """Test de la recherche de catégories d'actif"""
        # Recherche par nom
        categories = self.env['e_gestock.asset_category'].search([('name', 'ilike', 'Catégorie')])
        self.assertEqual(len(categories), 2)  # Seulement les catégories actives
        self.assertIn(self.category1, categories)
        self.assertIn(self.category2, categories)
        self.assertNotIn(self.category3, categories)
        
        # Recherche par code
        categories = self.env['e_gestock.asset_category'].search([('code', '=', 'CAT_AST1')])
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], self.category1)
        
        # Recherche par méthode d'amortissement
        categories = self.env['e_gestock.asset_category'].search([('depreciation_method', '=', 'linear')])
        self.assertEqual(len(categories), 1)  # Seulement les catégories actives
        self.assertEqual(categories[0], self.category1)
        
        # Recherche incluant les archives
        categories = self.env['e_gestock.asset_category'].with_context(active_test=False).search([])
        self.assertEqual(len(categories), 3)
        self.assertIn(self.category1, categories)
        self.assertIn(self.category2, categories)
        self.assertIn(self.category3, categories)

    def test_category_archive(self):
        """Test de l'archivage d'une catégorie d'actif"""
        # Archiver une catégorie
        self.category1.write({'active': False})
        self.assertFalse(self.category1.active)
        
        # Vérifier que la catégorie n'apparaît plus dans les recherches par défaut
        categories = self.env['e_gestock.asset_category'].search([])
        self.assertNotIn(self.category1, categories)
        self.assertIn(self.category2, categories)
        
        # Réactiver la catégorie
        self.category1.write({'active': True})
        self.assertTrue(self.category1.active)
        
        # Vérifier que la catégorie apparaît à nouveau dans les recherches par défaut
        categories = self.env['e_gestock.asset_category'].search([])
        self.assertIn(self.category1, categories)
        self.assertIn(self.category2, categories)

    def test_category_constraints(self):
        """Test des contraintes sur les catégories d'actif"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.asset_category'].create({
                'name': 'Catégorie Asset Dupliquée',
                'code': 'CAT_AST1',  # Code déjà utilisé
                'depreciation_method': 'linear',
                'depreciation_rate': 25.0,
                'active': True,
            })
        
        # Test de la contrainte sur le taux d'amortissement
        with self.assertRaises(ValidationError):
            self.category1.write({'depreciation_rate': 0.0})
        
        with self.assertRaises(ValidationError):
            self.category1.write({'depreciation_rate': 101.0})
