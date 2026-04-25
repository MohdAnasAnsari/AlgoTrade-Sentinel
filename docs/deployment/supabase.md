# Supabase Setup

Supabase is the recommended free PostgreSQL provider for production.

## Create the project

1. Create a new Supabase project.
2. Open **Project Settings → Database**.
3. Copy the pooled Postgres connection string.
4. Replace the password placeholder with your database password.

Use the pooled connection string in:

- Render `DATABASE_URL`
- local `.env.production`

## Run migrations against Supabase

Option A: Alembic directly

```bash
$env:DATABASE_URL="postgresql://..."
cd backend
alembic upgrade head
```

Option B: Supabase CLI

```bash
supabase link
supabase db push --db-url "postgresql://..."
```

## Recommended connection choice

- Use the pooler connection string for long-running app traffic.
- Keep a direct connection string available for admin tools and one-off maintenance if your environment supports it.

## References

- Supabase connection strings: https://supabase.com/docs/reference/postgres/connection-strings
- Supabase database migrations: https://supabase.com/docs/guides/deployment/database-migrations
- Supabase CLI: https://supabase.com/docs/reference/cli/supabase-link
