# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestComiteReception(TransactionCase):
    """Tests pour le modèle comite_reception du module e_gestock_reception"""

    def setUp(self):
        super(TestComiteReception, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Comité',
            'code': 'STR_COM',
        })
        
        # Créer des utilisateurs de test
        self.user1 = self.env['res.users'].create({
            'name': 'Membre Comité 1',
            'login': 'membre_comite1',
            'email': 'membre_comite1@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_user').id)],
        })
        
        self.user2 = self.env['res.users'].create({
            'name': 'Membre Comité 2',
            'login': 'membre_comite2',
            'email': 'membre_comite2@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_user').id)],
        })
        
        self.user3 = self.env['res.users'].create({
            'name': 'Membre Comité 3',
            'login': 'membre_comite3',
            'email': 'membre_comite3@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_reception_manager').id)],
        })
        
        # Créer un comité de réception
        self.comite = self.env['e_gestock.comite_reception'].create({
            'name': 'Comité de Réception Test',
            'code': 'COM001',
            'structure_id': self.structure.id,
            'date_creation': datetime.now().strftime('%Y-%m-%d'),
            'state': 'draft',
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

    def test_comite_creation(self):
        """Test de la création d'un comité de réception"""
        self.assertEqual(self.comite.name, 'Comité de Réception Test')
        self.assertEqual(self.comite.code, 'COM001')
        self.assertEqual(self.comite.structure_id, self.structure)
        self.assertEqual(self.comite.state, 'draft')
        self.assertEqual(len(self.comite.member_ids), 3)
        
        # Vérifier les membres du comité
        president = self.comite.member_ids.filtered(lambda m: m.role == 'president')
        self.assertEqual(president.user_id, self.user1)
        
        members = self.comite.member_ids.filtered(lambda m: m.role == 'member')
        self.assertEqual(members.user_id, self.user2)
        
        secretary = self.comite.member_ids.filtered(lambda m: m.role == 'secretary')
        self.assertEqual(secretary.user_id, self.user3)

    def test_comite_validation(self):
        """Test de la validation d'un comité de réception"""
        # Valider le comité
        self.comite.action_validate()
        
        # Vérifier l'état du comité
        self.assertEqual(self.comite.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.comite.date_validation)

    def test_comite_activation(self):
        """Test de l'activation d'un comité de réception"""
        # Valider puis activer le comité
        self.comite.action_validate()
        self.comite.action_activate()
        
        # Vérifier l'état du comité
        self.assertEqual(self.comite.state, 'active')
        
        # Vérifier que la date d'activation est définie
        self.assertTrue(self.comite.date_activation)

    def test_comite_deactivation(self):
        """Test de la désactivation d'un comité de réception"""
        # Valider, activer puis désactiver le comité
        self.comite.action_validate()
        self.comite.action_activate()
        self.comite.action_deactivate()
        
        # Vérifier l'état du comité
        self.assertEqual(self.comite.state, 'inactive')
        
        # Vérifier que la date de désactivation est définie
        self.assertTrue(self.comite.date_deactivation)

    def test_comite_cancel(self):
        """Test de l'annulation d'un comité de réception"""
        # Annuler le comité
        self.comite.action_cancel()
        
        # Vérifier l'état du comité
        self.assertEqual(self.comite.state, 'cancel')

    def test_comite_reset(self):
        """Test de la réinitialisation d'un comité de réception"""
        # Valider puis annuler le comité
        self.comite.action_validate()
        self.comite.action_cancel()
        
        # Réinitialiser le comité
        self.comite.action_reset()
        
        # Vérifier l'état du comité
        self.assertEqual(self.comite.state, 'draft')

    def test_comite_constraints(self):
        """Test des contraintes sur les comités de réception"""
        # Test de la contrainte sur l'unicité des rôles
        with self.assertRaises(ValidationError):
            self.comite.member_ids[1].write({'role': 'president'})  # Déjà un président
        
        # Test de la contrainte sur le nombre minimum de membres
        with self.assertRaises(ValidationError):
            self.comite.member_ids = [(5, 0, 0)]  # Supprimer tous les membres
