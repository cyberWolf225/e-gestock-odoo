# Module de reporting (e_gestock_reports)

## Description
Le module e_gestock_reports fournit un ensemble complet de rapports et tableaux de bord pour la solution E-GESTOCK sur Odoo 18 Community. Il permet d'analyser les données de tous les modules fonctionnels et de générer des rapports personnalisables et dynamiques pour faciliter la prise de décision.

## Dépendances
- e_gestock_base
- e_gestock_inventory
- e_gestock_purchase
- e_gestock_reception
- e_gestock_budget
- e_gestock_supplier
- e_gestock_asset
- base
- mail
- web

## Fonctionnalités principales

### 1. Rapports standards

#### 1.1 Rapports de stock
- **État des stocks** : Niveaux de stock par article, dépôt et famille
- **Mouvements de stock** : Historique des mouvements par période
- **Analyse des rotations** : Taux de rotation par article/famille
- **Valorisation des stocks** : Valeur des stocks par dépôt et famille
- **Alertes de stock** : Articles sous le seuil minimum

#### 1.2 Rapports d'achat
- **Suivi des demandes** : État des demandes d'achat par statut
- **Analyse des prix** : Évolution des prix d'achat par article/fournisseur
- **Performance fournisseurs** : Évaluation des délais et conformité
- **Engagements budgétaires** : Suivi des engagements par structure/famille
- **Comparaison des offres** : Analyse comparative des cotations

#### 1.3 Rapports budgétaires
- **Consommation budgétaire** : Suivi par structure et compte budgétaire
- **Prévisions vs réalisations** : Comparaison budget alloué/consommé
- **Analyse des écarts** : Identification des dépassements
- **Historique budgétaire** : Évolution sur plusieurs exercices
- **Alertes budgétaires** : Seuils d'alerte sur consommation

#### 1.4 Rapports sur les immobilisations
- **Inventaire des biens** : Liste des immobilisations par catégorie
- **Suivi des amortissements** : Tableaux d'amortissement par bien
- **Planning de maintenance** : Calendrier des interventions
- **Analyse des coûts** : Coûts de maintenance par immobilisation
- **État des garanties** : Suivi des garanties par échéance

### 2. Tableaux de bord dynamiques

#### 2.1 Tableau de bord direction
- **Vue d'ensemble budgétaire** : Consommation globale par structure
- **Performance achats** : Indicateurs clés sur les économies réalisées
- **État des stocks** : Synthèse de la valorisation des stocks
- **Alertes critiques** : Tous niveaux confondus
- **Indicateurs de performance** : KPIs principaux de tous les modules

#### 2.2 Tableau de bord achats
- **Suivi des demandes** : Répartition par état et par type
- **Délais de traitement** : Temps moyen par étape du workflow
- **Performance des fournisseurs** : Notes par critère d'évaluation
- **Répartition des dépenses** : Par famille et par fournisseur
- **Économies réalisées** : Écart entre estimations et achats réels

#### 2.3 Tableau de bord stocks
- **Niveaux de stock** : Par dépôt et par famille
- **Mouvements récents** : Entrées/sorties par période
- **Taux de rotation** : Par article et par famille
- **Articles critiques** : Ruptures potentielles ou surstocks
- **Valeur du stock** : Évolution dans le temps

#### 2.4 Tableau de bord budget
- **Consommation budgétaire** : Par structure et par compte
- **Rythme de consommation** : Tendance et projection
- **Engagements en cours** : Montants engagés non consommés
- **Top des postes de dépense** : Par famille de produits
- **Alertes de dépassement** : Comptes approchant leur limite

### 3. Rapports personnalisables

#### 3.1 Générateur de rapports
- Interface de création de rapports personnalisés
- Sélection des dimensions d'analyse (axes)
- Choix des mesures et agrégations
- Filtres dynamiques multicritères
- Export dans différents formats (Excel, PDF, CSV)

#### 3.2 Planification et distribution
- Planification de l'exécution périodique des rapports
- Distribution automatique par email
- Historisation des rapports générés
- Paramétrage des destinataires par type de rapport
- Conditions de déclenchement configurables

