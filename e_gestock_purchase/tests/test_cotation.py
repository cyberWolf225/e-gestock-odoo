# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestCotation(TransactionCase):
    """Tests pour le modèle cotation du module e_gestock_purchase"""

    def setUp(self):
        super(TestCotation, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Cotation',
            'code': 'STR_COT',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Cotation',
            'code': 'SEC_COT',
            'structure_id': self.structure.id,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Cotation',
            'code': 'FAM_COT',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Cotation',
            'code': 'CAT_COT',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        self.article1 = self.env['e_gestock.article'].create({
            'name': 'Article Test Cotation 1',
            'code': 'ART_COT1',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        self.article2 = self.env['e_gestock.article'].create({
            'name': 'Article Test Cotation 2',
            'code': 'ART_COT2',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test Cotation',
            'login': 'user_test_cotation',
            'email': 'user_test_cotation@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_purchase_manager').id)],
        })
        
        # Créer un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test',
            'email': 'fournisseur@test.com',
            'supplier_rank': 1,
        })
        
        # Créer une demande de cotation
        self.demande_cotation = self.env['e_gestock.demande_cotation'].create({
            'name': 'DC-TEST-001',
            'demandeur_id': self.user.id,
            'section_id': self.section.id,
            'date_demande': '2023-01-01',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': self.article1.id,
                    'quantity': 10.0,
                    'description': 'Description article 1',
                }),
                (0, 0, {
                    'article_id': self.article2.id,
                    'quantity': 5.0,
                    'description': 'Description article 2',
                }),
            ],
        })
        
        # Ajouter le fournisseur à la demande de cotation
        self.fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].create({
            'demande_id': self.demande_cotation.id,
            'partner_id': self.partner.id,
        })
        
        # Valider la demande de cotation
        self.demande_cotation.action_validate()
        
        # Créer une cotation
        self.cotation = self.env['e_gestock.cotation'].create({
            'name': 'COT-TEST-001',
            'demande_id': self.demande_cotation.id,
            'partner_id': self.partner.id,
            'date_cotation': '2023-01-15',
            'state': 'draft',
            'line_ids': [
                (0, 0, {
                    'article_id': self.article1.id,
                    'quantity': 10.0,
                    'price_unit': 100.0,
                    'description': 'Description article 1',
                }),
                (0, 0, {
                    'article_id': self.article2.id,
                    'quantity': 5.0,
                    'price_unit': 200.0,
                    'description': 'Description article 2',
                }),
            ],
        })

    def test_cotation_creation(self):
        """Test de la création d'une cotation"""
        self.assertEqual(self.cotation.name, 'COT-TEST-001')
        self.assertEqual(self.cotation.demande_id, self.demande_cotation)
        self.assertEqual(self.cotation.partner_id, self.partner)
        self.assertEqual(self.cotation.date_cotation, '2023-01-15')
        self.assertEqual(self.cotation.state, 'draft')
        self.assertEqual(len(self.cotation.line_ids), 2)
        
        # Vérifier les lignes de la cotation
        self.assertEqual(self.cotation.line_ids[0].article_id, self.article1)
        self.assertEqual(self.cotation.line_ids[0].quantity, 10.0)
        self.assertEqual(self.cotation.line_ids[0].price_unit, 100.0)
        self.assertEqual(self.cotation.line_ids[0].description, 'Description article 1')
        self.assertEqual(self.cotation.line_ids[1].article_id, self.article2)
        self.assertEqual(self.cotation.line_ids[1].quantity, 5.0)
        self.assertEqual(self.cotation.line_ids[1].price_unit, 200.0)
        self.assertEqual(self.cotation.line_ids[1].description, 'Description article 2')

    def test_cotation_validation(self):
        """Test de la validation d'une cotation"""
        # Valider la cotation
        self.cotation.action_validate()
        
        # Vérifier l'état de la cotation
        self.assertEqual(self.cotation.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.cotation.date_validation)

    def test_cotation_cancel(self):
        """Test de l'annulation d'une cotation"""
        # Annuler la cotation
        self.cotation.action_cancel()
        
        # Vérifier l'état de la cotation
        self.assertEqual(self.cotation.state, 'cancel')

    def test_cotation_reset(self):
        """Test de la réinitialisation d'une cotation"""
        # Valider puis annuler la cotation
        self.cotation.action_validate()
        self.cotation.action_cancel()
        
        # Réinitialiser la cotation
        self.cotation.action_reset()
        
        # Vérifier l'état de la cotation
        self.assertEqual(self.cotation.state, 'draft')

    def test_cotation_amount_total(self):
        """Test du calcul du montant total de la cotation"""
        # Calculer le montant total attendu
        expected_total = 10.0 * 100.0 + 5.0 * 200.0  # 1000 + 1000 = 2000
        
        # Vérifier le montant total calculé
        self.assertEqual(self.cotation.amount_total, expected_total)
