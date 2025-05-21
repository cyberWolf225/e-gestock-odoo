# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import os
import logging

_logger = logging.getLogger(__name__)

class FamilleArticle(models.Model):
    _name = 'e_gestock.famille'
    _description = 'Famille d\'articles'
    _order = 'ref_fam'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'design_fam'

    ref_fam = fields.Char(
        string='Référence',
        required=True,
        tracking=True,
        index=True,
        help="Référence unique de la famille (ex: 610225, 632510, ...)"
    )

    design_fam = fields.Char(
        string='Désignation',
        required=True,
        tracking=True,
        help="Nom de la famille d'articles"
    )

    description = fields.Text(
        string='Description',
        tracking=True,
        help="Description détaillée de la famille d'articles"
    )

    article_ids = fields.One2many(
        'e_gestock.article',
        'famille_id',
        string='Articles',
        help="Articles appartenant à cette famille"
    )

    article_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_article_count',
        store=True,
        help="Nombre d'articles dans cette famille"
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si cette famille est actuellement utilisable"
    )

    date = fields.Date(
        string='Date de création',
        default=fields.Date.context_today,
        tracking=True,
        help="Date de création de la famille d'articles"
    )

    budgetary_account = fields.Boolean(
        string='Compte budgétaire',
        default=True,
        tracking=True,
        help="Indique si cette famille sert de compte budgétaire"
    )

    _sql_constraints = [
        ('ref_fam_unique', 'UNIQUE(ref_fam)', 'La référence de famille doit être unique!')
    ]

    @api.depends('article_ids')
    def _compute_article_count(self):
        """Calcule le nombre d'articles dans cette famille"""
        for record in self:
            record.article_count = len(record.article_ids)

    @api.constrains('ref_fam')
    def _check_ref_fam_format(self):
        """Vérifie que la référence de famille respecte le format attendu"""
        # Ignorer la vérification si le contexte le demande (lors du chargement des données JSON)
        if self.env.context.get('skip_ref_fam_check'):
            return

        for record in self:
            if not record.ref_fam:
                continue

            if not record.ref_fam.isdigit():
                raise ValidationError(_("La référence de famille doit contenir uniquement des chiffres!"))

            if len(record.ref_fam) != 6:
                raise ValidationError(_("La référence de famille doit contenir exactement 6 chiffres!"))

    def get_next_article_sequence(self):
        """Retourne le prochain numéro de séquence pour un nouvel article dans cette famille"""
        last_article = self.env['e_gestock.article'].search([
            ('famille_id', '=', self.id)
        ], order='ref_article desc', limit=1)

        if not last_article:
            return 1

        last_seq = int(last_article.ref_article[-2:])
        return last_seq + 1

    def name_get(self):
        """Affiche la référence et la désignation dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.ref_fam} - {record.design_fam}" if record.ref_fam else record.design_fam
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par référence ou par désignation"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('ref_fam', operator, name), ('design_fam', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def action_view_articles(self):
        """Ouvre la vue des articles de cette famille"""
        self.ensure_one()
        return {
            'name': _('Articles'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.article',
            'view_mode': 'tree,form',
            'domain': [('famille_id', '=', self.id)],
            'context': {'default_famille_id': self.id},
        }

    @api.model
    def load_from_json(self, file_path):
        """Charge les familles d'articles depuis un fichier JSON

        Args:
            file_path (str): Chemin relatif du fichier JSON dans le module

        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        try:
            # Construire le chemin absolu du fichier
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(module_path, file_path)

            _logger.info(f"Chargement des familles d'articles depuis {full_path}")

            # Vérifier si le fichier existe
            if not os.path.isfile(full_path):
                _logger.error(f"Le fichier {full_path} n'existe pas")
                return False

            # Lire le contenu du fichier JSON
            with open(full_path, 'r', encoding='utf-8') as file:
                familles_data = json.load(file)

            # Créer les familles d'articles
            for famille_data in familles_data:
                ref_fam = famille_data.get('ref_fam')
                design_fam = famille_data.get('design_fam')
                budgetary_account = famille_data.get('budgetary_account', True)

                # Vérifier si la famille existe déjà
                existing_famille = self.search([('ref_fam', '=', ref_fam)], limit=1)
                if existing_famille:
                    _logger.info(f"La famille {ref_fam} existe déjà, mise à jour")
                    existing_famille.write({
                        'design_fam': design_fam,
                        'budgetary_account': budgetary_account,
                    })
                else:
                    _logger.info(f"Création de la famille {ref_fam}")
                    # Désactiver temporairement la contrainte sur le format de la référence
                    self = self.with_context(skip_ref_fam_check=True)
                    self.create({
                        'ref_fam': ref_fam,
                        'design_fam': design_fam,
                        'budgetary_account': budgetary_account,
                    })

            return True
        except Exception as e:
            _logger.error(f"Erreur lors du chargement des familles d'articles: {e}")
            return False