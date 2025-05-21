# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestInventory(TransactionCase):
    """Tests pour le modèle inventory du module e_gestock_inventory"""

    def setUp(self):
        super(TestInventory, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Inventaire',
            'code': 'STR_INV',
        })
        
        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test Inventaire',
            'code': 'DEP_INV',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Inventaire',
            'code': 'FAM_INV',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Inventaire',
            'code': 'CAT_INV',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        self.article1 = self.env['e_gestock.article'].create({
            'name': 'Article Test Inventaire 1',
            'code': 'ART_INV1',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        self.article2 = self.env['e_gestock.article'].create({
            'name': 'Article Test Inventaire 2',
            'code': 'ART_INV2',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        # Créer des articles en stock
        self.stock_item1 = self.env['e_gestock.stock_item'].create({
            'article_id': self.article1.id,
            'depot_id': self.depot.id,
            'quantity': 100.0,
        })
        
        self.stock_item2 = self.env['e_gestock.stock_item'].create({
            'article_id': self.article2.id,
            'depot_id': self.depot.id,
            'quantity': 50.0,
        })

    def test_inventory_creation(self):
        """Test de la création d'un inventaire"""
        # Créer un inventaire
        inventory = self.env['e_gestock.inventory'].create({
            'name': 'Inventaire Test',
            'depot_id': self.depot.id,
            'state': 'draft',
        })
        
        self.assertEqual(inventory.name, 'Inventaire Test')
        self.assertEqual(inventory.depot_id, self.depot)
        self.assertEqual(inventory.state, 'draft')
        self.assertEqual(len(inventory.line_ids), 0)

    def test_inventory_start(self):
        """Test du démarrage d'un inventaire"""
        # Créer un inventaire
        inventory = self.env['e_gestock.inventory'].create({
            'name': 'Inventaire Test Démarrage',
            'depot_id': self.depot.id,
            'state': 'draft',
        })
        
        # Démarrer l'inventaire
        inventory.action_start()
        
        # Vérifier l'état de l'inventaire
        self.assertEqual(inventory.state, 'in_progress')
        
        # Vérifier que les lignes d'inventaire ont été créées
        self.assertEqual(len(inventory.line_ids), 2)
        
        # Vérifier les lignes d'inventaire
        line1 = inventory.line_ids.filtered(lambda l: l.article_id == self.article1)
        self.assertEqual(line1.theoretical_qty, 100.0)
        self.assertEqual(line1.product_qty, 0.0)
        
        line2 = inventory.line_ids.filtered(lambda l: l.article_id == self.article2)
        self.assertEqual(line2.theoretical_qty, 50.0)
        self.assertEqual(line2.product_qty, 0.0)

    def test_inventory_validation(self):
        """Test de la validation d'un inventaire"""
        # Créer un inventaire
        inventory = self.env['e_gestock.inventory'].create({
            'name': 'Inventaire Test Validation',
            'depot_id': self.depot.id,
            'state': 'draft',
        })
        
        # Démarrer l'inventaire
        inventory.action_start()
        
        # Mettre à jour les quantités comptées
        line1 = inventory.line_ids.filtered(lambda l: l.article_id == self.article1)
        line1.write({'product_qty': 90.0})  # 10 de moins
        
        line2 = inventory.line_ids.filtered(lambda l: l.article_id == self.article2)
        line2.write({'product_qty': 55.0})  # 5 de plus
        
        # Valider l'inventaire
        inventory.action_validate()
        
        # Vérifier l'état de l'inventaire
        self.assertEqual(inventory.state, 'done')
        
        # Vérifier les quantités en stock
        stock_item1 = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item1.quantity, 90.0)  # Mise à jour à 90
        
        stock_item2 = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article2.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item2.quantity, 55.0)  # Mise à jour à 55

    def test_inventory_cancel(self):
        """Test de l'annulation d'un inventaire"""
        # Créer un inventaire
        inventory = self.env['e_gestock.inventory'].create({
            'name': 'Inventaire Test Annulation',
            'depot_id': self.depot.id,
            'state': 'draft',
        })
        
        # Démarrer l'inventaire
        inventory.action_start()
        
        # Annuler l'inventaire
        inventory.action_cancel()
        
        # Vérifier l'état de l'inventaire
        self.assertEqual(inventory.state, 'cancel')
        
        # Vérifier que les quantités en stock n'ont pas changé
        stock_item1 = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article1.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item1.quantity, 100.0)  # Inchangé
        
        stock_item2 = self.env['e_gestock.stock_item'].search([
            ('article_id', '=', self.article2.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item2.quantity, 50.0)  # Inchangé
