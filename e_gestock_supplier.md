# Module de gestion des fournisseurs (e_gestock_supplier)


## Description
Le module e_gestock_supplier permet la gestion complète des fournisseurs dans la solution E-GESTOCK pour Odoo 18 Community. Il inclut la catégorisation des fournisseurs, la gestion des contrats, l'évaluation des performances et l'intégration avec le portail fournisseurs.

## Dépendances
- e_gestock_base
- e_gestock_purchase
- base
- mail
- portal
- product
- web

## Fonctionnalités principales

### 1. Gestion des fournisseurs

#### 1.1 Extension du modèle res.partner
- Synchronisation bidirectionnelle avec les partenaires Odoo
- Relation avec les familles d'articles et les produits fournis
- Système de notation automatisé pour les performances
- Statistiques d'achats (montants, délais, etc.)
- Catégorisation hiérarchique
- Support du workflow complet des achats
- Compatibilité avec le circuit de validation des achats

#### 1.2 Catégories de fournisseurs (e_gestock.supplier_category)
- `code` : Code unique de la catégorie
- `name` : Nom de la catégorie
- `parent_id` : Catégorie parente pour hiérarchie
- `note` : Description de la catégorie
- `active` : Statut actif/inactif

#### 1.3 Produits fournis (e_gestock.supplier_article)
- Lien entre fournisseurs et articles
- Prix spécifiques par fournisseur
- Conditions commerciales
- Historique des achats
- Délais de livraison par produit
- Remises spécifiques

### 2. Contrats fournisseurs

#### 2.1 Contrats (e_gestock.supplier_contract)
- `reference` : Référence unique du contrat
- `supplier_id` : Fournisseur concerné
- `type` : Type de contrat (cadre, ponctuel, service, maintenance)
- `date_debut` : Date de début du contrat
- `date_fin` : Date d'expiration
- `montant` : Montant du contrat
- `currency_id` : Devise
- `responsable_id` : Responsable du suivi
- `state` : État du contrat (brouillon, actif, expiré, résilié, renouvelé, annulé)
- `renew_auto` : Indicateur de renouvellement automatique
- `conditions_paiement` : Conditions de paiement négociées
- `remise` : Remise accordée
- `validateur_id` : Validateur du contrat
- `date_validation` : Date de validation

#### 2.2 Clauses contractuelles (e_gestock.contract_clause)
- `contract_id` : Contrat associé
- `name` : Titre de la clause
- `description` : Contenu de la clause
- `type` : Type de clause (exclusivité, confidentialité, garantie, etc.)
- `is_required` : Caractère obligatoire

#### 2.3 Gestion du cycle de vie des contrats
- Système de renouvellement automatique ou manuel
- Alertes avant expiration
- Historique des modifications
- Suivi des conditions contractuelles
- Circuit de validation des contrats

### 3. Évaluation des fournisseurs

#### 3.1 Évaluations (e_gestock.supplier_evaluation)
- `supplier_id` : Fournisseur évalué
- `date` : Date d'évaluation
- `evaluateur_id` : Utilisateur évaluateur
- `note_globale` : Note globale calculée
- `periode_debut` : Début de la période évaluée
- `periode_fin` : Fin de la période évaluée
- `state` : État (brouillon, validé, archivé)

#### 3.2 Critères d'évaluation (e_gestock.evaluation_criteria)
- `name` : Nom du critère
- `description` : Description
- `poids` : Pondération (%)
- `active` : Statut actif/inactif

#### 3.3 Notes d'évaluation (e_gestock.evaluation_note)
- `evaluation_id` : Évaluation associée
- `criteria_id` : Critère évalué
- `note` : Note attribuée (sur 5 ou 10)
- `commentaire` : Commentaire justificatif

#### 3.4 Système d'évaluation multicritères
- Pondération personnalisable des critères
- Calcul automatique des notes globales
- Impact sur la classification du fournisseur
- Suivi des points forts et points faibles
- Historique des évaluations
- Intégration des données de performance des commandes

### 4. Portail fournisseurs

#### 4.1 Interface du portail
- Accès sécurisé via le portail Odoo
- Visualisation des demandes de cotation en attente
- Interface de saisie des prix et conditions
- Soumission des offres via le portail
- Suivi de l'état des demandes
- Historique des cotations précédentes
- Accès aux bons de commande
- Support du circuit de validation des achats

#### 4.2 Fonctionnalités avancées du portail
- Tableau de bord fournisseur personnalisé
- Vue des évaluations de performance
- Accès aux contrats actifs
- Gestion des retours et contestations
- Notification des différentes étapes de validation

### 5. Intégration avec le circuit de validation des achats

#### 5.1. Adaptation au workflow enrichi
- Support complet du circuit de validation (CMP, Budget, DCG, etc.)
- Notifications aux fournisseurs à chaque étape clé
- Accès aux documents selon l'état d'avancement
- Suivi des approbations en temps réel