### 4. Analyses statistiques avancées

#### 4.1 Analyses prédictives
- Prévision des besoins en approvisionnement
- Estimation des consommations budgétaires
- Anticipation des maintenances d'immobilisations
- Modèles de tendance pour les prix d'achat
- Alertes intelligentes basées sur l'historique

#### 4.2 Analyses multicritères
- Croisement de données inter-modules
- Regroupements hiérarchiques
- Analyses temporelles et saisonnières
- Comparaisons entre périodes
- Détection des anomalies et valeurs aberrantes

## Modèles de données

### 1. Configuration des rapports
```python
class Report(models.Model):
    _name = 'e_gestock.report'
    _description = 'Rapport personnalisé'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    model_id = fields.Many2one('ir.model', string='Modèle de données', required=True)
    type = fields.Selection([
        ('tabular', 'Tabulaire'),
        ('graph', 'Graphique'),
        ('pivot', 'Tableau croisé'),
        ('dashboard', 'Tableau de bord')
    ], string='Type de rapport', required=True)
    is_system = fields.Boolean(string='Rapport système', default=False)
    active = fields.Boolean(string='Actif', default=True)
    user_id = fields.Many2one('res.users', string='Créé par', default=lambda self: self.env.user)
    field_ids = fields.Many2many('ir.model.fields', string='Champs à afficher')
    filter_domain = fields.Char(string='Filtre (domaine)')
    groupby_ids = fields.Many2many('ir.model.fields', 'report_groupby_rel', 'report_id', 'field_id', 
                                   string='Regroupement')
    measure_ids = fields.Many2many('ir.model.fields', 'report_measure_rel', 'report_id', 'field_id', 
                                  string='Mesures')
    sort_field_id = fields.Many2one('ir.model.fields', string='Tri par')
    sort_order = fields.Selection([('asc', 'Ascendant'), ('desc', 'Descendant')], string='Ordre de tri')
    limit = fields.Integer(string='Limite de résultats', default=100)
    
    # Configuration de planification
    schedule_active = fields.Boolean(string='Planification active', default=False)
    schedule_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle')
    ], string='Fréquence')
    schedule_next_date = fields.Date(string='Prochaine exécution')
    schedule_email_ids = fields.Many2many('res.partner', string='Destinataires')
    schedule_template_id = fields.Many2one('mail.template', string='Modèle d\'email')
    
    # Paramètres visuels
    chart_type = fields.Selection([
        ('bar', 'Histogramme'),
        ('line', 'Courbe'),
        ('pie', 'Camembert'),
        ('radar', 'Radar'),
        ('gauge', 'Jauge')
    ], string='Type de graphique')
    
    # Historique des exécutions
    execution_ids = fields.One2many('e_gestock.report.execution', 'report_id', string='Historique d\'exécution')
```

### 2. Exécutions de rapports
```python
class ReportExecution(models.Model):
    _name = 'e_gestock.report.execution'
    _description = 'Exécution de rapport'
    _order = 'date desc'
    
    report_id = fields.Many2one('e_gestock.report', string='Rapport', required=True, ondelete='cascade')
    date = fields.Datetime(string='Date d\'exécution', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    filter_values = fields.Text(string='Valeurs des filtres')
    execution_time = fields.Float(string='Temps d\'exécution (s)')
    result_count = fields.Integer(string='Nombre de résultats')
    attachment_id = fields.Many2one('ir.attachment', string='Résultat sauvegardé')
    state = fields.Selection([
        ('success', 'Succès'),
        ('partial', 'Partiel'),
        ('error', 'Erreur')
    ], string='État', default='success')
    error_message = fields.Text(string='Message d\'erreur')
    
    def get_result_url(self):
        self.ensure_one()
        return '/web/content/%s?download=true' % self.attachment_id.id if self.attachment_id else ''
```

