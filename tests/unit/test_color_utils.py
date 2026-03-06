"""Tests for app.core.color_utils — WCAG and color manipulation utilities."""

import pytest
from app.core.color_utils import (
    RGB, HSL,
    hex_to_rgb, rgb_to_hex, hex_to_hsl, hsl_to_hex,
    get_luminance, get_contrast_ratio, is_color_dark,
    get_contrasting_text_color, validate_wcag_aa, validate_wcag_aa_large,
    lighten_color, darken_color, generate_color_variants,
    hex_to_rgba, generate_10_shade_scale,
)


class TestHexToRgb:
    def test_standard_hex(self):
        assert hex_to_rgb("#FF0000") == RGB(255, 0, 0)

    def test_shorthand_hex(self):
        assert hex_to_rgb("#F00") == RGB(255, 0, 0)

    def test_without_hash(self):
        assert hex_to_rgb("FF0000") == RGB(255, 0, 0)

    def test_invalid_returns_none(self):
        assert hex_to_rgb("invalid") is None

    def test_empty_returns_none(self):
        assert hex_to_rgb("") is None

    def test_invalid_chars_returns_none(self):
        assert hex_to_rgb("#GGGGGG") is None

    def test_pink(self):
        assert hex_to_rgb("#E91E63") == RGB(233, 30, 99)


class TestRgbToHex:
    def test_red(self):
        assert rgb_to_hex(RGB(255, 0, 0)) == "#FF0000"

    def test_pink(self):
        assert rgb_to_hex(RGB(233, 30, 99)) == "#E91E63"

    def test_black(self):
        assert rgb_to_hex(RGB(0, 0, 0)) == "#000000"


class TestHslConversions:
    def test_red_to_hsl(self):
        assert hex_to_hsl("#FF0000") == HSL(0, 100, 50)

    def test_hsl_to_red(self):
        assert hsl_to_hex(HSL(0, 100, 50)) == "#FF0000"

    def test_roundtrip(self):
        """HSL round-trip should preserve color (within rounding)."""
        original = "#E91E63"
        hsl = hex_to_hsl(original)
        assert hsl is not None
        result = hsl_to_hex(hsl)
        # Allow 1-step rounding difference per channel
        orig_rgb = hex_to_rgb(original)
        result_rgb = hex_to_rgb(result)
        assert orig_rgb is not None and result_rgb is not None
        assert abs(orig_rgb.r - result_rgb.r) <= 2
        assert abs(orig_rgb.g - result_rgb.g) <= 2
        assert abs(orig_rgb.b - result_rgb.b) <= 2

    def test_invalid_hsl(self):
        assert hex_to_hsl("invalid") is None


class TestWcagLuminance:
    def test_white(self):
        assert abs(get_luminance("#FFFFFF") - 1.0) < 0.01

    def test_black(self):
        assert abs(get_luminance("#000000") - 0.0) < 0.01


class TestContrastRatio:
    def test_black_white(self):
        assert get_contrast_ratio("#000000", "#FFFFFF") == 21.0

    def test_same_color(self):
        assert get_contrast_ratio("#FFFFFF", "#FFFFFF") == 1.0

    def test_symmetric(self):
        r1 = get_contrast_ratio("#E91E63", "#FFFFFF")
        r2 = get_contrast_ratio("#FFFFFF", "#E91E63")
        assert abs(r1 - r2) < 0.01


class TestColorDarkness:
    def test_black_is_dark(self):
        assert is_color_dark("#000000") is True

    def test_white_is_not_dark(self):
        assert is_color_dark("#FFFFFF") is False

    def test_contrasting_text_on_black(self):
        assert get_contrasting_text_color("#000000") == "#FFFFFF"

    def test_contrasting_text_on_white(self):
        assert get_contrasting_text_color("#FFFFFF") == "#000000"

    def test_contrasting_text_on_pink(self):
        # E91E63 has luminance ~0.19, above 0.179 threshold → black text
        assert get_contrasting_text_color("#E91E63") == "#000000"


class TestWcagValidation:
    def test_aa_passes_black_white(self):
        assert validate_wcag_aa("#000000", "#FFFFFF") is True

    def test_aa_fails_low_contrast(self):
        assert validate_wcag_aa("#777777", "#888888") is False

    def test_aa_large_passes(self):
        assert validate_wcag_aa_large("#555555", "#FFFFFF") is True


class TestColorManipulation:
    def test_lighten(self):
        result = lighten_color("#500711", 20)
        assert result != "#500711"  # Should be different
        result_hsl = hex_to_hsl(result)
        original_hsl = hex_to_hsl("#500711")
        assert result_hsl is not None and original_hsl is not None
        assert result_hsl.l > original_hsl.l

    def test_darken(self):
        result = darken_color("#FFFFFF", 50)
        lum = get_luminance(result)
        assert lum < get_luminance("#FFFFFF")

    def test_lighten_zero(self):
        assert lighten_color("#000000", 0) == "#000000"

    def test_color_variants(self):
        variants = generate_color_variants("#500711")
        assert set(variants.keys()) == {"base", "light", "lighter", "dark", "darker"}

    def test_hex_to_rgba(self):
        assert hex_to_rgba("#E91E63", 0.5) == "rgba(233, 30, 99, 0.5)"


class TestShadeScale:
    def test_scale_keys(self):
        scale = generate_10_shade_scale("#500711")
        expected = {"5", "10", "50", "100", "110", "130", "140", "160", "180"}
        assert set(scale.keys()) == expected

    def test_scale_base(self):
        scale = generate_10_shade_scale("#500711")
        assert scale["100"] == "#500711"

    def test_scale_values_are_hex(self):
        scale = generate_10_shade_scale("#500711")
        for v in scale.values():
            assert v.startswith("#") and len(v) == 7
