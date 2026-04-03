"""Tests for app/core/validation.py."""

import pytest

from app.core.validation import validate_uuid_param


class TestValidateUuidParam:
    """Tests for validate_uuid_param()."""

    def test_valid_lowercase_uuid(self):
        """A well-formed lowercase UUID passes and is returned unchanged."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_uuid_param(uuid) == uuid

    def test_uppercase_uuid_is_normalised_to_lowercase(self):
        """An uppercase UUID is accepted and returned in lowercase."""
        upper = "550E8400-E29B-41D4-A716-446655440000"
        assert validate_uuid_param(upper) == upper.lower()

    def test_mixed_case_uuid_is_normalised(self):
        """A mixed-case UUID is accepted and lowered."""
        mixed = "550e8400-E29B-41d4-A716-446655440000"
        assert validate_uuid_param(mixed) == mixed.lower()

    def test_invalid_format_raises_value_error(self):
        """A string that isn't a valid UUID raises ValueError."""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            validate_uuid_param("not-a-uuid")

    def test_empty_string_raises_value_error(self):
        """An empty string is not a valid UUID."""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            validate_uuid_param("")

    def test_none_raises_type_error(self):
        """None is not a string; re.match will raise TypeError."""
        with pytest.raises(TypeError):
            validate_uuid_param(None)  # type: ignore[arg-type]

    def test_uuid_without_hyphens_raises_value_error(self):
        """A hex string missing hyphens is rejected."""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            validate_uuid_param("550e8400e29b41d4a716446655440000")  # pragma: allowlist secret
