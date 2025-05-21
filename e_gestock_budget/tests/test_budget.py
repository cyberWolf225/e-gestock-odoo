# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestBudget(TransactionCase):
    """Tests pour le modèle budget du module e_gestock_budget"""

    def setUp(self):
        super(TestBudget, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Budget',
            'code': 'STR_BUD',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Budget',
            'code': 'SEC_BUD',
            'structure_id': self.structure.id,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Budget',
            'code': 'FAM_BUD',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Budget',
            'code': 'CAT_BUD',
            'famille_id': self.famille.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Budget',
            'login': 'user_test_budget',
            'email': 'user_test_budget@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_budget_manager').id)],
        })
        
        # Créer un exercice fiscal
        current_year = datetime.now().year
        self.fiscal_year = self.env['e_gestock.fiscal_year'].create({
            'name': f'Exercice {current_year}',
            'code': f'EX{current_year}',
            'date_start': f'{current_year}-01-01',
            'date_end': f'{current_year}-12-31',
            'state': 'open',
        })
        
        # Créer un budget
        self.budget = self.env['e_gestock.budget'].create({
            'name': 'Budget Test',
            'code': 'BUD001',
            'fiscal_year_id': self.fiscal_year.id,
            'structure_id': self.structure.id,
            'date_start': f'{current_year}-01-01',
            'date_end': f'{current_year}-12-31',
            'amount_total': 1000000.0,
            'state': 'draft',
        })
        
        # Créer des lignes de budget
        self.budget_line1 = self.env['e_gestock.budget_line'].create({
            'budget_id': self.budget.id,
            'name': 'Ligne Budget 1',
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'amount_allocated': 500000.0,
        })
        
        self.budget_line2 = self.env['e_gestock.budget_line'].create({
            'budget_id': self.budget.id,
            'name': 'Ligne Budget 2',
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'amount_allocated': 500000.0,
        })

    def test_budget_creation(self):
        """Test de la création d'un budget"""
        self.assertEqual(self.budget.name, 'Budget Test')
        self.assertEqual(self.budget.code, 'BUD001')
        self.assertEqual(self.budget.fiscal_year_id, self.fiscal_year)
        self.assertEqual(self.budget.structure_id, self.structure)
        self.assertEqual(self.budget.amount_total, 1000000.0)
        self.assertEqual(self.budget.state, 'draft')
        self.assertEqual(len(self.budget.line_ids), 2)
        
        # Vérifier les lignes du budget
        self.assertEqual(self.budget.line_ids[0].name, 'Ligne Budget 1')
        self.assertEqual(self.budget.line_ids[0].section_id, self.section)
        self.assertEqual(self.budget.line_ids[0].famille_id, self.famille)
        self.assertEqual(self.budget.line_ids[0].amount_allocated, 500000.0)
        self.assertEqual(self.budget.line_ids[1].name, 'Ligne Budget 2')
        self.assertEqual(self.budget.line_ids[1].section_id, self.section)
        self.assertEqual(self.budget.line_ids[1].famille_id, self.famille)
        self.assertEqual(self.budget.line_ids[1].amount_allocated, 500000.0)

    def test_budget_validation(self):
        """Test de la validation d'un budget"""
        # Valider le budget
        self.budget.action_validate()
        
        # Vérifier l'état du budget
        self.assertEqual(self.budget.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.budget.date_validation)

    def test_budget_approval(self):
        """Test de l'approbation d'un budget"""
        # Valider puis approuver le budget
        self.budget.action_validate()
        self.budget.action_approve()
        
        # Vérifier l'état du budget
        self.assertEqual(self.budget.state, 'approved')
        
        # Vérifier que la date d'approbation est définie
        self.assertTrue(self.budget.date_approval)

    def test_budget_cancel(self):
        """Test de l'annulation d'un budget"""
        # Annuler le budget
        self.budget.action_cancel()
        
        # Vérifier l'état du budget
        self.assertEqual(self.budget.state, 'cancel')

    def test_budget_reset(self):
        """Test de la réinitialisation d'un budget"""
        # Valider puis annuler le budget
        self.budget.action_validate()
        self.budget.action_cancel()
        
        # Réinitialiser le budget
        self.budget.action_reset()
        
        # Vérifier l'état du budget
        self.assertEqual(self.budget.state, 'draft')

    def test_budget_amount_allocated(self):
        """Test du calcul du montant alloué du budget"""
        # Calculer le montant alloué attendu
        expected_allocated = 500000.0 + 500000.0  # 1000000
        
        # Vérifier le montant alloué calculé
        self.assertEqual(self.budget.amount_allocated, expected_allocated)

    def test_budget_amount_available(self):
        """Test du calcul du montant disponible du budget"""
        # Calculer le montant disponible attendu
        expected_available = 1000000.0 - 0.0  # 1000000 - 0 (pas d'engagement)
        
        # Vérifier le montant disponible calculé
        self.assertEqual(self.budget.amount_available, expected_available)
