# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestPerdiemBeneficiary(TransactionCase):
    """Tests pour le modèle perdiem_beneficiary du module e_gestock_perdiem"""

    def setUp(self):
        super(TestPerdiemBeneficiary, self).setUp()
        # Créer des bénéficiaires
        self.beneficiary1 = self.env['e_gestock.perdiem_beneficiary'].create({
            'name': 'Bénéficiaire Test 1',
            'identification': 'ID001',
            'function': 'Fonction Test 1',
            'active': True,
        })
        
        self.beneficiary2 = self.env['e_gestock.perdiem_beneficiary'].create({
            'name': 'Bénéficiaire Test 2',
            'identification': 'ID002',
            'function': 'Fonction Test 2',
            'active': True,
        })
        
        self.beneficiary3 = self.env['e_gestock.perdiem_beneficiary'].create({
            'name': 'Bénéficiaire Test 3',
            'identification': 'ID003',
            'function': 'Fonction Test 3',
            'active': False,  # Bénéficiaire inactif
        })

    def test_beneficiary_creation(self):
        """Test de la création d'un bénéficiaire"""
        self.assertEqual(self.beneficiary1.name, 'Bénéficiaire Test 1')
        self.assertEqual(self.beneficiary1.identification, 'ID001')
        self.assertEqual(self.beneficiary1.function, 'Fonction Test 1')
        self.assertTrue(self.beneficiary1.active)
        
        self.assertEqual(self.beneficiary2.name, 'Bénéficiaire Test 2')
        self.assertEqual(self.beneficiary2.identification, 'ID002')
        self.assertEqual(self.beneficiary2.function, 'Fonction Test 2')
        self.assertTrue(self.beneficiary2.active)
        
        self.assertEqual(self.beneficiary3.name, 'Bénéficiaire Test 3')
        self.assertEqual(self.beneficiary3.identification, 'ID003')
        self.assertEqual(self.beneficiary3.function, 'Fonction Test 3')
        self.assertFalse(self.beneficiary3.active)

    def test_beneficiary_search(self):
        """Test de la recherche de bénéficiaires"""
        # Recherche par nom
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].search([('name', 'ilike', 'Bénéficiaire')])
        self.assertEqual(len(beneficiaries), 2)  # Seulement les bénéficiaires actifs
        self.assertIn(self.beneficiary1, beneficiaries)
        self.assertIn(self.beneficiary2, beneficiaries)
        self.assertNotIn(self.beneficiary3, beneficiaries)
        
        # Recherche par identification
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].search([('identification', '=', 'ID001')])
        self.assertEqual(len(beneficiaries), 1)
        self.assertEqual(beneficiaries[0], self.beneficiary1)
        
        # Recherche incluant les archives
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].with_context(active_test=False).search([])
        self.assertEqual(len(beneficiaries), 3)
        self.assertIn(self.beneficiary1, beneficiaries)
        self.assertIn(self.beneficiary2, beneficiaries)
        self.assertIn(self.beneficiary3, beneficiaries)

    def test_beneficiary_archive(self):
        """Test de l'archivage d'un bénéficiaire"""
        # Archiver un bénéficiaire
        self.beneficiary1.write({'active': False})
        self.assertFalse(self.beneficiary1.active)
        
        # Vérifier que le bénéficiaire n'apparaît plus dans les recherches par défaut
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].search([])
        self.assertNotIn(self.beneficiary1, beneficiaries)
        self.assertIn(self.beneficiary2, beneficiaries)
        
        # Réactiver le bénéficiaire
        self.beneficiary1.write({'active': True})
        self.assertTrue(self.beneficiary1.active)
        
        # Vérifier que le bénéficiaire apparaît à nouveau dans les recherches par défaut
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].search([])
        self.assertIn(self.beneficiary1, beneficiaries)
        self.assertIn(self.beneficiary2, beneficiaries)

    def test_beneficiary_constraints(self):
        """Test des contraintes sur les bénéficiaires"""
        # Test de l'unicité de l'identification
        with self.assertRaises(Exception):
            self.env['e_gestock.perdiem_beneficiary'].create({
                'name': 'Bénéficiaire Dupliqué',
                'identification': 'ID001',  # Identification déjà utilisée
                'function': 'Fonction Dupliquée',
                'active': True,
            })

    def test_beneficiary_name_search(self):
        """Test de la recherche par nom des bénéficiaires"""
        # Recherche par nom
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].name_search('Bénéficiaire')
        self.assertEqual(len(beneficiaries), 2)  # Seulement les bénéficiaires actifs
        
        # Recherche par identification
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].name_search('ID001')
        self.assertEqual(len(beneficiaries), 1)
        self.assertEqual(beneficiaries[0][0], self.beneficiary1.id)
        
        # Recherche par fonction
        beneficiaries = self.env['e_gestock.perdiem_beneficiary'].name_search('Fonction Test 2')
        self.assertEqual(len(beneficiaries), 1)
        self.assertEqual(beneficiaries[0][0], self.beneficiary2.id)
