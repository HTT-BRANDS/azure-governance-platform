"""Tests for design_tokens module."""
import pytest
from pathlib import Path
from app.core.design_tokens import *

def test_load_brands():
    r = load_brands()
    assert len(r) == 5

def test_brand_keys():
    r = load_brands()
    assert set(r.keys()) == {"httbrands","frenchies","bishops","lashlounge","deltacrown"}

def test_get_brand_valid():
    b = get_brand("httbrands")
    assert b.name == "Head to Toe Brands"

def test_get_brand_invalid():
    with pytest.raises(KeyError):
        get_brand("nonexistent")

def test_brand_colors_valid():
    b = get_brand("httbrands")
    assert b.colors.primary.startswith("#")
    assert b.colors.background.startswith("#")

def test_brand_typography():
    b = get_brand("httbrands")
    assert b.typography.headingFont == "Montserrat"

def test_brand_design_system():
    b = get_brand("httbrands")
    assert b.designSystem.shadowStyle == ShadowStyle.SHARP

def test_google_fonts_url():
    b = get_brand("httbrands")
    url = get_google_fonts_url(b)
    assert "fonts.googleapis.com" in url
    assert "Montserrat" in url

def test_hex_color_validation():
    with pytest.raises(Exception):
        BrandColors(primary="invalid",accent="#FFFFFF",background="#FFFFFF",text="#000000")

def test_registry_getitem():
    r = load_brands()
    b = r["frenchies"]
    assert b.name == "Frenchies Modern Nail Care"

def test_registry_iteration():
    r = load_brands()
    keys = list(r)
    assert len(keys) == 5

def test_shadow_style_enum():
    assert ShadowStyle.SOFT.value == "soft"
    assert ShadowStyle.SHARP.value == "sharp"
    assert ShadowStyle.NONE.value == "none"
