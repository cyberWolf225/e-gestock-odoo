# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestStockItem(TransactionCase):
    """Tests pour le modèle stock_item du module e_gestock_inventory"""

    def setUp(self):
        super(TestStockItem, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Stock',
            'code': 'STR_STOCK',
        })
        
        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test Stock',
            'code': 'DEP_STOCK',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Stock',
            'code': 'FAM_STOCK',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Stock',
            'code': 'CAT_STOCK',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        self.article = self.env['e_gestock.article'].create({
            'name': 'Article Test Stock',
            'code': 'ART_STOCK',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        # Créer un article en stock
        self.stock_item = self.env['e_gestock.stock_item'].create({
            'article_id': self.article.id,
            'depot_id': self.depot.id,
            'quantity': 100.0,
        })

    def test_stock_item_creation(self):
        """Test de la création d'un article en stock"""
        self.assertEqual(self.stock_item.article_id, self.article)
        self.assertEqual(self.stock_item.depot_id, self.depot)
        self.assertEqual(self.stock_item.quantity, 100.0)

    def test_stock_item_update(self):
        """Test de la mise à jour d'un article en stock"""
        # Mettre à jour la quantité
        self.stock_item.write({'quantity': 150.0})
        self.assertEqual(self.stock_item.quantity, 150.0)

    def test_stock_item_constraints(self):
        """Test des contraintes sur les articles en stock"""
        # Test de l'unicité de l'article par dépôt
        with self.assertRaises(Exception):
            self.env['e_gestock.stock_item'].create({
                'article_id': self.article.id,
                'depot_id': self.depot.id,  # Même article et même dépôt
                'quantity': 50.0,
            })

    def test_stock_item_search(self):
        """Test de la recherche d'articles en stock"""
        # Recherche par article
        stock_items = self.env['e_gestock.stock_item'].search([('article_id', '=', self.article.id)])
        self.assertEqual(len(stock_items), 1)
        self.assertEqual(stock_items[0], self.stock_item)
        
        # Recherche par dépôt
        stock_items = self.env['e_gestock.stock_item'].search([('depot_id', '=', self.depot.id)])
        self.assertEqual(len(stock_items), 1)
        self.assertEqual(stock_items[0], self.stock_item)
        
        # Recherche par quantité
        stock_items = self.env['e_gestock.stock_item'].search([('quantity', '>=', 50.0)])
        self.assertIn(self.stock_item, stock_items)

    def test_stock_item_name_get(self):
        """Test de l'affichage du nom de l'article en stock"""
        name = self.stock_item.name_get()[0][1]
        self.assertEqual(name, 'Article Test Stock (Dépôt Test Stock)')
