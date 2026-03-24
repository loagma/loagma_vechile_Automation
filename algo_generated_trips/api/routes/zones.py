"""
Zone management API routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from api.models.zone import ZoneSummaryResponse, ZoneSummaryListResponse
from typing import Optional

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=ZoneSummaryListResponse)
def list_zones(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all zones
    """
    try:
        if skip < 0:
            raise HTTPException(status_code=400, detail="skip must be >= 0")
        if limit < 1 or limit > 500:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
        if status is not None and status not in {"active", "inactive"}:
            raise HTTPException(status_code=400, detail="status must be 'active' or 'inactive'")

        filters = []
        params = {"skip": skip, "limit": limit}

        if status is not None:
            filters.append("status = :status")
            params["status"] = status

        where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""

        count_query = f"SELECT COUNT(*) FROM trip_cards{where_clause}"
        total = db.execute(text(count_query), params).fetchone()[0]

        query = (
            "SELECT zone_id, zone_name, status, created_at "
            f"FROM trip_cards{where_clause} "
            "ORDER BY zone_id "
            "LIMIT :limit OFFSET :skip"
        )
        result = db.execute(text(query), params)
        zones = [
            ZoneSummaryResponse(
                zone_id=row[0],
                zone_name=row[1],
                status=row[2],
                created_at=row[3]
            )
            for row in result.fetchall()
        ]

        return ZoneSummaryListResponse(total=total, zones=zones)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
