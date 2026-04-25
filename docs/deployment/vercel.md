# Vercel Deployment

This guide assumes:

- the repository stays monorepo-style
- the Vercel project root directory is set to `frontend`
- the included [`frontend/vercel.json`](../../frontend/vercel.json) is committed

## Steps

1. Create a new Vercel project and import this Git repository.
2. In the Vercel project settings, set **Root Directory** to `frontend`.
3. Keep the detected framework as **Next.js**.
4. Use the default build command `npm run build`.
5. Leave Output Directory empty so Vercel uses the Next.js default.
6. Add these environment variables in the Vercel dashboard:
   - `NEXT_PUBLIC_API_URL=https://your-backend-service.onrender.com`
   - `NEXT_PUBLIC_SITE_URL=https://your-frontend-domain.vercel.app`
   - `NEXT_PUBLIC_APP_NAME=AlgoTrade Sentinel`
   - `INTERNAL_API_URL=https://your-backend-service.onrender.com`
7. Trigger a production deployment from the dashboard or push to `main`.
8. After deploy, open `/api/health` on the Vercel domain to verify frontend-to-backend connectivity.

## CLI flow

```bash
cd frontend
npx vercel pull --yes --environment=production
npx vercel build --prod
npx vercel deploy --prebuilt --prod
```

## Notes

- Vercel automatically detects Next.js and uses the project-level build settings for the `frontend` root.
- If you use preview deployments, set a preview-safe `NEXT_PUBLIC_API_URL` as well.

## References

- Vercel builds: https://vercel.com/docs/deployments/builds/
- Vercel build configuration: https://vercel.com/docs/deployments/configure-a-build
- Vercel environment variables: https://vercel.com/docs/environment-variables
- Vercel CLI deploy: https://vercel.com/docs/cli/deploy
