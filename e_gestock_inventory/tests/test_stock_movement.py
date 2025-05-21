# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestStockMovement(TransactionCase):
    """Tests pour le modèle stock_movement du module e_gestock_inventory"""

    def setUp(self):
        super(TestStockMovement, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Mouvement',
            'code': 'STR_MVT',
        })
        
        self.depot_source = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Source',
            'code': 'DEP_SRC',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.depot_dest = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Destination',
            'code': 'DEP_DEST',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Mouvement',
            'code': 'FAM_MVT',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Mouvement',
            'code': 'CAT_MVT',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        self.article1 = self.env['e_gestock.article'].create({
            'name': 'Article Test Mouvement 1',
            'code': 'ART_MVT1',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        self.article2 = self.env['e_gestock.article'].create({
            'name': 'Article Test Mouvement 2',
            'code': 'ART_MVT2',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        # Créer des articles en stock
        self.stock_item1 = self.env['e_gestock.stock_item'].create({
            'article_id': self.article1.id,
            'depot_id': self.depot_source.id,
            'quantity': 100.0,
        })
        
        self.stock_item2 = self.env['e_gestock.stock_item'].create({
            'article_id': self.article2.id,
            'depot_id': self.depot_source.id,
            'quantity': 50.0,
        })

    def test_stock_movement_creation(self):
        """Test de la création d'un mouvement de stock"""
        # Créer un mouvement de stock
        movement = self.env['e_gestock.stock_movement'].create({
            'name': 'Mouvement Test',
            'source_depot_id': self.depot_source.id,
            'dest_depot_id': self.depot_dest.id,
            'movement_type': 'transfer',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': self.article1.id,
                    'quantity': 10.0,
                }),
                (0, 0, {
                    'article_id': self.article2.id,
                    'quantity': 5.0,
                }),
            ],
        })
        
        self.assertEqual(movement.name, 'Mouvement Test')
        self.assertEqual(movement.source_depot_id, self.depot_source)
        self.assertEqual(movement.dest_depot_id, self.depot_dest)
        self.assertEqual(movement.movement_type, 'transfer')
        self.assertEqual(movement.state, 'draft')
        self.assertEqual(len(movement.line_ids), 2)
        
        # Vérifier les lignes du mouvement
        self.assertEqual(movement.line_ids[0].article_id, self.article1)
        self.assertEqual(movement.line_ids[0].quantity, 10.0)
        self.assertEqual(movement.line_ids[1].article_id, self.article2)
        self.assertEqual(movement.line_ids[1].quantity, 5.0)

    def test_stock_movement_validation(self):
        """Test de la validation d'un mouvement de stock"""
        # Créer un mouvement de stock
        movement = self.env['e_gestock.stock_movement'].create({
            'name': 'Mouvement Test Validation',
            'source_depot_id': self.depot_source.id,
            'dest_depot_id': self.depot_dest.id,
            'movement_type': 'transfer',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': self.article1.id,
                    'quantity': 10.0,
                }),
                (0, 0, {
                    'article_id': self.article2.id,
                    'quantity': 5.0,
                }),
            ],
        })
        
        # Valider le mouvement
        movement.action_validate()
        
        # Vérifier l'état du mouvement
        self.assertEqual(movement.state, 'done')
        
        # Vérifier les quantités en stock
        stock_item1_source = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot_source.id),
        ])
        self.assertEqual(stock_item1_source.quantity, 90.0)  # 100 - 10
        
        stock_item2_source = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article2.id),
            ('depot_id', '=', self.depot_source.id),
        ])
        self.assertEqual(stock_item2_source.quantity, 45.0)  # 50 - 5
        
        stock_item1_dest = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot_dest.id),
        ])
        self.assertEqual(stock_item1_dest.quantity, 10.0)
        
        stock_item2_dest = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article2.id),
            ('depot_id', '=', self.depot_dest.id),
        ])
        self.assertEqual(stock_item2_dest.quantity, 5.0)

    def test_stock_movement_cancel(self):
        """Test de l'annulation d'un mouvement de stock"""
        # Créer un mouvement de stock
        movement = self.env['e_gestock.stock_movement'].create({
            'name': 'Mouvement Test Annulation',
            'source_depot_id': self.depot_source.id,
            'dest_depot_id': self.depot_dest.id,
            'movement_type': 'transfer',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': self.article1.id,
                    'quantity': 10.0,
                }),
            ],
        })
        
        # Valider le mouvement
        movement.action_validate()
        
        # Annuler le mouvement
        movement.action_cancel()
        
        # Vérifier l'état du mouvement
        self.assertEqual(movement.state, 'cancel')
        
        # Vérifier les quantités en stock (retour à l'état initial)
        stock_item1_source = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot_source.id),
        ])
        self.assertEqual(stock_item1_source.quantity, 100.0)  # Retour à 100
        
        stock_item1_dest = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot_dest.id),
        ])
        self.assertEqual(stock_item1_dest.quantity, 0.0)  # Retour à 0
