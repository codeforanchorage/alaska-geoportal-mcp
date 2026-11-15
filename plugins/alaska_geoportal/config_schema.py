"""Pydantic configuration schema for the Alaska Geoportal plugin."""

from typing import List

from pydantic import Field, field_validator

from arcgis_hub.config_schema import (
    HubConfigBase,
    PartnerOrg,
    validate_group_id_list,
    validate_partner_org_list,
)

__all__ = ["AlaskaGeoportalPluginConfig", "PartnerOrg"]


class AlaskaGeoportalPluginConfig(HubConfigBase):
    """Configuration schema for the Alaska Geoportal plugin.

    Validates plugin configuration for accessing the State of Alaska
    Geoportal -- the Alaska Geospatial Office's ArcGIS Online
    organization -- through the ArcGIS Portal REST API. The shared fields
    (portal_base_url, org_id, city_name, gallery_url, timeout) and
    `PartnerOrg` come from opencontext-arcgis-hub.
    """

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
    partner_orgs: List[PartnerOrg] = Field(
        default_factory=list,
        description=(
            "Alaska partner organizations (boroughs, other state agencies) "
            "whose items and services are also allowed. Federal tenants "
            "are deliberately not listed."
        ),
    )

    @field_validator("gallery_group_ids")
    @classmethod
    def validate_group_ids(cls, v: List[str]) -> List[str]:
        """Every group id must be a 32-char hex ArcGIS id."""
        return validate_group_id_list(v)

    @field_validator("partner_orgs")
    @classmethod
    def validate_partner_orgs(cls, v: List[PartnerOrg]) -> List[PartnerOrg]:
        return validate_partner_org_list(v)
