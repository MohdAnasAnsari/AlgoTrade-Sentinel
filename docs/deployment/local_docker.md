# Local Docker Compose

From a fresh clone, you can bring up the full stack in roughly 10 commands.

## Quick start

```bash
copy .env.example .env
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d db mlflow prefect
docker compose -f docker-compose.yml run --rm backend /bin/sh /app/scripts/init_db.sh
docker compose -f docker-compose.yml run --rm backend /bin/sh /app/scripts/seed_data.sh
docker compose -f docker-compose.yml up -d backend frontend
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml logs backend --tail 50
docker compose -f docker-compose.yml logs frontend --tail 50
start http://localhost:3000
```

## URLs

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- MLflow: http://localhost:5000
- Prefect: http://localhost:4200

## Daily commands

```bash
make dev
make prod
make migrate
make seed
make down
```

## Notes

- Use `docker-compose.dev.yml` when you want live reload for both the frontend and backend.
- The backend mounts `ml_artifacts` at `/app/ml/artifacts` and runs Alembic on startup.
