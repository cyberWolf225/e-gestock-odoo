# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestPerdiem(TransactionCase):
    """Tests pour le modèle perdiem du module e_gestock_perdiem"""

    def setUp(self):
        super(TestPerdiem, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Perdiem',
            'code': 'STR_PER',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Perdiem',
            'code': 'SEC_PER',
            'structure_id': self.structure.id,
        })
        
        # Créer des utilisateurs de test
        self.user_requester = self.env['res.users'].create({
            'name': 'Demandeur Perdiem',
            'login': 'demandeur_perdiem',
            'email': 'demandeur_perdiem@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_perdiem_requester').id)],
        })
        
        self.user_validator = self.env['res.users'].create({
            'name': 'Validateur Perdiem',
            'login': 'validateur_perdiem',
            'email': 'validateur_perdiem@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_perdiem_validator').id)],
        })
        
        self.user_manager = self.env['res.users'].create({
            'name': 'Gestionnaire Perdiem',
            'login': 'gestionnaire_perdiem',
            'email': 'gestionnaire_perdiem@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_perdiem_manager').id)],
        })
        
        # Créer des bénéficiaires
        self.beneficiary1 = self.env['e_gestock.perdiem_beneficiary'].create({
            'name': 'Bénéficiaire 1',
            'identification': 'ID001',
            'function': 'Fonction 1',
            'active': True,
        })
        
        self.beneficiary2 = self.env['e_gestock.perdiem_beneficiary'].create({
            'name': 'Bénéficiaire 2',
            'identification': 'ID002',
            'function': 'Fonction 2',
            'active': True,
        })
        
        # Créer un perdiem
        today = datetime.now().date()
        self.perdiem = self.env['e_gestock.perdiem'].create({
            'name': 'Perdiem Test',
            'requester_id': self.user_requester.id,
            'section_id': self.section.id,
            'mission': 'Mission de test',
            'location': 'Lieu de test',
            'date_start': today.strftime('%Y-%m-%d'),
            'date_end': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
            'state': 'draft',
            'beneficiary_ids': [
                (0, 0, {
                    'beneficiary_id': self.beneficiary1.id,
                    'amount_per_day': 50000.0,
                    'days': 5,
                }),
                (0, 0, {
                    'beneficiary_id': self.beneficiary2.id,
                    'amount_per_day': 40000.0,
                    'days': 5,
                }),
            ],
        })

    def test_perdiem_creation(self):
        """Test de la création d'un perdiem"""
        self.assertEqual(self.perdiem.name, 'Perdiem Test')
        self.assertEqual(self.perdiem.requester_id, self.user_requester)
        self.assertEqual(self.perdiem.section_id, self.section)
        self.assertEqual(self.perdiem.mission, 'Mission de test')
        self.assertEqual(self.perdiem.location, 'Lieu de test')
        self.assertEqual(self.perdiem.state, 'draft')
        self.assertEqual(len(self.perdiem.beneficiary_ids), 2)
        
        # Vérifier les bénéficiaires du perdiem
        line1 = self.perdiem.beneficiary_ids.filtered(lambda l: l.beneficiary_id == self.beneficiary1)
        self.assertEqual(line1.amount_per_day, 50000.0)
        self.assertEqual(line1.days, 5)
        self.assertEqual(line1.amount_total, 250000.0)  # 50000 * 5
        
        line2 = self.perdiem.beneficiary_ids.filtered(lambda l: l.beneficiary_id == self.beneficiary2)
        self.assertEqual(line2.amount_per_day, 40000.0)
        self.assertEqual(line2.days, 5)
        self.assertEqual(line2.amount_total, 200000.0)  # 40000 * 5

    def test_perdiem_amount_total(self):
        """Test du calcul du montant total du perdiem"""
        # Calculer le montant total attendu
        expected_total = 250000.0 + 200000.0  # 450000
        
        # Vérifier le montant total calculé
        self.assertEqual(self.perdiem.amount_total, expected_total)

    def test_perdiem_submission(self):
        """Test de la soumission d'un perdiem"""
        # Soumettre le perdiem
        self.perdiem.action_submit()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'submitted')
        
        # Vérifier que la date de soumission est définie
        self.assertTrue(self.perdiem.date_submission)

    def test_perdiem_validation(self):
        """Test de la validation d'un perdiem"""
        # Soumettre puis valider le perdiem
        self.perdiem.action_submit()
        self.perdiem.with_user(self.user_validator).action_validate()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.perdiem.date_validation)
        
        # Vérifier que le validateur est défini
        self.assertEqual(self.perdiem.validator_id, self.user_validator)

    def test_perdiem_approval(self):
        """Test de l'approbation d'un perdiem"""
        # Soumettre, valider puis approuver le perdiem
        self.perdiem.action_submit()
        self.perdiem.with_user(self.user_validator).action_validate()
        self.perdiem.with_user(self.user_manager).action_approve()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'approved')
        
        # Vérifier que la date d'approbation est définie
        self.assertTrue(self.perdiem.date_approval)
        
        # Vérifier que l'approbateur est défini
        self.assertEqual(self.perdiem.approver_id, self.user_manager)

    def test_perdiem_payment(self):
        """Test du paiement d'un perdiem"""
        # Soumettre, valider, approuver puis payer le perdiem
        self.perdiem.action_submit()
        self.perdiem.with_user(self.user_validator).action_validate()
        self.perdiem.with_user(self.user_manager).action_approve()
        self.perdiem.with_user(self.user_manager).action_pay()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'paid')
        
        # Vérifier que la date de paiement est définie
        self.assertTrue(self.perdiem.date_payment)

    def test_perdiem_cancel(self):
        """Test de l'annulation d'un perdiem"""
        # Annuler le perdiem
        self.perdiem.action_cancel()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'cancel')

    def test_perdiem_reset(self):
        """Test de la réinitialisation d'un perdiem"""
        # Soumettre puis annuler le perdiem
        self.perdiem.action_submit()
        self.perdiem.action_cancel()
        
        # Réinitialiser le perdiem
        self.perdiem.action_reset()
        
        # Vérifier l'état du perdiem
        self.assertEqual(self.perdiem.state, 'draft')
