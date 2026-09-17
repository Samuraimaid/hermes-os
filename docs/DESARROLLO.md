# Desarrollo

## Requisitos

- Docker Desktop o Docker Engine + Compose
- O bien: Python 3.12+, Node 20+, PostgreSQL 16

## Con Docker

```bash
cp .env.example .env
docker compose up --build
```

## Sin Docker (API)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Sin Docker (app)

```bash
cd frontend
npm install
npm run dev
```

La app de desarrollo apunta a `http://localhost:8000` si no hay `VITE_API_URL`.
