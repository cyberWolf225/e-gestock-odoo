# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestPVReception(TransactionCase):
    """Tests pour le modèle pv_reception du module e_gestock_reception"""

    def setUp(self):
        super(TestPVReception, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test PV',
            'code': 'STR_PV',
        })
        
        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test PV',
            'code': 'DEP_PV',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        # Créer un produit natif Odoo
        self.product = self.env['product.product'].create({
            'name': 'Produit Test PV',
            'type': 'product',
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
        })
        
        # Créer des utilisateurs de test
        self.user1 = self.env['res.users'].create({
            'name': 'Membre Comité 1',
            'login': 'membre_comite1_pv',
            'email': 'membre_comite1_pv@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_user').id)],
        })
        
        self.user2 = self.env['res.users'].create({
            'name': 'Membre Comité 2',
            'login': 'membre_comite2_pv',
            'email': 'membre_comite2_pv@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_user').id)],
        })
        
        self.user3 = self.env['res.users'].create({
            'name': 'Membre Comité 3',
            'login': 'membre_comite3_pv',
            'email': 'membre_comite3_pv@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_manager').id)],
        })
        
        # Créer un comité de réception
        self.comite = self.env['e_gestock.comite_reception'].create({
            'name': 'Comité de Réception Test PV',
            'code': 'COM_PV',
            'structure_id': self.structure.id,
            'date_creation': datetime.now().strftime('%Y-%m-%d'),
            'state': 'active',  # Comité actif
            'member_ids': [
                (0, 0, {
                    'user_id': self.user1.id,
                    'role': 'president',
                }),
                (0, 0, {
                    'user_id': self.user2.id,
                    'role': 'member',
                }),
                (0, 0, {
                    'user_id': self.user3.id,
                    'role': 'secretary',
                }),
            ],
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test PV',
            'email': 'fournisseur_pv@test.com',
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
            'name': 'REC-PV-001',
            'purchase_order_id': self.purchase_order.id,
            'partner_id': self.partner.id,
            'date_reception': datetime.now().strftime('%Y-%m-%d'),
            'depot_id': self.depot.id,
            'state': 'validated',  # Réception validée
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
        
        # Créer un PV de réception
        self.pv = self.env['e_gestock.pv_reception'].create({
            'name': 'PV-TEST-001',
            'reception_id': self.reception.id,
            'comite_id': self.comite.id,
            'date_pv': datetime.now().strftime('%Y-%m-%d'),
            'state': 'draft',
            'signature_ids': [
                (0, 0, {
                    'user_id': self.user1.id,
                    'role': 'president',
                    'signed': False,
                }),
                (0, 0, {
                    'user_id': self.user2.id,
                    'role': 'member',
                    'signed': False,
                }),
                (0, 0, {
                    'user_id': self.user3.id,
                    'role': 'secretary',
                    'signed': False,
                }),
            ],
        })

    def test_pv_creation(self):
        """Test de la création d'un PV de réception"""
        self.assertEqual(self.pv.name, 'PV-TEST-001')
        self.assertEqual(self.pv.reception_id, self.reception)
        self.assertEqual(self.pv.comite_id, self.comite)
        self.assertEqual(self.pv.state, 'draft')
        self.assertEqual(len(self.pv.signature_ids), 3)
        
        # Vérifier les signatures du PV
        president = self.pv.signature_ids.filtered(lambda s: s.role == 'president')
        self.assertEqual(president.user_id, self.user1)
        self.assertFalse(president.signed)
        
        member = self.pv.signature_ids.filtered(lambda s: s.role == 'member')
        self.assertEqual(member.user_id, self.user2)
        self.assertFalse(member.signed)
        
        secretary = self.pv.signature_ids.filtered(lambda s: s.role == 'secretary')
        self.assertEqual(secretary.user_id, self.user3)
        self.assertFalse(secretary.signed)

    def test_pv_signature(self):
        """Test de la signature d'un PV de réception"""
        # Signer le PV en tant que président
        president = self.pv.signature_ids.filtered(lambda s: s.role == 'president')
        president.action_sign()
        self.assertTrue(president.signed)
        self.assertTrue(president.date_signature)
        
        # Signer le PV en tant que membre
        member = self.pv.signature_ids.filtered(lambda s: s.role == 'member')
        member.action_sign()
        self.assertTrue(member.signed)
        self.assertTrue(member.date_signature)
        
        # Signer le PV en tant que secrétaire
        secretary = self.pv.signature_ids.filtered(lambda s: s.role == 'secretary')
        secretary.action_sign()
        self.assertTrue(secretary.signed)
        self.assertTrue(secretary.date_signature)
        
        # Vérifier que le PV est automatiquement validé
        self.assertEqual(self.pv.state, 'validated')

    def test_pv_validation(self):
        """Test de la validation d'un PV de réception"""
        # Signer le PV par tous les membres
        for signature in self.pv.signature_ids:
            signature.action_sign()
        
        # Vérifier l'état du PV
        self.assertEqual(self.pv.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.pv.date_validation)

    def test_pv_cancel(self):
        """Test de l'annulation d'un PV de réception"""
        # Annuler le PV
        self.pv.action_cancel()
        
        # Vérifier l'état du PV
        self.assertEqual(self.pv.state, 'cancel')

    def test_pv_reset(self):
        """Test de la réinitialisation d'un PV de réception"""
        # Signer le PV par tous les membres puis l'annuler
        for signature in self.pv.signature_ids:
            signature.action_sign()
        self.pv.action_cancel()
        
        # Réinitialiser le PV
        self.pv.action_reset()
        
        # Vérifier l'état du PV
        self.assertEqual(self.pv.state, 'draft')
        
        # Vérifier que les signatures sont réinitialisées
        for signature in self.pv.signature_ids:
            self.assertFalse(signature.signed)
            self.assertFalse(signature.date_signature)
