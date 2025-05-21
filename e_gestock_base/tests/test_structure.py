# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestStructure(TransactionCase):
    """Tests pour le modèle structure du module e_gestock_base"""

    def setUp(self):
        super(TestStructure, self).setUp()
        # Créer des données de test
        self.structure_parent = self.env['e_gestock.structure'].create({
            'nom_structure': 'Structure Parent',
            'code_structure': 'STR01',
        })

        self.structure_enfant = self.env['e_gestock.structure'].create({
            'nom_structure': 'Structure Enfant',
            'code_structure': 'STR02',
            'organisation_id': self.structure_parent.id,
        })

        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Test',
            'login': 'user_test',
            'email': 'user_test@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_user').id)],
        })

        # Associer l'utilisateur à la structure
        self.structure_enfant.write({
            'user_ids': [(4, self.user.id)],
        })

    def test_structure_creation(self):
        """Test de la création d'une structure"""
        self.assertEqual(self.structure_parent.nom_structure, 'Structure Parent')
        self.assertEqual(self.structure_parent.code_structure, 'STR01')
        self.assertFalse(self.structure_parent.organisation_id)

        self.assertEqual(self.structure_enfant.nom_structure, 'Structure Enfant')
        self.assertEqual(self.structure_enfant.code_structure, 'STR02')
        self.assertEqual(self.structure_enfant.organisation_id, self.structure_parent)

    def test_structure_hierarchy(self):
        """Test de la hiérarchie des structures"""
        # Vérifier que la structure parent a bien un enfant
        self.assertIn(self.structure_enfant, self.structure_parent.child_ids)

        # Vérifier que la structure enfant a bien un parent
        self.assertEqual(self.structure_enfant.organisation_id, self.structure_parent)

        # Créer une structure de niveau 3
        structure_niveau3 = self.env['e_gestock.structure'].create({
            'nom_structure': 'Structure Niveau 3',
            'code_structure': 'STR03',
            'organisation_id': self.structure_enfant.id,
        })

        # Vérifier la hiérarchie complète
        self.assertIn(structure_niveau3, self.structure_enfant.child_ids)
        self.assertEqual(structure_niveau3.organisation_id, self.structure_enfant)

    def test_structure_users(self):
        """Test des utilisateurs associés aux structures"""
        # Vérifier que l'utilisateur est bien associé à la structure
        self.assertIn(self.user, self.structure_enfant.user_ids)

        # Vérifier que la structure est bien associée à l'utilisateur
        self.assertIn(self.structure_enfant, self.user.structure_ids)

    def test_structure_constraints(self):
        """Test des contraintes sur les structures"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.structure'].create({
                'nom_structure': 'Structure Test',
                'code_structure': 'STR01',  # Code déjà utilisé
            })

        # Test de la contrainte de hiérarchie circulaire
        with self.assertRaises(Exception):
            self.structure_parent.write({
                'organisation_id': self.structure_enfant.id,
            })
