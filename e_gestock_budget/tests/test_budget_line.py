# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestBudgetLine(TransactionCase):
    """Tests pour le modèle budget_line du module e_gestock_budget"""

    def setUp(self):
        super(TestBudgetLine, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Budget Line',
            'code': 'STR_BL',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Budget Line',
            'code': 'SEC_BL',
            'structure_id': self.structure.id,
        })
        
        self.famille1 = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Budget Line 1',
            'code': 'FAM_BL1',
        })
        
        self.famille2 = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Budget Line 2',
            'code': 'FAM_BL2',
        })
        
        self.categorie1 = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Budget Line 1',
            'code': 'CAT_BL1',
            'famille_id': self.famille1.id,
        })
        
        self.categorie2 = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Budget Line 2',
            'code': 'CAT_BL2',
            'famille_id': self.famille2.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Budget Line',
            'login': 'user_test_budget_line',
            'email': 'user_test_budget_line@example.com',
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
            'name': 'Budget Test Line',
            'code': 'BUD002',
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
            'famille_id': self.famille1.id,
            'amount_allocated': 600000.0,
        })
        
        self.budget_line2 = self.env['e_gestock.budget_line'].create({
            'budget_id': self.budget.id,
            'name': 'Ligne Budget 2',
            'section_id': self.section.id,
            'famille_id': self.famille2.id,
            'amount_allocated': 400000.0,
        })

    def test_budget_line_creation(self):
        """Test de la création d'une ligne de budget"""
        self.assertEqual(self.budget_line1.name, 'Ligne Budget 1')
        self.assertEqual(self.budget_line1.budget_id, self.budget)
        self.assertEqual(self.budget_line1.section_id, self.section)
        self.assertEqual(self.budget_line1.famille_id, self.famille1)
        self.assertEqual(self.budget_line1.amount_allocated, 600000.0)
        
        self.assertEqual(self.budget_line2.name, 'Ligne Budget 2')
        self.assertEqual(self.budget_line2.budget_id, self.budget)
        self.assertEqual(self.budget_line2.section_id, self.section)
        self.assertEqual(self.budget_line2.famille_id, self.famille2)
        self.assertEqual(self.budget_line2.amount_allocated, 400000.0)

    def test_budget_line_amount_engaged(self):
        """Test du calcul du montant engagé d'une ligne de budget"""
        # Par défaut, le montant engagé est 0
        self.assertEqual(self.budget_line1.amount_engaged, 0.0)
        self.assertEqual(self.budget_line2.amount_engaged, 0.0)
        
        # Créer un engagement de budget
        engagement = self.env['e_gestock.budget_engagement'].create({
            'name': 'Engagement Test',
            'budget_line_id': self.budget_line1.id,
            'amount': 100000.0,
            'date_engagement': datetime.now().strftime('%Y-%m-%d'),
            'state': 'validated',
        })
        
        # Vérifier que le montant engagé est mis à jour
        self.assertEqual(self.budget_line1.amount_engaged, 100000.0)
        self.assertEqual(self.budget_line2.amount_engaged, 0.0)

    def test_budget_line_amount_available(self):
        """Test du calcul du montant disponible d'une ligne de budget"""
        # Par défaut, le montant disponible est égal au montant alloué
        self.assertEqual(self.budget_line1.amount_available, 600000.0)
        self.assertEqual(self.budget_line2.amount_available, 400000.0)
        
        # Créer un engagement de budget
        engagement = self.env['e_gestock.budget_engagement'].create({
            'name': 'Engagement Test',
            'budget_line_id': self.budget_line1.id,
            'amount': 100000.0,
            'date_engagement': datetime.now().strftime('%Y-%m-%d'),
            'state': 'validated',
        })
        
        # Vérifier que le montant disponible est mis à jour
        self.assertEqual(self.budget_line1.amount_available, 500000.0)  # 600000 - 100000
        self.assertEqual(self.budget_line2.amount_available, 400000.0)

    def test_budget_line_constraints(self):
        """Test des contraintes sur les lignes de budget"""
        # Test de la contrainte sur le montant alloué
        with self.assertRaises(ValidationError):
            self.budget_line1.write({'amount_allocated': -100.0})
        
        # Test de la contrainte sur l'unicité de la famille par section dans un budget
        with self.assertRaises(ValidationError):
            self.env['e_gestock.budget_line'].create({
                'budget_id': self.budget.id,
                'name': 'Ligne Budget Dupliquée',
                'section_id': self.section.id,
                'famille_id': self.famille1.id,  # Même famille que budget_line1
                'amount_allocated': 100000.0,
            })
