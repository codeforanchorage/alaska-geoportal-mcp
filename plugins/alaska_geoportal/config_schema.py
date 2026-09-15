"""Pydantic configuration schema for the Alaska Geoportal plugin."""

from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlaskaGeoportalPluginConfig(BaseModel):
    """Configuration schema for the Alaska Geoportal plugin.

    This schema validates plugin configuration for accessing the State of
    Alaska Geoportal -- the Alaska Geospatial Office's ArcGIS Online
    organization -- through the ArcGIS Portal REST API.
    """

    enabled: bool = Field(default=False, description="Whether plugin is enabled")
    portal_base_url: str = Field(
        ...,
        description=(
            "Base URL of ArcGIS Portal REST API "
            "(e.g., https://soa-dnr.maps.arcgis.com/sharing/rest)"
        ),
    )
    gallery_group_ids: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "ArcGIS group IDs whose union is the public Geoportal catalog. "
            "The Hub site's catalog spans one group per publishing "
            "division, so browse_gallery / find_gis_content search all of "
            "them in one query."
        ),
    )
    org_id: str = Field(..., description="ArcGIS organization ID")
    city_name: str = Field(
        ..., description="Name of the organization / jurisdiction"
    )
    gallery_url: str = Field(
        ..., description="Public URL for the Geoportal search page"
    )
    timeout: int = Field(
        default=30, ge=1, le=300, description="HTTP request timeout in seconds"
    )

    @field_validator("portal_base_url")
    @classmethod
    def validate_portal_url(cls, v: str) -> str:
        """Validate that portal URL is well-formed."""
        if not v:
            raise ValueError("portal_base_url cannot be empty")
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError("URL must include scheme (http/https) and hostname")
            if result.scheme not in ("http", "https"):
                raise ValueError("URL scheme must be http or https")
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}")
        return v.rstrip("/")

    @field_validator("gallery_group_ids")
    @classmethod
    def validate_group_ids(cls, v: List[str]) -> List[str]:
        """Every group id must be a 32-char hex ArcGIS id.

        The ids are interpolated into a portal search query, so anything
        else would at best silently return nothing and at worst let a
        config typo widen the search.
        """
        cleaned: List[str] = []
        for gid in v:
            gid = (gid or "").strip()
            if len(gid) != 32 or any(
                c not in "0123456789abcdefABCDEF" for c in gid
            ):
                raise ValueError(
                    f"gallery_group_ids entry {gid!r} is not a 32-character "
                    f"hex ArcGIS group id"
                )
            if gid.lower() not in cleaned:
                cleaned.append(gid.lower())
        return cleaned

    @field_validator("gallery_url")
    @classmethod
    def validate_gallery_url(cls, v: str) -> str:
        """Validate that gallery URL is well-formed."""
        if not v:
            raise ValueError("gallery_url cannot be empty")
        try:
            result = urlparse(v)
            if not result.scheme or not result.netloc:
                raise ValueError("URL must include scheme (http/https) and hostname")
        except Exception as e:
            raise ValueError(f"Invalid gallery URL format: {e}")
        return v

    model_config = ConfigDict(extra="forbid")
