"""
Unit tests for app/core/privacy_config.py

Tests ConsentCategory enum, ConsentPreferences model,
and PrivacyConfig class (constants, categories, GPC override).
"""

from app.core.privacy_config import ConsentCategory, ConsentPreferences, PrivacyConfig


class TestConsentCategoryEnum:
    """Tests for ConsentCategory enum values."""

    def test_has_necessary_category(self):
        """NECESSARY category exists with correct value."""
        assert ConsentCategory.NECESSARY.value == "necessary"

    def test_has_functional_category(self):
        """FUNCTIONAL category exists with correct value."""
        assert ConsentCategory.FUNCTIONAL.value == "functional"

    def test_has_analytics_category(self):
        """ANALYTICS category exists with correct value."""
        assert ConsentCategory.ANALYTICS.value == "analytics"

    def test_has_marketing_category(self):
        """MARKETING category exists with correct value."""
        assert ConsentCategory.MARKETING.value == "marketing"

    def test_exactly_four_categories(self):
        """Enum contains exactly 4 categories — no accidental additions."""
        assert len(ConsentCategory) == 4

    def test_enum_members_are_unique(self):
        """All enum values are distinct strings."""
        values = [c.value for c in ConsentCategory]
        assert len(values) == len(set(values))


class TestConsentPreferencesDefaults:
    """Tests for ConsentPreferences default field values."""

    def test_necessary_defaults_true(self):
        """Necessary cookies default to True (always required)."""
        prefs = ConsentPreferences()
        assert prefs.necessary is True

    def test_optional_categories_default_false(self):
        """Functional, analytics, and marketing default to False (opt-in)."""
        prefs = ConsentPreferences()
        assert prefs.functional is False
        assert prefs.analytics is False
        assert prefs.marketing is False

    def test_metadata_defaults(self):
        """Metadata fields have sensible defaults."""
        prefs = ConsentPreferences()
        assert prefs.timestamp is None
        assert prefs.gpc_override is False
        assert prefs.version == "1.0"

    def test_custom_overrides_accepted(self):
        """All fields can be overridden at construction time."""
        prefs = ConsentPreferences(
            necessary=True,
            functional=True,
            analytics=True,
            marketing=True,
            timestamp="2026-01-01T00:00:00Z",
            gpc_override=True,
            version="2.0",
        )
        assert prefs.functional is True
        assert prefs.analytics is True
        assert prefs.marketing is True
        assert prefs.timestamp == "2026-01-01T00:00:00Z"
        assert prefs.gpc_override is True
        assert prefs.version == "2.0"

    def test_json_round_trip(self):
        """Preferences survive JSON serialisation and deserialisation."""
        original = ConsentPreferences(functional=True, analytics=True)
        json_str = original.model_dump_json()
        restored = ConsentPreferences.model_validate_json(json_str)

        assert restored.functional is original.functional
        assert restored.analytics is original.analytics
        assert restored.marketing is original.marketing
        assert restored.version == original.version


class TestPrivacyConfigConstants:
    """Tests for PrivacyConfig class-level constants."""

    def test_cookie_name(self):
        """Cookie name matches expected value."""
        assert PrivacyConfig.COOKIE_NAME == "consent_preferences"

    def test_cookie_max_age_is_one_year(self):
        """Cookie max age equals 1 year in seconds."""
        one_year_seconds = 365 * 24 * 60 * 60
        assert PrivacyConfig.COOKIE_MAX_AGE == one_year_seconds

    def test_cookie_max_age_is_positive_int(self):
        """Max age is a positive integer (guard against accidental float/zero)."""
        assert isinstance(PrivacyConfig.COOKIE_MAX_AGE, int)
        assert PrivacyConfig.COOKIE_MAX_AGE > 0


class TestPrivacyConfigGetCategories:
    """Tests for PrivacyConfig.get_categories()."""

    def test_returns_all_four_categories(self):
        """get_categories returns a dict keyed by every ConsentCategory member."""
        categories = PrivacyConfig.get_categories()
        for member in ConsentCategory:
            assert member in categories, f"Missing category: {member}"

    def test_necessary_is_required(self):
        """Necessary category is marked as required."""
        categories = PrivacyConfig.get_categories()
        assert categories[ConsentCategory.NECESSARY]["required"] is True

    def test_non_necessary_not_required(self):
        """Functional, analytics, and marketing are not required."""
        categories = PrivacyConfig.get_categories()
        for cat in (
            ConsentCategory.FUNCTIONAL,
            ConsentCategory.ANALYTICS,
            ConsentCategory.MARKETING,
        ):
            assert categories[cat]["required"] is False, f"{cat} should not be required"

    def test_category_metadata_structure(self):
        """Each category has name, description, required, and cookies keys."""
        expected_keys = {"name", "description", "required", "cookies"}
        for cat, meta in PrivacyConfig.get_categories().items():
            assert set(meta.keys()) == expected_keys, f"Bad keys for {cat}: {meta.keys()}"

    def test_each_category_has_cookies_list(self):
        """Each category lists at least one associated cookie."""
        for cat, meta in PrivacyConfig.get_categories().items():
            assert isinstance(meta["cookies"], list)
            assert len(meta["cookies"]) > 0, f"{cat} has no cookies listed"


class TestApplyGpcOverride:
    """Tests for PrivacyConfig.apply_gpc_override()."""

    def test_gpc_disables_analytics_and_marketing(self):
        """GPC override sets analytics and marketing to False."""
        prefs = ConsentPreferences(analytics=True, marketing=True)
        result = PrivacyConfig.apply_gpc_override(prefs)

        assert result.analytics is False
        assert result.marketing is False

    def test_gpc_sets_override_flag(self):
        """GPC override marks gpc_override as True."""
        prefs = ConsentPreferences()
        result = PrivacyConfig.apply_gpc_override(prefs)
        assert result.gpc_override is True

    def test_gpc_preserves_necessary_and_functional(self):
        """GPC override does not touch necessary or functional consent."""
        prefs = ConsentPreferences(necessary=True, functional=True)
        result = PrivacyConfig.apply_gpc_override(prefs)

        assert result.necessary is True
        assert result.functional is True

    def test_gpc_returns_same_object(self):
        """apply_gpc_override mutates and returns the same preferences instance."""
        prefs = ConsentPreferences(analytics=True, marketing=True)
        result = PrivacyConfig.apply_gpc_override(prefs)
        assert result is prefs

    def test_gpc_idempotent(self):
        """Applying GPC override twice produces the same result."""
        prefs = ConsentPreferences(analytics=True, marketing=True)
        PrivacyConfig.apply_gpc_override(prefs)
        PrivacyConfig.apply_gpc_override(prefs)

        assert prefs.analytics is False
        assert prefs.marketing is False
        assert prefs.gpc_override is True
