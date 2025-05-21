# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import json
import os

_logger = logging.getLogger(__name__)

class Depot(models.Model):
    _name = 'e_gestock.depot'
    _description = 'Dépôt'
    _order = 'ref_depot'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'design_dep'

    ref_depot = fields.Integer(
        string='Référence',
        required=True,
        tracking=True,
        index=True,
        help="Référence unique du dépôt (ex: 83, 51, ...)"
    )

    design_dep = fields.Char(
        string='Désignation',
        required=True,
        tracking=True,
        help="Nom du dépôt"
    )

    tel_dep = fields.Char(
        string='Téléphone',
        tracking=True,
        help="Numéro de téléphone du dépôt"
    )

    adr_dep = fields.Char(
        string='Adresse',
        tracking=True,
        help="Adresse du dépôt"
    )

    principal = fields.Boolean(
        string='Dépôt principal',
        default=False,
        tracking=True,
        help="Indique s'il s'agit du dépôt principal"
    )

    code_ville = fields.Integer(
        string='Code ville',
        tracking=True,
        help="Code de la ville où se trouve le dépôt"
    )

    structure_ids = fields.One2many(
        'e_gestock.structure',
        'ref_depot',
        string='Structures associées',
        help="Structures liées à ce dépôt"
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Entrepôt Odoo',
        ondelete='restrict',
        copy=False,
        help="Entrepôt Odoo correspondant à ce dépôt"
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Emplacement Odoo',
        ondelete='restrict',
        copy=False,
        help="Emplacement Odoo correspondant à ce dépôt"
    )

    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable',
        tracking=True,
        help="Utilisateur responsable de ce dépôt"
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si ce dépôt est actuellement utilisable"
    )

    structure_count = fields.Integer(
        string='Nombre de structures',
        compute='_compute_structure_count',
        store=True,
        help="Nombre de structures associées à ce dépôt"
    )

    _sql_constraints = [
        ('ref_depot_unique', 'UNIQUE(ref_depot)', 'La référence du dépôt doit être unique!')
    ]

    @api.depends('structure_ids')
    def _compute_structure_count(self):
        """Calcule le nombre de structures associées à ce dépôt"""
        for record in self:
            record.structure_count = len(record.structure_ids)

    @api.constrains('principal')
    def _check_principal_uniqueness(self):
        """Vérifie qu'il n'y a qu'un seul dépôt principal"""
        for record in self:
            if record.principal:
                principal_count = self.search_count([
                    ('principal', '=', True),
                    ('id', '!=', record.id),
                    ('active', '=', True)
                ])
                if principal_count > 0:
                    raise ValidationError(_("Il ne peut y avoir qu'un seul dépôt principal actif!"))

    def _create_warehouse(self):
        """Crée l'entrepôt et l'emplacement correspondants après la sauvegarde complète du dépôt"""
        # Utiliser une nouvelle transaction pour éviter d'affecter la transaction principale
        with self.env.cr.savepoint():
            for depot in self:
                try:
                    # Vérifier si le dépôt existe toujours et n'a pas déjà un entrepôt
                    depot_exists = self.env['e_gestock.depot'].browse(depot.id).exists()
                    if not depot_exists:
                        _logger.warning(f"Le dépôt {depot.id} n'existe plus, impossible de créer l'entrepôt")
                        continue

                    if not depot.warehouse_id and depot.design_dep and depot.ref_depot:
                        code = f"D{depot.ref_depot}"
                        if len(code) > 5:  # Contrainte Odoo: code entrepôt <= 5 caractères
                            code = code[:5]

                        # Vérifier si un entrepôt avec ce code existe déjà
                        existing_warehouse = self.env['stock.warehouse'].sudo().search([('code', '=', code)], limit=1)
                        if existing_warehouse:
                            _logger.info(f"Un entrepôt avec le code {code} existe déjà, utilisation de celui-ci")
                            self.env['e_gestock.depot'].browse(depot.id).write({
                                'warehouse_id': existing_warehouse.id,
                                'location_id': existing_warehouse.lot_stock_id.id if existing_warehouse.lot_stock_id else False
                            })
                            continue

                        warehouse_vals = {
                            'name': depot.design_dep,
                            'code': code,
                            'company_id': self.env.company.id,
                        }
                        warehouse = self.env['stock.warehouse'].sudo().create(warehouse_vals)
                        if warehouse and warehouse.id:
                            self.env['e_gestock.depot'].browse(depot.id).write({
                                'warehouse_id': warehouse.id,
                                'location_id': warehouse.lot_stock_id.id if warehouse.lot_stock_id else False
                            })
                except Exception as e:
                    _logger.error(f"Erreur lors de la création de l'entrepôt pour le dépôt {depot.id if depot else 'inconnu'}: {e}")
                    # Ne pas propager l'erreur pour éviter d'annuler la transaction principale

    @api.model_create_multi
    def create(self, vals_list):
        """Création du dépôt sans création immédiate de l'entrepôt pour éviter les erreurs"""
        depots = super(Depot, self).create(vals_list)

        # Programmer la création de l'entrepôt pour après la transaction
        # Utiliser une fonction lambda pour éviter les problèmes de référence
        if depots:
            self.env.cr.postcommit.add(lambda: self.browse(depots.ids)._create_warehouse())

        return depots

    def name_get(self):
        """Affiche la référence et la désignation dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.ref_depot} - {record.design_dep}" if record.ref_depot else record.design_dep
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par référence ou par désignation"""
        args = args or []
        domain = []
        if name:
            if name.isdigit():
                domain = [('ref_depot', '=', int(name))]
            else:
                domain = [('design_dep', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def action_view_warehouse(self):
        """Ouvre la vue de l'entrepôt associé"""
        self.ensure_one()
        if not self.warehouse_id:
            # Créer l'entrepôt s'il n'existe pas encore
            self._create_warehouse()

        if self.warehouse_id:
            return {
                'name': _('Entrepôt'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.warehouse',
                'view_mode': 'form',
                'res_id': self.warehouse_id.id,
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Information'),
                'message': _('Aucun entrepôt associé à ce dépôt.'),
                'sticky': False,
            }
        }

    @api.model
    def load_from_json(self, file_path):
        """Charge les dépôts depuis un fichier JSON

        Args:
            file_path (str): Chemin relatif du fichier JSON dans le module

        Returns:
            bool: True si le chargement a réussi, False sinon
        """
        try:
            # Construire le chemin absolu du fichier
            module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(module_path, file_path)

            _logger.info(f"Chargement des dépôts depuis {full_path}")

            # Vérifier si le fichier existe
            if not os.path.isfile(full_path):
                _logger.error(f"Le fichier {full_path} n'existe pas")
                return False

            # Lire le contenu du fichier JSON
            with open(full_path, 'r', encoding='utf-8') as file:
                depots_data = json.load(file)

            # Créer les dépôts
            for depot_data in depots_data:
                code_depot = depot_data.get('code_depot')
                nom_depot = depot_data.get('nom_depot')
                structure_code = depot_data.get('structure_id')
                responsable_id = depot_data.get('responsable_id', 1)  # Par défaut admin

                # Rechercher la structure associée
                structure = None
                if structure_code:
                    structure = self.env['e_gestock.structure'].search([('code_structure', '=', structure_code)], limit=1)
                    if not structure:
                        _logger.warning(f"Structure {structure_code} non trouvée pour le dépôt {code_depot}")

                # Convertir le code_depot en entier pour ref_depot
                try:
                    ref_depot = int(code_depot.replace('DEP-', ''))
                except (ValueError, AttributeError):
                    ref_depot = len(self.search([])) + 1
                    _logger.warning(f"Code dépôt {code_depot} non convertible en entier, utilisation de {ref_depot}")

                # Vérifier si le dépôt existe déjà
                existing_depot = self.search([('ref_depot', '=', ref_depot)], limit=1)
                if existing_depot:
                    _logger.info(f"Le dépôt {code_depot} existe déjà, mise à jour")
                    existing_depot.write({
                        'design_dep': nom_depot,
                        'responsable_id': responsable_id,
                    })
                else:
                    _logger.info(f"Création du dépôt {code_depot}")
                    self.create({
                        'ref_depot': ref_depot,
                        'design_dep': nom_depot,
                        'responsable_id': responsable_id,
                    })

            return True
        except Exception as e:
            _logger.error(f"Erreur lors du chargement des dépôts: {e}")
            return False