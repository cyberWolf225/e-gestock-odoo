# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import os
import logging

_logger = logging.getLogger(__name__)

class TypeGestion(models.Model):
    _name = 'e_gestock.type_gestion'
    _description = 'Type de gestion'
    _order = 'code_gestion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'libelle_gestion'

    code_gestion = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        index=True,
        help="Code unique du type de gestion (ex: A, G, E, ...)"
    )

    libelle_gestion = fields.Char(
        string='Libellé',
        required=True,
        tracking=True,
        help="Désignation du type de gestion"
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si ce type de gestion est actuellement utilisable"
    )

    section_ids = fields.One2many(
        'e_gestock.section',
        'code_gestion',
        string='Sections associées',
        help="Sections utilisant ce type de gestion"
    )

    section_count = fields.Integer(
        string='Nombre de sections',
        compute='_compute_section_count',
        help="Nombre de sections utilisant ce type de gestion"
    )

    _sql_constraints = [
        ('code_gestion_unique', 'UNIQUE(code_gestion)', 'Le code du type de gestion doit être unique!')
    ]

    @api.depends('section_ids')
    def _compute_section_count(self):
        """Calcule le nombre de sections utilisant ce type de gestion"""
        for record in self:
            record.section_count = len(record.section_ids)

    @api.constrains('code_gestion')
    def _check_code_gestion(self):
        """Vérifie que le code de gestion est valide (1 à 2 caractères)"""
        for record in self:
            if record.code_gestion and len(record.code_gestion) > 2:
                raise ValidationError(_("Le code de gestion ne doit pas dépasser 2 caractères!"))

    def name_get(self):
        """Affiche le code et le libellé dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.code_gestion} - {record.libelle_gestion}" if record.code_gestion else record.libelle_gestion
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par code ou par libellé"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code_gestion', operator, name), ('libelle_gestion', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def load_from_json(self, file_path):
        """Charge les types de gestion depuis un fichier JSON

        Args:
            file_path (str): Chemin relatif du fichier JSON dans le module

        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        try:
            # Construire le chemin absolu du fichier
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(module_path, file_path)

            _logger.info(f"Chargement des types de gestion depuis {full_path}")

            # Vérifier si le fichier existe
            if not os.path.isfile(full_path):
                _logger.error(f"Le fichier {full_path} n'existe pas")
                return False

            # Lire le contenu du fichier JSON
            with open(full_path, 'r', encoding='utf-8') as file:
                types_gestion_data = json.load(file)

            # Créer les types de gestion
            for type_gestion_data in types_gestion_data:
                code_gestion = type_gestion_data.get('code_gestion')
                libelle_gestion = type_gestion_data.get('libelle_gestion')

                # Vérifier si le type de gestion existe déjà
                existing_type = self.search([('code_gestion', '=', code_gestion)], limit=1)
                if existing_type:
                    _logger.info(f"Le type de gestion {code_gestion} existe déjà, mise à jour")
                    existing_type.write({
                        'libelle_gestion': libelle_gestion,
                    })
                else:
                    _logger.info(f"Création du type de gestion {code_gestion}")
                    self.create({
                        'code_gestion': code_gestion,
                        'libelle_gestion': libelle_gestion,
                    })

            return True
        except Exception as e:
            _logger.error(f"Erreur lors du chargement des types de gestion: {e}")
            return False