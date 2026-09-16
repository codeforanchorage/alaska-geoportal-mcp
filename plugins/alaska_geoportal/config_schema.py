"""Pydantic configuration schema for the Alaska Geoportal plugin."""

import re
from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

_HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")
_HOSTNAME = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


class PartnerOrg(BaseModel):
    """An Alaska partner organization whose layers this server may proxy.

    The Geoportal catalog spans content from boroughs and other state
    agencies that publish under their own ArcGIS Online organizations.
    Listing one here extends the tenant allowlist: items owned by
    ``org_id`` pass the ownership check, ``services*.arcgis.com/<org_id>``
    URLs pass the service-URL allowlist, and any ``hosts`` (the org's own
    ArcGIS Server, e.g. ``maps.matsugov.us``) are accepted by exact match.
    """

    org_id: str = Field(..., min_length=8, description="ArcGIS organization ID")
    name: str = Field(..., min_length=1, description="Display name used to label results")
    hosts: List[str] = Field(
        default_factory=list,
        description="Extra on-prem hostnames to accept (exact match, lowercase)",
    )

    @field_validator("hosts")
    @classmethod
    def validate_hosts(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        for h in v:
            h = (h or "").strip().lower()
            if not _HOSTNAME.match(h):
                raise ValueError(
                    f"partner host {h!r} must be a bare lowercase hostname "
                    f"(no scheme, path or wildcard)"
                )
            if h not in cleaned:
                cleaned.append(h)
        return cleaned

    model_config = ConfigDict(extra="forbid")


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
    partner_orgs: List[PartnerOrg] = Field(
        default_factory=list,
        description=(
            "Alaska partner organizations (boroughs, other state agencies) "
            "whose items and services are also allowed. Federal tenants "
            "are deliberately not listed."
        ),
    )
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
            if not _HEX32.match(gid):
                raise ValueError(
                    f"gallery_group_ids entry {gid!r} is not a 32-character "
                    f"hex ArcGIS group id"
                )
            if gid.lower() not in cleaned:
                cleaned.append(gid.lower())
        return cleaned

    @field_validator("partner_orgs")
    @classmethod
    def validate_partner_orgs(cls, v: List[PartnerOrg]) -> List[PartnerOrg]:
        seen = set()
        for p in v:
            key = p.org_id.lower()
            if key in seen:
                raise ValueError(f"partner_orgs lists org_id {p.org_id!r} twice")
            seen.add(key)
        return v

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