#### 5.2. Mécanismes de cotation améliorés
- Support des saisies de cotations avec TVA et remises
- Interface adaptée pour les nouveaux champs obligatoires
- Gestion des délais en accord avec le processus de validation

## Modèles de données

### 1. Extension res.partner



### 2. Catégories de fournisseurs


### 3. Articles fournis
```python
class SupplierArticle(models.Model):
    _name = 'e_gestock.supplier_article'
    _description = 'Article fourni par un fournisseur'
    
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True, ondelete='cascade')
    article_id = fields.Many2one('e_gestock.article', string='Article', required=True)
    product_id = fields.Many2one('product.product', string='Produit Odoo', related='article_id.product_id')
    prix_unitaire = fields.Float(string='Prix unitaire')
    currency_id = fields.Many2one('res.currency', string='Devise')
    date_debut = fields.Date(string='Date début validité')
    date_fin = fields.Date(string='Date fin validité')
    delai_livraison = fields.Integer(string='Délai de livraison (jours)')
    quantite_min = fields.Float(string='Quantité minimale')
    remise = fields.Float(string='Remise (%)')
    remise_generale = fields.Float(string='Remise générale (%)')
    tva = fields.Float(string='TVA (%)')
    notes = fields.Text(string='Notes')
    is_preferred = fields.Boolean(string='Fournisseur préféré', default=False)
    
    _sql_constraints = [
        ('supplier_article_uniq', 'unique(supplier_id, article_id)', 
         'Un article ne peut être associé qu\'une seule fois à un fournisseur!')
    ]
    
    @api.model
    def create(self, vals):
        if vals.get('is_preferred'):
            # Désactiver le statut préféré des autres fournisseurs pour cet article
            self.search([
                ('article_id', '=', vals.get('article_id')),
                ('is_preferred', '=', True)
            ]).write({'is_preferred': False})
        return super(SupplierArticle, self).create(vals)
```

### 4. Contrats fournisseurs
```python
class SupplierContract(models.Model):
    _name = 'e_gestock.supplier_contract'
    _description = 'Contrat fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    reference = fields.Char(string='Référence', required=True, readonly=True, default='Nouveau')
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True, 
                                domain=[('supplier_rank', '>', 0)], tracking=True)
    type = fields.Selection([
        ('framework', 'Contrat cadre'),
        ('punctual', 'Contrat ponctuel'),
        ('service', 'Contrat de service'),
        ('maintenance', 'Contrat de maintenance')
    ], string='Type de contrat', required=True, tracking=True)
    date_debut = fields.Date(string='Date de début', required=True, tracking=True)
    date_fin = fields.Date(string='Date de fin', tracking=True)
    montant = fields.Monetary(string='Montant', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Devise')
    responsable_id = fields.Many2one('res.users', string='Responsable', tracking=True,
                                   default=lambda self: self.env.user)
    validateur_id = fields.Many2one('res.users', string='Validateur', tracking=True)
    date_validation = fields.Date(string='Date de validation', tracking=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('submitted', 'Soumis'),
        ('validated', 'Validé'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('terminated', 'Résilié'),
        ('renewed', 'Renouvelé'),
        ('cancelled', 'Annulé')
    ], string='État', default='draft', tracking=True)
    renew_auto = fields.Boolean(string='Renouvellement automatique', default=False)
    renewal_reminder = fields.Integer(string='Rappel renouvellement (jours)', default=30)
    clause_ids = fields.One2many('e_gestock.contract_clause', 'contract_id', string='Clauses')
    conditions_paiement = fields.Char(string='Conditions de paiement')
    remise = fields.Float(string='Remise (%)')
    is_exclusive = fields.Boolean(string='Exclusivité', default=False)
    famille_ids = fields.Many2many('e_gestock.famille', string='Familles d\'articles concernées')
    note = fields.Text(string='Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Pièces jointes')
    purchase_order_ids = fields.One2many('purchase.order', 'e_gestock_contract_id', string='Commandes liées')
    
    @api.model
    def create(self, vals):
        if vals.get('reference', 'Nouveau') == 'Nouveau':
            vals['reference'] = self.env['ir.sequence'].next_by_code('e_gestock.supplier_contract')
        return super(SupplierContract, self).create(vals)
    
    def action_submit(self):
        self.state = 'submitted'
    
    def action_validate(self):
        self.write({
            'state': 'validated',
            'validateur_id': self.env.user.id,
            'date_validation': fields.Date.today()
        })
    
    def action_activate(self):
        if self.state != 'validated':
            raise UserError(_("Le contrat doit être validé avant d'être activé."))
        self.state = 'active'
    
    @api.model
    def _cron_check_expiring_contracts(self):
        """Vérifier les contrats qui vont expirer bientôt"""
        today = fields.Date.today()
        for contract in self.search([('state', '=', 'active'), ('date_fin', '!=', False)]):
            days_before_expiry = (contract.date_fin - today).days
            if days_before_expiry <= contract.renewal_reminder:
                # Notifier le responsable
                contract.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Contrat à renouveler'),
                    note=_('Le contrat %s expire dans %s jours.') % (contract.reference, days_before_expiry),
                    user_id=contract.responsable_id.id,
                    date_deadline=contract.date_fin)
```

