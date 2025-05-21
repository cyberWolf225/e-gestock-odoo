from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PVSignature(models.Model):
    _name = 'e_gestock.pv_signature'
    _description = 'Signature du PV de réception'
    
    pv_id = fields.Many2one('e_gestock.pv_reception', string='PV', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Membre', required=True)
    signed = fields.Boolean(string='Signé', default=False)
    date_signature = fields.Datetime(string='Date signature', readonly=True)
    comments = fields.Text(string='Commentaires')
    
    @api.constrains('user_id')
    def _check_membre_comite(self):
        for signature in self:
            if signature.pv_id.comite_id and signature.pv_id.comite_id.membre_ids:
                if signature.user_id not in signature.pv_id.comite_id.membre_ids:
                    raise ValidationError(_("L'utilisateur doit être membre du comité de réception."))
    
    @api.onchange('signed')
    def _onchange_signed(self):
        if self.signed and not self.date_signature:
            self.date_signature = fields.Datetime.now()
    
    def action_sign(self):
        """Signer le PV en tant que membre"""
        self.ensure_one()
        
        if self.env.user != self.user_id:
            raise UserError(_("Vous ne pouvez signer que votre propre ligne."))
        
        if self.signed:
            raise UserError(_("Vous avez déjà signé ce PV."))
        
        self.write({
            'signed': True,
            'date_signature': fields.Datetime.now(),
        })
        
        return True 