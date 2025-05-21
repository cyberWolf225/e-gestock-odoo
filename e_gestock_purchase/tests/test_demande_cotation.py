# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('post_install', '-at_install')
class TestDemandeCotation(TransactionCase):
    """Tests pour le modèle demande_cotation du module e_gestock_purchase"""

    def setUp(self):
        super(TestDemandeCotation, self).setUp()
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
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_purchase_user').id)],
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

    def test_demande_cotation_creation(self):
        """Test de la création d'une demande de cotation"""
        self.assertEqual(self.demande_cotation.name, 'DC-TEST-001')
        self.assertEqual(self.demande_cotation.demandeur_id, self.user)
        self.assertEqual(self.demande_cotation.section_id, self.section)
        self.assertEqual(self.demande_cotation.date_demande, '2023-01-01')
        self.assertEqual(self.demande_cotation.state, 'draft')
        self.assertEqual(len(self.demande_cotation.line_ids), 2)
        
        # Vérifier les lignes de la demande de cotation
        self.assertEqual(self.demande_cotation.line_ids[0].article_id, self.article1)
        self.assertEqual(self.demande_cotation.line_ids[0].quantity, 10.0)
        self.assertEqual(self.demande_cotation.line_ids[0].description, 'Description article 1')
        self.assertEqual(self.demande_cotation.line_ids[1].article_id, self.article2)
        self.assertEqual(self.demande_cotation.line_ids[1].quantity, 5.0)
        self.assertEqual(self.demande_cotation.line_ids[1].description, 'Description article 2')

    def test_demande_cotation_validation(self):
        """Test de la validation d'une demande de cotation"""
        # Valider la demande de cotation
        self.demande_cotation.action_validate()
        
        # Vérifier l'état de la demande de cotation
        self.assertEqual(self.demande_cotation.state, 'validated')
        
        # Vérifier que la date de validation est définie
        self.assertTrue(self.demande_cotation.date_validation)

    def test_demande_cotation_cancel(self):
        """Test de l'annulation d'une demande de cotation"""
        # Annuler la demande de cotation
        self.demande_cotation.action_cancel()
        
        # Vérifier l'état de la demande de cotation
        self.assertEqual(self.demande_cotation.state, 'cancel')

    def test_demande_cotation_reset(self):
        """Test de la réinitialisation d'une demande de cotation"""
        # Valider puis annuler la demande de cotation
        self.demande_cotation.action_validate()
        self.demande_cotation.action_cancel()
        
        # Réinitialiser la demande de cotation
        self.demande_cotation.action_reset()
        
        # Vérifier l'état de la demande de cotation
        self.assertEqual(self.demande_cotation.state, 'draft')

    def test_demande_cotation_add_fournisseur(self):
        """Test de l'ajout d'un fournisseur à une demande de cotation"""
        # Créer un fournisseur
        partner = self.env['res.partner'].create({
            'name': 'Fournisseur Test',
            'email': 'fournisseur@test.com',
            'supplier_rank': 1,
        })
        
        # Ajouter le fournisseur à la demande de cotation
        fournisseur = self.env['e_gestock.demande_cotation_fournisseur'].create({
            'demande_id': self.demande_cotation.id,
            'partner_id': partner.id,
        })
        
        # Vérifier que le fournisseur est bien ajouté
        self.assertIn(fournisseur, self.demande_cotation.fournisseur_ids)
        self.assertEqual(fournisseur.partner_id, partner)
