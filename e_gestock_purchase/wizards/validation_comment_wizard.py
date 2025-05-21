from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ValidationCommentWizard(models.TransientModel):
    _name = 'e_gestock.validation_comment_wizard'
    _description = 'Assistant de validation avec commentaire'

    purchase_order_id = fields.Many2one('e_gestock.purchase_order', string='Bon de commande', required=True)
    validation_type = fields.Selection([
        ('cmp', 'Validation CMP'),
        ('budget', 'Validation Contrôle Budgétaire'),
        ('dcg_dept', 'Validation Chef Département DCG'),
        ('dcg', 'Validation Responsable DCG'),
        ('dgaaf', 'Validation DGAAF'),
        ('dg', 'Validation DG'),
        ('reception', 'Validation Réception')
    ], string='Type de validation', required=True)
    comment = fields.Text(string='Commentaire')
    next_state = fields.Char(string='État suivant', required=True)

    def action_validate(self):
        """Valide le bon de commande avec le commentaire"""
        self.ensure_one()

        if not self.purchase_order_id:
            raise UserError(_("Aucun bon de commande sélectionné."))

        # Mettre à jour l'état et le commentaire en fonction du type de validation
        vals = {
            'state_approbation': self.next_state
        }

        # Obtenir l'utilisateur actuel et la date/heure actuelle
        current_user = self.env.user
        current_datetime = fields.Datetime.now()

        if self.validation_type == 'cmp':
            vals['cmp_comment'] = self.comment
            vals['cmp_validator_id'] = current_user.id
            vals['cmp_validation_date'] = current_datetime
        elif self.validation_type == 'budget':
            vals['budget_comment'] = self.comment
            vals['budget_validator_id'] = current_user.id
            vals['budget_validation_date'] = current_datetime
        elif self.validation_type == 'dcg_dept':
            vals['dcg_dept_comment'] = self.comment
            vals['dcg_dept_validator_id'] = current_user.id
            vals['dcg_dept_validation_date'] = current_datetime
        elif self.validation_type == 'dcg':
            vals['dcg_comment'] = self.comment
            vals['dcg_validator_id'] = current_user.id
            vals['dcg_validation_date'] = current_datetime
        elif self.validation_type == 'dgaaf':
            vals['dgaaf_comment'] = self.comment
            vals['dgaaf_validator_id'] = current_user.id
            vals['dgaaf_validation_date'] = current_datetime
        elif self.validation_type == 'dg':
            vals['dg_comment'] = self.comment
            vals['dg_validator_id'] = current_user.id
            vals['dg_validation_date'] = current_datetime
        elif self.validation_type == 'reception':
            vals['reception_comment'] = self.comment
            vals['reception_validator_id'] = current_user.id
            vals['reception_validation_date'] = current_datetime

        self.purchase_order_id.write(vals)

        # Message dans le chatter
        validation_name = dict(self._fields['validation_type'].selection).get(self.validation_type)
        message = _("%s effectuée.") % validation_name
        if self.comment:
            message += _(" Commentaire: %s") % self.comment

        self.purchase_order_id.message_post(
            body=message,
            subtype_id=self.env.ref('mail.mt_note').id
        )

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Annule la validation"""
        return {'type': 'ir.actions.act_window_close'}
