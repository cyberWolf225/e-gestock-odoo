from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DemandeCotationLine(models.Model):
    _name = 'e_gestock.demande_cotation_line'
    _description = 'Ligne de demande de cotation'
    _order = 'sequence, id'

    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Séquence', default=10)
    article_id = fields.Many2one('e_gestock.article', string='Article',
                                domain="[('famille_id', '=', parent.compte_budg_id)]")
    ref_article = fields.Char(related='article_id.ref_article', string='Réf. article', store=True)
    designation = fields.Char(string='Désignation article', required=True)
    description = fields.Text(string='Description article')

    quantite = fields.Float(string='Qté demandée', required=True, default=1.0)
    quantite_accordee = fields.Float(string='Qté accordée', default=0.0)
    unite_id = fields.Many2one('uom.uom', string='Unité')

    prix_unitaire_estime = fields.Float(string='Prix unitaire estimé', compute='_compute_prix_unitaire_estime',
                                      readonly=True, store=True)
    prix_unitaire = fields.Float(string='Prix unitaire', digits='Product Price')
    montant_estime = fields.Float(string='Montant estimé', compute='_compute_montant_estime', store=True)

    echantillon = fields.Binary(string='Échantillon')
    echantillon_filename = fields.Char(string='Nom du fichier')
    is_selected = fields.Boolean(string='Sélectionnée', default=False,
                               help="Sélection par le responsable des achats lors de la validation")

    state = fields.Selection(related='demande_id.state', string='État', store=True)

    # Champ pour suivre les cotations liées à cette ligne
    cotation_line_ids = fields.One2many('e_gestock.cotation_line', 'demande_line_id', string='Lignes de cotation')

    @api.onchange('article_id')
    def _onchange_article_id(self):
        if self.article_id:
            self.designation = self.article_id.design_article
            self.unite_id = self.article_id.code_unite
            # Utiliser le prix d'achat de l'article s'il existe, sinon utiliser le prix estimé
            if hasattr(self.article_id, 'prix_achat') and self.article_id.prix_achat:
                self.prix_unitaire = self.article_id.prix_achat
            else:
                self.prix_unitaire = self.prix_unitaire_estime

    @api.depends('article_id')
    def _compute_prix_unitaire_estime(self):
        for line in self:
            prix = 0.0
            if line.article_id and line.article_id.product_id:
                # Utiliser le prix standard du produit Odoo lié
                prix = line.article_id.product_id.standard_price
            line.prix_unitaire_estime = prix

    @api.depends('quantite', 'prix_unitaire_estime')
    def _compute_montant_estime(self):
        for line in self:
            line.montant_estime = line.quantite * line.prix_unitaire_estime

    @api.constrains('article_id', 'designation')
    def _check_article_or_designation(self):
        for line in self:
            if line.demande_id.is_stockable and not line.article_id:
                raise ValidationError(_("Pour une demande stockable, vous devez sélectionner un article."))
            if not line.designation:
                raise ValidationError(_("La désignation est obligatoire."))

    @api.constrains('quantite', 'quantite_accordee')
    def _check_quantities(self):
        for line in self:
            if line.quantite <= 0:
                raise ValidationError(_("La quantité demandée doit être supérieure à zéro."))
            if line.is_selected and line.quantite_accordee <= 0:
                raise ValidationError(_("Pour les lignes sélectionnées, la quantité accordée doit être supérieure à zéro."))
            if line.quantite_accordee > line.quantite:
                raise ValidationError(_("La quantité accordée ne peut pas dépasser la quantité demandée."))

    def name_get(self):
        """Personnalisation de l'affichage du nom des lignes"""
        result = []
        for line in self:
            name = f"{line.demande_id.reference or ''} - {line.article_id.ref_article or ''} {line.designation or ''}"
            result.append((line.id, name))
        return result