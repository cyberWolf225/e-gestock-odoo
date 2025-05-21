from odoo import models, fields, api, _

class DemandeCotationBase(models.Model):
    """
    Modèle de base pour les demandes de cotation.
    Ce modèle est défini dans e_gestock_base pour éviter les dépendances circulaires
    entre e_gestock_budget et e_gestock_purchase.
    
    La définition complète est dans e_gestock_purchase/models/demande_cotation.py
    """
    _name = 'e_gestock.demande_cotation'
    _description = 'Demande de cotation (Base)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    
    # Champs minimaux nécessaires pour le fonctionnement du module budget
    reference = fields.Char(string='N° Demande', required=True, copy=False, readonly=True, 
                      default=lambda self: _('Nouveau'))
    
    date = fields.Date(string='Date', required=True, 
                       default=fields.Date.context_today, tracking=True)
    
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', 
                                 required=True, tracking=True)
    
    section_id = fields.Many2one('e_gestock.section', string='Section', 
                               domain="[('code_structure', '=', structure_id)]", tracking=True)
    
    famille_id = fields.Many2one('e_gestock.famille', string='Famille', 
                               required=True, tracking=True)
    
    type_gestion_id = fields.Many2one('e_gestock.type_gestion', string='Type de gestion', 
                                    required=True, tracking=True)
    
    # Champ nécessaire pour la méthode _compute_montant_total
    line_ids = fields.One2many('e_gestock.demande_cotation_line', 'demande_id', 
                             string='Lignes', copy=True)
    
    montant_total = fields.Monetary(string='Montant Total', compute='_compute_montant_total', 
                                  store=True, tracking=True)
    
    currency_id = fields.Many2one('res.currency', string='Devise', 
                                default=lambda self: self.env.company.currency_id)
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumise'),
        ('validated', 'Validée'),
        ('budget_checked', 'Budget vérifié'),
        ('approved', 'Approuvée'),
        ('engaged', 'Engagée'),
        ('quotation', 'En attente cotation'),
        ('quoted', 'Cotations reçues'),
        ('selected', 'Fournisseur sélectionné'),
        ('po_generated', 'BC généré'),
        ('delivered', 'Livrée'),
        ('received', 'Réceptionnée'),
        ('cancelled', 'Annulée')
    ], string='État', default='draft', tracking=True, copy=False, index=True)
    
    @api.depends('line_ids.prix_total')
    def _compute_montant_total(self):
        for record in self:
            total = 0.0
            if record.line_ids:
                total = sum(record.line_ids.mapped('prix_total'))
            record.montant_total = total


class DemandeCotationLine(models.Model):
    """
    Modèle de base pour les lignes de demande de cotation.
    """
    _name = 'e_gestock.demande_cotation_line'
    _description = 'Ligne de demande de cotation (Base)'
    
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande', 
                               required=True, ondelete='cascade')
    
    article_id = fields.Many2one('e_gestock.article', string='Article')
    
    designation = fields.Char(string='Désignation', required=True)
    
    quantite = fields.Float(string='Quantité', required=True, default=1.0)
    
    # Champ nécessaire pour le calcul du montant total
    prix_total = fields.Float(string='Prix total', compute='_compute_prix_total', store=True)
    prix_unitaire = fields.Float(string='Prix unitaire', default=0.0)
    
    @api.depends('quantite', 'prix_unitaire')
    def _compute_prix_total(self):
        for line in self:
            line.prix_total = line.quantite * line.prix_unitaire
