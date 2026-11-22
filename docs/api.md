# API contracts (implemented so far)
Base URL: `http://localhost:8000/api`. All endpoints except /health need `Authorization: Bearer <supabase access token>`.

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| GET | /health | no | – | `{status, supabase_configured}` |
| GET | /ai/status | yes | – | placeholder `{implemented:false,...}` until Phase 3 |
| GET | /profile | yes | – | `{id, full_name, email, created_at, updated_at}` |
| PUT | /profile | yes | `{full_name}` (1–100 chars; unknown fields → 422) | updated profile |

Errors: 401 missing/invalid token, 422 validation, 503 Supabase unreachable/not configured, 502 database error.
Remaining endpoints from the master plan are unchanged and will be documented as they are built.
