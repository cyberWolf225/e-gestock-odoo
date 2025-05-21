# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestReception(TransactionCase):
    """Tests pour le modèle reception du module e_gestock_reception"""

    def setUp(self):
        super(TestReception, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Réception',
            'code': 'STR_REC',
        })
        
        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test Réception',
            'code': 'DEP_REC',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Réception',
            'code': 'FAM_REC',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Réception',
            'code': 'CAT_REC',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        # Créer un produit natif Odoo
        self.product = self.env['product.product'].create({
            'name': 'Produit Test Réception',
            'type': 'product',
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Réception',
            'login': 'user_test_reception',
            'email': 'user_test_reception@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_manager').id)],
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test Réception',
            'email': 'fournisseur_reception@test.com',
            'supplier_rank': 1,
        })
        
        # Créer un bon de commande
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': datetime.now().strftime('%Y-%m-%d'),
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': 'Description produit',
                    'product_qty': 10.0,
                    'product_uom': self.uom_unit.id,
                    'price_unit': 100.0,
                    'date_planned': datetime.now().strftime('%Y-%m-%d'),
                }),
            ],
        })
        
        # Confirmer le bon de commande
        self.purchase_order.button_confirm()
        
        # Créer une réception
        self.reception = self.env['e_gestock.reception'].create({
            'name': 'REC-TEST-001',
            'purchase_order_id': self.purchase_order.id,
            'partner_id': self.partner.id,
            'date_reception': datetime.now().strftime('%Y-%m-%d'),
            'depot_id': self.depot.id,
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': 'Description produit',
                    'quantity_ordered': 10.0,
                    'quantity_received': 10.0,
                    'uom_id': self.uom_unit.id,
                }),
            ],
        })

    def test_reception_creation(self):
        """Test de la création d'une réception"""
        self.assertEqual(self.reception.name, 'REC-TEST-001')
        self.assertEqual(self.reception.purchase_order_id, self.purchase_order)
        self.assertEqual(self.reception.partner_id, self.partner)
        self.assertEqual(self.reception.depot_id, self.depot)
        self.assertEqual(self.reception.state, 'draft')
        self.assertEqual(len(self.reception.line_ids), 1)
        
        # Vérifier les lignes de la réception
        self.assertEqual(self.reception.line_ids[0].product_id, self.product)
        self.assertEqual(self.reception.line_ids[0].name, 'Description produit')
        self.assertEqual(self.reception.line_ids[0].quantity_ordered, 10.0)
        self.assertEqual(self.reception.line_ids[0].quantity_received, 10.0)
        self.assertEqual(self.reception.line_ids[0].uom_id, self.uom_unit)

    def test_reception_validation(self):
        """Test de la validation d'une réception"""
        # Valider la réception
        self.reception.action_validate()
        
        # Vérifier l'état de la réception
        self.assertEqual(self.reception.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.reception.date_validation)
        
        # Vérifier que les quantités en stock sont mises à jour
        stock_item = self.env['e_gestock.stock_item'].search([
            ('product_id', '=', self.product.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item.quantity, 10.0)

    def test_reception_cancel(self):
        """Test de l'annulation d'une réception"""
        # Valider puis annuler la réception
        self.reception.action_validate()
        self.reception.action_cancel()
        
        # Vérifier l'état de la réception
        self.assertEqual(self.reception.state, 'cancel')
        
        # Vérifier que les quantités en stock sont mises à jour
        stock_item = self.env['e_gestock.stock_item'].search([
            ('product_id', '=', self.product.id),
            ('depot_id', '=', self.depot.id),
        ])
        self.assertEqual(stock_item.quantity, 0.0)  # Retour à 0

    def test_reception_reset(self):
        """Test de la réinitialisation d'une réception"""
        # Valider puis annuler la réception
        self.reception.action_validate()
        self.reception.action_cancel()
        
        # Réinitialiser la réception
        self.reception.action_reset()
        
        # Vérifier l'état de la réception
        self.assertEqual(self.reception.state, 'draft')

    def test_reception_constraints(self):
        """Test des contraintes sur les réceptions"""
        # Test de la contrainte sur les quantités reçues
        with self.assertRaises(ValidationError):
            self.reception.line_ids[0].write({'quantity_received': -1.0})
        
        # Test de la contrainte sur la modification d'une réception validée
        self.reception.action_validate()
        with self.assertRaises(ValidationError):
            self.reception.write({'date_reception': '2023-01-01'})
