# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestDepot(TransactionCase):
    """Tests pour le modèle dépôt du module e_gestock_base"""

    def setUp(self):
        super(TestDepot, self).setUp()
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Dépôt',
            'code': 'STR_DEP',
        })
        
        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test',
            'code': 'DEP01',
            'structure_id': self.structure.id,
            'active': True,
        })
        
        # Créer un utilisateur de test
        self.user = self.env['res.users'].create({
            'name': 'Responsable Dépôt Test',
            'login': 'resp_depot_test',
            'email': 'resp_depot_test@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_resp_depot').id)],
        })
        
        # Associer l'utilisateur au dépôt
        self.depot.write({
            'user_ids': [(4, self.user.id)],
        })

    def test_depot_creation(self):
        """Test de la création d'un dépôt"""
        self.assertEqual(self.depot.name, 'Dépôt Test')
        self.assertEqual(self.depot.code, 'DEP01')
        self.assertEqual(self.depot.structure_id, self.structure)
        self.assertTrue(self.depot.active)

    def test_depot_users(self):
        """Test des utilisateurs associés aux dépôts"""
        # Vérifier que l'utilisateur est bien associé au dépôt
        self.assertIn(self.user, self.depot.user_ids)
        
        # Vérifier que le dépôt est bien associé à l'utilisateur
        self.assertIn(self.depot, self.user.depot_ids)

    def test_depot_constraints(self):
        """Test des contraintes sur les dépôts"""
        # Test de l'unicité du code
        with self.assertRaises(Exception):
            self.env['e_gestock.depot'].create({
                'name': 'Dépôt Test 2',
                'code': 'DEP01',  # Code déjà utilisé
                'structure_id': self.structure.id,
                'active': True,
            })
        
        # Test de l'unicité du code par structure
        structure2 = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Dépôt 2',
            'code': 'STR_DEP2',
        })
        
        # Cela devrait fonctionner car le code est unique par structure
        depot2 = self.env['e_gestock.depot'].create({
            'name': 'Dépôt Test 2',
            'code': 'DEP01',  # Même code mais structure différente
            'structure_id': structure2.id,
            'active': True,
        })
        
        self.assertEqual(depot2.code, 'DEP01')
        self.assertEqual(depot2.structure_id, structure2)

    def test_depot_archive(self):
        """Test de l'archivage d'un dépôt"""
        # Archiver le dépôt
        self.depot.write({'active': False})
        self.assertFalse(self.depot.active)
        
        # Vérifier que le dépôt n'apparaît plus dans les recherches par défaut
        depots = self.env['e_gestock.depot'].search([])
        self.assertNotIn(self.depot, depots)
        
        # Vérifier que le dépôt apparaît dans les recherches incluant les archives
        depots = self.env['e_gestock.depot'].with_context(active_test=False).search([])
        self.assertIn(self.depot, depots)
        
        # Réactiver le dépôt
        self.depot.write({'active': True})
        self.assertTrue(self.depot.active)
        
        # Vérifier que le dépôt apparaît à nouveau dans les recherches par défaut
        depots = self.env['e_gestock.depot'].search([])
        self.assertIn(self.depot, depots)
