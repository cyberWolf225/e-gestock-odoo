from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CotationLine(models.Model):
    _name = 'e_gestock.cotation_line'
    _description = 'Ligne de cotation fournisseur'
    _order = 'sequence, id'
    
    cotation_id = fields.Many2one('e_gestock.cotation', string='Cotation', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Séquence', default=10)
    
    demande_line_id = fields.Many2one('e_gestock.demande_cotation_line', string='Ligne de demande',
                                    domain="[('demande_id', '=', parent.demande_id)]")
    
    article_id = fields.Many2one('e_gestock.article', string='Article', 
                               related='demande_line_id.article_id', store=True, readonly=True)
    ref_article = fields.Char(string='Réf. article', related='article_id.ref_article', store=True, readonly=True)
    designation = fields.Char(string='Désignation', related='demande_line_id.designation', store=True, readonly=True)
    description = fields.Text(string='Description', related='demande_line_id.description', readonly=True)
    
    quantite = fields.Float(string='Qté demandée', related='demande_line_id.quantite_accordee', readonly=True)
    quantite_a_servir = fields.Float(string='Qté à servir', required=True, default=0.0)
    
    unite_id = fields.Many2one('uom.uom', string='Unité', related='demande_line_id.unite_id', readonly=True, store=True)
    
    prix_unitaire = fields.Float(string='Prix unitaire', required=True, default=0.0)
    remise_ligne = fields.Float(string='Remise ligne (%)', default=0.0)
    montant = fields.Float(string='Montant', compute='_compute_montant', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise', related='cotation_id.currency_id', readonly=True)
    
    echantillon = fields.Binary(string='Échantillon proposé')
    echantillon_filename = fields.Char(string='Nom du fichier échantillon')
    
    state = fields.Selection(related='cotation_id.state', string='État', store=True)
    
    @api.depends('quantite_a_servir', 'prix_unitaire', 'remise_ligne')
    def _compute_montant(self):
        for line in self:
            # Calcul du montant HT avec remise ligne
            montant_avant_remise = line.quantite_a_servir * line.prix_unitaire
            remise = montant_avant_remise * (line.remise_ligne / 100.0)
            line.montant = montant_avant_remise - remise
    
    @api.onchange('demande_line_id')
    def _onchange_demande_line_id(self):
        if self.demande_line_id:
            self.quantite_a_servir = self.demande_line_id.quantite_accordee
    
    @api.constrains('quantite_a_servir', 'prix_unitaire')
    def _check_values(self):
        for line in self:
            if line.quantite_a_servir <= 0:
                raise ValidationError(_("La quantité à servir doit être supérieure à zéro."))
            if line.prix_unitaire < 0:
                raise ValidationError(_("Le prix unitaire ne peut pas être négatif."))
    
    def name_get(self):
        result = []
        for line in self:
            name = f"{line.cotation_id.reference or ''} - {line.designation or ''}"
            result.append((line.id, name))
        return result 