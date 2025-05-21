# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestAssetMaintenance(TransactionCase):
    """Tests pour le modèle asset_maintenance du module e_gestock_asset"""

    def setUp(self):
        super(TestAssetMaintenance, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Maintenance',
            'code': 'STR_MAINT',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Maintenance',
            'code': 'SEC_MAINT',
            'structure_id': self.structure.id,
        })
        
        # Créer une catégorie d'actif
        self.category = self.env['e_gestock.asset_category'].create({
            'name': 'Catégorie Asset Maintenance',
            'code': 'CAT_MAINT',
            'depreciation_method': 'linear',
            'depreciation_rate': 20.0,  # 5 ans
            'active': True,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Maintenance',
            'login': 'user_test_maintenance',
            'email': 'user_test_maintenance@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_asset_maintenance').id)],
        })
        
        # Créer un actif
        self.asset = self.env['e_gestock.asset'].create({
            'name': 'Asset Test Maintenance',
            'code': 'AST_MAINT',
            'category_id': self.category.id,
            'acquisition_date': datetime.now().strftime('%Y-%m-%d'),
            'acquisition_value': 1000000.0,
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'state': 'in_use',  # Actif en service
            'user_id': self.user.id,
        })
        
        # Créer une maintenance
        self.maintenance = self.env['e_gestock.asset_maintenance'].create({
            'name': 'Maintenance Test',
            'asset_id': self.asset.id,
            'date_request': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Description de la maintenance',
            'maintenance_type': 'corrective',
            'state': 'draft',
            'user_id': self.user.id,
        })

    def test_maintenance_creation(self):
        """Test de la création d'une maintenance"""
        self.assertEqual(self.maintenance.name, 'Maintenance Test')
        self.assertEqual(self.maintenance.asset_id, self.asset)
        self.assertEqual(self.maintenance.description, 'Description de la maintenance')
        self.assertEqual(self.maintenance.maintenance_type, 'corrective')
        self.assertEqual(self.maintenance.state, 'draft')
        self.assertEqual(self.maintenance.user_id, self.user)

    def test_maintenance_validation(self):
        """Test de la validation d'une maintenance"""
        # Valider la maintenance
        self.maintenance.action_validate()
        
        # Vérifier l'état de la maintenance
        self.assertEqual(self.maintenance.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.maintenance.date_validation)

    def test_maintenance_start(self):
        """Test du démarrage d'une maintenance"""
        # Valider puis démarrer la maintenance
        self.maintenance.action_validate()
        self.maintenance.action_start()
        
        # Vérifier l'état de la maintenance
        self.assertEqual(self.maintenance.state, 'in_progress')
        
        # Vérifier que la date de début est définie
        self.assertTrue(self.maintenance.date_start)
        
        # Vérifier que l'actif est en maintenance
        self.assertEqual(self.asset.state, 'maintenance')

    def test_maintenance_complete(self):
        """Test de la finalisation d'une maintenance"""
        # Valider, démarrer puis finaliser la maintenance
        self.maintenance.action_validate()
        self.maintenance.action_start()
        self.maintenance.action_complete()
        
        # Vérifier l'état de la maintenance
        self.assertEqual(self.maintenance.state, 'done')
        
        # Vérifier que la date de fin est définie
        self.assertTrue(self.maintenance.date_end)
        
        # Vérifier que l'actif est de nouveau en service
        self.assertEqual(self.asset.state, 'in_use')

    def test_maintenance_cancel(self):
        """Test de l'annulation d'une maintenance"""
        # Valider, démarrer puis annuler la maintenance
        self.maintenance.action_validate()
        self.maintenance.action_start()
        self.maintenance.action_cancel()
        
        # Vérifier l'état de la maintenance
        self.assertEqual(self.maintenance.state, 'cancel')
        
        # Vérifier que l'actif est de nouveau en service
        self.assertEqual(self.asset.state, 'in_use')

    def test_maintenance_reset(self):
        """Test de la réinitialisation d'une maintenance"""
        # Valider puis annuler la maintenance
        self.maintenance.action_validate()
        self.maintenance.action_cancel()
        
        # Réinitialiser la maintenance
        self.maintenance.action_reset()
        
        # Vérifier l'état de la maintenance
        self.assertEqual(self.maintenance.state, 'draft')

    def test_maintenance_constraints(self):
        """Test des contraintes sur les maintenances"""
        # Test de la contrainte sur la date de fin
        with self.assertRaises(ValidationError):
            self.maintenance.write({
                'date_end': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                'date_start': datetime.now().strftime('%Y-%m-%d'),
            })
        
        # Test de la contrainte sur l'actif en maintenance
        maintenance2 = self.env['e_gestock.asset_maintenance'].create({
            'name': 'Maintenance Test 2',
            'asset_id': self.asset.id,
            'date_request': datetime.now().strftime('%Y-%m-%d'),
            'description': 'Description de la maintenance 2',
            'maintenance_type': 'preventive',
            'state': 'draft',
            'user_id': self.user.id,
        })
        
        # Valider et démarrer la première maintenance
        self.maintenance.action_validate()
        self.maintenance.action_start()
        
        # Essayer de démarrer la deuxième maintenance (devrait échouer)
        maintenance2.action_validate()
        with self.assertRaises(ValidationError):
            maintenance2.action_start()
