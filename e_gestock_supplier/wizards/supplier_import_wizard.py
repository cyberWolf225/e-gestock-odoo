from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import csv
import io
import logging

_logger = logging.getLogger(__name__)

class SupplierImportWizard(models.TransientModel):
    _name = 'e_gestock.supplier_import_wizard'
    _description = 'Assistant d\'importation de fournisseurs'
    
    file = fields.Binary(string='Fichier CSV', required=True)
    file_name = fields.Char(string='Nom du fichier')
    delimiter = fields.Selection([
        (',', 'Virgule (,)'),
        (';', 'Point-virgule (;)'),
        ('\t', 'Tabulation')
    ], string='Délimiteur', default=',', required=True)
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('utf-16', 'UTF-16'),
        ('windows-1252', 'Windows-1252'),
        ('latin-1', 'Latin-1'),
    ], string='Encodage', default='utf-8', required=True)
    category_id = fields.Many2one(
        'e_gestock.supplier_category',
        string='Catégorie par défaut')
    skip_header = fields.Boolean(
        string='Ignorer l\'en-tête', 
        default=True,
        help="Cocher si le fichier contient une ligne d'en-tête")
    
    # Colonnes du fichier
    name_col = fields.Integer(string='Colonne Nom', default=0)
    email_col = fields.Integer(string='Colonne Email', default=1)
    phone_col = fields.Integer(string='Colonne Téléphone', default=2)
    street_col = fields.Integer(string='Colonne Adresse', default=3)
    city_col = fields.Integer(string='Colonne Ville', default=4)
    zip_col = fields.Integer(string='Colonne Code Postal', default=5)
    country_col = fields.Integer(string='Colonne Pays', default=6)
    vat_col = fields.Integer(string='Colonne Numéro TVA', default=7)
    website_col = fields.Integer(string='Colonne Site Web', default=8)
    
    result_log = fields.Text(string='Résultat', readonly=True)
    partner_ids = fields.Many2many(
        'res.partner',
        string='Fournisseurs importés')
    
    total_count = fields.Integer(string='Total de lignes', readonly=True)
    success_count = fields.Integer(string='Lignes importées', readonly=True)
    error_count = fields.Integer(string='Lignes en erreur', readonly=True)
    imported = fields.Boolean(string='Importation effectuée', readonly=True)
    
    def action_import(self):
        """Importer les fournisseurs depuis le fichier CSV"""
        self.ensure_one()
        
        if not self.file:
            raise UserError(_('Veuillez sélectionner un fichier CSV à importer.'))
        
        # Réinitialiser les compteurs
        self.write({
            'result_log': '',
            'partner_ids': [(5, 0, 0)],
            'total_count': 0,
            'success_count': 0,
            'error_count': 0,
            'imported': False,
        })
        
        # Décoder le fichier
        csv_data = base64.b64decode(self.file)
        file_input = io.StringIO(csv_data.decode(self.encoding))
        
        reader = csv.reader(file_input, delimiter=self.delimiter)
        
        if self.skip_header:
            next(reader, None)  # Ignorer la première ligne
        
        partner_obj = self.env['res.partner']
        country_obj = self.env['res.country']
        
        # Variables pour les résultats
        total_lines = 0
        imported_lines = 0
        error_lines = 0
        created_partners = self.env['res.partner']
        results = []
        
        # Traiter chaque ligne
        for row_number, row in enumerate(reader, start=1):
            total_lines += 1
            
            try:
                # Vérifier que la ligne a suffisamment de colonnes
                if len(row) <= max(self.name_col, self.email_col, self.phone_col, 
                                  self.street_col, self.city_col, self.zip_col, 
                                  self.country_col, self.vat_col, self.website_col):
                    raise UserError(_('La ligne %s n\'a pas assez de colonnes') % row_number)
                
                # Extraire les données
                name = row[self.name_col].strip() if self.name_col < len(row) else ''
                email = row[self.email_col].strip() if self.email_col < len(row) else ''
                phone = row[self.phone_col].strip() if self.phone_col < len(row) else ''
                street = row[self.street_col].strip() if self.street_col < len(row) else ''
                city = row[self.city_col].strip() if self.city_col < len(row) else ''
                zip_code = row[self.zip_col].strip() if self.zip_col < len(row) else ''
                country_name = row[self.country_col].strip() if self.country_col < len(row) else ''
                vat = row[self.vat_col].strip() if self.vat_col < len(row) else ''
                website = row[self.website_col].strip() if self.website_col < len(row) else ''
                
                # Validation
                if not name:
                    raise UserError(_('Le nom est obligatoire (ligne %s)') % row_number)
                
                # Rechercher le pays
                country_id = False
                if country_name:
                    country = country_obj.search([
                        '|', ('name', '=ilike', country_name), ('code', '=ilike', country_name)
                    ], limit=1)
                    if country:
                        country_id = country.id
                
                # Créer ou mettre à jour le fournisseur
                partner_values = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'street': street,
                    'city': city,
                    'zip': zip_code,
                    'country_id': country_id,
                    'vat': vat,
                    'website': website,
                    'company_type': 'company',
                    'supplier_rank': 1,
                    'e_gestock_supplier_category_id': self.category_id.id if self.category_id else False,
                }
                
                # Vérifier si le fournisseur existe déjà
                existing_partner = False
                if email:
                    existing_partner = partner_obj.search([('email', '=', email)], limit=1)
                if not existing_partner and name:
                    existing_partner = partner_obj.search([('name', '=', name)], limit=1)
                
                if existing_partner:
                    # Mettre à jour le fournisseur existant
                    existing_partner.write(partner_values)
                    partner = existing_partner
                    results.append(f"Ligne {row_number}: Fournisseur mis à jour - {name}")
                else:
                    # Créer un nouveau fournisseur
                    partner = partner_obj.create(partner_values)
                    results.append(f"Ligne {row_number}: Fournisseur créé - {name}")
                
                created_partners |= partner
                imported_lines += 1
                
            except Exception as e:
                error_lines += 1
                error_msg = str(e).replace('\n', ' ')
                results.append(f"Ligne {row_number}: ERREUR - {error_msg}")
                _logger.error("Erreur lors de l'importation du fournisseur à la ligne %s: %s", row_number, str(e))
        
        # Mettre à jour le résultat
        result_log = '\n'.join(results)
        self.write({
            'result_log': result_log,
            'partner_ids': [(6, 0, created_partners.ids)],
            'total_count': total_lines,
            'success_count': imported_lines,
            'error_count': error_lines,
            'imported': True,
        })
        
        return {
            'name': _('Résultat de l\'importation'),
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.supplier_import_wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        } 