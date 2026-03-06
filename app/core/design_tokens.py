"""Design token models and brand configuration loader.

Pydantic v2 models mirroring ~/dev/DNS-Domain-Management/lib/types/brand.ts.
Loads brand configurations from config/brands.yaml.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

__all__ = [
    "ShadowStyle", "BrandLogo", "BrandColors", "BrandTypography",
    "BrandDesignSystem", "BrandPageConfig", "BrandConfig", "BrandConfigFull",
    "BrandRegistry", "load_brands", "get_brand", "get_google_fonts_url",
]

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_BRANDS_PATH = Path("config/brands.yaml")


class ShadowStyle(str, Enum):
    """Shadow style preference for brand design system."""
    SOFT = "soft"
    SHARP = "sharp"
    NONE = "none"


def _validate_hex(v: str) -> str:
    """Validate hex color format (#RRGGBB)."""
    if not _HEX_COLOR_RE.match(v):
        raise ValueError(f"Invalid hex color: {v!r} (must be #RRGGBB)")
    return v.upper()


class BrandLogo(BaseModel):
    """Brand logo paths with variants."""
    primary: str
    white: str | None = None
    icon: str | None = None


class BrandColors(BaseModel):
    """Brand color palette."""
    primary: str
    secondary: str | None = None
    accent: str
    background: str
    text: str
    gradient: str | None = None
    palette: list[str] | None = None

    @field_validator("primary", "accent", "background", "text", mode="before")
    @classmethod
    def validate_required_colors(cls, v: str) -> str:
        return _validate_hex(v)

    @field_validator("secondary", mode="before")
    @classmethod
    def validate_optional_color(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_hex(v)


class BrandTypography(BaseModel):
    """Typography configuration."""
    headingFont: str = Field(alias="headingFont")
    bodyFont: str = Field(alias="bodyFont")

    model_config = {"populate_by_name": True}


class BrandDesignSystem(BaseModel):
    """Design system UI tokens."""
    borderRadius: str = Field(alias="borderRadius")
    shadowStyle: ShadowStyle = Field(alias="shadowStyle")

    model_config = {"populate_by_name": True}


class BrandPageConfig(BaseModel):
    """Page configuration for scanning."""
    url: str
    name: str
    waitFor: str | None = None


class BrandConfig(BaseModel):
    """Core brand configuration (matches TypeScript BrandConfig)."""
    name: str
    domain: str | None = None
    logo: BrandLogo
    colors: BrandColors
    typography: BrandTypography
    designSystem: BrandDesignSystem = Field(alias="designSystem")

    model_config = {"populate_by_name": True}


class BrandConfigFull(BrandConfig):
    """Extended brand config with metadata (matches TypeScript BrandConfigFull)."""
    key: str = ""
    shortName: str = Field(default="", alias="shortName")
    domains: list[str] = Field(default_factory=list)
    primaryDomain: str = Field(default="", alias="primaryDomain")
    pages: list[BrandPageConfig] = Field(default_factory=list)
    description: str | None = None
    logoUrl: str | None = None


class BrandRegistry(BaseModel):
    """Registry of all brand configurations."""
    brands: dict[str, BrandConfigFull]

    def keys(self) -> list[str]:
        return list(self.brands.keys())

    def get(self, key: str) -> BrandConfigFull | None:
        return self.brands.get(key)

    def __getitem__(self, key: str) -> BrandConfigFull:
        return self.brands[key]

    def __len__(self) -> int:
        return len(self.brands)

    def __iter__(self):
        return iter(self.brands)


def load_brands(path: Path = _BRANDS_PATH) -> BrandRegistry:
    """Load and validate brand configurations from YAML.

    Args:
        path: Path to brands.yaml file.

    Returns:
        BrandRegistry with validated brand configs.

    Raises:
        FileNotFoundError: If YAML file doesn't exist.
        ValueError: If validation fails.
    """
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    brands_raw: dict[str, Any] = raw.get("brands", {})
    brands: dict[str, BrandConfigFull] = {}

    for key, data in brands_raw.items():
        data["key"] = key
        if "domain" not in data and "primaryDomain" in data:
            data["domain"] = data["primaryDomain"]
        brands[key] = BrandConfigFull.model_validate(data)

    return BrandRegistry(brands=brands)


# Module-level cache
_registry: BrandRegistry | None = None


def get_brand(key: str, path: Path = _BRANDS_PATH) -> BrandConfigFull:
    """Get a single brand by key. Loads and caches registry on first call.

    Raises:
        KeyError: If brand key not found.
    """
    global _registry
    if _registry is None:
        _registry = load_brands(path)
    brand = _registry.get(key)
    if brand is None:
        raise KeyError(f"Brand not found: {key!r}. Available: {_registry.keys()}")
    return brand


def get_google_fonts_url(brand: BrandConfig) -> str:
    """Generate Google Fonts URL for brand typography.

    >>> get_google_fonts_url(brand)  # doctest: +SKIP
    'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Open+Sans:wght@400;500;600;700&display=swap'
    """
    fonts = {brand.typography.headingFont, brand.typography.bodyFont}
    params = "&".join(
        f"family={font.replace(' ', '+')}:wght@400;500;600;700"
        for font in sorted(fonts)
    )
    return f"https://fonts.googleapis.com/css2?{params}&display=swap"
