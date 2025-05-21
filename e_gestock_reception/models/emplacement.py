# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class Emplacement(models.Model):
    _name = 'e_gestock.emplacement'
    _description = 'Emplacement de stockage'
    _order = 'code'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True)

    # Hiérarchie des emplacements
    parent_id = fields.Many2one('e_gestock.emplacement', string='Emplacement parent')
    child_ids = fields.One2many('e_gestock.emplacement', 'parent_id', string='Emplacements enfants')

    # Type d'emplacement
    type = fields.Selection([
        ('reception', 'Réception'),
        ('stockage', 'Stockage'),
        ('preparation', 'Préparation'),
        ('expedition', 'Expédition'),
        ('quarantaine', 'Quarantaine'),
        ('rebut', 'Rebut'),
        ('autre', 'Autre')
    ], string='Type', required=True, default='stockage')

    # Caractéristiques
    capacite = fields.Float(string='Capacité (kg)', default=0)
    volume = fields.Float(string='Volume (m³)', default=0)
    hauteur = fields.Float(string='Hauteur (m)', default=0)
    largeur = fields.Float(string='Largeur (m)', default=0)
    profondeur = fields.Float(string='Profondeur (m)', default=0)

    # Contraintes
    temperature_min = fields.Float(string='Température min (°C)')
    temperature_max = fields.Float(string='Température max (°C)')
    humidite_min = fields.Float(string='Humidité min (%)')
    humidite_max = fields.Float(string='Humidité max (%)')

    # Lien avec Odoo
    location_id = fields.Many2one('stock.location', string='Emplacement Odoo')

    # Autres informations
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)

    _sql_constraints = [
        ('code_depot_uniq', 'unique(code, depot_id)', 'Le code de l\'emplacement doit être unique par dépôt!')
    ]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for record in self:
            if not record.parent_id:
                continue

            # Vérifier que le parent est dans le même dépôt
            if record.parent_id.depot_id != record.depot_id:
                raise ValidationError(_("L'emplacement parent doit être dans le même dépôt."))

            # Vérifier qu'il n'y a pas de boucle dans la hiérarchie
            parent = record.parent_id
            while parent:
                if parent.id == record.id:
                    raise ValidationError(_("Boucle détectée dans la hiérarchie des emplacements."))
                parent = parent.parent_id

    def name_get(self):
        result = []
        for record in self:
            if record.parent_id:
                name = f"{record.parent_id.name}/{record.name}"
            else:
                name = f"{record.depot_id.name}/{record.name}"
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        results = super(Emplacement, self).create(vals_list)

        # Création automatique de l'emplacement Odoo correspondant
        for res in results:
            if not res.location_id:
                parent_location = False
                if res.parent_id and res.parent_id.location_id:
                    parent_location = res.parent_id.location_id.id
                else:
                    # Trouver l'emplacement du dépôt
                    depot_location = self.env['stock.location'].search([
                        ('usage', '=', 'internal'),
                        ('e_gestock_depot_id', '=', res.depot_id.id)
                    ], limit=1)

                    if depot_location:
                        parent_location = depot_location.id
                    else:
                        # Utiliser l'emplacement interne par défaut
                        parent_location = self.env.ref('stock.stock_location_stock').id

                location_vals = {
                    'name': res.name,
                    'location_id': parent_location,
                    'usage': 'internal',
                    'e_gestock_emplacement_id': res.id,
                }

                # Adapter le type d'usage en fonction du type d'emplacement
                if res.type == 'quarantaine':
                    location_vals['usage'] = 'inventory'
                elif res.type == 'rebut':
                    location_vals['usage'] = 'inventory'

                location = self.env['stock.location'].create(location_vals)
                res.location_id = location.id

        return results

    def write(self, vals):
        res = super(Emplacement, self).write(vals)

        # Mise à jour de l'emplacement Odoo correspondant
        if 'name' in vals or 'parent_id' in vals:
            for record in self:
                if record.location_id:
                    location_vals = {'name': record.name}

                    if 'parent_id' in vals:
                        if record.parent_id and record.parent_id.location_id:
                            location_vals['location_id'] = record.parent_id.location_id.id
                        else:
                            # Trouver l'emplacement du dépôt
                            depot_location = self.env['stock.location'].search([
                                ('usage', '=', 'internal'),
                                ('e_gestock_depot_id', '=', record.depot_id.id)
                            ], limit=1)

                            if depot_location:
                                location_vals['location_id'] = depot_location.id

                    record.location_id.write(location_vals)

        return res

    @api.model
    def get_suggested_location(self, article_id, depot_id, quantite=1.0):
        """Retourne l'emplacement suggéré pour un article dans un dépôt"""
        article = self.env['e_gestock.article'].browse(article_id)
        if not article:
            return False

        # Vérifier si l'article a un emplacement préféré dans ce dépôt
        article_location = self.env['e_gestock.article.emplacement'].search([
            ('article_id', '=', article_id),
            ('depot_id', '=', depot_id)
        ], limit=1)

        if article_location and article_location.emplacement_id:
            return article_location.emplacement_id

        # Sinon, chercher un emplacement approprié en fonction des caractéristiques de l'article
        domain = [
            ('depot_id', '=', depot_id),
            ('type', '=', 'stockage'),
            ('active', '=', True)
        ]

        # Ajouter des contraintes en fonction des caractéristiques de l'article
        if article.temperature_min or article.temperature_max:
            if article.temperature_min:
                domain.append(('temperature_min', '<=', article.temperature_min))
            if article.temperature_max:
                domain.append(('temperature_max', '>=', article.temperature_max))

        # Trouver les emplacements qui correspondent aux critères
        emplacements = self.search(domain)

        # Si aucun emplacement ne correspond, retourner l'emplacement de réception par défaut
        if not emplacements:
            return self.search([
                ('depot_id', '=', depot_id),
                ('type', '=', 'reception'),
                ('active', '=', True)
            ], limit=1)

        return emplacements[0]


class ArticleEmplacement(models.Model):
    _name = 'e_gestock.article.emplacement'
    _description = 'Emplacement préféré par article'
    _order = 'article_id, depot_id'

    article_id = fields.Many2one('e_gestock.article', string='Article', required=True, ondelete='cascade')
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True)
    emplacement_id = fields.Many2one('e_gestock.emplacement', string='Emplacement préféré', required=True,
                                   domain="[('depot_id', '=', depot_id), ('type', '=', 'stockage')]")

    _sql_constraints = [
        ('article_depot_uniq', 'unique(article_id, depot_id)',
         'Un article ne peut avoir qu\'un seul emplacement préféré par dépôt!')
    ]
