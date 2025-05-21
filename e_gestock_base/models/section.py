# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import os
import logging

_logger = logging.getLogger(__name__)

class Section(models.Model):
    _name = 'e_gestock.section'
    _description = 'Section de structure'
    _order = 'code_section'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nom_section'

    code_section = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        index=True,
        help="Code unique de la section (ex: 910101, 920301, ...)"
    )

    code_structure = fields.Many2one(
        'e_gestock.structure',
        string='Structure parente',
        required=True,
        tracking=True,
        help="Structure à laquelle appartient cette section"
    )

    nom_section = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
        help="Nom descriptif de la section"
    )

    num_section = fields.Char(
        string='Numéro',
        tracking=True,
        help="Numéro de la section"
    )

    code_gestion = fields.Many2one(
        'e_gestock.type_gestion',
        string='Type de gestion',
        tracking=True,
        help="Type de gestion associé à cette section"
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si cette section est actuellement utilisable"
    )

    _sql_constraints = [
        ('code_section_unique', 'UNIQUE(code_section)', 'Le code de section doit être unique!')
    ]

    @api.constrains('code_section')
    def _check_code_section_format(self):
        """Vérifie que le code de section respecte le format attendu"""
        # Ignorer la vérification si le contexte le demande (lors du chargement des données JSON)
        if self.env.context.get('skip_code_section_check'):
            return

        for record in self:
            if not record.code_section:
                continue

            if not record.code_section.isdigit():
                raise ValidationError(_("Le code de section doit contenir uniquement des chiffres!"))

            if len(record.code_section) != 6:
                raise ValidationError(_("Le code de section doit contenir exactement 6 chiffres!"))

            structure_code = record.code_section[:4]
            if record.code_structure and record.code_structure.code_structure != structure_code:
                raise ValidationError(_("Les 4 premiers chiffres du code section doivent correspondre au code de la structure parente!"))

    @api.onchange('code_structure')
    def _onchange_code_structure(self):
        """Préremplit le début du code section avec le code de la structure"""
        if self.code_structure and not self.code_section:
            self.code_section = self.code_structure.code_structure + "01"

    def name_get(self):
        """Affiche le code et le nom dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.code_section} - {record.nom_section}" if record.code_section else record.nom_section
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par code ou par nom"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code_section', operator, name), ('nom_section', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def load_from_json(self, file_path):
        """Charge les sections depuis un fichier JSON

        Args:
            file_path (str): Chemin relatif du fichier JSON dans le module

        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        try:
            # Construire le chemin absolu du fichier
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(module_path, file_path)

            _logger.info(f"Chargement des sections depuis {full_path}")

            # Vérifier si le fichier existe
            if not os.path.isfile(full_path):
                _logger.error(f"Le fichier {full_path} n'existe pas")
                return False

            # Lire le contenu du fichier JSON
            with open(full_path, 'r', encoding='utf-8') as file:
                sections_data = json.load(file)

            # Créer les sections
            for section_data in sections_data:
                code_section = section_data.get('code_section')
                nom_section = section_data.get('nom_section')
                structure_code = section_data.get('structure_id')

                # Rechercher la structure parente
                structure = self.env['e_gestock.structure'].search([('code_structure', '=', structure_code)], limit=1)
                if not structure:
                    _logger.warning(f"Structure {structure_code} non trouvée pour la section {code_section}")
                    continue

                # Vérifier si la section existe déjà
                existing_section = self.search([('code_section', '=', code_section)], limit=1)
                if existing_section:
                    _logger.info(f"La section {code_section} existe déjà, mise à jour")
                    existing_section.write({
                        'nom_section': nom_section,
                        'code_structure': structure.id,
                    })
                else:
                    _logger.info(f"Création de la section {code_section}")
                    # Désactiver temporairement la contrainte sur le format du code
                    self = self.with_context(skip_code_section_check=True)
                    self.create({
                        'code_section': code_section,
                        'nom_section': nom_section,
                        'code_structure': structure.id,
                    })

            return True
        except Exception as e:
            _logger.error(f"Erreur lors du chargement des sections: {e}")
            return False