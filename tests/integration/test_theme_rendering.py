"""Integration tests for brand theme rendering pipeline."""
import pytest
from app.core.design_tokens import load_brands, get_brand
from app.core.css_generator import generate_brand_css_variables, generate_scoped_brand_css
from app.core.color_utils import get_contrast_ratio

@pytest.fixture
def registry():
    return load_brands()

def test_all_brands_generate_css(registry):
    for key in registry:
        brand = registry[key]
        v = generate_brand_css_variables(brand)
        assert len(v) >= 40, f"{key} has only {len(v)} vars"
        assert "--brand-primary" in v

def test_all_brands_valid_hex(registry):
    import re
    hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for key in registry:
        brand = registry[key]
        assert hex_re.match(brand.colors.primary), f"{key} primary invalid"
        assert hex_re.match(brand.colors.accent), f"{key} accent invalid"

def test_all_brands_scoped_css(registry):
    for key in registry:
        css = generate_scoped_brand_css(key, registry[key])
        assert f'[data-brand="{key}"]' in css
        assert css.count("{") == css.count("}")

def test_all_brands_text_contrast(registry):
    for key in registry:
        brand = registry[key]
        v = generate_brand_css_variables(brand)
        text_on_primary = v["--text-on-primary"]
        ratio = get_contrast_ratio(brand.colors.primary, text_on_primary)
        assert ratio >= 3.0, f"{key}: contrast {ratio} < 3.0"

def test_five_brands_loaded(registry):
    assert len(registry) == 5
