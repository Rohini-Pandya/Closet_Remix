# Architecture (as built through Phase 2)

Browser (React) ──REST + Bearer JWT──▶ FastAPI ──▶ Supabase (Auth verify, PostgREST as the user, Storage)
                                          └──▶ (Phase 3) RF-DETR service, Ollama

- Login/registration happen in the browser with Supabase Auth (anon key). The browser gets a JWT.
- Every API call sends `Authorization: Bearer <jwt>`. FastAPI verifies it via Supabase `GET /auth/v1/user` and uses ONLY that identity.
- FastAPI talks to Postgres through PostgREST **with the user's JWT**, so Row Level Security enforces ownership even if app code is wrong.
- No service-role key is used yet; when needed (Phase 3 cleanup) it stays in the backend only.
- Demo mode: if the frontend has no Supabase env vars it runs with mock data and no login.

## Data model decisions
- `outfits` holds one row per unique combination per user (`combo_key` = sorted item ids). Not-For-Me, saved and worn all reference the combination.
- saved / feedback / history use a composite FK `(outfit_id, user_id)` so rows can only point at the same user's outfits.
- `outfit_wear_history` has `unique (user_id, outfit_id, worn_on)` — double clicks cannot create duplicates.
- Deleting a wardrobe item deletes the outfits containing it (trigger) and, by cascade, their saved/feedback/history rows.
