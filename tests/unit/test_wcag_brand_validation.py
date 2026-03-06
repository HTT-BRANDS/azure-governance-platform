"""WCAG 2.2 AA validation for all brand color combinations."""
import pytest
from app.core.design_tokens import load_brands
from app.core.color_utils import get_contrast_ratio, validate_wcag_aa

@pytest.fixture
def registry():
    return load_brands()

@pytest.fixture(params=["httbrands","frenchies","bishops","lashlounge","deltacrown"])
def brand(request, registry):
    return registry[request.param]

def test_primary_on_white(brand):
    r = get_contrast_ratio(brand.colors.primary, "#FFFFFF")
    assert r >= 4.5, f"{brand.name} primary on white: {r}"

def test_primary_on_background(brand):
    r = get_contrast_ratio(brand.colors.primary, brand.colors.background)
    assert r >= 4.5, f"{brand.name} primary on bg: {r}"

def test_text_on_background(brand):
    r = get_contrast_ratio(brand.colors.text, brand.colors.background)
    assert r >= 4.5, f"{brand.name} text on bg: {r}"

def test_accent_large_text(brand):
    r = get_contrast_ratio(brand.colors.accent, brand.colors.background)
    assert r >= 3.0, f"{brand.name} accent large text: {r}"
