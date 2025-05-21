# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PerdiemBeneficiary(models.Model):
    _name = 'e_gestock.perdiem.beneficiary'
    _description = 'Bénéficiaire de Perdiem'
    _order = 'id'
    
    name = fields.Char(string='Nom et prénoms', required=True)
    montant = fields.Float(string='Montant', required=True)
    perdiem_id = fields.Many2one('e_gestock.perdiem', string='Perdiem', required=True, ondelete='cascade')
    
    # Pièce jointe
    piece = fields.Binary(string='Pièce justificative')
    piece_name = fields.Char(string='Nom du fichier')
    
    # Champs calculés
    currency_id = fields.Many2one('res.currency', string='Devise', 
                                 default=lambda self: self.env.company.currency_id)
    
    @api.constrains('montant')
    def _check_montant(self):
        """Vérifie que le montant est positif."""
        for record in self:
            if record.montant <= 0:
                raise ValidationError(_("Le montant doit être supérieur à zéro."))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de la méthode create pour mettre à jour le montant total du perdiem."""
        res = super(PerdiemBeneficiary, self).create(vals_list)
        # Mise à jour du montant total du perdiem
        perdiem_ids = set(rec.perdiem_id.id for rec in res)
        for perdiem_id in perdiem_ids:
            self.env['e_gestock.perdiem'].browse(perdiem_id)._compute_montant_total()
        return res
    
    def write(self, vals):
        """Surcharge de la méthode write pour mettre à jour le montant total du perdiem."""
        res = super(PerdiemBeneficiary, self).write(vals)
        # Mise à jour du montant total du perdiem si le montant a changé
        if 'montant' in vals:
            perdiem_ids = set(rec.perdiem_id.id for rec in self)
            for perdiem_id in perdiem_ids:
                self.env['e_gestock.perdiem'].browse(perdiem_id)._compute_montant_total()
        return res
    
    def unlink(self):
        """Surcharge de la méthode unlink pour mettre à jour le montant total du perdiem."""
        perdiem_ids = set(rec.perdiem_id.id for rec in self)
        res = super(PerdiemBeneficiary, self).unlink()
        # Mise à jour du montant total du perdiem
        for perdiem_id in perdiem_ids:
            perdiem = self.env['e_gestock.perdiem'].browse(perdiem_id)
            if perdiem.exists():
                perdiem._compute_montant_total()
        return res