### 3. Indicateurs de performance (KPI)
```python
class Kpi(models.Model):
    _name = 'e_gestock.kpi'
    _description = 'Indicateur de performance'
    
    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('purchase', 'Achats'),
        ('inventory', 'Stocks'),
        ('budget', 'Budget'),
        ('supplier', 'Fournisseurs'),
        ('asset', 'Immobilisations'),
        ('general', 'Général')
    ], string='Catégorie', required=True)
    calculation_method = fields.Text(string='Méthode de calcul')
    sql_query = fields.Text(string='Requête SQL')
    model_id = fields.Many2one('ir.model', string='Modèle source')
    field_id = fields.Many2one('ir.model.fields', string='Champ source')
    aggregate_function = fields.Selection([
        ('count', 'Nombre'),
        ('sum', 'Somme'),
        ('avg', 'Moyenne'),
        ('min', 'Minimum'),
        ('max', 'Maximum')
    ], string='Fonction d\'agrégation')
    filter_domain = fields.Char(string='Filtre (domaine)')
    comparison_period = fields.Selection([
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
        ('quarter', 'Trimestre'),
        ('year', 'Année')
    ], string='Période de comparaison')
    target_value = fields.Float(string='Valeur cible')
    min_threshold = fields.Float(string='Seuil minimum')
    max_threshold = fields.Float(string='Seuil maximum')
    unit = fields.Char(string='Unité')
    active = fields.Boolean(string='Actif', default=True)
    
    # Historique des valeurs
    value_ids = fields.One2many('e_gestock.kpi.value', 'kpi_id', string='Valeurs historiques')
    
    # Calcul dynamique
    value = fields.Float(string='Valeur actuelle', compute='_compute_value')
    trend = fields.Float(string='Tendance', compute='_compute_trend')
    
    @api.depends('value_ids')
    def _compute_value(self):
        for kpi in self:
            current_value = self.env['e_gestock.kpi.value'].search([
                ('kpi_id', '=', kpi.id)
            ], limit=1, order='date desc')
            kpi.value = current_value.value if current_value else 0.0
    
    @api.depends('value_ids', 'comparison_period')
    def _compute_trend(self):
        for kpi in self:
            # Calcul de la tendance par rapport à la période précédente
            current_value = self.env['e_gestock.kpi.value'].search([
                ('kpi_id', '=', kpi.id)
            ], limit=1, order='date desc')
            
            if not current_value:
                kpi.trend = 0.0
                continue
            
            # Récupération de la valeur précédente selon la période de comparaison
            previous_date = None
            if kpi.comparison_period == 'day':
                previous_date = current_value.date - timedelta(days=1)
            elif kpi.comparison_period == 'week':
                previous_date = current_value.date - timedelta(weeks=1)
            elif kpi.comparison_period == 'month':
                previous_date = current_value.date - relativedelta(months=1)
            elif kpi.comparison_period == 'quarter':
                previous_date = current_value.date - relativedelta(months=3)
            elif kpi.comparison_period == 'year':
                previous_date = current_value.date - relativedelta(years=1)
            else:
                kpi.trend = 0.0
                continue
            
            previous_value = self.env['e_gestock.kpi.value'].search([
                ('kpi_id', '=', kpi.id),
                ('date', '<=', previous_date)
            ], limit=1, order='date desc')
            
            if not previous_value or previous_value.value == 0:
                kpi.trend = 0.0
            else:
                kpi.trend = ((current_value.value - previous_value.value) / previous_value.value) * 100
```

### 4. Valeurs des KPI
```python
class KpiValue(models.Model):
    _name = 'e_gestock.kpi.value'
    _description = 'Valeur d\'indicateur de performance'
    _order = 'date desc'
    
    kpi_id = fields.Many2one('e_gestock.kpi', string='Indicateur', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    value = fields.Float(string='Valeur', required=True)
    target = fields.Float(string='Cible')
    note = fields.Text(string='Note')
    
    _sql_constraints = [
        ('kpi_date_uniq', 'unique(kpi_id, date)', 'Une seule valeur par jour et par indicateur!')
    ]
```

