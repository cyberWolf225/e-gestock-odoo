# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime

@tagged('post_install', '-at_install')
class TestSupplierEvaluation(TransactionCase):
    """Tests pour le modèle supplier_evaluation du module e_gestock_supplier"""

    def setUp(self):
        super(TestSupplierEvaluation, self).setUp()
        # Créer des données de test
        self.category = self.env['e_gestock.supplier_category'].create({
            'name': 'Catégorie Fournisseur Évaluation',
            'code': 'CAT_FOUR_EVAL',
            'description': 'Description catégorie évaluation',
            'active': True,
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test Évaluation',
            'email': 'fournisseur_evaluation@test.com',
            'supplier_rank': 1,
            'supplier_category_id': self.category.id,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Évaluation',
            'login': 'user_test_evaluation',
            'email': 'user_test_evaluation@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_supplier_manager').id)],
        })
        
        # Créer des critères d'évaluation
        self.criterion1 = self.env['e_gestock.evaluation_criterion'].create({
            'name': 'Qualité des produits',
            'description': 'Évaluation de la qualité des produits',
            'weight': 40.0,
            'active': True,
        })
        
        self.criterion2 = self.env['e_gestock.evaluation_criterion'].create({
            'name': 'Respect des délais',
            'description': 'Évaluation du respect des délais de livraison',
            'weight': 30.0,
            'active': True,
        })
        
        self.criterion3 = self.env['e_gestock.evaluation_criterion'].create({
            'name': 'Service client',
            'description': 'Évaluation du service client',
            'weight': 30.0,
            'active': True,
        })
        
        # Créer une évaluation de fournisseur
        self.evaluation = self.env['e_gestock.supplier_evaluation'].create({
            'name': 'Évaluation Test',
            'partner_id': self.partner.id,
            'user_id': self.user.id,
            'date_evaluation': datetime.now().strftime('%Y-%m-%d'),
            'state': 'draft',
            'note': 'Note d\'évaluation',
            'line_ids': [
                (0, 0, {
                    'criterion_id': self.criterion1.id,
                    'score': 8.0,
                    'comment': 'Bonne qualité des produits',
                }),
                (0, 0, {
                    'criterion_id': self.criterion2.id,
                    'score': 7.0,
                    'comment': 'Délais généralement respectés',
                }),
                (0, 0, {
                    'criterion_id': self.criterion3.id,
                    'score': 9.0,
                    'comment': 'Excellent service client',
                }),
            ],
        })

    def test_evaluation_creation(self):
        """Test de la création d'une évaluation de fournisseur"""
        self.assertEqual(self.evaluation.name, 'Évaluation Test')
        self.assertEqual(self.evaluation.partner_id, self.partner)
        self.assertEqual(self.evaluation.user_id, self.user)
        self.assertEqual(self.evaluation.state, 'draft')
        self.assertEqual(self.evaluation.note, 'Note d\'évaluation')
        self.assertEqual(len(self.evaluation.line_ids), 3)
        
        # Vérifier les lignes d'évaluation
        line1 = self.evaluation.line_ids.filtered(lambda l: l.criterion_id == self.criterion1)
        self.assertEqual(line1.score, 8.0)
        self.assertEqual(line1.comment, 'Bonne qualité des produits')
        
        line2 = self.evaluation.line_ids.filtered(lambda l: l.criterion_id == self.criterion2)
        self.assertEqual(line2.score, 7.0)
        self.assertEqual(line2.comment, 'Délais généralement respectés')
        
        line3 = self.evaluation.line_ids.filtered(lambda l: l.criterion_id == self.criterion3)
        self.assertEqual(line3.score, 9.0)
        self.assertEqual(line3.comment, 'Excellent service client')

    def test_evaluation_validation(self):
        """Test de la validation d'une évaluation de fournisseur"""
        # Valider l'évaluation
        self.evaluation.action_validate()
        
        # Vérifier l'état de l'évaluation
        self.assertEqual(self.evaluation.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.evaluation.date_validation)

    def test_evaluation_cancel(self):
        """Test de l'annulation d'une évaluation de fournisseur"""
        # Annuler l'évaluation
        self.evaluation.action_cancel()
        
        # Vérifier l'état de l'évaluation
        self.assertEqual(self.evaluation.state, 'cancel')

    def test_evaluation_reset(self):
        """Test de la réinitialisation d'une évaluation de fournisseur"""
        # Valider puis annuler l'évaluation
        self.evaluation.action_validate()
        self.evaluation.action_cancel()
        
        # Réinitialiser l'évaluation
        self.evaluation.action_reset()
        
        # Vérifier l'état de l'évaluation
        self.assertEqual(self.evaluation.state, 'draft')

    def test_evaluation_score_calculation(self):
        """Test du calcul du score global d'une évaluation de fournisseur"""
        # Calculer le score global attendu
        expected_score = (8.0 * 40.0 + 7.0 * 30.0 + 9.0 * 30.0) / 100.0  # (8*0.4 + 7*0.3 + 9*0.3) = 8.0
        
        # Vérifier le score global calculé
        self.assertEqual(self.evaluation.global_score, expected_score)

    def test_evaluation_constraints(self):
        """Test des contraintes sur les évaluations de fournisseur"""
        # Test de la contrainte sur les scores
        with self.assertRaises(ValidationError):
            self.evaluation.line_ids[0].write({'score': 11.0})  # Score > 10
        
        with self.assertRaises(ValidationError):
            self.evaluation.line_ids[0].write({'score': -1.0})  # Score < 0
