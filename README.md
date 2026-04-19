# AD Recon & Attack Path Mapper

Outil complet pour l'énumération Active Directory, la détection de mauvaises configurations, la visualisation des chemins d'attaque et la génération de rapports PDF.

## Stack technique

| Composant  | Technologie              |
|------------|--------------------------|
| Backend    | Python 3.12 + FastAPI    |
| Base de données | Neo4j 5.x (graphe) |
| Frontend   | React 18 + D3.js         |
| Serveur web | Nginx                   |
| Conteneurs | Docker + Docker Compose  |

## Prérequis

- Docker ≥ 24
- Docker Compose ≥ 2.20

## Démarrage rapide

```bash
# Cloner le projet
git clone <repo> ad-mapper
cd ad-mapper

# Lancer tous les services
docker compose up --build -d

# Vérifier que tout tourne
docker compose ps
```

L'interface est accessible sur : **http://localhost**

L'API FastAPI (docs Swagger) : **http://localhost:8000/docs**

Neo4j Browser : **http://localhost:7474** (neo4j / adm4pp3r2025)

## Utilisation

### 1. Reconnaissance AD

Rendez-vous sur `/recon` et renseignez :
- IP ou FQDN du contrôleur de domaine
- Nom du domaine (ex: `corp.local`)
- Identifiants d'un compte avec accès LDAP

La reconnaissance énumère :
- Utilisateurs, groupes, machines, OUs
- SPNs (Kerberoastables), adminCount, statuts

### 2. Graphe AD

Visualisation D3 force-directed des relations AD :
- Cliquez sur un nœud pour voir ses propriétés
- Les nœuds à risque élevé sont entourés d'un anneau rouge
- Zoom / déplacement / drag & drop

### 3. Mauvaises configurations

Détection automatique de :
- Comptes admin Kerberoastables (CVSS 8.8)
- Systèmes EOL / obsolètes (CVSS 9.8)
- Comptes admin dormants
- Mots de passe > 1 an
- Groupes privilégiés surchargés
- Descriptions sensibles exposées

### 4. Chemins d'attaque

Scénarios d'exploitation priorisés par sévérité avec étapes détaillées.

### 5. Rapport PDF

Génération d'un rapport Red Team complet avec :
- Page de couverture classifiée
- Résumé exécutif avec statistiques
- Toutes les mauvaises configurations avec preuves
- Chemins d'attaque documentés
- Recommandations priorisées (J+0 / J+30 / J+90)

## Structure du projet

```
ad-mapper/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/          # Routes FastAPI
│       ├── core/         # Config, DB
│       ├── models/       # Schémas Pydantic
│       └── services/     # Logique métier
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── pages/        # Dashboard, Recon, Graph...
        ├── components/   # Layout, Sidebar
        └── utils/        # Client API
```

## Arrêter les services

```bash
docker compose down

# Supprimer aussi les volumes (données Neo4j, rapports)
docker compose down -v
```

## Avertissement légal

Cet outil est destiné à un usage **éducatif et dans le cadre de missions Red Team autorisées** uniquement. Toute utilisation sur des systèmes sans autorisation explicite est illégale.
