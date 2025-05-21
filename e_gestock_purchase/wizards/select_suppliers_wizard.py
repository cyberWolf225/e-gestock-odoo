from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SelectSuppliersWizard(models.TransientModel):
    _name = 'e_gestock.select_suppliers_wizard'
    _description = 'Assistant de sélection des fournisseurs'
    
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande de cotation', 
                               required=True, readonly=True)
    supplier_ids = fields.Many2many('res.partner', string='Fournisseurs', 
                                  domain=[('supplier_rank', '>', 0)], required=True)
    
    code_echeance = fields.Selection([
        ('standard', 'Standard (7 jours)'),
        ('urgent', 'Urgent (3 jours)'),
        ('tres_urgent', 'Très urgent (1 jour)'),
    ], string='Code d\'échéance', default='standard', required=True)
    
    type_achat = fields.Selection([
        ('direct', 'Achat direct'),
        ('appel_offre', 'Appel d\'offres'),
        ('consultation', 'Consultation restreinte')
    ], string='Type d\'achat', default='direct', required=True)
    
    taux_acompte = fields.Float(string='Taux d\'acompte (%)', default=0.0)
    
    date_envoi = fields.Date(string='Date d\'envoi', default=fields.Date.context_today, required=True)
    
    @api.model
    def default_get(self, fields):
        res = super(SelectSuppliersWizard, self).default_get(fields)
        
        # Récupérer l'ID de la demande depuis le contexte
        demande_id = self.env.context.get('default_demande_id')
        if demande_id:
            demande = self.env['e_gestock.demande_cotation'].browse(demande_id)
            if demande.exists():
                res['demande_id'] = demande.id
                
                # Récupérer les fournisseurs présélectionnés
                if demande.supplier_ids:
                    res['supplier_ids'] = [(6, 0, demande.supplier_ids.ids)]
        
        return res
    
    def action_create_supplier_quotations(self):
        """Crée les demandes de cotation pour les fournisseurs sélectionnés"""
        self.ensure_one()
        
        if not self.supplier_ids:
            raise UserError(_("Veuillez sélectionner au moins un fournisseur."))
        
        if self.demande_id.state != 'quotation':
            raise UserError(_("La demande de cotation doit être à l'état 'En attente de cotation'."))
        
        # Créer les demandes de cotation pour chaque fournisseur
        demandes_fournisseur = self.env['e_gestock.demande_cotation_fournisseur']
        for supplier in self.supplier_ids:
            # Vérifier si une demande existe déjà pour ce fournisseur
            existing = self.env['e_gestock.demande_cotation_fournisseur'].search([
                ('demande_id', '=', self.demande_id.id),
                ('supplier_id', '=', supplier.id),
                ('state', 'not in', ['cancelled'])
            ])
            
            if not existing:
                # Créer une nouvelle demande de cotation fournisseur
                vals = {
                    'demande_id': self.demande_id.id,
                    'supplier_id': supplier.id,
                    'date_envoi': self.date_envoi,
                    'code_echeance': self.code_echeance,
                    'type_achat': self.type_achat,
                    'taux_acompte': self.taux_acompte,
                    'state': 'draft'
                }
                demande_fourn = self.env['e_gestock.demande_cotation_fournisseur'].create(vals)
                demandes_fournisseur += demande_fourn
        
        # Mettre à jour les fournisseurs présélectionnés de la demande
        self.demande_id.write({
            'supplier_ids': [(6, 0, self.supplier_ids.ids)]
        })
        
        # Afficher les demandes de cotation fournisseur créées
        if not demandes_fournisseur:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Information'),
                    'message': _('Aucune nouvelle demande de cotation fournisseur créée.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Ouvrir la vue des demandes de cotation fournisseur
        return {
            'name': _('Demandes de cotation fournisseurs'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'e_gestock.demande_cotation_fournisseur',
            'domain': [('id', 'in', demandes_fournisseur.ids)],
            'target': 'current',
        } 