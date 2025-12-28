# SIRET Extractor

Application web pour extraire les informations legales d'entreprises francaises a partir de numeros SIRET.

## Fonctionnalites

- Extraction de donnees depuis l'API INSEE SIRENE (raison sociale, adresse, APE, forme juridique)
- Extraction de donnees depuis l'API RNE INPI (capital social, dirigeants)
- Upload de fichiers CSV ou saisie manuelle de SIRET
- Export des resultats en CSV ou Excel
- Interface moderne avec mode sombre
- Gestion du rate limiting et des erreurs

## Donnees extraites

| Champ | Source |
|-------|--------|
| Raison sociale | INSEE |
| RCS | Calcule |
| Forme juridique | INSEE |
| Capital | RNE |
| TVA Intracommunautaire | Calcule |
| Code APE | INSEE |
| Adresse | INSEE |
| Dirigeant (nom, prenom, fonction) | RNE |

## Installation

### Prerequis

- Python 3.11+
- Node.js 18+
- Docker et Docker Compose (optionnel)

### Configuration

1. Copiez le fichier `.env.example` vers `.env` :
   ```bash
   cp .env.example .env
   ```

2. Renseignez vos cles API dans le fichier `.env` :
   ```env
   INSEE_API_KEY=votre-cle-insee
   RNE_JWT_TOKEN=votre-token-jwt-rne
   ```

### Obtenir les cles API

#### API INSEE SIRENE

1. Creez un compte sur [api.insee.fr](https://api.insee.fr)
2. Abonnez-vous a l'API SIRENE
3. Recuperez votre cle API dans votre espace personnel

#### API RNE (INPI)

1. Creez un compte sur [data.inpi.fr](https://data.inpi.fr)
2. Generez un token JWT dans votre espace
3. **Note**: Le token expire periodiquement (voir date d'expiration dans le payload JWT)

### Demarrage avec Docker (recommande)

```bash
docker-compose up -d
```

L'application sera accessible sur http://localhost

### Demarrage sans Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

Le backend sera accessible sur http://localhost:8000

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Le frontend sera accessible sur http://localhost:5173

## Utilisation

1. Ouvrez l'application dans votre navigateur
2. Uploadez un fichier CSV contenant les SIRET ou saisissez-les manuellement
3. Cliquez sur "Extraire les informations"
4. Attendez la fin du traitement
5. Telechargez les resultats en CSV ou Excel

### Format du fichier CSV

Le fichier CSV peut avoir :
- Une seule colonne avec les numeros SIRET
- Ou une colonne nommee "SIRET" parmi d'autres colonnes

Exemple :
```csv
SIRET
94346082400015
85126724500013
87891869700029
```

## API Endpoints

| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/extract` | Demarre une extraction avec liste de SIRET |
| POST | `/api/upload` | Upload un fichier CSV |
| GET | `/api/job/{id}/status` | Statut d'un job |
| GET | `/api/job/{id}/results` | Resultats d'un job |
| GET | `/api/job/{id}/download` | Telecharge les resultats |

## Renouvellement du token RNE

Le token JWT de l'API RNE expire periodiquement. Pour le renouveler :

1. Connectez-vous a [data.inpi.fr](https://data.inpi.fr)
2. Allez dans votre espace personnel > API
3. Generez un nouveau token
4. Mettez a jour la variable `RNE_JWT_TOKEN` dans le fichier `.env`
5. Redemarrez l'application

## Rate Limiting

- **API INSEE** : 30 requetes/minute (gere automatiquement)
- **API RNE** : Limites non documentees, backoff exponentiel en cas d'erreur

## Structure du projet

```
siret-extractor/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── services/
│   │   ├── insee_client.py  # Client API INSEE
│   │   ├── rne_client.py    # Client API RNE
│   │   └── data_processor.py
│   ├── models/
│   │   └── schemas.py       # Modeles Pydantic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── services/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Tests

```bash
cd backend
pytest tests/ -v
```

## Licence

MIT
