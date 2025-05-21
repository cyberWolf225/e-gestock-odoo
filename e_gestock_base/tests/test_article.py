# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestArticle(TransactionCase):
    """Tests pour le modèle article du module e_gestock_base"""

    def setUp(self):
        super(TestArticle, self).setUp()
        # Créer des données de test
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test',
            'code': 'FAM01',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test',
            'code': 'CAT01',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        # Créer un article de test
        self.article = self.env['e_gestock.article'].create({
            'name': 'Article Test',
            'code': 'ART001',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })

    def test_article_creation(self):
        """Test de la création d'un article"""
        self.assertEqual(self.article.name, 'Article Test')
        self.assertEqual(self.article.code, 'ART001')
        self.assertEqual(self.article.famille_id, self.famille)
        self.assertEqual(self.article.categorie_id, self.categorie)
        self.assertEqual(self.article.uom_id, self.uom_unit)
        self.assertEqual(self.article.type, 'product')

    def test_article_name_get(self):
        """Test de l'affichage du nom de l'article"""
        name = self.article.name_get()[0][1]
        self.assertEqual(name, '[ART001] Article Test')

    def test_article_search(self):
        """Test de la recherche d'articles"""
        # Recherche par code
        articles = self.env['e_gestock.article'].search([('code', '=', 'ART001')])
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0], self.article)
        
        # Recherche par nom
        articles = self.env['e_gestock.article'].search([('name', 'ilike', 'Test')])
        self.assertIn(self.article, articles)

    def test_article_constraints(self):
        """Test des contraintes sur les articles"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.article'].create({
                'name': 'Article Test 2',
                'code': 'ART001',  # Code déjà utilisé
                'famille_id': self.famille.id,
                'categorie_id': self.categorie.id,
                'uom_id': self.uom_unit.id,
                'type': 'product',
            })

    def test_article_onchange(self):
        """Test des méthodes onchange"""
        # Créer un nouvel article sans catégorie
        article = self.env['e_gestock.article'].new({
            'name': 'Article Test Onchange',
            'code': 'ART002',
            'famille_id': self.famille.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        # Vérifier que les catégories disponibles sont filtrées par famille
        domain = article._onchange_famille_id()
        self.assertEqual(domain['domain']['categorie_id'], [('famille_id', '=', self.famille.id)])
