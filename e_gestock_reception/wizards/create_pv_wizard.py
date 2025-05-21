from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CreatePVWizard(models.TransientModel):
    _name = 'e_gestock.create_pv_wizard'
    _description = 'Assistant de création de PV'
    
    reception_id = fields.Many2one('e_gestock.reception', string='Réception', required=True, 
                                  domain=[('state', '=', 'comite_validation')])
    comite_id = fields.Many2one('e_gestock.comite_reception', string='Comité', 
                              related='reception_id.comite_reception_id', readonly=True)
    date = fields.Date(string='Date du PV', default=fields.Date.context_today, required=True)
    observation = fields.Text(string='Observations')
    decision = fields.Selection([
        ('accepted', 'Accepté'),
        ('accepted_reserve', 'Accepté avec réserves'),
        ('rejected', 'Rejeté')
    ], string='Décision', required=True, default='accepted')
    
    # Champs pour les réserves
    reserve_ids = fields.One2many('e_gestock.create_pv_wizard_reserve', 'wizard_id', string='Réserves')
    
    @api.onchange('reception_id')
    def _onchange_reception_id(self):
        if self.reception_id:
            # Vérifier s'il existe déjà un PV pour cette réception
            existing_pv = self.env['e_gestock.pv_reception'].search([
                ('reception_id', '=', self.reception_id.id),
                ('state', '!=', 'cancelled')
            ], limit=1)
            
            if existing_pv:
                return {
                    'warning': {
                        'title': _('PV existant'),
                        'message': _('Il existe déjà un procès-verbal pour cette réception. Vous allez créer un PV supplémentaire.')
                    }
                }
    
    @api.onchange('decision')
    def _onchange_decision(self):
        if self.decision != 'accepted_reserve':
            self.reserve_ids = [(5, 0, 0)]  # Supprime toutes les lignes de réserve
    
    def action_create_pv(self):
        """Créer le PV de réception"""
        self.ensure_one()
        
        if self.decision == 'accepted_reserve' and not self.reserve_ids:
            raise UserError(_("Vous devez spécifier au moins une réserve lorsque la décision est 'Accepté avec réserves'."))
        
        # Création du PV
        pv_vals = {
            'reception_id': self.reception_id.id,
            'date': self.date,
            'observation': self.observation,
            'decision': self.decision,
        }
        
        pv = self.env['e_gestock.pv_reception'].create(pv_vals)
        
        # Ajout des réserves si nécessaire
        if self.decision == 'accepted_reserve':
            for reserve in self.reserve_ids:
                self.env['e_gestock.pv_reserve'].create({
                    'pv_id': pv.id,
                    'line_id': reserve.line_id.id,
                    'description': reserve.description,
                    'action_corrective': reserve.action_corrective,
                    'date_echeance': reserve.date_echeance,
                    'responsable_id': reserve.responsable_id.id,
                })
        
        # Générer les signatures pour le président et le secrétaire
        if pv.comite_id.president_id:
            pv.president_signature = pv.comite_id.president_id == self.env.user
            
        if pv.comite_id.secretaire_id:
            pv.secretaire_signature = pv.comite_id.secretaire_id == self.env.user
            
        # Générer les signatures pour les membres du comité
        if pv.comite_id.membre_ids:
            for membre in pv.comite_id.membre_ids:
                self.env['e_gestock.pv_signature'].create({
                    'pv_id': pv.id,
                    'user_id': membre.id,
                    'signed': membre.id == self.env.user.id,
                    'date_signature': fields.Datetime.now() if membre.id == self.env.user.id else False,
                })
            
        # Ouvrir le PV créé
        return {
            'name': _('Procès-verbal'),
            'view_mode': 'form',
            'res_model': 'e_gestock.pv_reception',
            'res_id': pv.id,
            'type': 'ir.actions.act_window',
        }


class CreatePVWizardReserve(models.TransientModel):
    _name = 'e_gestock.create_pv_wizard_reserve'
    _description = 'Ligne de réserve dans l\'assistant de création de PV'
    
    wizard_id = fields.Many2one('e_gestock.create_pv_wizard', string='Assistant', required=True, ondelete='cascade')
    line_id = fields.Many2one('e_gestock.reception_line', string='Ligne concernée', required=True)
    description = fields.Text(string='Description', required=True)
    action_corrective = fields.Text(string='Action corrective')
    date_echeance = fields.Date(string='Date d\'échéance')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    
    @api.onchange('line_id')
    def _onchange_line_id(self):
        if self.line_id:
            if not self.description:
                article_name = self.line_id.article_id.name if self.line_id.article_id else self.line_id.designation
                self.description = _("Problème sur l'article %s") % article_name 