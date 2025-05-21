from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class ContractRenewalWizard(models.TransientModel):
    _name = 'e_gestock.contract_renewal_wizard'
    _description = 'Assistant de renouvellement de contrat'
    
    contract_id = fields.Many2one(
        'e_gestock.supplier_contract',
        string='Contrat à renouveler',
        required=True,
        readonly=True)
    supplier_id = fields.Many2one(
        related='contract_id.supplier_id',
        string='Fournisseur',
        readonly=True)
    current_start_date = fields.Date(
        related='contract_id.date_debut',
        string='Date de début actuelle',
        readonly=True)
    current_end_date = fields.Date(
        related='contract_id.date_fin',
        string='Date de fin actuelle',
        readonly=True)
    duration_days = fields.Integer(
        string='Durée (jours)',
        compute='_compute_duration',
        readonly=True)
    
    # Nouvelles valeurs
    new_start_date = fields.Date(
        string='Nouvelle date de début',
        required=True,
        default=fields.Date.context_today)
    new_end_date = fields.Date(
        string='Nouvelle date de fin',
        required=True)
    keep_duration = fields.Boolean(
        string='Conserver la durée',
        default=True,
        help="Si coché, la date de fin sera calculée automatiquement en fonction de la durée du contrat d'origine")
    montant = fields.Monetary(
        string='Nouveau montant',
        currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        related='contract_id.currency_id',
        readonly=True)
    remise = fields.Float(
        string='Nouvelle remise (%)',
        digits='Discount')
    update_clauses = fields.Boolean(
        string='Mettre à jour les clauses',
        default=True,
        help="Si coché, les clauses du contrat d'origine seront copiées")
    note = fields.Text(
        string='Notes de renouvellement')
    
    @api.depends('contract_id', 'contract_id.date_debut', 'contract_id.date_fin')
    def _compute_duration(self):
        for wizard in self:
            if wizard.contract_id and wizard.contract_id.date_debut and wizard.contract_id.date_fin:
                wizard.duration_days = (wizard.contract_id.date_fin - wizard.contract_id.date_debut).days
            else:
                wizard.duration_days = 365  # Durée par défaut d'un an
    
    @api.onchange('new_start_date', 'keep_duration', 'duration_days')
    def _onchange_start_date(self):
        if self.new_start_date and self.keep_duration:
            self.new_end_date = self.new_start_date + timedelta(days=self.duration_days)
    
    @api.onchange('contract_id')
    def _onchange_contract(self):
        if self.contract_id:
            self.montant = self.contract_id.montant
            self.remise = self.contract_id.remise
    
    def action_renew(self):
        """Renouveler le contrat"""
        self.ensure_one()
        
        if not self.contract_id:
            raise UserError(_('Aucun contrat à renouveler n\'a été sélectionné.'))
        
        if self.new_start_date < fields.Date.today():
            raise UserError(_('La date de début de renouvellement ne peut pas être dans le passé.'))
        
        if self.new_end_date <= self.new_start_date:
            raise UserError(_('La date de fin doit être postérieure à la date de début.'))
        
        # Créer le nouveau contrat en copiant l'ancien
        values = {
            'name': f"{self.contract_id.name} (Renouvellement)",
            'date_debut': self.new_start_date,
            'date_fin': self.new_end_date,
            'date_signature': False,
            'date_validation': False,
            'state': 'draft',
            'parent_id': self.contract_id.id,
            'renewal_count': 0,
            'validateur_id': False,
            'note': self.note,
        }
        
        # Mettre à jour le montant et la remise si spécifiés
        if self.montant:
            values['montant'] = self.montant
        if self.remise:
            values['remise'] = self.remise
        
        new_contract = self.contract_id.copy(values)
        
        # Gérer les clauses
        if not self.update_clauses:
            new_contract.clause_ids.unlink()
        
        # Mettre à jour le contrat actuel
        self.contract_id.write({
            'state': 'renewed',
            'renewal_count': self.contract_id.renewal_count + 1,
            'active': False
        })
        
        # Ouvrir le nouveau contrat
        return {
            'name': _('Contrat renouvelé'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
            'target': 'current',
        } 