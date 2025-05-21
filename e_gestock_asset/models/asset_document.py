# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AssetDocument(models.Model):
    _name = 'e_gestock.asset_document'
    _description = 'Document d\'immobilisation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    
    name = fields.Char(string='Nom', required=True, tracking=True)
    asset_id = fields.Many2one('e_gestock.asset', string='Immobilisation', required=True, tracking=True)
    date = fields.Date(string='Date', required=True, tracking=True, default=fields.Date.today)
    
    # Type de document
    type = fields.Selection([
        ('invoice', 'Facture'),
        ('warranty', 'Garantie'),
        ('manual', 'Manuel'),
        ('certificate', 'Certificat'),
        ('contract', 'Contrat'),
        ('photo', 'Photo'),
        ('other', 'Autre')
    ], string='Type de document', required=True, tracking=True, default='other')
    
    # Document
    document = fields.Binary(string='Document', attachment=True, required=True)
    document_filename = fields.Char(string='Nom du fichier')
    
    # Informations complémentaires
    description = fields.Text(string='Description', tracking=True)
    
    # Dates de validité
    date_expiration = fields.Date(string='Date d\'expiration', tracking=True)
    
    # État
    active = fields.Boolean(string='Actif', default=True, tracking=True)
    
    @api.onchange('type')
    def _onchange_type(self):
        """Met à jour le nom du document en fonction du type sélectionné."""
        if self.type and not self.name:
            type_names = {
                'invoice': _('Facture'),
                'warranty': _('Garantie'),
                'manual': _('Manuel'),
                'certificate': _('Certificat'),
                'contract': _('Contrat'),
                'photo': _('Photo'),
                'other': _('Document')
            }
            self.name = f"{type_names.get(self.type, 'Document')} - {self.asset_id.name if self.asset_id else ''}"
