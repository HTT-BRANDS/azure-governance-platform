"""Contract checks for staging API coverage tests."""

from tests.staging import test_api_coverage


def test_route_mount_timeout_has_b1_staging_headroom():
    """Route mounting validates existence, not latency SLOs.

    Staging runs on constrained B1 infrastructure and can transiently exceed
    10s immediately after deploy even when routes are mounted correctly. Keep
    the timeout high enough that CI reports real 404/500 failures instead of
    Azure having a tiny post-deploy nap.
    """
    assert test_api_coverage.ROUTE_MOUNT_TIMEOUT_SECONDS >= 30
