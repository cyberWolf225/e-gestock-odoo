# -*- coding: utf-8 -*-

from odoo.tests import common, tagged
from odoo.exceptions import AccessError, ValidationError, UserError
from datetime import datetime, timedelta

@tagged('post_install', '-at_install', 'e_gestock', 'workflow')
class TestDemandeAchatWorkflow(common.TransactionCase):
    """
    Test du workflow complet des demandes d'achat
    """

    def setUp(self):
        super(TestDemandeAchatWorkflow, self).setUp()

        # Création des utilisateurs de test avec différents rôles
        self.user_gestionnaire_achats = self._create_user('gestionnaire_achats', ['e_gestock_base.group_e_gestock_purchase_user'])
        self.user_section_manager = self._create_user('section_manager', ['e_gestock_base.group_section_manager'])
        self.user_structure_manager = self._create_user('structure_manager', ['e_gestock_base.group_structure_manager'])
        self.user_resp_achats = self._create_user('resp_achats', ['e_gestock_base.group_e_gestock_purchase_manager'])
        self.user_resp_dmp = self._create_user('resp_dmp', ['e_gestock_base.group_e_gestock_resp_dmp'])
        self.user_budget_controller = self._create_user('budget_controller', ['e_gestock_base.group_e_gestock_budget_controller'])
        self.user_dfc_validator = self._create_user('dfc_validator', ['e_gestock_base.group_dfc_validator'])
        self.user_dgaa_validator = self._create_user('dgaa_validator', ['e_gestock_base.group_dgaa_validator'])
        self.user_dg_validator = self._create_user('dg_validator', ['e_gestock_base.group_dg_validator'])
        self.user_budget_engager = self._create_user('budget_engager', ['e_gestock_base.group_budget_engager'])
        self.user_quotation_manager = self._create_user('quotation_manager', ['e_gestock_base.group_quotation_manager'])

        # Création des données de test
        self.structure = self.env['e_gestock.structure'].create({
            'code_structure': 'STR001',
            'nom_structure': 'Structure de test'
        })

        self.section = self.env['e_gestock.section'].create({
            'code_section': 'SEC001',
            'nom_section': 'Section de test',
            'structure_id': self.structure.id
        })

        self.famille = self.env['e_gestock.famille'].create({
            'ref_fam': 'FAM001',
            'design_fam': 'Famille de test'
        })

        self.depot = self.env['e_gestock.depot'].create({
            'name': 'Dépôt de test',
            'code': 'DEP001'
        })

        # Création d'un exercice budgétaire et d'un crédit
        self.exercice = self.env['e_gestock.exercise'].create({
            'name': '2025',
            'date_debut': '2025-01-01',
            'date_fin': '2025-12-31',
            'is_active': True
        })

        self.credit = self.env['e_gestock.credit'].create({
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'exercise_id': self.exercice.id,
            'montant': 10000000.0,
            'montant_consomme': 0.0
        })

        # Création d'un article
        self.article = self.env['e_gestock.article'].create({
            'ref_article': 'ART001',
            'design_article': 'Article de test',
            'famille_id': self.famille.id,
            'prix': 100000.0
        })

        # Création d'un fournisseur
        self.partner = self.env['res.partner'].create({
            'name': 'Fournisseur de test',
            'supplier_rank': 1
        })

    def _create_user(self, login, groups):
        """Crée un utilisateur avec les groupes spécifiés"""
        user = self.env['res.users'].create({
            'name': f'User {login}',
            'login': login,
            'email': f'{login}@example.com',
            'groups_id': [(6, 0, [self.env.ref(group).id for group in groups])]
        })
        return user

    def _create_demande_achat(self, user):
        """Crée une demande d'achat avec l'utilisateur spécifié"""
        return self.env['e_gestock.demande_achat'].with_user(user).create({
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'type_commande': 'stockable',
            'depot_id': self.depot.id,
            'motif': 'Test du workflow',
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 10,
                'prix_unitaire': 100000.0
            })]
        })

    def test_workflow_complet_petit_montant(self):
        """Test du workflow complet pour une demande de petit montant (< 5M)"""
        # Création de la demande par le gestionnaire des achats
        demande = self._create_demande_achat(self.user_gestionnaire_achats)
        self.assertEqual(demande.state, 'draft', "La demande devrait être en état brouillon")

        # Soumission de la demande
        demande.with_user(self.user_gestionnaire_achats).action_submit()
        self.assertEqual(demande.state, 'submitted', "La demande devrait être en état soumise")

        # Validation par le responsable de section
        demande.with_user(self.user_section_manager).action_validate_section()
        self.assertEqual(demande.state, 'section_validated', "La demande devrait être validée par la section")

        # Validation par le responsable de structure
        demande.with_user(self.user_structure_manager).action_validate_structure()
        self.assertEqual(demande.state, 'structure_validated', "La demande devrait être validée par la structure")

        # Validation par le responsable des achats
        demande.with_user(self.user_resp_achats).action_validate_achat()
        self.assertEqual(demande.state, 'achat_validated', "La demande devrait être validée par les achats")

        # Validation par le responsable DMP
        demande.with_user(self.user_resp_dmp).action_validate_dmp()
        self.assertEqual(demande.state, 'dmp_validated', "La demande devrait être validée par la DMP")

        # Contrôle budgétaire
        demande.with_user(self.user_budget_controller).action_check_budget()
        self.assertEqual(demande.state, 'budget_checked', "La demande devrait avoir passé le contrôle budgétaire")

        # Validation par la DFC
        demande.with_user(self.user_dfc_validator).action_validate_dfc()
        self.assertEqual(demande.state, 'dfc_validated', "La demande devrait être validée par la DFC")

        # Validation par le DGA (montant < 5M)
        demande.with_user(self.user_dgaa_validator).action_validate_dga()
        self.assertEqual(demande.state, 'dga_validated', "La demande devrait être validée par le DGA")

        # Engagement budgétaire
        demande.with_user(self.user_budget_engager).action_engage()
        self.assertEqual(demande.state, 'engaged', "La demande devrait être engagée")
        self.assertTrue(demande.engagement_ref, "Une référence d'engagement devrait être générée")

        # Mise en cotation
        demande.with_user(self.user_quotation_manager).action_quotation()
        self.assertEqual(demande.state, 'quotation', "La demande devrait être en cotation")

        # Création d'une cotation
        cotation = self.env['e_gestock.cotation'].with_user(self.user_quotation_manager).create({
            'demande_id': demande.id,
            'partner_id': self.partner.id,
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 10,
                'prix_unitaire': 100000.0
            })]
        })

        # Confirmation de la cotation
        cotation.with_user(self.user_quotation_manager).action_confirm()

        # Marquer la demande comme cotée
        demande.with_user(self.user_quotation_manager).write({'cotation_best_id': cotation.id})
        demande.with_user(self.user_quotation_manager).action_mark_quoted()
        self.assertEqual(demande.state, 'quoted', "La demande devrait être cotée")

        # Sélection du mieux-disant
        demande.with_user(self.user_quotation_manager).action_select_best()
        self.assertEqual(demande.state, 'best_selected', "Le mieux-disant devrait être sélectionné")

        # Génération du bon de commande
        demande.with_user(self.user_resp_achats).action_generate_po()
        self.assertEqual(demande.state, 'po_generated', "Le bon de commande devrait être généré")
        self.assertTrue(demande.purchase_order_id, "Un bon de commande devrait être lié")

        # Vérification finale
        self.assertEqual(demande.state, 'po_generated', "La demande devrait être à l'état BC généré")

    def test_workflow_complet_grand_montant(self):
        """Test du workflow complet pour une demande de grand montant (≥ 5M)"""
        # Création de la demande par le gestionnaire des achats avec un montant élevé
        demande = self.env['e_gestock.demande_achat'].with_user(self.user_gestionnaire_achats).create({
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'type_commande': 'stockable',
            'depot_id': self.depot.id,
            'motif': 'Test du workflow grand montant',
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 60,
                'prix_unitaire': 100000.0  # 60 * 100000 = 6M > 5M
            })]
        })

        self.assertEqual(demande.state, 'draft', "La demande devrait être en état brouillon")

        # Soumission de la demande
        demande.with_user(self.user_gestionnaire_achats).action_submit()
        self.assertEqual(demande.state, 'submitted', "La demande devrait être en état soumise")

        # Validation par le responsable de section
        demande.with_user(self.user_section_manager).action_validate_section()
        self.assertEqual(demande.state, 'section_validated', "La demande devrait être validée par la section")

        # Validation par le responsable de structure
        demande.with_user(self.user_structure_manager).action_validate_structure()
        self.assertEqual(demande.state, 'structure_validated', "La demande devrait être validée par la structure")

        # Validation par le responsable des achats
        demande.with_user(self.user_resp_achats).action_validate_achat()
        self.assertEqual(demande.state, 'achat_validated', "La demande devrait être validée par les achats")

        # Validation par le responsable DMP
        demande.with_user(self.user_resp_dmp).action_validate_dmp()
        self.assertEqual(demande.state, 'dmp_validated', "La demande devrait être validée par la DMP")

        # Contrôle budgétaire
        demande.with_user(self.user_budget_controller).action_check_budget()
        self.assertEqual(demande.state, 'budget_checked', "La demande devrait avoir passé le contrôle budgétaire")

        # Validation par la DFC
        demande.with_user(self.user_dfc_validator).action_validate_dfc()
        self.assertEqual(demande.state, 'dfc_validated', "La demande devrait être validée par la DFC")

        # Validation par le DG (montant ≥ 5M)
        demande.with_user(self.user_dg_validator).action_validate_dg()
        self.assertEqual(demande.state, 'dg_validated', "La demande devrait être validée par le DG")

        # Engagement budgétaire
        demande.with_user(self.user_budget_engager).action_engage()
        self.assertEqual(demande.state, 'engaged', "La demande devrait être engagée")
        self.assertTrue(demande.engagement_ref, "Une référence d'engagement devrait être générée")

        # Mise en cotation
        demande.with_user(self.user_quotation_manager).action_quotation()
        self.assertEqual(demande.state, 'quotation', "La demande devrait être en cotation")

        # Création d'une cotation
        cotation = self.env['e_gestock.cotation'].with_user(self.user_quotation_manager).create({
            'demande_id': demande.id,
            'partner_id': self.partner.id,
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 60,
                'prix_unitaire': 100000.0
            })]
        })

        # Confirmation de la cotation
        cotation.with_user(self.user_quotation_manager).action_confirm()

        # Marquer la demande comme cotée
        demande.with_user(self.user_quotation_manager).write({'cotation_best_id': cotation.id})
        demande.with_user(self.user_quotation_manager).action_mark_quoted()
        self.assertEqual(demande.state, 'quoted', "La demande devrait être cotée")

        # Sélection du mieux-disant
        demande.with_user(self.user_quotation_manager).action_select_best()
        self.assertEqual(demande.state, 'best_selected', "Le mieux-disant devrait être sélectionné")

        # Génération du bon de commande
        demande.with_user(self.user_resp_achats).action_generate_po()
        self.assertEqual(demande.state, 'po_generated', "Le bon de commande devrait être généré")
        self.assertTrue(demande.purchase_order_id, "Un bon de commande devrait être lié")

        # Vérification finale
        self.assertEqual(demande.state, 'po_generated', "La demande devrait être à l'état BC généré")

    def test_restrictions_acces(self):
        """Test des restrictions d'accès selon les rôles"""
        # Création d'un utilisateur sans rôle E-GESTOCK
        user_sans_role = self.env['res.users'].create({
            'name': 'User sans role',
            'login': 'user_sans_role',
            'email': 'user_sans_role@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

        # Création d'une demande d'achat
        demande = self._create_demande_achat(self.user_gestionnaire_achats)

        # Test 1: Un utilisateur sans rôle E-GESTOCK ne devrait pas pouvoir accéder aux demandes d'achat
        with self.assertRaises(AccessError):
            demande.with_user(user_sans_role).read(['name'])

        # Test 2: Un utilisateur sans rôle E-GESTOCK ne devrait pas pouvoir créer une demande d'achat
        with self.assertRaises(AccessError):
            self.env['e_gestock.demande_achat'].with_user(user_sans_role).create({
                'structure_id': self.structure.id,
                'section_id': self.section.id,
                'famille_id': self.famille.id,
                'type_commande': 'stockable',
                'depot_id': self.depot.id,
                'motif': 'Test des restrictions'
            })

        # Test 3: Un utilisateur avec un rôle E-GESTOCK mais sans droit de validation ne devrait pas pouvoir valider
        # Soumettre la demande
        demande.with_user(self.user_gestionnaire_achats).action_submit()

        # Un gestionnaire des achats ne devrait pas pouvoir valider au niveau section
        with self.assertRaises(AccessError):
            demande.with_user(self.user_gestionnaire_achats).action_validate_section()

        # Test 4: Vérification que le DGA ne peut pas valider une demande de grand montant
        # Créer une demande avec un montant élevé
        demande_grand_montant = self.env['e_gestock.demande_achat'].with_user(self.user_gestionnaire_achats).create({
            'structure_id': self.structure.id,
            'section_id': self.section.id,
            'famille_id': self.famille.id,
            'type_commande': 'stockable',
            'depot_id': self.depot.id,
            'motif': 'Test des restrictions grand montant',
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 60,
                'prix_unitaire': 100000.0  # 60 * 100000 = 6M > 5M
            })]
        })

        # Faire avancer la demande jusqu'à l'état dfc_validated
        demande_grand_montant.with_user(self.user_gestionnaire_achats).action_submit()
        demande_grand_montant.with_user(self.user_section_manager).action_validate_section()
        demande_grand_montant.with_user(self.user_structure_manager).action_validate_structure()
        demande_grand_montant.with_user(self.user_resp_achats).action_validate_achat()
        demande_grand_montant.with_user(self.user_resp_dmp).action_validate_dmp()
        demande_grand_montant.with_user(self.user_budget_controller).action_check_budget()
        demande_grand_montant.with_user(self.user_dfc_validator).action_validate_dfc()

        # Le DGA ne devrait pas pouvoir valider une demande de grand montant
        with self.assertRaises(UserError):
            demande_grand_montant.with_user(self.user_dgaa_validator).action_validate_dga()

        # Test 5: Vérification que le DG ne peut pas valider une demande de petit montant
        # Créer une demande avec un petit montant
        demande_petit_montant = self._create_demande_achat(self.user_gestionnaire_achats)

        # Faire avancer la demande jusqu'à l'état dfc_validated
        demande_petit_montant.with_user(self.user_gestionnaire_achats).action_submit()
        demande_petit_montant.with_user(self.user_section_manager).action_validate_section()
        demande_petit_montant.with_user(self.user_structure_manager).action_validate_structure()
        demande_petit_montant.with_user(self.user_resp_achats).action_validate_achat()
        demande_petit_montant.with_user(self.user_resp_dmp).action_validate_dmp()
        demande_petit_montant.with_user(self.user_budget_controller).action_check_budget()
        demande_petit_montant.with_user(self.user_dfc_validator).action_validate_dfc()

        # Le DG ne devrait pas pouvoir valider une demande de petit montant
        with self.assertRaises(UserError):
            demande_petit_montant.with_user(self.user_dg_validator).action_validate_dg()

    def test_processus_cotation(self):
        """Test spécifique du processus de cotation"""
        # Création d'un deuxième fournisseur pour comparer les cotations
        partner2 = self.env['res.partner'].create({
            'name': 'Fournisseur 2',
            'supplier_rank': 1
        })

        # Création de la demande et avancement jusqu'à l'état 'quotation'
        demande = self._create_demande_achat(self.user_gestionnaire_achats)
        demande.with_user(self.user_gestionnaire_achats).action_submit()
        demande.with_user(self.user_section_manager).action_validate_section()
        demande.with_user(self.user_structure_manager).action_validate_structure()
        demande.with_user(self.user_resp_achats).action_validate_achat()
        demande.with_user(self.user_resp_dmp).action_validate_dmp()
        demande.with_user(self.user_budget_controller).action_check_budget()
        demande.with_user(self.user_dfc_validator).action_validate_dfc()
        demande.with_user(self.user_dgaa_validator).action_validate_dga()
        demande.with_user(self.user_budget_engager).action_engage()
        demande.with_user(self.user_quotation_manager).action_quotation()

        self.assertEqual(demande.state, 'quotation', "La demande devrait être en état de cotation")

        # Création de deux cotations pour la même demande
        cotation1 = self.env['e_gestock.cotation'].with_user(self.user_quotation_manager).create({
            'demande_id': demande.id,
            'partner_id': self.partner.id,
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 10,
                'prix_unitaire': 100000.0  # Prix total: 1M
            })]
        })

        cotation2 = self.env['e_gestock.cotation'].with_user(self.user_quotation_manager).create({
            'demande_id': demande.id,
            'partner_id': partner2.id,
            'line_ids': [(0, 0, {
                'article_id': self.article.id,
                'quantite': 10,
                'prix_unitaire': 90000.0  # Prix total: 900K (moins cher)
            })]
        })

        # Confirmation des cotations
        cotation1.with_user(self.user_quotation_manager).action_confirm()
        cotation2.with_user(self.user_quotation_manager).action_confirm()

        # Vérification que les deux cotations sont bien liées à la demande
        self.assertEqual(len(demande.cotation_ids), 2, "La demande devrait avoir 2 cotations")

        # Marquer la demande comme cotée
        demande.with_user(self.user_quotation_manager).action_mark_quoted()
        self.assertEqual(demande.state, 'quoted', "La demande devrait être à l'état cotée")

        # Sélection du mieux-disant (cotation2 car moins chère)
        demande.with_user(self.user_quotation_manager).write({'cotation_best_id': cotation2.id})
        demande.with_user(self.user_quotation_manager).action_select_best()

        # Vérification que la cotation2 est bien sélectionnée et la cotation1 rejetée
        cotation2.refresh()
        cotation1.refresh()
        self.assertEqual(cotation2.state, 'selected', "La cotation2 devrait être sélectionnée")
        self.assertEqual(cotation1.state, 'rejected', "La cotation1 devrait être rejetée")

        # Génération du bon de commande
        demande.with_user(self.user_resp_achats).action_generate_po()
        self.assertEqual(demande.state, 'po_generated', "Le bon de commande devrait être généré")

        # Vérification que le bon de commande est bien créé avec le bon fournisseur
        self.assertTrue(demande.purchase_order_id, "Un bon de commande devrait être lié")
        self.assertEqual(demande.purchase_order_id.partner_id, partner2, "Le fournisseur du BC devrait être le fournisseur 2")