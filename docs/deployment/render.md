# Render Deployment

This guide deploys the FastAPI backend from the repository root with the included [`render.yaml`](../../render.yaml).

## Steps

1. Create a new Render Blueprint and connect this repository.
2. Confirm Render reads `render.yaml` from the repo root.
3. Keep the backend service type as **Web Service** and runtime as **Docker**.
4. Make sure the service uses:
   - Dockerfile path: `./backend/Dockerfile`
   - Docker build context: `.`
   - Health check path: `/health`
5. Add or update these environment variables in Render:
   - `FRONTEND_URL=https://your-frontend-domain.vercel.app`
   - `CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]`
   - `DATABASE_URL=<your-supabase-pooled-postgres-url>`
   - `SECRET_KEY=<long-random-secret>`
   - `MLFLOW_TRACKING_URI=<your-mlflow-url-or-file-uri>`
   - `PREFECT_API_URL=<optional-prefect-url>`
   - `ENABLE_APSCHEDULER=true`
6. Deploy the service and verify:
   - `/health`
   - `/api/system/status`

## Using a Deploy Hook

Create a Render deploy hook for the service and store it as the GitHub secret `RENDER_DEPLOY_HOOK_URL`. The included deploy workflow calls that hook on pushes to `main`.

## Notes

- The Docker image copies `backend`, `ml`, `mlops`, `config`, and `scripts`, so monitoring and scheduled flows can run inside the Render container.
- If you do not run Prefect separately, the backend falls back to APScheduler.
- Render free web services use an ephemeral filesystem, so do not rely on local ML artifacts for long-term persistence there. Use Supabase for the database and an external artifact store or hosted MLflow when you need persistence.

## References

- Render FastAPI guide: https://render.com/docs/deploy-fastapi
- Render health checks: https://render.com/docs/health-checks
- Render Blueprint spec: https://render.com/docs/blueprint-spec
- Render environment variables: https://render.com/docs/environment-variables
- Render free tier limitations: https://render.com/docs/free
- Render persistent disks: https://render.com/docs/disks
