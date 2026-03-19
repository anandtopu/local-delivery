from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_read_db, get_write_db
from app.models.orm import DistributionCenter, Inventory
from app.models.schemas import DCCreate, DCResponse

router = APIRouter()


@router.get("", response_model=list[DCResponse])
async def list_dcs(
    region: str | None = Query(None, description="Filter by region_id (first 3 digits of ZIP)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    read_db: AsyncSession = Depends(get_read_db),
):
    """List distribution centres, optionally filtered by region."""
    stmt = select(DistributionCenter).offset(skip).limit(limit)
    if region:
        stmt = stmt.where(DistributionCenter.region_id == region)
    result = await read_db.execute(stmt)
    dcs = result.scalars().all()

    # Enrich with inventory_count
    dc_ids = [dc.id for dc in dcs]
    inv_counts: dict[int, int] = {}
    if dc_ids:
        count_result = await read_db.execute(
            select(Inventory.dc_id, func.count(Inventory.id).label("cnt"))
            .where(Inventory.dc_id.in_(dc_ids), Inventory.quantity > 0)
            .group_by(Inventory.dc_id)
        )
        inv_counts = {row.dc_id: row.cnt for row in count_result}

    out = []
    for dc in dcs:
        d = DCResponse.model_validate(dc)
        d.inventory_count = inv_counts.get(dc.id, 0)
        out.append(d)
    return out


@router.get("/{dc_id}", response_model=DCResponse)
async def get_dc(
    dc_id: int,
    read_db: AsyncSession = Depends(get_read_db),
):
    """Get a single DC with its inventory count."""
    result = await read_db.execute(select(DistributionCenter).where(DistributionCenter.id == dc_id))
    dc = result.scalar_one_or_none()
    if dc is None:
        raise HTTPException(status_code=404, detail="Distribution center not found")

    count_result = await read_db.execute(
        select(func.count(Inventory.id)).where(Inventory.dc_id == dc_id, Inventory.quantity > 0)
    )
    inv_count = count_result.scalar_one() or 0

    resp = DCResponse.model_validate(dc)
    resp.inventory_count = inv_count
    return resp


@router.post("", response_model=DCResponse, status_code=201)
async def create_dc(
    payload: DCCreate,
    write_db: AsyncSession = Depends(get_write_db),
):
    """Create a new distribution centre. region_id is auto-computed from zipcode[:3]."""
    region_id = payload.zipcode[:3]
    dc = DistributionCenter(
        name=payload.name,
        lat=payload.lat,
        lng=payload.lng,
        zipcode=payload.zipcode,
        region_id=region_id,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        is_active=payload.is_active,
    )
    write_db.add(dc)
    await write_db.flush()
    await write_db.refresh(dc)
    resp = DCResponse.model_validate(dc)
    resp.inventory_count = 0
    return resp
