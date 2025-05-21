# Guide de test manuel du workflow des demandes d'achat

Ce guide vous permettra de vérifier manuellement que le workflow des demandes d'achat fonctionne correctement après les modifications de sécurité.

## Prérequis

1. Assurez-vous que les modules suivants sont installés et à jour :
   - e_gestock_base
   - e_gestock_budget
   - e_gestock_inventory
   - e_gestock_purchase
   - e_gestock_supplier
   - e_gestock_reception

2. Créez plusieurs utilisateurs avec différents rôles E-GESTOCK :
   - Utilisateur 1 : Gestionnaire des achats (group_e_gestock_purchase_user)
   - Utilisateur 2 : Responsable de section (group_section_manager)
   - Utilisateur 3 : Responsable de structure (group_structure_manager)
   - Utilisateur 4 : Responsable des achats (group_e_gestock_purchase_manager)
   - Utilisateur 5 : Responsable DMP (group_e_gestock_resp_dmp)
   - Utilisateur 6 : Contrôleur budget (group_e_gestock_budget_controller)
   - Utilisateur 7 : Validateur DFC (group_dfc_validator)
   - Utilisateur 8 : Validateur DGA (group_dgaa_validator)
   - Utilisateur 9 : Validateur DG (group_dg_validator)
   - Utilisateur 10 : Engageur budget (group_budget_engager)
   - Utilisateur 11 : Gestionnaire des cotations (group_quotation_manager)
   - Utilisateur 12 : Sans rôle E-GESTOCK (uniquement base.group_user)

## Test 1 : Vérification des restrictions d'accès

1. Connectez-vous avec l'Utilisateur 12 (sans rôle E-GESTOCK)
2. Essayez d'accéder au menu E-GESTOCK > Achats
3. Vérifiez que l'accès est refusé ou que le menu n'est pas visible
4. Essayez d'accéder directement à une demande d'achat via son URL (par exemple, /web#id=1&model=e_gestock.demande_achat&view_type=form)
5. Vérifiez que l'accès est refusé

## Test 2 : Workflow complet pour une demande de petit montant (< 5M)

1. Connectez-vous avec l'Utilisateur 1 (Gestionnaire des achats)
2. Créez une nouvelle demande d'achat avec un montant total inférieur à 5 000 000
3. Soumettez la demande
4. Déconnectez-vous et connectez-vous avec l'Utilisateur 2 (Responsable de section)
5. Validez la demande au niveau section
6. Déconnectez-vous et connectez-vous avec l'Utilisateur 3 (Responsable de structure)
7. Validez la demande au niveau structure
8. Déconnectez-vous et connectez-vous avec l'Utilisateur 4 (Responsable des achats)
9. Validez la demande au niveau achats
10. Déconnectez-vous et connectez-vous avec l'Utilisateur 5 (Responsable DMP)
11. Validez la demande au niveau DMP
12. Déconnectez-vous et connectez-vous avec l'Utilisateur 6 (Contrôleur budget)
13. Effectuez le contrôle budgétaire
14. Déconnectez-vous et connectez-vous avec l'Utilisateur 7 (Validateur DFC)
15. Validez la demande au niveau DFC
16. Déconnectez-vous et connectez-vous avec l'Utilisateur 8 (Validateur DGA)
17. Validez la demande au niveau DGA
18. Déconnectez-vous et connectez-vous avec l'Utilisateur 10 (Engageur budget)
19. Engagez la demande
20. Déconnectez-vous et connectez-vous avec l'Utilisateur 11 (Gestionnaire des cotations)
21. Mettez la demande en cotation
22. Créez plusieurs cotations pour différents fournisseurs
23. Marquez la demande comme cotée
24. Sélectionnez le mieux-disant
25. Déconnectez-vous et connectez-vous avec l'Utilisateur 4 (Responsable des achats)
26. Générez le bon de commande
27. Vérifiez que le bon de commande est bien créé

## Test 3 : Workflow complet pour une demande de grand montant (≥ 5M)

1. Connectez-vous avec l'Utilisateur 1 (Gestionnaire des achats)
2. Créez une nouvelle demande d'achat avec un montant total supérieur ou égal à 5 000 000
3. Suivez les mêmes étapes que pour le Test 2 jusqu'à l'étape 15
4. Après la validation DFC, connectez-vous avec l'Utilisateur 9 (Validateur DG) au lieu de l'Utilisateur 8
5. Validez la demande au niveau DG
6. Continuez avec les étapes restantes comme dans le Test 2

## Test 4 : Vérification des contrôles d'accès spécifiques

1. Connectez-vous avec l'Utilisateur 8 (Validateur DGA)
2. Essayez de valider une demande de grand montant (≥ 5M) qui est à l'état "Validée DFC"
3. Vérifiez que l'action est refusée

4. Connectez-vous avec l'Utilisateur 9 (Validateur DG)
5. Essayez de valider une demande de petit montant (< 5M) qui est à l'état "Validée DFC"
6. Vérifiez que l'action est refusée

7. Connectez-vous avec l'Utilisateur 1 (Gestionnaire des achats)
8. Créez une demande d'achat et soumettez-la
9. Essayez de valider directement la demande au niveau section
10. Vérifiez que l'action est refusée

## Test 5 : Vérification du processus de cotation

1. Connectez-vous avec l'Utilisateur 11 (Gestionnaire des cotations)
2. Accédez à une demande d'achat à l'état "Engagée"
3. Mettez la demande en cotation
4. Créez plusieurs cotations pour différents fournisseurs avec des prix différents
5. Marquez la demande comme cotée
6. Sélectionnez le fournisseur avec le prix le plus bas comme mieux-disant
7. Vérifiez que les autres cotations sont automatiquement rejetées
8. Déconnectez-vous et connectez-vous avec l'Utilisateur 4 (Responsable des achats)
9. Générez le bon de commande
10. Vérifiez que le bon de commande est créé avec le fournisseur sélectionné comme mieux-disant

## Conclusion

Si tous les tests ci-dessus sont réussis, cela signifie que :
1. Les restrictions d'accès fonctionnent correctement
2. Le workflow des demandes d'achat fonctionne correctement pour les petits et grands montants
3. Les contrôles d'accès spécifiques sont appliqués correctement
4. Le processus de cotation fonctionne correctement

En cas d'échec d'un test, notez précisément à quelle étape le problème est survenu et quel message d'erreur a été affiché, le cas échéant.
