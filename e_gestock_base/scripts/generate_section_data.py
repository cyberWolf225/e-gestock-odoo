#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import re

# Chemin vers le répertoire data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def generate_section_xml():
    """Génère un fichier XML unique pour toutes les sections."""
    json_file = os.path.join(DATA_DIR, 'sections.json')
    xml_file = os.path.join(DATA_DIR, 'section_data.xml')
    
    # Vérifier si le fichier JSON existe
    if not os.path.exists(json_file):
        print(f"Erreur: Le fichier {json_file} n'existe pas.")
        return
    
    # Charger les données JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data_json = json.load(f)
    
    # Extraire les sections du JSON
    sections_data = data_json.get('rows', [])
    
    # Générer le contenu XML
    xml_content = '<?xml version="1.0" encoding="utf-8"?>\n'
    xml_content += '<odoo>\n'
    xml_content += '    <data noupdate="1">\n'
    xml_content += '        <!-- Sections importées du fichier JSON -->\n'
    
    # Parcourir les sections et les ajouter au XML
    for section in sections_data:
        xml_content += f'        <record id="section_{section["code_section"]}" model="e_gestock.section">\n'
        xml_content += f'            <field name="code_section">{section["code_section"]}</field>\n'
        xml_content += f'            <field name="nom_section">{section["nom_section"]}</field>\n'
        xml_content += f'            <field name="code_structure" ref="structure_{section["code_structure"]}"/>\n'
        
        # Ajouter la référence au type de gestion si disponible
        if section.get('code_gestion'):
            xml_content += f'            <field name="code_gestion" ref="type_gestion_{section["code_gestion"].lower()}"/>\n'
        
        xml_content += '        </record>\n'
        xml_content += '        \n'
    
    # Fermer les balises
    xml_content += '    </data>\n'
    xml_content += '</odoo>\n'
    
    # Écrire dans le fichier
    with open(xml_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Fichier {xml_file} généré avec succès.")
    print(f"Nombre de sections générées: {len(sections_data)}")

if __name__ == '__main__':
    generate_section_xml() 