### 5. Tableaux de bord
```python
class Dashboard(models.Model):
    _name = 'e_gestock.dashboard'
    _description = 'Tableau de bord'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    is_system = fields.Boolean(string='Tableau de bord système', default=False)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    is_favorite = fields.Boolean(string='Favori', default=False)
    layout = fields.Selection([
        ('grid', 'Grille'),
        ('flow', 'Flux'),
        ('columns', 'Colonnes')
    ], string='Disposition', default='grid')
    widget_ids = fields.One2many('e_gestock.dashboard.widget', 'dashboard_id', string='Widgets')
    active = fields.Boolean(string='Actif', default=True)
    category = fields.Selection([
        ('purchase', 'Achats'),
        ('inventory', 'Stocks'),
        ('budget', 'Budget'),
        ('supplier', 'Fournisseurs'),
        ('asset', 'Immobilisations'),
        ('general', 'Général')
    ], string='Catégorie', required=True, default='general')
    
    def get_data(self):
        self.ensure_one()
        result = {
            'name': self.name,
            'description': self.description,
            'layout': self.layout,
            'widgets': []
        }
        
        for widget in self.widget_ids:
            widget_data = widget.get_data()
            if widget_data:
                result['widgets'].append(widget_data)
        
        return result
```

### 6. Widgets de tableau de bord
```python
class DashboardWidget(models.Model):
    _name = 'e_gestock.dashboard.widget'
    _description = 'Widget de tableau de bord'
    _order = 'sequence, id'
    
    name = fields.Char(string='Nom', required=True)
    dashboard_id = fields.Many2one('e_gestock.dashboard', string='Tableau de bord', 
                                 required=True, ondelete='cascade')
    type = fields.Selection([
        ('kpi', 'Indicateur'),
        ('chart', 'Graphique'),
        ('list', 'Liste'),
        ('pivot', 'Tableau croisé'),
        ('alert', 'Alerte')
    ], string='Type', required=True)
    size_x = fields.Integer(string='Largeur', default=1)
    size_y = fields.Integer(string='Hauteur', default=1)
    position_x = fields.Integer(string='Position X', default=0)
    position_y = fields.Integer(string='Position Y', default=0)
    sequence = fields.Integer(string='Séquence', default=10)
    color = fields.Char(string='Couleur', default='#875A7B')
    
    # Contenu du widget
    kpi_id = fields.Many2one('e_gestock.kpi', string='Indicateur')
    report_id = fields.Many2one('e_gestock.report', string='Rapport')
    model_id = fields.Many2one('ir.model', string='Modèle de données')
    domain = fields.Char(string='Filtre (domaine)')
    
    # Options d'affichage
    display_mode = fields.Selection([
        ('number', 'Nombre'),
        ('trend', 'Tendance'),
        ('progress', 'Progression'),
        ('table', 'Tableau'),
        ('chart', 'Graphique')
    ], string='Mode d\'affichage', default='number')
    
    icon = fields.Char(string='Icône')
    limit = fields.Integer(string='Limite de résultats', default=5)
    
    def get_data(self):
        self.ensure_one()
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'size_x': self.size_x,
            'size_y': self.size_y,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'display_mode': self.display_mode,
            'color': self.color,
            'icon': self.icon,
            'content': None
        }
        
        # Récupération du contenu selon le type
        if self.type == 'kpi' and self.kpi_id:
            data['content'] = {
                'value': self.kpi_id.value,
                'trend': self.kpi_id.trend,
                'unit': self.kpi_id.unit,
                'target': self.kpi_id.target_value,
                'min_threshold': self.kpi_id.min_threshold,
                'max_threshold': self.kpi_id.max_threshold
            }
        elif self.type == 'chart' and self.report_id:
            # Récupérer les données du rapport pour le graphique
            data['content'] = self._get_chart_data()
        elif self.type == 'list' and self.model_id:
            # Récupérer les données sous forme de liste
            data['content'] = self._get_list_data()
            
        return data
```

## Structure du module

