# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestSection(TransactionCase):
    """Tests pour le modèle section du module e_gestock_base"""

    def setUp(self):
        super(TestSection, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'nom_structure': 'Structure Test',
            'code_structure': 'STR01',
        })

        self.section = self.env['e_gestock.section'].create({
            'nom_section': 'Section Test',
            'code_section': 'SEC01',
            'code_structure': self.structure.id,
        })

        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Utilisateur Section Test',
            'login': 'user_section_test',
            'email': 'user_section_test@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_section_manager').id)],
        })

        # Associer l'utilisateur à la section
        self.section.write({
            'user_ids': [(4, self.user.id)],
        })

    def test_section_creation(self):
        """Test de la création d'une section"""
        self.assertEqual(self.section.nom_section, 'Section Test')
        self.assertEqual(self.section.code_section, 'SEC01')
        self.assertEqual(self.section.code_structure, self.structure)

    def test_section_users(self):
        """Test des utilisateurs associés aux sections"""
        # Vérifier que l'utilisateur est bien associé à la section
        self.assertIn(self.user, self.section.user_ids)

        # Vérifier que la section est bien associée à l'utilisateur
        self.assertIn(self.section, self.user.section_ids)

    def test_section_constraints(self):
        """Test des contraintes sur les sections"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.section'].create({
                'nom_section': 'Section Test 2',
                'code_section': 'SEC01',  # Code déjà utilisé
                'code_structure': self.structure.id,
            })

        # Test de l'unicité du code par structure
        structure2 = self.env['e_gestock.structure'].create({
            'nom_structure': 'Structure Test 2',
            'code_structure': 'STR02',
        })

        # Cela devrait fonctionner car le code est unique par structure
        section2 = self.env['e_gestock.section'].create({
            'nom_section': 'Section Test 2',
            'code_section': 'SEC01',  # Même code mais structure différente
            'code_structure': structure2.id,
        })

        self.assertEqual(section2.code_section, 'SEC01')
        self.assertEqual(section2.code_structure, structure2)

    def test_section_name_get(self):
        """Test de l'affichage du nom de la section"""
        name = self.section.name_get()[0][1]
        self.assertEqual(name, 'SEC01 - Section Test')

        # Test avec l'option show_structure
        name = self.section.with_context(show_structure=True).name_get()[0][1]
        self.assertEqual(name, 'SEC01 - Section Test')
