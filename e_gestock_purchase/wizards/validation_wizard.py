from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class ValidationWizard(models.TransientModel):
    _name = 'e_gestock.validation_wizard'
    _description = 'Assistant de validation'

    workflow_id = fields.Many2one('e_gestock.purchase_workflow', string='Workflow d\'achat', required=True)
    validation_type = fields.Selection([
        ('resp_achat', 'Validation responsable achats'),
        ('cmp_request', 'Validation CMP (demande)'),
        ('cmp_choice', 'Validation CMP (choix fournisseur)'),
        ('budget', 'Contrôle budgétaire'),
        ('dcg_dept', 'Validation Chef Département DCG'),
        ('dcg', 'Validation Responsable DCG'),
        ('dgaaf', 'Validation DGAAF'),
        ('dg', 'Validation DG'),
    ], string='Type de validation', required=True)
    
    next_state = fields.Char(string='État suivant', required=True)
    comment = fields.Text(string='Commentaire')
    
    # Pour la validation du responsable achats uniquement
    line_ids = fields.One2many('e_gestock.validation_wizard.line', 'wizard_id', string='Lignes')
    validate_all = fields.Boolean(string='Tout valider', default=True)
    
    @api.onchange('workflow_id', 'validation_type')
    def _onchange_workflow(self):
        """Charge les lignes lors de la validation par le responsable achats"""
        if self.validation_type == 'resp_achat' and self.workflow_id:
            lines = []
            for line in self.workflow_id.line_ids:
                lines.append((0, 0, {
                    'line_id': line.id,
                    'article_id': line.article_id.id,
                    'reference': line.reference,
                    'description': line.description,
                    'quantite': line.quantite,
                    'quantite_accordee': line.quantite,  # Par défaut, on accorde la quantité demandée
                    'to_validate': True,  # Par défaut, toutes les lignes sont à valider
                }))
            self.line_ids = lines
    
    @api.onchange('validate_all')
    def _onchange_validate_all(self):
        """Coche ou décoche toutes les lignes"""
        if self.line_ids:
            for line in self.line_ids:
                line.to_validate = self.validate_all
    
    def action_validate(self):
        """Validation"""
        self.ensure_one()
        
        if not self.workflow_id:
            raise UserError(_("Aucun workflow d'achat sélectionné."))
        
        # Traitement spécifique pour chaque type de validation
        if self.validation_type == 'resp_achat':
            return self._validate_resp_achat()
        elif self.validation_type == 'cmp_request':
            return self._validate_cmp_request()
        elif self.validation_type == 'cmp_choice':
            return self._validate_cmp_choice()
        elif self.validation_type == 'budget':
            return self._validate_budget()
        elif self.validation_type == 'dcg_dept':
            return self._validate_dcg_dept()
        elif self.validation_type == 'dcg':
            return self._validate_dcg()
        elif self.validation_type == 'dgaaf':
            return self._validate_dgaaf()
        elif self.validation_type == 'dg':
            return self._validate_dg()
        else:
            raise UserError(_("Type de validation non reconnu."))
    
    def _validate_resp_achat(self):
        """Validation par le responsable des achats"""
        # Vérifier qu'au moins une ligne est validée
        validated_lines = self.line_ids.filtered(lambda l: l.to_validate)
        if not validated_lines:
            raise UserError(_("Veuillez sélectionner au moins une ligne à valider."))
        
        # Mettre à jour les quantités accordées
        for wiz_line in validated_lines:
            line = self.env['e_gestock.purchase_workflow_line'].browse(wiz_line.line_id)
            line.write({
                'quantite_accordee': wiz_line.quantite_accordee
            })
        
        # Mettre à jour le workflow
        self.workflow_id.write({
            'state': self.next_state,
            'resp_achat_id': self.env.user.id,
            'resp_achat_date': fields.Datetime.now(),
            'resp_achat_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_cmp_request(self):
        """Validation de la demande de cotation par le responsable CMP"""
        self.workflow_id.write({
            'state': self.next_state,
            'cmp_request_validator_id': self.env.user.id,
            'cmp_request_date': fields.Datetime.now(),
            'cmp_request_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_cmp_choice(self):
        """Validation du choix du fournisseur par le responsable CMP"""
        self.workflow_id.write({
            'state': self.next_state,
            'cmp_choice_validator_id': self.env.user.id,
            'cmp_choice_date': fields.Datetime.now(),
            'cmp_choice_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_budget(self):
        """Contrôle budgétaire"""
        self.workflow_id.write({
            'state': self.next_state,
            'budget_validator_id': self.env.user.id,
            'budget_date': fields.Datetime.now(),
            'budget_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_dcg_dept(self):
        """Validation par le chef département DCG"""
        self.workflow_id.write({
            'state': self.next_state,
            'dcg_dept_validator_id': self.env.user.id,
            'dcg_dept_date': fields.Datetime.now(),
            'dcg_dept_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_dcg(self):
        """Validation par le responsable DCG"""
        self.workflow_id.write({
            'state': self.next_state,
            'dcg_validator_id': self.env.user.id,
            'dcg_date': fields.Datetime.now(),
            'dcg_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_dgaaf(self):
        """Validation par le DGAAF"""
        self.workflow_id.write({
            'state': self.next_state,
            'dgaaf_validator_id': self.env.user.id,
            'dgaaf_date': fields.Datetime.now(),
            'dgaaf_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _validate_dg(self):
        """Validation par le DG"""
        self.workflow_id.write({
            'state': self.next_state,
            'dg_validator_id': self.env.user.id,
            'dg_date': fields.Datetime.now(),
            'dg_comment': self.comment,
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
    def action_cancel(self):
        """Annule la validation et ferme l'assistant"""
        return {'type': 'ir.actions.act_window_close'}


class ValidationWizardLine(models.TransientModel):
    _name = 'e_gestock.validation_wizard.line'
    _description = 'Ligne de l\'assistant de validation'
    
    wizard_id = fields.Many2one('e_gestock.validation_wizard', string='Assistant de validation', required=True, ondelete='cascade')
    line_id = fields.Integer(string='ID de la ligne de workflow')
    
    article_id = fields.Many2one('e_gestock.article', string='Article', readonly=True)
    reference = fields.Char(string='Référence', readonly=True)
    description = fields.Text(string='Description', readonly=True)
    quantite = fields.Float(string='Quantité demandée', readonly=True)
    quantite_accordee = fields.Float(string='Quantité accordée', required=True)
    
    to_validate = fields.Boolean(string='À valider', default=True) 