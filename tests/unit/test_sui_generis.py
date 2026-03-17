"""Unit tests for Sui Generis MSP integration placeholder.

Tests the placeholder client in app/integrations/sui_generis.py.

Traces: RC-030, RC-031 (Phase 2 — Sui Generis integration)
"""

import pytest

from app.integrations.sui_generis import SuiGenerisClient


class TestSuiGenerisClient:
    """Tests for SuiGenerisClient placeholder."""

    def test_init_raises_not_implemented(self):
        """Client should raise NotImplementedError on instantiation."""
        with pytest.raises(NotImplementedError) as exc_info:
            SuiGenerisClient()
        assert "Phase 2" in str(exc_info.value)
        assert "Q3 2025" in str(exc_info.value)

    def test_error_message_includes_contact(self):
        """Error message should include contact info."""
        with pytest.raises(NotImplementedError) as exc_info:
            SuiGenerisClient()
        assert "Sui Generis" in str(exc_info.value)

    def test_class_has_expected_methods(self):
        """Class should define the planned API surface."""
        assert hasattr(SuiGenerisClient, "get_device_compliance")
        assert hasattr(SuiGenerisClient, "get_endpoint_security")
        assert hasattr(SuiGenerisClient, "get_patch_management")
        assert hasattr(SuiGenerisClient, "sync_asset_inventory")

    def test_methods_are_async(self):
        """All data methods should be async (coroutine functions)."""
        import asyncio

        assert asyncio.iscoroutinefunction(SuiGenerisClient.get_device_compliance)
        assert asyncio.iscoroutinefunction(SuiGenerisClient.get_endpoint_security)
        assert asyncio.iscoroutinefunction(SuiGenerisClient.get_patch_management)
        assert asyncio.iscoroutinefunction(SuiGenerisClient.sync_asset_inventory)
