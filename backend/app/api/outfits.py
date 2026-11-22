
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthUser, get_current_user
from app.core.config import Settings, get_settings
from app.core.http import get_http
from app.database.supabase_rest import UserDB
from app.schemas.outfits import OutfitCreate

router = APIRouter(prefix="/outfits", tags=["outfits"])


def _db(
    client: httpx.AsyncClient = Depends(get_http),
    settings: Settings = Depends(get_settings),
    user: AuthUser = Depends(get_current_user),
) -> UserDB:
    return UserDB(client, settings, user)


async def _get_outfit(db: UserDB, outfit_id: str):
    outfits = await db.select(
        "outfits",
        {"select": "*", "id": f"eq.{outfit_id}"},
    )

    if not outfits:
        return None

    outfit = outfits[0]

    links = await db.select(
        "outfit_items",
        {"select": "wardrobe_item_id", "outfit_id": f"eq.{outfit_id}"},
    )

    item_ids = [row["wardrobe_item_id"] for row in links]

    items = []
    if item_ids:
        items = await db.select(
            "wardrobe_items",
            {"select": "*", "id": f"in.({','.join(item_ids)})"},
        )

    outfit["items"] = items
    return outfit


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_outfit(
    body: OutfitCreate,
    user: AuthUser = Depends(get_current_user),
    db: UserDB = Depends(_db),
):
    try:
        item_ids = list(
            dict.fromkeys(str(UUID(item_id)) for item_id in body.wardrobe_item_ids)
        )
    except ValueError:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid wardrobe item ID",
        )

    if not item_ids:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "At least one wardrobe item is required",
        )

    owned_items = await db.select(
        "wardrobe_items",
        {
            "select": "id",
            "id": f"in.({','.join(item_ids)})",
        },
    )

    if len(owned_items) != len(item_ids):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "One or more wardrobe items were not found",
        )

    combo_key = ",".join(sorted(item_ids))

    existing = await db.select(
        "outfits",
        {"select": "id", "combo_key": f"eq.{combo_key}"},
    )

    if existing:
        outfit_id = existing[0]["id"]
    else:
        values = body.model_dump(exclude={"wardrobe_item_ids"})
        values["user_id"] = user.id
        values["combo_key"] = combo_key

        created = await db.insert("outfits", values)

        if not created:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "Could not create outfit",
            )

        outfit_id = created[0]["id"]

    existing_links = await db.select(
        "outfit_items",
        {"select": "wardrobe_item_id", "outfit_id": f"eq.{outfit_id}"},
    )
    linked_ids = {row["wardrobe_item_id"] for row in existing_links}

    for item_id in item_ids:
        if item_id not in linked_ids:
            await db.insert(
                "outfit_items",
                {
                    "outfit_id": outfit_id,
                    "wardrobe_item_id": item_id,
                },
            )

    result = await _get_outfit(db, outfit_id)

    if not result:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Outfit could not be retrieved",
        )

    return result


@router.get("/saved")
async def get_saved_outfits(db: UserDB = Depends(_db)):
    saved_rows = await db.select(
        "saved_outfits",
        {"select": "*", "order": "saved_at.desc"},
    )

    results = []

    for saved in saved_rows:
        outfit = await _get_outfit(db, saved["outfit_id"])

        if not outfit:
            continue

        history = await db.select(
            "outfit_wear_history",
            {
                "select": "worn_at",
                "outfit_id": f"eq.{saved['outfit_id']}",
                "order": "worn_at.desc",
                "limit": "1",
            },
        )

        outfit["saved_at"] = saved["saved_at"]
        outfit["worn"] = bool(history)
        outfit["last_worn_at"] = history[0]["worn_at"] if history else None

        results.append(outfit)

    return results


@router.get("/saved-ids")
async def get_saved_ids(db: UserDB = Depends(_db)):
    rows = await db.select(
        "saved_outfits",
        {"select": "outfit_id"},
    )
    return [row["outfit_id"] for row in rows]


@router.get("/worn-today-ids")
async def get_worn_today_ids(db: UserDB = Depends(_db)):
    rows = await db.select(
        "outfit_wear_history",
        {
            "select": "outfit_id",
            "worn_on": f"eq.{date.today().isoformat()}",
        },
    )
    return list({row["outfit_id"] for row in rows})


@router.post("/{outfit_id}/save")
async def save_outfit(
    outfit_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: UserDB = Depends(_db),
):
    outfit = await _get_outfit(db, str(outfit_id))

    if not outfit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outfit not found")

    existing = await db.select(
        "saved_outfits",
        {"select": "id", "outfit_id": f"eq.{outfit_id}"},
    )

    if not existing:
        await db.insert(
            "saved_outfits",
            {
                "user_id": user.id,
                "outfit_id": str(outfit_id),
            },
        )

    return {"ok": True}


@router.delete("/{outfit_id}/save")
async def remove_saved_outfit(
    outfit_id: UUID,
    db: UserDB = Depends(_db),
):
    await db.delete(
        "saved_outfits",
        {"outfit_id": f"eq.{outfit_id}"},
    )
    return {"ok": True}


@router.post("/{outfit_id}/feedback")
async def mark_not_for_me(
    outfit_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: UserDB = Depends(_db),
):
    outfit = await _get_outfit(db, str(outfit_id))

    if not outfit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outfit not found")

    existing = await db.select(
        "outfit_feedback",
        {
            "select": "id",
            "outfit_id": f"eq.{outfit_id}",
            "feedback_type": "eq.NOT_FOR_ME",
        },
    )

    if not existing:
        await db.insert(
            "outfit_feedback",
            {
                "user_id": user.id,
                "outfit_id": str(outfit_id),
                "feedback_type": "NOT_FOR_ME",
            },
        )

    return {"ok": True}


@router.post("/{outfit_id}/worn")
async def mark_outfit_worn(
    outfit_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: UserDB = Depends(_db),
):
    outfit = await _get_outfit(db, str(outfit_id))

    if not outfit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Outfit not found")

    today = date.today().isoformat()

    existing = await db.select(
        "outfit_wear_history",
        {
            "select": "id",
            "outfit_id": f"eq.{outfit_id}",
            "worn_on": f"eq.{today}",
        },
    )

    if not existing:
        await db.insert(
            "outfit_wear_history",
            {
                "user_id": user.id,
                "outfit_id": str(outfit_id),
                "occasion": outfit.get("occasion"),
                "worn_on": today,
            },
        )

    return {"ok": True}


@router.get("/history")
async def get_outfit_history(db: UserDB = Depends(_db)):
    rows = await db.select(
        "outfit_wear_history",
        {
            "select": "*",
            "order": "worn_at.desc",
        },
    )

    counts = {}
    for row in rows:
        outfit_id = row["outfit_id"]
        counts[outfit_id] = counts.get(outfit_id, 0) + 1

    results = []
    recent_limit = datetime.now(timezone.utc) - timedelta(days=7)

    for row in rows:
        outfit = await _get_outfit(db, row["outfit_id"])

        if not outfit:
            continue

        worn_at = datetime.fromisoformat(
            row["worn_at"].replace("Z", "+00:00")
        )

        repeat_count = counts[row["outfit_id"]]

        results.append(
            {
                "id": row["id"],
                "worn_at": row["worn_at"],
                "occasion": row.get("occasion"),
                "outfit": outfit,
                "recently_worn": worn_at >= recent_limit,
                "repeated": repeat_count > 1,
                "repeat_count": repeat_count,
            }
        )

    return results
