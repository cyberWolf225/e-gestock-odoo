# Scripts de Migration des Groupes d'Utilisateurs E-GESTOCK

Ce répertoire contient des scripts pour migrer les utilisateurs des anciens groupes vers les nouveaux groupes, mettre à jour les références aux groupes dans le code, et tester les accès des utilisateurs.

## Liste des Scripts

- `update_group_references.py` : Met à jour les références aux groupes dans les fichiers XML et Python.
- `migrate_user_groups.py` : Migre les utilisateurs des anciens groupes vers les nouveaux groupes.
- `test_user_access.py` : Teste les accès des utilisateurs aux différents modèles.
- `run_all_scripts.py` : Exécute tous les scripts dans l'ordre.
- `run_migration.bat` : Script batch pour exécuter le script principal depuis Windows.

## Prérequis

- Python 3.6 ou supérieur
- Odoo 18
- Module `lxml` pour Python (pour le script `update_group_references.py`)

## Utilisation

### Méthode 1 : Exécution du script batch

1. Double-cliquez sur le fichier `run_migration.bat`.
2. Attendez que tous les scripts soient exécutés.
3. Vérifiez les fichiers de log pour les résultats.

### Méthode 2 : Exécution manuelle des scripts

1. Ouvrez une invite de commande.
2. Naviguez vers le répertoire racine d'Odoo.
3. Exécutez les scripts dans l'ordre suivant :

```bash
python custom/e_gestock_base/scripts/update_group_references.py
python custom/e_gestock_base/scripts/migrate_user_groups.py
python custom/e_gestock_base/scripts/test_user_access.py
```

## Fichiers de Log

Chaque script génère un fichier de log dans le répertoire courant :

- `update_group_references.log` : Log de la mise à jour des références aux groupes.
- `migrate_user_groups.log` : Log de la migration des utilisateurs.
- `test_user_access.log` : Log des tests d'accès.
- `run_all_scripts.log` : Log de l'exécution de tous les scripts.

## Mapping des Groupes

Le mapping des anciens groupes vers les nouveaux groupes est défini dans les scripts `update_group_references.py` et `migrate_user_groups.py`. Voici un résumé :

| Ancien Groupe | Nouveau Groupe |
|---------------|----------------|
| `purchase.group_purchase_user` | `e_gestock_base.group_e_gestock_purchase_user` |
| `purchase.group_purchase_manager` | `e_gestock_base.group_e_gestock_purchase_manager` |
| `e_gestock_purchase.group_e_gestock_gestionnaire_achats` | `e_gestock_base.group_e_gestock_purchase_user` |
| `e_gestock_purchase.group_e_gestock_resp_achats` | `e_gestock_base.group_e_gestock_purchase_manager` |
| `e_gestock_purchase.group_quotation_manager` | `e_gestock_base.group_e_gestock_quotation_manager` |
| `e_gestock_purchase.group_e_gestock_controle_budg` | `e_gestock_base.group_e_gestock_budget_controller` |
| `e_gestock_base.group_e_gestock_controle_budg` | `e_gestock_base.group_e_gestock_budget_controller` |
| `e_gestock_base.group_e_gestock_engageur_budg` | `e_gestock_base.group_e_gestock_budget_engager` |
| `e_gestock_base.group_e_gestock_resp_reception` | `e_gestock_base.group_e_gestock_reception_manager` |
| `e_gestock_base.group_e_gestock_gestionnaire_stocks` | `e_gestock_base.group_e_gestock_inventory_user` |
| `e_gestock_base.group_e_gestock_resp_stocks` | `e_gestock_base.group_e_gestock_inventory_manager` |

## Dépannage

Si vous rencontrez des erreurs lors de l'exécution des scripts, vérifiez les fichiers de log pour plus de détails. Voici quelques problèmes courants et leurs solutions :

- **Erreur d'importation d'Odoo** : Assurez-vous que les scripts sont exécutés dans l'environnement Odoo.
- **Erreur d'importation de lxml** : Installez le module lxml avec la commande `pip install lxml`.
- **Erreur de connexion à la base de données** : Vérifiez que la base de données `egestock` existe et est accessible.
- **Erreur de référence à un groupe inexistant** : Vérifiez que les groupes référencés dans les scripts existent dans la base de données.

## Remarques

- Les scripts doivent être exécutés après la mise à jour du module `e_gestock_base`.
- Les scripts ne suppriment pas les anciens groupes, ils ajoutent simplement les utilisateurs aux nouveaux groupes.
- Les tests d'accès peuvent prendre un certain temps à s'exécuter, surtout si vous avez beaucoup d'utilisateurs.
