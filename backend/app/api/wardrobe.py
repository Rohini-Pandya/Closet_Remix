
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthUser, get_current_user
from app.core.config import Settings, get_settings
from app.core.http import get_http
from app.database.supabase_rest import UserDB
from app.schemas.wardrobe import (
    WardrobeItemCreate,
    WardrobeItemOut,
    WardrobeItemUpdate,
)

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


def _db(
    client: httpx.AsyncClient = Depends(get_http),
    settings: Settings = Depends(get_settings),
    user: AuthUser = Depends(get_current_user),
) -> UserDB:
    return UserDB(client, settings, user)


@router.get("", response_model=list[WardrobeItemOut])
async def get_wardrobe(db: UserDB = Depends(_db)):
    return await db.select(
        "wardrobe_items",
        {"select": "*", "order": "created_at.desc"},
    )


@router.post(
    "",
    response_model=WardrobeItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_wardrobe_item(
    body: WardrobeItemCreate,
    user: AuthUser = Depends(get_current_user),
    db: UserDB = Depends(_db),
):
    values = body.model_dump()
    values["user_id"] = user.id

    rows = await db.insert("wardrobe_items", values)

    if not rows:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Could not create wardrobe item",
        )

    return rows[0]


@router.patch("/{item_id}", response_model=WardrobeItemOut)
async def update_wardrobe_item(
    item_id: UUID,
    body: WardrobeItemUpdate,
    db: UserDB = Depends(_db),
):
    values = body.model_dump(exclude_unset=True)

    if not values:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No changes provided",
        )

    rows = await db.update(
        "wardrobe_items",
        {"id": f"eq.{item_id}"},
        values,
    )

    if not rows:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Wardrobe item not found",
        )

    return rows[0]


@router.delete("/{item_id}")
async def delete_wardrobe_item(
    item_id: UUID,
    db: UserDB = Depends(_db),
):
    rows = await db.delete(
        "wardrobe_items",
        {"id": f"eq.{item_id}"},
    )

    if not rows:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Wardrobe item not found",
        )

    return {"ok": True}
