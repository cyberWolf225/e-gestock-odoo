# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import uuid
import logging

_logger = logging.getLogger(__name__)

class Article(models.Model):
    _name = 'e_gestock.article'
    _description = 'Article E-Gestock'
    _order = 'ref_article'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'design_article'

    ref_article = fields.Char(
        string='Référence',
        required=False,  # Changé de True à False pour permettre la création sans référence
        tracking=True,
        index=True,
        readonly=True,
        help="Référence unique de l'article (généré automatiquement)"
    )

    design_article = fields.Char(
        string='Désignation',
        required=True,
        tracking=True,
        help="Nom de l'article"
    )

    famille_id = fields.Many2one(
        'e_gestock.famille',
        string='Famille',
        required=True,
        tracking=True,
        help="Famille à laquelle appartient cet article"
    )

    ref_fam = fields.Char(
        related='famille_id.ref_fam',
        string='Référence famille',
        store=True,
        readonly=True,
        help="Référence de la famille d'articles"
    )

    categorie_id = fields.Many2one(
        'e_gestock.categorie',
        string='Catégorie',
        tracking=True,
        help="Catégorie de l'article"
    )

    type_articles_id = fields.Integer(
        string='Type d\'article',
        tracking=True,
        help="Type d'article"
    )

    code_unite = fields.Many2one(
        'uom.uom',
        string='Unité de mesure',
        tracking=True,
        required=True,
        help="Unité de mesure de l'article"
    )

    # Temporairement commenté car le module account n'est pas installé
    # ref_taxe = fields.Many2one(
    #     'account.tax',
    #     string='Taxe applicable',
    #     tracking=True,
    #     help="Taxe applicable à l'article"
    # )

    # Champ temporaire pour remplacer ref_taxe
    ref_taxe_name = fields.Char(
        string='Taxe applicable',
        tracking=True,
        help="Nom de la taxe applicable à l'article (temporaire)"
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produit Odoo',
        ondelete='set null',
        copy=False,
        help="Produit Odoo correspondant à cet article"
    )

    flag_actif = fields.Boolean(
        string='Actif',
        default=True,
        tracking=True,
        help="Indique si cet article est actuellement utilisable"
    )

    qr_code = fields.Char(
        string='Code QR',
        readonly=True,
        copy=False,
        help="Code QR unique pour l'article (pour l'application mobile)"
    )

    image = fields.Binary(
        related='product_id.image_1920',
        string='Image',
        readonly=True,
        help="Image de l'article"
    )

    description = fields.Text(
        string='Description',
        tracking=True,
        help="Description détaillée de l'article"
    )

    created_at = fields.Datetime(
        string='Date de création',
        readonly=True,
        default=fields.Datetime.now,
        help="Date de création de l'article"
    )

    updated_at = fields.Datetime(
        string='Date de mise à jour',
        readonly=True,
        help="Date de dernière mise à jour de l'article"
    )

    prix_achat = fields.Float(
        string='Prix d\'achat',
        digits='Product Price',
        tracking=True,
        help="Prix d'achat de l'article"
    )

    _sql_constraints = [
        ('ref_article_unique', 'UNIQUE(ref_article)', 'La référence de l\'article doit être unique!')
    ]

    def _create_or_update_product(self):
        """Crée ou met à jour le produit Odoo associé après la sauvegarde de l'article"""
        for article in self:
            # Vérifier si le produit existe déjà
            if article.product_id:
                # Mettre à jour le produit existant
                product_vals = {
                    'name': article.design_article,
                    'default_code': article.ref_article,
                    'uom_id': article.code_unite.id,
                    'uom_po_id': article.code_unite.id,
                    'description': article.description or False,
                    'active': article.flag_actif,
                }
                # Temporairement commenté car le champ ref_taxe n'est plus utilisé
                # if article.ref_taxe:
                #     product_vals['taxes_id'] = [(6, 0, [article.ref_taxe.id])]
                try:
                    article.product_id.write(product_vals)
                except Exception as e:
                    _logger.error(f"Erreur lors de la mise à jour du produit pour l'article {article.ref_article}: {e}")
            else:
                # Créer un nouveau produit
                try:
                    product_vals = {
                        'name': article.design_article,
                        'default_code': article.ref_article,
                        'type': 'consu',  # 'consu' est la valeur correcte pour les biens dans Odoo 18
                        'uom_id': article.code_unite.id,
                        'uom_po_id': article.code_unite.id,
                        'description': article.description or False,
                        'active': article.flag_actif,
                    }
                    # Temporairement commenté car le champ ref_taxe n'est plus utilisé
                    # if article.ref_taxe:
                    #     product_vals['taxes_id'] = [(6, 0, [article.ref_taxe.id])]

                    product = self.env['product.product'].sudo().create(product_vals)
                    if product and product.id:
                        # Mise à jour directe via SQL pour éviter les boucles de récursion
                        self.env.cr.execute(
                            "UPDATE e_gestock_article SET product_id = %s WHERE id = %s",
                            (product.id, article.id)
                        )
                except Exception as e:
                    _logger.error(f"Erreur lors de la création du produit pour l'article {article.ref_article}: {e}")

    @api.model_create_multi
    def create(self, vals_list):
        """Génère automatiquement la référence de l'article"""
        articles_to_create = []
        for vals in vals_list:
            # Génération de la référence de l'article si non fournie
            if not vals.get('ref_article'):
                try:
                    # Vérifier si la famille est spécifiée
                    famille_id = vals.get('famille_id')
                    if not famille_id:
                        raise ValidationError(_("Veuillez sélectionner une famille d'articles pour générer la référence."))

                    famille = self.env['e_gestock.famille'].browse(famille_id)
                    if not famille.exists():
                        raise ValidationError(_("La famille d'articles sélectionnée n'existe pas."))

                    # Obtenir le prochain numéro de séquence
                    next_seq = famille.get_next_article_sequence()
                    # Formater la référence: ref_fam + numéro séquentiel sur 2 chiffres
                    vals['ref_article'] = famille.ref_fam + str(next_seq).zfill(2)
                    _logger.info(f"Référence article générée: {vals['ref_article']} pour la famille {famille.ref_fam}")
                except Exception as e:
                    _logger.error(f"Erreur lors de la génération de la référence article: {e}")
                    # Générer une référence aléatoire en cas d'erreur
                    vals['ref_article'] = str(uuid.uuid4())[:8].upper()
                    _logger.info(f"Référence aléatoire générée: {vals['ref_article']}")

            # Si la référence est toujours vide, générer une référence aléatoire
            if not vals.get('ref_article'):
                vals['ref_article'] = f"TMP-{str(uuid.uuid4())[:8].upper()}"
                _logger.info(f"Référence temporaire générée: {vals['ref_article']}")

            # Génération du code QR
            if not vals.get('qr_code'):
                vals['qr_code'] = str(uuid.uuid4())

            # Création de l'article sans le produit associé pour éviter les erreurs
            vals['product_id'] = False  # Force à False pour éviter les erreurs
            articles_to_create.append(vals)

        articles = super(Article, self).create(articles_to_create)

        # Planifier la création du produit après la transaction
        for article in articles:
            self.env.cr.postcommit.add(article._create_or_update_product)

        return articles

    def write(self, vals):
        """Met à jour l'article et planifie la mise à jour du produit Odoo associé"""
        # Mise à jour de la date de modification
        vals['updated_at'] = fields.Datetime.now()

        # Exécution de la mise à jour
        res = super(Article, self).write(vals)

        # Planifier la mise à jour du produit après la transaction si des champs pertinents ont changé
        important_fields = ['design_article', 'ref_article', 'code_unite', 'ref_taxe_name', 'description', 'flag_actif']
        if any(field in vals for field in important_fields):
            self.env.cr.postcommit.add(self._create_or_update_product)

        return res

    def unlink(self):
        """Supprime également le produit Odoo associé"""
        products = self.mapped('product_id')
        res = super(Article, self).unlink()
        if products:
            try:
                products.unlink()
            except Exception as e:
                _logger.error(f"Erreur lors de la suppression des produits: {e}")
        return res

    def name_get(self):
        """Affiche la référence et la désignation dans les listes déroulantes"""
        result = []
        for record in self:
            name = f"{record.ref_article} - {record.design_article}" if record.ref_article else record.design_article
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Permet de rechercher par référence ou par désignation"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('ref_article', operator, name), ('design_article', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.onchange('famille_id')
    def _onchange_famille_id(self):
        """Génère une référence temporaire lorsque la famille est sélectionnée"""
        if self.famille_id and not self._origin.id:
            try:
                # Obtenir le prochain numéro de séquence
                next_seq = self.famille_id.get_next_article_sequence()
                # Formater la référence: ref_fam + numéro séquentiel sur 2 chiffres
                self.ref_article = self.famille_id.ref_fam + str(next_seq).zfill(2)
                _logger.info(f"Référence article générée (onchange): {self.ref_article} pour la famille {self.famille_id.ref_fam}")
            except Exception as e:
                _logger.error(f"Erreur lors de la génération de la référence article (onchange): {e}")
                # Ne pas générer de référence aléatoire ici, cela sera fait dans la méthode create si nécessaire

    def action_view_product(self):
        """Ouvre la vue du produit Odoo associé"""
        self.ensure_one()

        if not self.product_id:
            # Créer le produit s'il n'existe pas encore
            self._create_or_update_product()
            # Rafraîchir l'enregistrement pour voir le nouveau produit
            self.env.cr.execute("SELECT product_id FROM e_gestock_article WHERE id = %s", (self.id,))
            product_id = self.env.cr.fetchone()
            if product_id and product_id[0]:
                product = self.env['product.product'].browse(product_id[0])
                if product.exists():
                    return {
                        'name': _('Produit'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'product.product',
                        'view_mode': 'form',
                        'res_id': product.id,
                    }

            # Si pas de produit, afficher une notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Information'),
                    'message': _('Impossible de créer ou d\'accéder au produit associé.'),
                    'sticky': False,
                }
            }

        # Ouvrir le produit existant
        return {
            'name': _('Produit'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'form',
            'res_id': self.product_id.id,
        }

    def toggle_active(self):
        """Inverse la valeur du champ flag_actif (utilisé pour l'archivage)"""
        for record in self:
            record.flag_actif = not record.flag_actif
            # La mise à jour du produit se fera via postcommit hook