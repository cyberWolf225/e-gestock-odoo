# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestSupplierCategory(TransactionCase):
    """Tests pour le modèle supplier_category du module e_gestock_supplier"""

    def setUp(self):
        super(TestSupplierCategory, self).setUp()
        # Créer des données de test
        self.category1 = self.env['e_gestock.supplier_category'].create({
            'name': 'Catégorie Fournisseur 1',
            'code': 'CAT_FOUR1',
            'description': 'Description catégorie 1',
            'active': True,
        })
        
        self.category2 = self.env['e_gestock.supplier_category'].create({
            'name': 'Catégorie Fournisseur 2',
            'code': 'CAT_FOUR2',
            'description': 'Description catégorie 2',
            'active': True,
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test Catégorie',
            'email': 'fournisseur_categorie@test.com',
            'supplier_rank': 1,
            'supplier_category_id': self.category1.id,
        })

    def test_category_creation(self):
        """Test de la création d'une catégorie de fournisseur"""
        self.assertEqual(self.category1.name, 'Catégorie Fournisseur 1')
        self.assertEqual(self.category1.code, 'CAT_FOUR1')
        self.assertEqual(self.category1.description, 'Description catégorie 1')
        self.assertTrue(self.category1.active)
        
        self.assertEqual(self.category2.name, 'Catégorie Fournisseur 2')
        self.assertEqual(self.category2.code, 'CAT_FOUR2')
        self.assertEqual(self.category2.description, 'Description catégorie 2')
        self.assertTrue(self.category2.active)

    def test_category_supplier_assignment(self):
        """Test de l'assignation d'une catégorie à un fournisseur"""
        self.assertEqual(self.partner.supplier_category_id, self.category1)
        
        # Changer la catégorie du fournisseur
        self.partner.write({'supplier_category_id': self.category2.id})
        self.assertEqual(self.partner.supplier_category_id, self.category2)

    def test_category_archive(self):
        """Test de l'archivage d'une catégorie de fournisseur"""
        # Archiver la catégorie
        self.category1.write({'active': False})
        self.assertFalse(self.category1.active)
        
        # Vérifier que la catégorie n'apparaît plus dans les recherches par défaut
        categories = self.env['e_gestock.supplier_category'].search([])
        self.assertNotIn(self.category1, categories)
        
        # Vérifier que la catégorie apparaît dans les recherches incluant les archives
        categories = self.env['e_gestock.supplier_category'].with_context(active_test=False).search([])
        self.assertIn(self.category1, categories)
        
        # Réactiver la catégorie
        self.category1.write({'active': True})
        self.assertTrue(self.category1.active)
        
        # Vérifier que la catégorie apparaît à nouveau dans les recherches par défaut
        categories = self.env['e_gestock.supplier_category'].search([])
        self.assertIn(self.category1, categories)

    def test_category_constraints(self):
        """Test des contraintes sur les catégories de fournisseur"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.supplier_category'].create({
                'name': 'Catégorie Fournisseur Dupliquée',
                'code': 'CAT_FOUR1',  # Code déjà utilisé
                'description': 'Description catégorie dupliquée',
                'active': True,
            })

    def test_category_search(self):
        """Test de la recherche de catégories de fournisseur"""
        # Recherche par nom
        categories = self.env['e_gestock.supplier_category'].search([('name', 'ilike', 'Catégorie')])
        self.assertEqual(len(categories), 2)
        self.assertIn(self.category1, categories)
        self.assertIn(self.category2, categories)
        
        # Recherche par code
        categories = self.env['e_gestock.supplier_category'].search([('code', '=', 'CAT_FOUR1')])
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], self.category1)
