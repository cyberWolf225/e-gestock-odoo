# Module API (e_gestock_api)

## Description
Le module e_gestock_api fournit une interface d'accès programmatique à la solution E-GESTOCK via une API REST sécurisée. Ce module est spécialement conçu pour les applications mobiles et systèmes externes qui ont besoin d'interagir avec les données E-GESTOCK.

## Dépendances
- e_gestock_base
- base
- mail
- web

## Fonctionnalités principales

### 1. API REST pour application mobile

#### 1.1 Infrastructure d'API
- Exposition d'une API REST sécurisée pour l'application mobile
- Authentification par token JWT pour sécuriser les accès
- Protection contre les attaques CSRF et XSS
- Mécanismes de rate-limiting pour éviter les abus
- Validation stricte des entrées utilisateur
- Journalisation des accès pour audit de sécurité
- Documentation interactive avec Swagger/OpenAPI

#### 1.2 Endpoints principaux
L'API exposera les endpoints suivants:
- `/api/v1/auth` - Authentification et rafraîchissement des jetons
- `/api/v1/products` - Accès aux informations des produits
- `/api/v1/products/qr/{code}` - Lecture des articles via code QR
- `/api/v1/stocks` - Consultation des niveaux de stock
- `/api/v1/suppliers` - Informations sur les fournisseurs
- `/api/v1/movements` - Historique des mouvements de stock

#### 1.3 Authentification et sécurité
- Utilisation obligatoire du protocole HTTPS
- Authentification par jetons JWT avec signature sécurisée
- Durée de validité configurable des jetons
- Mécanisme de rafraîchissement des jetons
- Contrôles d'accès basés sur les profils utilisateur
- Groupe de sécurité spécifique `group_e_gestock_api_mobile`

### 2. Gestion des codes QR

#### 2.1 Génération de codes QR
- Génération automatique de codes QR uniques pour chaque article
- Stockage du code QR dans la fiche article (e_gestock.article)
- Possibilité d'imprimer des étiquettes avec code QR
- Service de régénération des codes QR

#### 2.2 Lecture des codes QR
- Endpoint dédié pour la lecture d'informations via code QR
- Structure de réponse standardisée avec toutes les informations pertinentes
- Statistiques d'utilisation des codes QR

### 3. Intégration avec systèmes externes

#### 3.1 Webhooks
- Configuration de webhooks pour notifier les systèmes externes des événements clés
- Gestion des abonnements aux événements
- Traçabilité des notifications envoyées

#### 3.2 Export de données
- Services d'export de données dans des formats standards (JSON, CSV)
- Filtrage des données exportées
- Compression des données pour optimiser la bande passante

## Modèles de données

### 1. Jetons d'API (e_gestock.api_token)
- `user_id` : Utilisateur associé
- `token` : Jeton JWT généré
- `expiration_date` : Date d'expiration
- `is_valid` : État de validité
- `refresh_token` : Jeton de rafraîchissement
- `ip_address` : Dernière adresse IP utilisée
- `user_agent` : Information sur le client
- `last_used` : Dernière utilisation

### 2. Logs d'accès API (e_gestock.api_log)
- `user_id` : Utilisateur associé
- `endpoint` : Endpoint accédé
- `method` : Méthode HTTP (GET, POST, etc.)
- `status_code` : Code de statut HTTP
- `ip_address` : Adresse IP
- `user_agent` : Information sur le client
- `request_time` : Heure de la requête
- `response_time` : Temps de réponse
- `request_data` : Données de la requête
- `response_data` : Données de la réponse

### 3. Configuration API (e_gestock.api_config)
- `token_validity` : Durée de validité des jetons (en heures)
- `rate_limit` : Limite de requêtes par minute
- `max_failed_attempts` : Nombre maximal de tentatives d'authentification échouées
- `block_duration` : Durée de blocage après échec (en minutes)
- `log_level` : Niveau de journalisation
- `active_endpoints` : Liste des endpoints activés

## Contrôleurs

### Authentification
```python
@http.route('/api/v1/auth/token', type='json', auth='none', methods=['POST'], csrf=False)
def get_token(self, login, password, **kw):
    # Authentification et génération du token JWT
    pass

@http.route('/api/v1/auth/refresh', type='json', auth='jwt', methods=['POST'], csrf=False)
def refresh_token(self, **kw):
    # Rafraîchissement du token
    pass

@http.route('/api/v1/auth/verify', type='json', auth='jwt', methods=['POST'], csrf=False)
def verify_token(self, **kw):
    # Vérification de la validité du token
    pass
```

