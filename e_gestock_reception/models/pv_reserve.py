from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PVReserve(models.Model):
    _name = 'e_gestock.pv_reserve'
    _description = 'Réserve sur PV de réception'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    pv_id = fields.Many2one('e_gestock.pv_reception', string='PV', required=True, ondelete='cascade')
    line_id = fields.Many2one('e_gestock.reception_line', string='Ligne concernée',
                           domain="[('reception_id', '=', parent.reception_id)]")
    description = fields.Text(string='Description', required=True, tracking=True)
    action_corrective = fields.Text(string='Action corrective', tracking=True)
    date_echeance = fields.Date(string='Date d\'échéance', tracking=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    
    state = fields.Selection([
        ('open', 'Ouverte'),
        ('closed', 'Résolue')
    ], string='État', default='open', tracking=True)
    
    date_resolution = fields.Date(string='Date de résolution', readonly=True)
    commentaire_resolution = fields.Text(string='Commentaire de résolution')
    
    # Pour le suivi
    created_by_id = fields.Many2one('res.users', string='Créée par', default=lambda self: self.env.user, readonly=True)
    
    @api.onchange('line_id')
    def _onchange_line_id(self):
        if self.line_id and not self.description:
            self.description = _("Problème sur l'article %s") % (self.line_id.article_id.design_article or self.line_id.designation or '')
    
    def action_resolve(self):
        """Marquer la réserve comme résolue"""
        self.ensure_one()
        
        if not self.commentaire_resolution:
            raise UserError(_("Veuillez fournir un commentaire sur la résolution."))
        
        self.write({
            'state': 'closed',
            'date_resolution': fields.Date.today(),
        })
        
        return True
    
    def action_reopen(self):
        """Réouvrir une réserve fermée"""
        self.ensure_one()
        
        if self.state != 'closed':
            raise UserError(_("Vous ne pouvez réouvrir qu'une réserve déjà résolue."))
        
        self.write({
            'state': 'open',
            'date_resolution': False,
        })
        
        return True 