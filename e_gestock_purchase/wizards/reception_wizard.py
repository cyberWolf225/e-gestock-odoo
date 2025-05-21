from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReceptionWizard(models.TransientModel):
    _name = 'e_gestock.reception_wizard'
    _description = 'Assistant de réception'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande',
                                       related='workflow_id.purchase_order_id', readonly=True)
    
    committee_id = fields.Many2one('e_gestock.reception_committee', string='Comité de réception', required=True,
                                 domain=[('active', '=', True)])
    date_reception = fields.Datetime(string='Date de réception', required=True, default=fields.Datetime.now)
    comment = fields.Text(string='Commentaire')
    
    line_ids = fields.One2many('e_gestock.reception_wizard.line', 'wizard_id', string='Lignes de réception')
    
    @api.onchange('workflow_id')
    def _onchange_workflow(self):
        """Charge les lignes de réception"""
        if self.workflow_id and self.purchase_order_id:
            lines = []
            for line in self.purchase_order_id.order_line:
                lines.append((0, 0, {
                    'line_id': line.id,
                    'article_id': line.article_id.id,
                    'description': line.description,
                    'quantite_commandee': line.product_qty,
                    'quantite_recue': line.product_qty,  # Par défaut, on reçoit la quantité commandée
                }))
            self.line_ids = lines
    
    def action_receive(self):
        """Valide la réception de la commande"""
        self.ensure_one()
        
        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande n'est associé à ce workflow."))
        
        if not self.committee_id:
            raise UserError(_("Veuillez sélectionner un comité de réception."))
        
        if not self.line_ids:
            raise UserError(_("Aucune ligne à réceptionner."))
        
        # Mettre à jour les quantités reçues sur les lignes du bon de commande
        for wiz_line in self.line_ids:
            line = self.env['e_gestock.purchase_order_line'].browse(wiz_line.line_id)
            if line:
                line.write({
                    'qty_received': wiz_line.quantite_recue
                })
        
        # Mettre à jour le bon de commande
        self.purchase_order_id.write({
            'committee_id': self.committee_id.id,
            'reception_validator_id': self.env.user.id,
            'reception_validation_date': self.date_reception,
            'reception_comment': self.comment,
            'state_approbation': 'received',
            'state': 'done'
        })
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': 'received',
            'committee_id': self.committee_id.id,
            'reception_date': self.date_reception,
            'reception_comment': self.comment
        })
        
        # Mettre à jour le stock
        self._update_stock()
        
        return {
            'type': 'ir.actions.act_window_close'
        }
    
    def _update_stock(self):
        """Met à jour les stocks après réception"""
        for wiz_line in self.line_ids:
            if wiz_line.quantite_recue <= 0:
                continue
                
            line = self.env['e_gestock.purchase_order_line'].browse(wiz_line.line_id)
            if not line or not line.article_id:
                continue
                
            # Rechercher l'élément de stock existant
            stock_item = self.env['e_gestock.stock_item'].search([
                ('article_id', '=', line.article_id.id),
                ('depot_id', '=', self.committee_id.structure_id.depot_id.id)
            ], limit=1)
            
            if stock_item:
                # Mettre à jour la quantité
                stock_item.write({
                    'quantite_disponible': stock_item.quantite_disponible + wiz_line.quantite_recue
                })
            else:
                # Créer un nouvel élément de stock
                self.env['e_gestock.stock_item'].create({
                    'article_id': line.article_id.id,
                    'depot_id': self.committee_id.structure_id.depot_id.id,
                    'quantite_disponible': wiz_line.quantite_recue
                })
            
            # Créer un mouvement de stock
            self.env['e_gestock.stock_movement'].create({
                'type': 'reception',
                'date': self.date_reception,
                'depot_destination_id': self.committee_id.structure_id.depot_id.id,
                'responsable_id': self.env.user.id,
                'notes': f"Réception de la commande {self.purchase_order_id.name}",
                'origine': 'purchase',
                'reference_origine': self.purchase_order_id.name,
                'state': 'done',
                'line_ids': [(0, 0, {
                    'article_id': line.article_id.id,
                    'quantite': wiz_line.quantite_recue,
                    'prix_unitaire': line.price_unit
                })]
            })


class ReceptionWizardLine(models.TransientModel):
    _name = 'e_gestock.reception_wizard.line'
    _description = 'Ligne de l\'assistant de réception'
    
    wizard_id = fields.Many2one('e_gestock.reception_wizard', string='Assistant de réception', required=True, ondelete='cascade')
    line_id = fields.Integer(string='ID de la ligne de commande')
    
    article_id = fields.Many2one('e_gestock.article', string='Article', readonly=True)
    description = fields.Text(string='Description', readonly=True)
    quantite_commandee = fields.Float(string='Quantité commandée', readonly=True)
    quantite_recue = fields.Float(string='Quantité reçue', required=True) 