#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de migration des comités de réception
Ce script fusionne les données des modèles e_gestock.comite_reception et e_gestock.reception_committee
en un seul modèle e_gestock.reception_committee dans le module e_gestock_base.
"""

import logging
import sys
import os

# Ajouter le chemin d'Odoo au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

_logger = logging.getLogger(__name__)

def migrate_reception_committees(env):
    """
    Migre les données des comités de réception
    :param env: Environnement Odoo
    """
    _logger.info("Début de la migration des comités de réception")

    # Vérifier si les modèles existent
    if not env['ir.model'].search([('model', '=', 'e_gestock.reception_committee')]):
        _logger.error("Le modèle e_gestock.reception_committee n'existe pas")
        return False

    # Vérifier si le modèle e_gestock.comite_reception existe
    old_model_exists = bool(env['ir.model'].search([('model', '=', 'e_gestock.comite_reception')]))

    # Récupérer les comités de réception existants dans le nouveau modèle
    existing_committees = env['e_gestock.reception_committee'].search([])
    existing_codes = {committee.code for committee in existing_committees}

    # Migrer les données de l'ancien modèle si celui-ci existe
    if old_model_exists:
        try:
            # Récupérer les comités de réception de l'ancien modèle
            old_committees = env['e_gestock.comite_reception'].search([])
            _logger.info(f"Nombre de comités de réception dans l'ancien modèle: {len(old_committees)}")

            # Créer les nouveaux comités de réception
            for old_committee in old_committees:
                # Générer un code unique
                code = f"COM/{old_committee.id:04d}"
                if code in existing_codes:
                    code = f"COM/OLD/{old_committee.id:04d}"

                # Créer le nouveau comité
                new_committee_vals = {
                    'name': old_committee.name,
                    'code': code,
                    'active': True,
                    'structure_id': old_committee.structure_id.id if hasattr(old_committee, 'structure_id') and old_committee.structure_id else False,
                    'responsible_id': old_committee.responsable_id.id if hasattr(old_committee, 'responsable_id') and old_committee.responsable_id else SUPERUSER_ID,
                    'quorum': old_committee.quorum if hasattr(old_committee, 'quorum') else 3,
                    'notes': f"Migré depuis l'ancien modèle (ID: {old_committee.id})",
                }

                # Ajouter les membres si disponibles
                if hasattr(old_committee, 'member_ids') and old_committee.member_ids:
                    new_committee_vals['member_ids'] = [(6, 0, old_committee.member_ids.ids)]

                # Créer le nouveau comité
                new_committee = env['e_gestock.reception_committee'].create(new_committee_vals)
                _logger.info(f"Comité migré: {new_committee.name} (ID: {new_committee.id})")

                # Mettre à jour les références dans les réceptions
                try:
                    if 'e_gestock.reception' in env:
                        receptions = env['e_gestock.reception'].search([
                            ('comite_reception_id', '=', old_committee.id)
                        ])
                        for reception in receptions:
                            reception.write({
                                'committee_id': new_committee.id,
                                'comite_reception_id': False,
                            })
                        _logger.info(f"Mise à jour de {len(receptions)} réceptions pour le comité {new_committee.name}")
                except Exception as e:
                    _logger.error(f"Erreur lors de la mise à jour des réceptions: {e}")

                # Mettre à jour les références dans les bons de commande
                try:
                    if 'e_gestock.purchase_order' in env:
                        # Rechercher les bons de commande avec l'ancien comité
                        purchase_orders = env['e_gestock.purchase_order'].search([
                            '|',
                            ('reception_committee_id', '=', old_committee.id),
                            ('comite_reception_id', '=', old_committee.id)
                        ])
                        for po in purchase_orders:
                            po.write({
                                'committee_id': new_committee.id,
                                'reception_committee_id': False,
                                'comite_reception_id': False,
                            })
                        _logger.info(f"Mise à jour de {len(purchase_orders)} bons de commande pour le comité {new_committee.name}")
                except Exception as e:
                    _logger.error(f"Erreur lors de la mise à jour des bons de commande: {e}")

            _logger.info("Migration des comités de réception terminée avec succès")
            return True

        except Exception as e:
            _logger.error(f"Erreur lors de la migration des comités de réception: {e}")
            return False
    else:
        _logger.info("Le modèle e_gestock.comite_reception n'existe pas, aucune migration nécessaire")
        return True

def main():
    """
    Point d'entrée principal du script
    """
    # Configuration de la connexion à Odoo
    config['db_name'] = 'egestock'  # Remplacer par le nom de votre base de données

    # Créer un environnement Odoo
    with api.Environment.manage():
        registry = odoo.modules.registry.Registry(config['db_name'])
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            migrate_reception_committees(env)

if __name__ == '__main__':
    main()
