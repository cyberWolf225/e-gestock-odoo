from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockTransferWizard(models.TransientModel):
    _name = 'e_gestock.stock_transfer_wizard'
    _description = 'Assistant de transfert de stock'
    
    depot_source_id = fields.Many2one('e_gestock.depot', string='Dépôt source', required=True)
    depot_destination_id = fields.Many2one('e_gestock.depot', string='Dépôt destination', required=True,
                                        domain="[('id', '!=', depot_source_id)]")
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    notes = fields.Text(string='Notes')
    line_ids = fields.One2many('e_gestock.stock_transfer_wizard.line', 'wizard_id', string='Lignes')
    
    @api.onchange('depot_source_id')
    def _onchange_depot_source(self):
        if self.depot_source_id and self.depot_destination_id and self.depot_source_id == self.depot_destination_id:
            self.depot_destination_id = False
            return {'warning': {'title': _('Attention'), 'message': _('Les dépôts source et destination doivent être différents.')}}
    
    def action_transfer(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError(_("Veuillez ajouter au moins une ligne à transférer."))
            
        if self.depot_source_id == self.depot_destination_id:
            raise UserError(_("Les dépôts source et destination doivent être différents."))
            
        # Créer le mouvement de stock
        movement_vals = {
            'type': 'transfer',
            'date': self.date,
            'depot_source_id': self.depot_source_id.id,
            'depot_destination_id': self.depot_destination_id.id,
            'responsable_id': self.env.user.id,
            'notes': self.notes,
            'origine': 'internal',
        }
        
        movement = self.env['e_gestock.stock_movement'].create(movement_vals)
        
        # Ajouter les lignes
        for line in self.line_ids:
            self.env['e_gestock.stock_movement_line'].create({
                'movement_id': movement.id,
                'article_id': line.article_id.id,
                'quantite': line.quantite,
                'prix_unitaire': line.prix_unitaire,
            })
        
        # Confirmer le mouvement
        movement.action_confirm()
        
        # Ouvrir le mouvement créé
        return {
            'name': _('Transfert de stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.stock_movement',
            'view_mode': 'form',
            'res_id': movement.id,
            'target': 'current',
        }


class StockTransferWizardLine(models.TransientModel):
    _name = 'e_gestock.stock_transfer_wizard.line'
    _description = 'Ligne d\'assistant de transfert de stock'
    
    wizard_id = fields.Many2one('e_gestock.stock_transfer_wizard', string='Assistant', required=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite = fields.Float(string='Quantité', digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.code_unite')
    prix_unitaire = fields.Float(string='Prix unitaire')
    quantite_disponible = fields.Float(string='Disponible', compute='_compute_quantite_disponible')
    
    @api.depends('article_id', 'wizard_id.depot_source_id')
    def _compute_quantite_disponible(self):
        for line in self:
            if line.article_id and line.wizard_id.depot_source_id:
                stock_item = self.env['e_gestock.stock_item'].search([
                    ('article_id', '=', line.article_id.id),
                    ('depot_id', '=', line.wizard_id.depot_source_id.id)
                ], limit=1)
                line.quantite_disponible = stock_item.quantite_disponible if stock_item else 0.0
            else:
                line.quantite_disponible = 0.0
    
    @api.onchange('article_id')
    def _onchange_article_id(self):
        if self.article_id and self.wizard_id.depot_source_id:
            stock_item = self.env['e_gestock.stock_item'].search([
                ('article_id', '=', self.article_id.id),
                ('depot_id', '=', self.wizard_id.depot_source_id.id)
            ], limit=1)
            if stock_item:
                self.prix_unitaire = stock_item.prix_unitaire
    
    @api.constrains('quantite', 'quantite_disponible')
    def _check_quantite(self):
        for line in self:
            if line.quantite <= 0:
                raise UserError(_("La quantité doit être positive."))
            if line.quantite > line.quantite_disponible:
                raise UserError(_("La quantité à transférer pour l'article '%s' ne peut pas dépasser la quantité disponible.") % line.article_id.design_article) 