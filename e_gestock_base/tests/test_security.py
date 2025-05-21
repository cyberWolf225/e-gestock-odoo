# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError

@tagged('post_install', '-at_install')
class TestSecurity(TransactionCase):
    """Tests pour la sécurité du module e_gestock_base"""

    def setUp(self):
        super(TestSecurity, self).setUp()
        # Créer des utilisateurs de test avec différents niveaux d'accès
        
        # Utilisateur de base
        self.user_base = self.env['res.users'].create({
            'name': 'Utilisateur Base',
            'login': 'user_base',
            'email': 'user_base@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_user').id)],
        })
        
        # Utilisateur administrateur
        self.user_admin = self.env['res.users'].create({
            'name': 'Utilisateur Admin',
            'login': 'user_admin',
            'email': 'user_admin@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_admin').id)],
        })
        
        # Utilisateur direction
        self.user_direction = self.env['res.users'].create({
            'name': 'Utilisateur Direction',
            'login': 'user_direction',
            'email': 'user_direction@example.com',
            'groups_id': [(4, self.env.ref('e_gestock_base.group_e_gestock_direction').id)],
        })
        
        # Créer des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'name': 'Structure Test Sécurité',
            'code': 'STR_SEC',
        })
        
        self.section = self.env['e_gestock.section'].create({
            'name': 'Section Test Sécurité',
            'code': 'SEC_SEC',
            'structure_id': self.structure.id,
        })
        
        self.famille = self.env['e_gestock.famille'].create({
            'name': 'Famille Test Sécurité',
            'code': 'FAM_SEC',
        })
        
        self.categorie = self.env['e_gestock.categorie'].create({
            'name': 'Catégorie Test Sécurité',
            'code': 'CAT_SEC',
            'famille_id': self.famille.id,
        })
        
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        
        self.article = self.env['e_gestock.article'].create({
            'name': 'Article Test Sécurité',
            'code': 'ART_SEC',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })

    def test_user_access_rights(self):
        """Test des droits d'accès des utilisateurs"""
        # Utilisateur de base - Lecture seule
        article = self.article.with_user(self.user_base)
        self.assertEqual(article.name, 'Article Test Sécurité')  # Peut lire
        
        with self.assertRaises(AccessError):
            article.write({'name': 'Article Test Sécurité Modifié'})  # Ne peut pas modifier
        
        with self.assertRaises(AccessError):
            self.env['e_gestock.article'].with_user(self.user_base).create({
                'name': 'Nouvel Article',
                'code': 'NEW_ART',
                'famille_id': self.famille.id,
                'categorie_id': self.categorie.id,
                'uom_id': self.uom_unit.id,
                'type': 'product',
            })  # Ne peut pas créer
        
        # Utilisateur administrateur - Accès complet
        article_admin = self.article.with_user(self.user_admin)
        article_admin.write({'name': 'Article Test Sécurité Admin'})  # Peut modifier
        self.assertEqual(article_admin.name, 'Article Test Sécurité Admin')
        
        new_article = self.env['e_gestock.article'].with_user(self.user_admin).create({
            'name': 'Nouvel Article Admin',
            'code': 'NEW_ART_ADMIN',
            'famille_id': self.famille.id,
            'categorie_id': self.categorie.id,
            'uom_id': self.uom_unit.id,
            'type': 'product',
        })  # Peut créer
        self.assertEqual(new_article.name, 'Nouvel Article Admin')
        
        # Utilisateur direction - Accès complet
        article_direction = self.article.with_user(self.user_direction)
        article_direction.write({'name': 'Article Test Sécurité Direction'})  # Peut modifier
        self.assertEqual(article_direction.name, 'Article Test Sécurité Direction')

    def test_group_inheritance(self):
        """Test de l'héritage des groupes"""
        # Vérifier que l'administrateur a les droits de l'utilisateur de base
        self.assertIn(
            self.env.ref('e_gestock_base.group_e_gestock_user'),
            self.user_admin.groups_id
        )
        
        # Vérifier que la direction a les droits de l'administrateur
        self.assertIn(
            self.env.ref('e_gestock_base.group_e_gestock_admin'),
            self.user_direction.groups_id
        )
