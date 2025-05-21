# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestPurchaseOrder(TransactionCase):
    """Tests pour le modèle purchase.order du module e_gestock_purchase"""

    def setUp(self):
        super(TestPurchaseOrder, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Achat',
            'code': 'STR_ACH',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Achat',
            'code': 'SEC_ACH',
            'structure_id': self.structure.id,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Achat',
            'code': 'FAM_ACH',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Achat',
            'code': 'CAT_ACH',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        # Créer un produit natif Odoo
        self.product = self.env['product.product'].create({
            'name': 'Produit Test Achat',
            'type': 'product',
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Achat',
            'login': 'user_test_achat',
            'email': 'user_test_achat@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_purchase_manager').id)],
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test Achat',
            'email': 'fournisseur_achat@test.com',
            'supplier_rank': 1,
        })
        
        # Créer une demande de cotation
        self.demande_cotation = self.env['e_gestock.demande_cotation'].create({
            'name': 'DC-TEST-002',
            'demandeur_id': self.user.id,
            'section_id': self.section.id,
            'date_demande': '2023-02-01',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': False,  # Pas d'article e_gestock
                    'product_id': self.product.id,  # Produit natif Odoo
                    'quantity': 10.0,
                    'description': 'Description produit',
                }),
            ],
        })
        
        # Ajouter le fournisseur à la demande de cotation
        self.fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].create({
            'demande_id': self.demande_cotation.id,
            'partner_id': self.partner.id,
        })
        
        # Valider la demande de cotation
        self.demande_cotation.action_validate()
        
        # Créer une cotation
        self.cotation = self.env['e_gestock.cotation'].create({
            'name': 'COT-TEST-002',
            'demande_id': self.demande_cotation.id,
            'partner_id': self.partner.id,
            'date_cotation': '2023-02-15',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': False,  # Pas d'article e_gestock
                    'product_id': self.product.id,  # Produit natif Odoo
                    'quantity': 10.0,
                    'price_unit': 100.0,
                    'description': 'Description produit',
                }),
            ],
        })
        
        # Valider la cotation
        self.cotation.action_validate()
        
        # Créer un bon de commande à partir de la cotation
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'date_order': '2023-02-20',
            'cotation_id': self.cotation.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': 'Description produit',
                    'product_qty': 10.0,
                    'product_uom': self.uom_unit.id,
                    'price_unit': 100.0,
                    'date_planned': '2023-03-01',
                }),
            ],
        })

    def test_purchase_order_creation(self):
        """Test de la création d'un bon de commande"""
        self.assertEqual(self.purchase_order.partner_id, self.partner)
        self.assertEqual(self.purchase_order.date_order.strftime('%Y-%m-%d'), '2023-02-20')
        self.assertEqual(self.purchase_order.cotation_id, self.cotation)
        self.assertEqual(len(self.purchase_order.order_line), 1)
        
        # Vérifier les lignes du bon de commande
        self.assertEqual(self.purchase_order.order_line[0].product_id, self.product)
        self.assertEqual(self.purchase_order.order_line[0].name, 'Description produit')
        self.assertEqual(self.purchase_order.order_line[0].product_qty, 10.0)
        self.assertEqual(self.purchase_order.order_line[0].product_uom, self.uom_unit)
        self.assertEqual(self.purchase_order.order_line[0].price_unit, 100.0)
        self.assertEqual(self.purchase_order.order_line[0].date_planned.strftime('%Y-%m-%d'), '2023-03-01')

    def test_purchase_order_confirmation(self):
        """Test de la confirmation d'un bon de commande"""
        # Confirmer le bon de commande
        self.purchase_order.button_confirm()
        
        # Vérifier l'état du bon de commande
        self.assertEqual(self.purchase_order.state, 'purchase')
        
        # Vérifier que la date de confirmation est définie
        self.assertTrue(self.purchase_order.date_approve)

    def test_purchase_order_cancel(self):
        """Test de l'annulation d'un bon de commande"""
        # Annuler le bon de commande
        self.purchase_order.button_cancel()
        
        # Vérifier l'état du bon de commande
        self.assertEqual(self.purchase_order.state, 'cancel')

    def test_purchase_order_reset(self):
        """Test de la réinitialisation d'un bon de commande"""
        # Confirmer puis annuler le bon de commande
        self.purchase_order.button_confirm()
        self.purchase_order.button_cancel()
        
        # Réinitialiser le bon de commande
        self.purchase_order.button_draft()
        
        # Vérifier l'état du bon de commande
        self.assertEqual(self.purchase_order.state, 'draft')

    def test_purchase_order_amount_total(self):
        """Test du calcul du montant total du bon de commande"""
        # Calculer le montant total attendu
        expected_total = 10.0 * 100.0  # 1000
        
        # Vérifier le montant total calculé
        self.assertEqual(self.purchase_order.amount_total, expected_total)