```
e_gestock_reports/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── report.py
  │   ├── report_execution.py
  │   ├── kpi.py
  │   ├── kpi_value.py
  │   ├── dashboard.py
  │   └── dashboard_widget.py
  ├── views/
  │   ├── report_views.xml
  │   ├── kpi_views.xml
  │   ├── dashboard_views.xml
  │   ├── report_templates.xml
  │   └── menu_views.xml
  ├── wizards/
  │   ├── __init__.py
  │   ├── report_generator_wizard.py
  │   └── dashboard_generator_wizard.py
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_reports_security.xml
  ├── report/
  │   ├── stock_report.xml
  │   ├── purchase_report.xml
  │   ├── budget_report.xml
  │   └── asset_report.xml
  ├── static/
  │   ├── src/
  │   │   ├── js/
  │   │   │   ├── dashboard.js
  │   │   │   └── report_generator.js
  │   │   └── css/
  │   │       ├── dashboard.css
  │   │       └── reports.css
  │   └── lib/
  │       └── chart.js
  └── data/
      ├── report_data.xml
      ├── kpi_data.xml
      └── dashboard_data.xml
```

## Rapports prédéfinis

### 1. Rapports de stock
- Inventaire valorisé par dépôt
- État des stocks par famille d'articles
- Analyse des mouvements de stock
- Taux de rotation des stocks
- Alertes de stocks minimums

### 2. Rapports d'achats
- Suivi des demandes d'achat par état
- Analyse des prix par fournisseur
- Analyse des délais de livraison
- Conformité des livraisons
- Comparatif des cotations

### 3. Rapports budgétaires
- État de consommation par structure
- Suivi des engagements budgétaires
- Analyse des écarts budget/réalisé
- Prévisions de consommation
- Historique des consommations par famille

### 4. Rapports fournisseurs
- Performance des fournisseurs
- Volumes d'achat par fournisseur
- Analyse des prix par famille d'articles
- Suivi des contrats en cours
- Historique des évaluations

### 5. Rapports immobilisations
- Inventaire des immobilisations
- Suivi des amortissements
- Planning de maintenance
- Analyse des coûts de maintenance
- Suivi des garanties

## KPIs prédéfinis

### 1. KPIs Achats
- Délai moyen de traitement des demandes d'achat
- Taux de demandes validées
- Économies réalisées (écart budget/réel)
- Nombre de demandes en attente par étape
- Montant total des demandes par mois

### 2. KPIs Stocks
- Valeur totale des stocks
- Taux de rotation moyen
- Nombre d'articles à risque de rupture
- Taux d'écart d'inventaire
- Volume des mouvements mensuels

### 3. KPIs Budget
- Taux de consommation budgétaire
- Montant des engagements en cours
- Nombre de dépassements budgétaires
- Projection de fin d'exercice
- Taux d'utilisation par structure

### 4. KPIs Fournisseurs
- Note moyenne des fournisseurs
- Taux de conformité des livraisons
- Délai moyen de livraison
- Nombre de contrats actifs
- Montant des engagements fournisseurs

## Tableaux de bord prédéfinis

### 1. Tableau de bord Direction
- Vue synthétique de tous les KPIs critiques
- État global du budget
- Alertes prioritaires
- Tendances principales
- Volumes d'activité par module

### 2. Tableau de bord Achats
- Suivi des demandes par état
- Performance des approbations
- Économies réalisées
- Top fournisseurs
- Délais moyens par étape

### 3. Tableau de bord Stocks
- État des stocks par dépôt
- Analyse des mouvements
- Articles critiques
- Valorisation
- Prévisions de rupture

### 4. Tableau de bord Budget
- Consommation par structure
- Projections de fin d'exercice
- Alertes de dépassement
- Rythme de consommation
- Répartition par famille

## Règles de sécurité

### 1. Accès aux rapports
- **Groupe Direction** : Accès à tous les rapports et tableaux de bord
- **Groupe Responsable de module** : Accès aux rapports de son domaine
- **Groupe Utilisateur** : Accès aux rapports basiques
- **Groupe Analyste** : Création et modification des rapports personnalisés

### 2. Accès aux tableaux de bord
- **Groupe Direction** : Accès à tous les tableaux de bord
- **Groupe Responsable de module** : Accès aux tableaux de bord de son domaine
- **Groupe Utilisateur** : Accès aux tableaux de bord basiques
- **Groupe Analyste** : Création et modification des tableaux de bord 