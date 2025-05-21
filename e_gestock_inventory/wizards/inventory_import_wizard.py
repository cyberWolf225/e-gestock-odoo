from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import csv
import io

class InventoryImportWizard(models.TransientModel):
    _name = 'e_gestock.inventory.import.wizard'
    _description = 'Assistant d\'import d\'inventaire'
    
    inventory_id = fields.Many2one('e_gestock.inventory', string='Inventaire', required=True,
                                 domain=[('state', '=', 'in_progress')])
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', related='inventory_id.depot_id', readonly=True)
    file = fields.Binary(string='Fichier CSV/Excel', required=True)
    filename = fields.Char(string='Nom du fichier')
    delimiter = fields.Selection([
        (',', 'Virgule (,)'),
        (';', 'Point-virgule (;)'),
        ('\t', 'Tabulation (\\t)')
    ], string='Délimiteur', default=';')
    skip_header = fields.Boolean(string='Ignorer l\'entête', default=True)
    
    def action_import(self):
        self.ensure_one()
        
        if self.inventory_id.state != 'in_progress':
            raise UserError(_("L'inventaire doit être à l'état 'En cours' pour importer des données."))
        
        try:
            # Décoder le fichier
            data = base64.b64decode(self.file)
            file_input = io.StringIO(data.decode('utf-8'))
            file_content = csv.reader(file_input, delimiter=self.delimiter)
            
            # Ignorer l'entête si nécessaire
            if self.skip_header:
                next(file_content)
            
            # Parcourir les lignes
            for row_num, row in enumerate(file_content, start=1):
                if len(row) < 2:
                    raise UserError(_("La ligne %s ne contient pas assez de colonnes.") % row_num)
                
                try:
                    # Colonne 1: Référence article
                    article_ref = row[0].strip()
                    # Colonne 2: Quantité réelle
                    quantity = float(row[1].strip().replace(',', '.'))
                    
                    # Rechercher l'article
                    article = self.env['e_gestock.article'].search([('ref_article', '=', article_ref)], limit=1)
                    if not article:
                        raise UserError(_("L'article avec la référence '%s' n'existe pas.") % article_ref)
                    
                    # Rechercher la ligne d'inventaire
                    inventory_line = self.env['e_gestock.inventory_line'].search([
                        ('inventory_id', '=', self.inventory_id.id),
                        ('article_id', '=', article.id)
                    ], limit=1)
                    
                    if inventory_line:
                        # Mettre à jour la ligne existante
                        inventory_line.write({
                            'quantite_reelle': quantity,
                            'is_counted': True
                        })
                    else:
                        # Créer une nouvelle ligne
                        self.env['e_gestock.inventory_line'].create({
                            'inventory_id': self.inventory_id.id,
                            'article_id': article.id,
                            'quantite_theorique': 0.0,  # Pas de stock existant
                            'quantite_reelle': quantity,
                            'is_counted': True
                        })
                        
                except ValueError:
                    raise UserError(_("La ligne %s contient une quantité invalide.") % row_num)
                except Exception as e:
                    raise UserError(_("Erreur à la ligne %s: %s") % (row_num, str(e)))
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'e_gestock.inventory',
                'view_mode': 'form',
                'res_id': self.inventory_id.id,
                'target': 'current',
                'context': {'import_successful': True}
            }
            
        except Exception as e:
            raise UserError(_("Erreur lors de l'import: %s") % str(e))


class InventoryAddArticleWizard(models.TransientModel):
    _name = 'e_gestock.inventory.add.article.wizard'
    _description = 'Assistant d\'ajout d\'article à l\'inventaire'
    
    inventory_id = fields.Many2one('e_gestock.inventory', string='Inventaire', required=True)
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', related='inventory_id.depot_id', readonly=True)
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    quantite_reelle = fields.Float(string='Quantité réelle', digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unité de mesure', related='article_id.code_unite')
    
    def action_add(self):
        self.ensure_one()
        
        if self.inventory_id.state != 'in_progress':
            raise UserError(_("L'inventaire doit être à l'état 'En cours' pour ajouter un article."))
        
        # Vérifier si l'article existe déjà dans l'inventaire
        existing_line = self.env['e_gestock.inventory_line'].search([
            ('inventory_id', '=', self.inventory_id.id),
            ('article_id', '=', self.article_id.id)
        ], limit=1)
        
        if existing_line:
            # Mettre à jour la ligne existante
            existing_line.write({
                'quantite_reelle': self.quantite_reelle,
                'is_counted': True
            })
        else:
            # Rechercher la quantité théorique
            stock_item = self.env['e_gestock.stock_item'].search([
                ('depot_id', '=', self.depot_id.id),
                ('article_id', '=', self.article_id.id)
            ], limit=1)
            
            # Créer une nouvelle ligne
            self.env['e_gestock.inventory_line'].create({
                'inventory_id': self.inventory_id.id,
                'article_id': self.article_id.id,
                'quantite_theorique': stock_item.quantite_disponible if stock_item else 0.0,
                'quantite_reelle': self.quantite_reelle,
                'is_counted': True
            })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'e_gestock.inventory',
            'view_mode': 'form',
            'res_id': self.inventory_id.id,
            'target': 'current',
        } 