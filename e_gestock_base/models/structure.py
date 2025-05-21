# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import os
import logging

_logger = logging.getLogger(__name__)

class Structure(models.Model):
    _name = 'e_gestock.structure'
    _description = 'Structure organisationnelle'
    _order = 'code_structure'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nom_structure'

    code_structure = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        index=True,
        help="Code unique de la structure (ex: 9101, 9102, ...)"
    )

    nom_structure = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
        help="Nom descriptif de la structure"
    )

    num_structure = fields.Integer(
        string='Numéro',
        tracking=True,
        help="Numéro de la structure"
    )

    ref_depot = fields.Many2one(
        'e_gestock.depot',
        string='Dépôt de référence',
        tracking=True,
        help="Dépôt associé à cette structure"
    )

    organisation_id = fields.Many2one(
        'e_gestock.structure',
        string='Organisation parente',
        tracking=True,
        domain="[('id', '!=', id)]",
        help="Organisation hiérarchique supérieure"
    )

    section_ids = fields.One2many(
        'e_gestock.section',
        'code_structure',
        string='Sections',
        help="Sections appartenant à cette structure"
    )

    section_count = fields.Integer(
        string='Nombre de sections',
        compute='_compute_section_count',
        store=True,
        help="Nombre de sections dans cette structure"
    )

    child_ids = fields.One2many(
        'e_gestock.structure',
        'organisation_id',
        string='Structures enfants',
        help="Structures organisationnelles subordonnées"
    )

    user_ids = fields.One2many(
        'res.users',
        'structure_id',
        string='Utilisateurs',
        help="Utilisateurs principalement affectés à cette structure"
    )

    user_count = fields.Integer(
        string='Nombre d\'utilisateurs',
        compute='_compute_user_count',
        store=True
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si cette structure est actuellement utilisable"
    )

    _sql_constraints = [
        ('code_structure_unique', 'UNIQUE(code_structure)', 'Le code de structure doit être unique!')
    ]

    @api.depends('section_ids')
    def _compute_section_count(self):
        """Calcule le nombre de sections dans cette structure"""
        for record in self:
            record.section_count = len(record.section_ids)

    @api.constrains('organisation_id')
    def _check_organisation_hierarchy(self):
        """Vérifie qu'il n'y a pas de boucle dans la hiérarchie des structures"""
        for record in self:
            if not record.organisation_id:
                continue
            parent = record.organisation_id
            while parent:
                if parent.id == record.id:
                    raise ValidationError(_("Boucle détectée dans la hiérarchie des structures!"))
                parent = parent.organisation_id

    @api.depends('user_ids')
    def _compute_user_count(self):
        """Calcule le nombre d'utilisateurs dans cette structure"""
        for record in self:
            record.user_count = len(record.user_ids)

    def name_get(self):
        """Affiche le code et le nom dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.code_structure} - {record.nom_structure}" if record.code_structure else record.nom_structure
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par code ou par nom"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code_structure', operator, name), ('nom_structure', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def load_from_json(self, file_path):
        """Charge les structures depuis un fichier JSON

        Args:
            file_path (str): Chemin relatif du fichier JSON dans le module

        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        try:
            # Construire le chemin absolu du fichier
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(module_path, file_path)

            _logger.info(f"Chargement des structures depuis {full_path}")

            # Vérifier si le fichier existe
            if not os.path.isfile(full_path):
                _logger.error(f"Le fichier {full_path} n'existe pas")
                return False

            # Lire le contenu du fichier JSON
            with open(full_path, 'r', encoding='utf-8') as file:
                structures_data = json.load(file)

            # Créer les structures
            for structure_data in structures_data:
                code_structure = structure_data.get('code_structure')
                nom_structure = structure_data.get('nom_structure')

                # Vérifier si la structure existe déjà
                existing_structure = self.search([('code_structure', '=', code_structure)], limit=1)
                if existing_structure:
                    _logger.info(f"La structure {code_structure} existe déjà, mise à jour")
                    existing_structure.write({
                        'nom_structure': nom_structure,
                    })
                else:
                    _logger.info(f"Création de la structure {code_structure}")
                    # Créer la structure sans organisation parente pour l'instant
                    self.create({
                        'code_structure': code_structure,
                        'nom_structure': nom_structure,
                    })

            # Mettre à jour les organisations parentes dans une seconde passe
            for structure_data in structures_data:
                code_structure = structure_data.get('code_structure')
                organisations_id = structure_data.get('organisations_id')

                if organisations_id:
                    structure = self.search([('code_structure', '=', code_structure)], limit=1)
                    parent = self.search([('code_structure', '=', organisations_id)], limit=1)

                    if structure and parent:
                        _logger.info(f"Mise à jour de l'organisation parente de {code_structure} vers {organisations_id}")
                        structure.write({
                            'organisation_id': parent.id,
                        })

            return True
        except Exception as e:
            _logger.error(f"Erreur lors du chargement des structures: {e}")
            return False