### 5. Clauses contractuelles
```python
class ContractClause(models.Model):
    _name = 'e_gestock.contract_clause'
    _description = 'Clause contractuelle'
    
    contract_id = fields.Many2one('e_gestock.supplier_contract', string='Contrat', required=True, ondelete='cascade')
    name = fields.Char(string='Titre', required=True)
    description = fields.Text(string='Contenu', required=True)
    type = fields.Selection([
        ('exclusivity', 'Exclusivité'),
        ('confidentiality', 'Confidentialité'),
        ('warranty', 'Garantie'),
        ('payment', 'Paiement'),
        ('delivery', 'Livraison'),
        ('termination', 'Résiliation'),
        ('other', 'Autre')
    ], string='Type', required=True)
    is_required = fields.Boolean(string='Obligatoire', default=False)
```

### 6. Évaluations des fournisseurs
```python
class SupplierEvaluation(models.Model):
    _name = 'e_gestock.supplier_evaluation'
    _description = 'Évaluation fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    supplier_id = fields.Many2one('res.partner', string='Fournisseur', required=True, tracking=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    evaluateur_id = fields.Many2one('res.users', string='Évaluateur', default=lambda self: self.env.user,
                                   required=True, tracking=True)
    note_globale = fields.Float(string='Note globale', compute='_compute_note_globale', store=True, tracking=True)
    periode_debut = fields.Date(string='Début période', required=True)
    periode_fin = fields.Date(string='Fin période', required=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('archived', 'Archivé')
    ], string='État', default='draft', tracking=True)
    note_ids = fields.One2many('e_gestock.evaluation_note', 'evaluation_id', string='Notes')
    
    @api.depends('note_ids', 'note_ids.note', 'note_ids.criteria_id.poids')
    def _compute_note_globale(self):
        for evaluation in self:
            if not evaluation.note_ids:
                evaluation.note_globale = 0.0
                continue
                
            total_poids = sum(note.criteria_id.poids for note in evaluation.note_ids)
            if total_poids == 0:
                evaluation.note_globale = 0.0
                continue
                
            # Calculer la note pondérée
            note_ponderee = sum((note.note * note.criteria_id.poids) for note in evaluation.note_ids) / total_poids
            evaluation.note_globale = note_ponderee
```

### 7. Critères d'évaluation
```python
class EvaluationCriteria(models.Model):
    _name = 'e_gestock.evaluation_criteria'
    _description = 'Critère d\'évaluation'
    
    name = fields.Char(string='Nom', required=True)
    description = fields.Text(string='Description')
    poids = fields.Float(string='Pondération (%)', required=True)
    active = fields.Boolean(string='Actif', default=True)
    
    @api.constrains('poids')
    def _check_poids(self):
        for criteria in self:
            if criteria.poids <= 0 or criteria.poids > 100:
                raise ValidationError(_("La pondération doit être comprise entre 0 et 100%."))
```

### 8. Notes d'évaluation
```python
class EvaluationNote(models.Model):
    _name = 'e_gestock.evaluation_note'
    _description = 'Note d\'évaluation'
    
    evaluation_id = fields.Many2one('e_gestock.supplier_evaluation', string='Évaluation', required=True, ondelete='cascade')
    criteria_id = fields.Many2one('e_gestock.evaluation_criteria', string='Critère', required=True)
    note = fields.Float(string='Note (sur 5)', required=True)
    commentaire = fields.Text(string='Commentaire')
    
    @api.constrains('note')
    def _check_note(self):
        for record in self:
            if record.note < 0 or record.note > 5:
                raise ValidationError(_("La note doit être comprise entre 0 et 5."))
```

### 9. Extension des bons de commande


## Intégration avec les autres modules

### 1. Intégration avec le module e_gestock_purchase
- Récupération des informations fournisseur lors de la création des demandes d'achat
- Intégration avec le processus de cotation des demandes
- Contrôle des contrats actifs lors de la sélection des fournisseurs
- Mise à jour automatique des informations de cotation dans le portail

### 2. Intégration avec le module e_gestock_base
- Utilisation des structures organisationnelles pour la gestion des habilitations
- Association des fournisseurs aux familles d'articles

### 3. Intégration avec le portail
- Interface de soumission des cotations
- Visualisation des demandes d'achat en cours
- Notifications par email des nouvelles demandes et des changements d'état
- Accès aux contrats et historique des commandes

### 4. Rapports
- Rapports d'évaluation des fournisseurs
- Contrats en cours par fournisseur
- Statistiques des achats par fournisseur
- Analyses des performances 



## Notes de développement
- Tous les modèles ont été implémentés selon les spécifications
- Le portail fournisseur est entièrement fonctionnel avec affichage des contrats, certifications et évaluations
- Les vues et les contrôleurs permettent une gestion complète du cycle de vie des fournisseurs
- L'intégration avec l'API fournit une interface pour les systèmes externes