### Gestion des produits
```python
@http.route('/api/v1/products', type='http', auth='jwt', methods=['GET'])
def get_products(self, **kw):
    # Récupération des produits avec filtres
    pass

@http.route('/api/v1/products/<int:product_id>', type='http', auth='jwt', methods=['GET'])
def get_product(self, product_id, **kw):
    # Récupération d'un produit spécifique
    pass

@http.route('/api/v1/products/qr/<code>', type='http', auth='jwt', methods=['GET'])
def get_product_by_qr(self, code, **kw):
    # Récupération des informations produit via QR code
    product = request.env['e_gestock.article'].sudo().search([('qr_code', '=', code)], limit=1)
    if not product:
        return http.Response(json.dumps({'error': 'Product not found'}), 
                          status=404, content_type='application/json')
    
    # Construction de la réponse avec toutes les infos requises
    data = {
        'article': {
            'ref': product.ref_article,
            'designation': product.design_article,
            'famille': product.famille_id.design_fam,
            'description': product.description or '',
        },
        'fournisseur': {
            'nom': product.last_supplier_id.name,
            'contact': product.last_supplier_id.phone,
        },
        'stock': {
            'quantite_disponible': product.get_stock_quantity(),
            'depots': product.get_stock_by_depot(),
        },
        'mouvements': product.get_recent_movements(),
    }
    
    return http.Response(json.dumps(data), 
                       status=200, content_type='application/json')
```

### Gestion des stocks
```python
@http.route('/api/v1/stocks', type='http', auth='jwt', methods=['GET'])
def get_stocks(self, **kw):
    # Récupération des niveaux de stock avec filtres
    pass

@http.route('/api/v1/stocks/depot/<int:depot_id>', type='http', auth='jwt', methods=['GET'])
def get_depot_stock(self, depot_id, **kw):
    # Récupération des stocks par dépôt
    pass
```

### Mouvements de stock
```python
@http.route('/api/v1/movements', type='http', auth='jwt', methods=['GET'])
def get_movements(self, **kw):
    # Récupération des mouvements de stock avec filtres
    pass

@http.route('/api/v1/movements/<int:movement_id>', type='http', auth='jwt', methods=['GET'])
def get_movement(self, movement_id, **kw):
    # Récupération d'un mouvement spécifique
    pass
```

### Fournisseurs
```python
@http.route('/api/v1/suppliers', type='http', auth='jwt', methods=['GET'])
def get_suppliers(self, **kw):
    # Récupération des fournisseurs avec filtres
    pass

@http.route('/api/v1/suppliers/<int:supplier_id>', type='http', auth='jwt', methods=['GET'])
def get_supplier(self, supplier_id, **kw):
    # Récupération d'un fournisseur spécifique
    pass
```

## Documentation et sécurité

### 1. Documentation API
- Interface Swagger/OpenAPI accessible via `/api/v1/docs`
- Documentation détaillée de chaque endpoint
- Exemples de requêtes et réponses
- Guide d'authentification

### 2. Sécurité
- Validation stricte des entrées
- Protection contre les injections SQL
- Limitation des tentatives d'authentification
- Journalisation des accès
- Vérification des permissions utilisateur
- Validation des jetons JWT

### 3. Logging et audit
- Journalisation complète de toutes les requêtes API
- Alertes en cas d'accès suspect
- Tableaux de bord d'utilisation de l'API
- Rapports d'audit périodiques

## Structure du module

```
e_gestock_api/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   ├── api_token.py
  │   ├── api_log.py
  │   └── api_config.py
  ├── controllers/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── auth.py
  │   ├── products.py
  │   ├── stocks.py
  │   ├── movements.py
  │   └── suppliers.py
  ├── security/
  │   ├── ir.model.access.csv
  │   └── e_gestock_api_security.xml
  ├── views/
  │   ├── api_views.xml
  │   └── menu_views.xml
  ├── static/
  │   ├── description/
  │   │   └── icon.png
  │   └── src/
  │       ├── js/
  │       │   └── swagger.js
  │       └── css/
  │           └── swagger.css
  └── data/
      └── api_config_data.xml
```

## Intégration avec l'application mobile

### 1. Points de connexion
- Authentification sécurisée par token JWT
- Endpoints optimisés pour les appareils mobiles
- Format de données JSON léger

### 2. Fonctionnalités mobiles
- Scan des codes QR
- Consultation des informations produit
- Visualisation des niveaux de stock
- Historique des mouvements
- Accès aux informations fournisseurs 