"""Tests for css_generator."""
import pytest
from app.core.css_generator import generate_color_variables, generate_typography_variables, generate_design_system_variables, generate_brand_css_variables, generate_scoped_brand_css, generate_inline_style, SHADOW_PRESETS
from app.core.design_tokens import *

@pytest.fixture
def b():
    return BrandConfig(name="T",logo=BrandLogo(primary="/l.svg"),
        colors=BrandColors(primary="#500711",accent="#FFC957",background="#FFFFFF",text="#141617",secondary="#D1BDBF"),
        typography=BrandTypography(headingFont="Montserrat",bodyFont="Open Sans"),
        designSystem=BrandDesignSystem(borderRadius="4px",shadowStyle=ShadowStyle.SHARP))

def test_primary(b): assert generate_color_variables(b)["--brand-primary"]=="#500711"
def test_shades(b):
    v=generate_color_variables(b)
    assert "--brand-primary-5" in v and "--brand-primary-180" in v
def test_base(b): assert generate_color_variables(b)["--brand-primary-100"]=="#500711"
def test_secondary(b): assert "--brand-secondary" in generate_color_variables(b)
def test_contrast(b): assert generate_color_variables(b)["--text-on-primary"] in ("#FFFFFF","#000000")
def test_gradient(b): assert "--brand-gradient" in generate_color_variables(b)
def test_heading(b): assert "Montserrat" in generate_typography_variables(b)["--brand-font-heading"]
def test_body(b): assert "Open Sans" in generate_typography_variables(b)["--brand-font-body"]
def test_radius(b): assert generate_design_system_variables(b)["--brand-radius"]=="4px"
def test_shadow(b): assert generate_design_system_variables(b)["--brand-shadow-style"]==SHADOW_PRESETS["sharp"]
def test_count(b): assert len(generate_brand_css_variables(b))>=40
def test_scoped(b): assert '[data-brand="x"]' in generate_scoped_brand_css("x",b)
def test_balanced(b): c=generate_scoped_brand_css("x",b); assert c.count("{")==c.count("}")
def test_inline(b): i=generate_inline_style(b); assert "{" not in i and "--brand-primary:" in i
