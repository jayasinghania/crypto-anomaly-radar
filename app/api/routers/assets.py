from fastapi import APIRouter

from app.config import ASSETS

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[str])
def list_assets() -> list[str]:
    """The basket of assets this pipeline tracks."""
    return ASSETS
