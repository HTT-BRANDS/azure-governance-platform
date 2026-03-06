"""Tests for theme_middleware module."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.core.theme_middleware import ThemeMiddleware, ThemeContext, get_theme_context, TENANT_CODE_TO_BRAND, DEFAULT_BRAND_KEY

def test_tenant_code_mapping():
    assert TENANT_CODE_TO_BRAND["HTT"] == "httbrands"
    assert TENANT_CODE_TO_BRAND["FN"] == "frenchies"
    assert len(TENANT_CODE_TO_BRAND) == 5

def test_default_brand_key():
    assert DEFAULT_BRAND_KEY == "httbrands"

def test_theme_context_properties():
    from app.core.design_tokens import get_brand
    from app.core.css_generator import generate_brand_css_variables, generate_inline_style
    from app.core.design_tokens import get_google_fonts_url
    brand = get_brand("httbrands")
    ctx = ThemeContext(
        brand_key="httbrands", brand_config=brand,
        css_variables=generate_brand_css_variables(brand),
        inline_style=generate_inline_style(brand),
        google_fonts_url=get_google_fonts_url(brand))
    assert ctx.brand_name == "Head to Toe Brands"
    assert ctx.logo_primary.endswith(".svg")

def test_theme_context_to_template():
    from app.core.design_tokens import get_brand
    from app.core.css_generator import generate_brand_css_variables, generate_inline_style
    from app.core.design_tokens import get_google_fonts_url
    brand = get_brand("frenchies")
    ctx = ThemeContext(
        brand_key="frenchies", brand_config=brand,
        css_variables=generate_brand_css_variables(brand),
        inline_style=generate_inline_style(brand),
        google_fonts_url=get_google_fonts_url(brand))
    t = ctx.to_template_context()
    assert t["brand"]["key"] == "frenchies"
    assert "css_variables" in t["brand"]
    assert "logo" in t["brand"]
    assert "typography" in t["brand"]

def test_theme_context_frozen():
    from app.core.design_tokens import get_brand
    from app.core.css_generator import generate_brand_css_variables, generate_inline_style
    from app.core.design_tokens import get_google_fonts_url
    brand = get_brand("httbrands")
    ctx = ThemeContext(
        brand_key="httbrands", brand_config=brand,
        css_variables=generate_brand_css_variables(brand),
        inline_style=generate_inline_style(brand),
        google_fonts_url=get_google_fonts_url(brand))
    with pytest.raises(Exception):
        ctx.brand_key = "other"

def test_middleware_init():
    app = MagicMock()
    mw = ThemeMiddleware(app)
    assert mw.default_brand_key == DEFAULT_BRAND_KEY

def test_middleware_build_cache():
    app = MagicMock()
    mw = ThemeMiddleware(app)
    ctx1 = mw._build_theme_context("httbrands")
    ctx2 = mw._build_theme_context("httbrands")
    assert ctx1 is ctx2  # cached

def test_middleware_fallback():
    app = MagicMock()
    mw = ThemeMiddleware(app)
    ctx = mw._build_theme_context("nonexistent")
    assert ctx.brand_key == DEFAULT_BRAND_KEY

def test_get_theme_context_fallback():
    req = MagicMock()
    req.state = MagicMock(spec=[])  # no theme attr
    ctx = get_theme_context(req)
    assert ctx.brand_key == DEFAULT_BRAND_KEY
    assert len(ctx.css_variables) >= 40
