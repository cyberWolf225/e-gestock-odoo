# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestAsset(TransactionCase):
    """Tests pour le modèle asset du module e_gestock_asset"""

    def setUp(self):
        super(TestAsset, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Asset',
            'code': 'STR_AST',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Asset',
            'code': 'SEC_AST',
            'structure_id': self.structure.id,
        })
        
        # Créer une catégorie d'actif
        self.category = self.env['e_gestock.asset_category'].create({
            'name': 'Catégorie Asset Test',
            'code': 'CAT_AST',
            'depreciation_method': 'linear',
            'depreciation_rate': 20.0,  # 5 ans
            'active': True,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Asset',
            'login': 'user_test_asset',
            'email': 'user_test_asset@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_asset_manager').id)],
        })
        
        # Créer un actif
        self.asset = self.env['e_gestock.asset'].create({
            'name': 'Asset Test',
            'code': 'AST001',
            'category_id': self.category.id,
            'acquisition_date': datetime.now().strftime('%Y-%m-%d'),
            'acquisition_value': 1000000.0,
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'state': 'draft',
            'user_id': self.user.id,
        })

    def test_asset_creation(self):
        """Test de la création d'un actif"""
        self.assertEqual(self.asset.name, 'Asset Test')
        self.assertEqual(self.asset.code, 'AST001')
        self.assertEqual(self.asset.category_id, self.category)
        self.assertEqual(self.asset.acquisition_value, 1000000.0)
        self.assertEqual(self.asset.structure_id, self.structure)
        self.assertEqual(self.asset.section_id, self.section)
        self.assertEqual(self.asset.state, 'draft')
        self.assertEqual(self.asset.user_id, self.user)

    def test_asset_validation(self):
        """Test de la validation d'un actif"""
        # Valider l'actif
        self.asset.action_validate()
        
        # Vérifier l'état de l'actif
        self.assertEqual(self.asset.state, 'in_use')
        
        # Vérifier que la date de mise en service est définie
        self.assertTrue(self.asset.in_use_date)

    def test_asset_depreciation(self):
        """Test du calcul de l'amortissement d'un actif"""
        # Valider l'actif
        self.asset.action_validate()
        
        # Calculer l'amortissement annuel attendu
        expected_annual_depreciation = 1000000.0 * 0.2  # 200000
        
        # Vérifier l'amortissement annuel calculé
        self.assertEqual(self.asset.annual_depreciation, expected_annual_depreciation)
        
        # Calculer l'amortissement cumulé attendu (0 car l'actif vient d'être mis en service)
        expected_accumulated_depreciation = 0.0
        
        # Vérifier l'amortissement cumulé calculé
        self.assertEqual(self.asset.accumulated_depreciation, expected_accumulated_depreciation)
        
        # Calculer la valeur nette comptable attendue
        expected_net_value = 1000000.0 - 0.0  # 1000000
        
        # Vérifier la valeur nette comptable calculée
        self.assertEqual(self.asset.net_value, expected_net_value)

    def test_asset_disposal(self):
        """Test de la mise au rebut d'un actif"""
        # Valider puis mettre au rebut l'actif
        self.asset.action_validate()
        self.asset.action_dispose()
        
        # Vérifier l'état de l'actif
        self.assertEqual(self.asset.state, 'disposed')
        
        # Vérifier que la date de mise au rebut est définie
        self.assertTrue(self.asset.disposal_date)

    def test_asset_cancel(self):
        """Test de l'annulation d'un actif"""
        # Annuler l'actif
        self.asset.action_cancel()
        
        # Vérifier l'état de l'actif
        self.assertEqual(self.asset.state, 'cancel')

    def test_asset_reset(self):
        """Test de la réinitialisation d'un actif"""
        # Valider puis annuler l'actif
        self.asset.action_validate()
        self.asset.action_cancel()
        
        # Réinitialiser l'actif
        self.asset.action_reset()
        
        # Vérifier l'état de l'actif
        self.assertEqual(self.asset.state, 'draft')

    def test_asset_constraints(self):
        """Test des contraintes sur les actifs"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.asset'].create({
                'name': 'Asset Test Dupliqué',
                'code': 'AST001',  # Code déjà utilisé
                'category_id': self.category.id,
                'acquisition_date': datetime.now().strftime('%Y-%m-%d'),
                'acquisition_value': 500000.0,
                'structure_id': self.structure.id,
                'section_id': self.section.id,
                'state': 'draft',
                'user_id': self.user.id,
            })
        
        # Test de la contrainte sur la valeur d'acquisition
        with self.assertRaises(ValidationError):
            self.asset.write({'acquisition_value': -100.0})
