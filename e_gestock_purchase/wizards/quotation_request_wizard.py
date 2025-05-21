from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QuotationRequestWizard(models.TransientModel):
    _name = 'e_gestock.quotation_request_wizard'
    _description = 'Assistant de demande de cotation'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    
    # Paramètres de la demande de cotation
    type_achat = fields.Selection([
        ('direct', 'Achat direct'),
        ('consultation', 'Consultation restreinte'),
        ('appel_offre', 'Appel d\'offres')
    ], string='Type d\'achat', required=True, default='direct')
    
    taux_acompte = fields.Float(string='Taux d\'acompte (%)', default=0.0)
    
    code_echeance = fields.Selection([
        ('immediate', 'Paiement immédiat'),
        ('30_days', '30 jours'),
        ('60_days', '60 jours'),
        ('90_days', '90 jours')
    ], string='Code échéance', required=True, default='immediate')
    
    delai_echeance = fields.Integer(string='Délai échéance (jours)', default=0)
    
    # Fournisseurs présélectionnés
    supplier_ids = fields.Many2many('res.partner', string='Fournisseurs',
                                  domain=[('supplier_rank', '>', 0)])
    
    @api.onchange('code_echeance')
    def _onchange_code_echeance(self):
        """Met à jour le délai d'échéance en fonction du code"""
        if self.code_echeance == 'immediate':
            self.delai_echeance = 0
        elif self.code_echeance == '30_days':
            self.delai_echeance = 30
        elif self.code_echeance == '60_days':
            self.delai_echeance = 60
        elif self.code_echeance == '90_days':
            self.delai_echeance = 90
    
    def action_create_quotation_request(self):
        """Crée la demande de cotation"""
        self.ensure_one()
        
        # Vérifier que des fournisseurs sont sélectionnés
        if not self.supplier_ids:
            raise UserError(_("Veuillez sélectionner au moins un fournisseur."))
        
        # Créer la demande de cotation
        demande_cotation = self.env['e_gestock.demande_cotation'].create({
            'exercice_id': self.env['e_gestock.exercise'].search([('active', '=', True)], limit=1).id,
            'structure_id': self.workflow_id.structure_id.id,
            'compte_budg_id': self.workflow_id.compte_budgetaire_id.id,
            'gestion_id': self.workflow_id.gestion_id.id,
            'intitule': self.workflow_id.intitule,
            'demandeur_id': self.workflow_id.demandeur_id.id,
            'note': self.workflow_id.notes,
            'supplier_ids': [(6, 0, self.supplier_ids.ids)],
            'state': 'approved',  # Directement en état approuvé car le workflow a déjà été validé
        })
        
        # Créer les lignes de la demande de cotation
        for wf_line in self.workflow_id.line_ids:
            self.env['e_gestock.demande_cotation_line'].create({
                'demande_id': demande_cotation.id,
                'article_id': wf_line.article_id.id,
                'quantite': wf_line.quantite_accordee or wf_line.quantite,
                'prix_unitaire': wf_line.prix_unitaire,
            })
        
        # Lier la demande de cotation au workflow
        self.workflow_id.write({
            'demande_cotation_id': demande_cotation.id,
            'state': 'quotation_request'
        })
        
        # Créer les demandes de cotation fournisseur
        for supplier in self.supplier_ids:
            self.env['e_gestock.demande_cotation_fournisseur'].create({
                'demande_id': demande_cotation.id,
                'supplier_id': supplier.id,
                'state': 'draft',
                'type_achat': self.type_achat,
                'taux_acompte': self.taux_acompte,
                'code_echeance': self.code_echeance,
                'delai_echeance': self.delai_echeance,
            })
        
        return {
            'type': 'ir.actions.act_window_close'
        } 