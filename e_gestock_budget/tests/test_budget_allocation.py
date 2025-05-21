# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestBudgetAllocation(TransactionCase):
    """Tests pour le modèle budget_allocation du module e_gestock_budget"""

    def setUp(self):
        super(TestBudgetAllocation, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Allocation',
            'code': 'STR_ALLOC',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Allocation',
            'code': 'SEC_ALLOC',
            'structure_id': self.structure.id,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Allocation',
            'code': 'FAM_ALLOC',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Allocation',
            'code': 'CAT_ALLOC',
            'famille_id': self.famille.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Allocation',
            'login': 'user_test_allocation',
            'email': 'user_test_allocation@example.com',
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
            'name': 'Budget Test Allocation',
            'code': 'BUD003',
            'fiscal_year_id': self.fiscal_year.id,
            'structure_id': self.structure.id,
            'date_start': f'{current_year}-01-01',
            'date_end': f'{current_year}-12-31',
            'amount_total': 1000000.0,
            'state': 'approved',  # Budget approuvé
        })
        
        # Créer une ligne de budget
        self.budget_line = self.env['e_gestock.budget_line'].create({
            'budget_id': self.budget.id,
            'name': 'Ligne Budget Allocation',
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'amount_allocated': 500000.0,
        })
        
        # Créer une allocation budgétaire
        self.allocation = self.env['e_gestock.budget_allocation'].create({
            'name': 'Allocation Test',
            'budget_line_id': self.budget_line.id,
            'date_allocation': datetime.now().strftime('%Y-%m-%d'),
            'amount': 100000.0,
            'description': 'Allocation de test',
            'state': 'draft',
        })

    def test_allocation_creation(self):
        """Test de la création d'une allocation budgétaire"""
        self.assertEqual(self.allocation.name, 'Allocation Test')
        self.assertEqual(self.allocation.budget_line_id, self.budget_line)
        self.assertEqual(self.allocation.amount, 100000.0)
        self.assertEqual(self.allocation.description, 'Allocation de test')
        self.assertEqual(self.allocation.state, 'draft')

    def test_allocation_validation(self):
        """Test de la validation d'une allocation budgétaire"""
        # Valider l'allocation
        self.allocation.action_validate()
        
        # Vérifier l'état de l'allocation
        self.assertEqual(self.allocation.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.allocation.date_validation)
        
        # Vérifier que le montant engagé de la ligne de budget est mis à jour
        self.assertEqual(self.budget_line.amount_engaged, 100000.0)
        
        # Vérifier que le montant disponible de la ligne de budget est mis à jour
        self.assertEqual(self.budget_line.amount_available, 400000.0)  # 500000 - 100000

    def test_allocation_cancel(self):
        """Test de l'annulation d'une allocation budgétaire"""
        # Valider puis annuler l'allocation
        self.allocation.action_validate()
        self.allocation.action_cancel()
        
        # Vérifier l'état de l'allocation
        self.assertEqual(self.allocation.state, 'cancel')
        
        # Vérifier que le montant engagé de la ligne de budget est mis à jour
        self.assertEqual(self.budget_line.amount_engaged, 0.0)
        
        # Vérifier que le montant disponible de la ligne de budget est mis à jour
        self.assertEqual(self.budget_line.amount_available, 500000.0)  # Retour à 500000

    def test_allocation_reset(self):
        """Test de la réinitialisation d'une allocation budgétaire"""
        # Valider puis annuler l'allocation
        self.allocation.action_validate()
        self.allocation.action_cancel()
        
        # Réinitialiser l'allocation
        self.allocation.action_reset()
        
        # Vérifier l'état de l'allocation
        self.assertEqual(self.allocation.state, 'draft')

    def test_allocation_constraints(self):
        """Test des contraintes sur les allocations budgétaires"""
        # Test de la contrainte sur le montant
        with self.assertRaises(ValidationError):
            self.allocation.write({'amount': -100.0})
        
        # Test de la contrainte sur le montant disponible
        with self.assertRaises(ValidationError):
            self.env['e_gestock.budget_allocation'].create({
                'name': 'Allocation Excessive',
                'budget_line_id': self.budget_line.id,
                'date_allocation': datetime.now().strftime('%Y-%m-%d'),
                'amount': 600000.0,  # Supérieur au montant disponible (500000)
                'description': 'Allocation excessive',
                'state': 'draft',
            })
