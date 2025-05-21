# Module budgétaire (e_gestock_budget)

## Description
Le module e_gestock_budget gère l'ensemble du processus budgétaire dans la solution E-GESTOCK pour Odoo 18 Community. Il permet de définir les exercices budgétaires, allouer des budgets par structure et famille d'articles, et suivre les consommations budgétaires en temps réel.

## Dépendances
- e_gestock_base
- base
- mail
- web

## Fonctionnalités principales

### 1. Exercices budgétaires

#### 1.1 Exercices (e_gestock.exercise)
- `code` : Code de l'exercice (ex: "2025")
- `name` : Nom de l'exercice 
- `date_debut` : Date de début
- `date_fin` : Date de fin
- `state` : État (ouvert/fermé)
- `is_active` : Indicateur d'activité (un seul exercice actif à la fois)
- `notes` : Notes et observations
- `responsable_id` : Responsable de l'exercice

#### 1.2 Gestion des exercices
- Création et configuration des exercices budgétaires
- Activation/désactivation des exercices
- Clôture des exercices avec contrôles de validation
- Verrouillage des opérations sur exercices fermés
- Statistiques globales de consommation

### 2. Crédits budgétaires

#### 2.1 Crédits budgétaires (e_gestock.credit_budget)
- `structure_id` : Structure concernée
- `section_id` : Section concernée (optionnel)
- `famille_id` : Famille d'articles (servant de compte budgétaire)
- `type_gestion_id` : Type de gestion
- `exercise_id` : Exercice budgétaire
- `montant_alloue` : Montant alloué
- `montant_engage` : Montant engagé
- `montant_consomme` : Montant consommé
- `montant_disponible` : Montant disponible (calculé)
- `threshold_percentage` : Pourcentage de seuil d'alerte
- `is_below_threshold` : Indicateur de dépassement de seuil

#### 2.2 Historique des opérations budgétaires (e_gestock.operation_budget)
- `credit_id` : Référence au crédit budgétaire
- `date` : Date de l'opération
- `montant` : Montant de l'opération
- `type` : Type d'opération (allocation, engagement, consommation, ajustement)
- `origine` : Document d'origine (demande d'achat, bon de commande)
- `ref_origine` : Référence du document d'origine
- `user_id` : Utilisateur ayant effectué l'opération
- `notes` : Notes explicatives
- `validateur_id` : Utilisateur validateur (pour opérations validées)
- `etape_validation` : Étape de validation concernée (CMP, Budget, DCG, etc.)

#### 2.3 Système d'allocation et de suivi
- Allocation des budgets par structure, section et famille d'articles
- Suivi des consommations budgétaires en temps réel
- Alertes sur seuils de consommation personnalisables
- Contrôle des dépassements avec blocage des opérations
- Ajustements budgétaires avec historique des modifications
- Reporting détaillé par compte budgétaire (famille d'articles)

### 3. Dotations budgétaires

#### 3.1 Dotations (e_gestock.dotation_budget)
- `depot_id` : Dépôt concerné
- `famille_id` : Famille d'articles
- `exercise_id` : Exercice budgétaire
- `montant_dotation` : Montant de la dotation
- `montant_consomme` : Montant consommé
- `montant_disponible` : Montant disponible (calculé)
- `responsable_id` : Responsable de la dotation

#### 3.2 Gestion des dotations
- Allocation des dotations par dépôt et famille d'articles
- Suivi des consommations par exercice
- Contrôles de validation pour éviter les soldes négatifs
- Historique des modifications

### 4. API de vérification budgétaire

#### 4.1 Services de vérification
- API pour la vérification des disponibilités budgétaires
- Méthodes de contrôle de budget disponible avant validation des demandes
- Mise à jour automatique des consommations budgétaires
- Verrouillage des opérations en cas de dépassement de budget

### 5. Analyses et statistiques

#### 5.1 Analyses budgétaires
- Suivi détaillé des consommations par période
- Analyse des tendances de consommation
- Comparaison entre budget alloué et consommé
- Prévisions budgétaires basées sur l'historique
- Identification des postes de dépense principaux

#### 5.2 Tableaux de bord
- Vue d'ensemble de l'état des budgets
- Alertes sur dépassements et seuils
- Indicateurs de performance budgétaire
- Évolution des consommations dans le temps

### 6. Intégration avec le circuit de validation

#### 6.1 Circuit de contrôle budgétaire
- Intégration dans le workflow complet des achats
- Validation budgétaire pour toutes les demandes d'achat
- Vérification automatique des fonds disponibles
- Blocage/déblocage conditionnel selon disponibilité budgétaire

#### 6.2 Étapes de validation budgétaire
- Vérification initiale lors de la soumission de la demande
- Contrôle formel par le Responsable contrôle budgétaire
- Support pour les demandes de dérogation
- Mécanisme de réallocation budgétaire en cas de besoin

## Modèles de données

### 1. Exercices budgétaires
```python
class Exercise(models.Model):
    _name = 'e_gestock.exercise'
    _description = 'Exercice budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    code = fields.Char(string='Code', required=True, tracking=True)
    name = fields.Char(string='Nom', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', required=True, tracking=True)
    state = fields.Selection([
        ('open', 'Ouvert'),
        ('closed', 'Fermé')
    ], string='État', default='open', tracking=True)
    is_active = fields.Boolean(string='Actif', default=False, tracking=True)
    notes = fields.Text(string='Notes')
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    credit_ids = fields.One2many('e_gestock.credit_budget', 'exercise_id', string='Crédits budgétaires')
    dotation_ids = fields.One2many('e_gestock.dotation_budget', 'exercise_id', string='Dotations')
    
    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Le code de l\'exercice doit être unique!')
    ]
    
    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for exercise in self:
            if exercise.date_fin <= exercise.date_debut:
                raise ValidationError(_("La date de fin doit être postérieure à la date de début!"))
    
    @api.constrains('is_active')
    def _check_active_unique(self):
        for exercise in self:
            if exercise.is_active:
                other_active = self.search([('is_active', '=', True), ('id', '!=', exercise.id)])
                if other_active:
                    raise ValidationError(_("Un seul exercice peut être actif à la fois!"))
```

### 2. Crédits budgétaires
```python
class CreditBudget(models.Model):
    _name = 'e_gestock.credit_budget'
    _description = 'Crédit budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    structure_id = fields.Many2one('e_gestock.structure', string='Structure', required=True, tracking=True)
    section_id = fields.Many2one('e_gestock.section', string='Section', tracking=True)
    famille_id = fields.Many2one('e_gestock.famille', string='Famille (Compte budgétaire)', required=True, tracking=True)
    type_gestion_id = fields.Many2one('e_gestock.type_gestion', string='Type de gestion', tracking=True)
    exercise_id = fields.Many2one('e_gestock.exercise', string='Exercice budgétaire', required=True, tracking=True,
                                 domain=[('state', '=', 'open')])
    montant_alloue = fields.Monetary(string='Montant alloué', required=True, tracking=True)
    montant_engage = fields.Monetary(string='Montant engagé', default=0.0, tracking=True)
    montant_consomme = fields.Monetary(string='Montant consommé', default=0.0, tracking=True)
    montant_disponible = fields.Monetary(string='Montant disponible', compute='_compute_montant_disponible', store=True)
    threshold_percentage = fields.Float(string='Seuil d\'alerte (%)', default=80.0)
    is_below_threshold = fields.Boolean(string='Sous le seuil', compute='_compute_is_below_threshold', store=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    operation_ids = fields.One2many('e_gestock.operation_budget', 'credit_id', string='Opérations')
    
    _sql_constraints = [
        ('structure_famille_exercise_uniq', 'unique(structure_id, famille_id, exercise_id, type_gestion_id)',
         'Un crédit budgétaire doit être unique par structure, famille, exercice et type de gestion!')
    ]
    
    @api.depends('montant_alloue', 'montant_engage', 'montant_consomme')
    def _compute_montant_disponible(self):
        for credit in self:
            credit.montant_disponible = credit.montant_alloue - credit.montant_engage
    
    @api.depends('montant_disponible', 'montant_alloue', 'threshold_percentage')
    def _compute_is_below_threshold(self):
        for credit in self:
            if credit.montant_alloue > 0:
                ratio = (credit.montant_disponible / credit.montant_alloue) * 100
                credit.is_below_threshold = ratio < (100 - credit.threshold_percentage)
            else:
                credit.is_below_threshold = True
```

### 3. Opérations budgétaires
```python
class OperationBudget(models.Model):
    _name = 'e_gestock.operation_budget'
    _description = 'Opération budgétaire'
    
    credit_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', required=True, ondelete='cascade')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    montant = fields.Monetary(string='Montant', required=True)
    type = fields.Selection([
        ('allocation', 'Allocation'),
        ('engagement', 'Engagement'),
        ('consommation', 'Consommation'),
        ('ajustement', 'Ajustement')
    ], string='Type d\'opération', required=True)
    origine = fields.Selection([
        ('demande_achat', 'Demande d\'achat'),
        ('bon_commande', 'Bon de commande'),
        ('manuel', 'Manuel'),
        ('init', 'Initialisation')
    ], string='Origine', required=True, default='manuel')
    ref_origine = fields.Char(string='Référence origine')
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, required=True)
    validateur_id = fields.Many2one('res.users', string='Validateur')
    etape_validation = fields.Selection([
        ('cmp', 'Validation CMP'),
        ('budget', 'Contrôle Budgétaire'),
        ('dcg_dept', 'Chef Département DCG'),
        ('dcg', 'Responsable DCG'),
        ('dgaaf', 'DGAAF'),
        ('dg', 'DG')
    ], string='Étape de validation')
    notes = fields.Text(string='Notes')
    currency_id = fields.Many2one('res.currency', string='Devise', related='credit_id.currency_id')
```

### 4. Dotations budgétaires
```python
class DotationBudget(models.Model):
    _name = 'e_gestock.dotation_budget'
    _description = 'Dotation budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    depot_id = fields.Many2one('e_gestock.depot', string='Dépôt', required=True, tracking=True)
    famille_id = fields.Many2one('e_gestock.famille', string='Famille', required=True, tracking=True)
    exercise_id = fields.Many2one('e_gestock.exercise', string='Exercice budgétaire', required=True, tracking=True)
    montant_dotation = fields.Monetary(string='Montant dotation', required=True, tracking=True)
    montant_consomme = fields.Monetary(string='Montant consommé', default=0.0, tracking=True)
    montant_disponible = fields.Monetary(string='Montant disponible', compute='_compute_montant_disponible', store=True)
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    
    _sql_constraints = [
        ('depot_famille_exercise_uniq', 'unique(depot_id, famille_id, exercise_id)',
         'Une dotation budgétaire doit être unique par dépôt, famille et exercice!')
    ]
    
    @api.depends('montant_dotation', 'montant_consomme')
    def _compute_montant_disponible(self):
        for dotation in self:
            dotation.montant_disponible = dotation.montant_dotation - dotation.montant_consomme
```

### 5. Intégration avec le circuit de validation

```python
class BudgetControl(models.Model):
    _name = 'e_gestock.budget_control'
    _description = 'Contrôle budgétaire'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    demande_id = fields.Many2one('e_gestock.demande_cotation', string='Demande d\'achat', required=True)
    credit_id = fields.Many2one('e_gestock.credit_budget', string='Crédit budgétaire', required=True)
    montant = fields.Monetary(string='Montant', related='demande_id.montant_total')
    currency_id = fields.Many2one('res.currency', string='Devise')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    controleur_id = fields.Many2one('res.users', string='Contrôleur budgétaire', 
                                   domain=[('groups_id', 'in', [lambda self: self.env.ref('e_gestock.group_budget_controller').id])])
    state = fields.Selection([
        ('draft', 'À contrôler'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('derogation', 'Dérogation')
    ], string='État', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    operation_id = fields.Many2one('e_gestock.operation_budget', string='Opération budgétaire')
    
    # Fonctions de validation
    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        # Création de l'opération budgétaire d'engagement
        operation = self.env['e_gestock.operation_budget'].create({
            'credit_id': self.credit_id.id,
            'date': fields.Datetime.now(),
            'montant': self.montant,
            'type': 'engagement',
            'origine': 'demande_achat',
            'ref_origine': self.demande_id.reference,
            'user_id': self.env.user.id,
            'validateur_id': self.controleur_id.id,
            'etape_validation': 'budget',
            'notes': self.notes
        })
        self.operation_id = operation.id
        # Mise à jour du crédit budgétaire
        self.credit_id.write({
            'montant_engage': self.credit_id.montant_engage + self.montant
        })
        # Mise à jour de l'état de la demande
        self.demande_id.write({'state': 'budget_checked'})
        
    def action_reject(self):
        self.ensure_one()
        self.state = 'rejected'
        # Notification au demandeur
        
    def action_derogation(self):
        self.ensure_one()
        self.state = 'derogation'
        # Workflow de dérogation spécifique
```

## Structure du module


## Vues principales

### 1. Vue formulaire du contrôle budgétaire

## Intégration avec les autres modules

### 1. Intégration avec le module e_gestock_purchase
- Contrôle budgétaire automatique à la soumission des demandes d'achat
- Blocage des demandes en cas de budget insuffisant
- Intégration dans le circuit de validation des achats
- Création d'opérations budgétaires à chaque étape du processus
- Extensions sur le modèle purchase.order pour le suivi budgétaire

### 2. Intégration avec le module e_gestock_base
- Utilisation des structures et familles d'articles comme axes budgétaires
- Extension du modèle e_gestock.famille pour les fonctionnalités de compte budgétaire
- Ajout de champs et méthodes d'analyse budgétaire aux structures

### 3. Rapports budgétaires améliorés
- Suivi des engagements par type de validation
- Tableau croisé par structure et étape de validation
- Historique des contrôles budgétaires
- Synthèse des dérogations accordées 