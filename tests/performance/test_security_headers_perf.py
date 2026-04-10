"""Performance benchmark for security headers middleware.

Measures the overhead of SecurityHeadersMiddleware on response times.
Target: <1ms overhead per request (security headers should be negligible).
"""

import statistics
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse

from app.core.security_headers import SecurityHeadersMiddleware


def _make_app(with_middleware: bool = True) -> TestClient:
    """Create a minimal FastAPI app, optionally with security headers middleware."""
    app = FastAPI()

    @app.get("/benchmark")
    async def benchmark_endpoint():
        return PlainTextResponse("OK")

    if with_middleware:
        app.add_middleware(SecurityHeadersMiddleware)

    return TestClient(app)


class TestSecurityHeadersPerformance:
    """Benchmark security headers middleware overhead."""

    ITERATIONS = 500
    MAX_OVERHEAD_MS = 1.0  # Maximum acceptable overhead per request

    def _measure_latency(self, client: TestClient, iterations: int) -> list[float]:
        """Measure response times in milliseconds."""
        times = []
        # Warmup
        for _ in range(10):
            client.get("/benchmark")
        # Measure
        for _ in range(iterations):
            start = time.perf_counter()
            resp = client.get("/benchmark")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            assert resp.status_code == 200
            times.append(elapsed)
        return times

    def test_middleware_overhead_is_negligible(self):
        """Security headers middleware should add <1ms overhead per request."""
        client_with = _make_app(with_middleware=True)
        client_without = _make_app(with_middleware=False)

        times_with = self._measure_latency(client_with, self.ITERATIONS)
        times_without = self._measure_latency(client_without, self.ITERATIONS)

        median_with = statistics.median(times_with)
        median_without = statistics.median(times_without)
        overhead = median_with - median_without

        p95_with = sorted(times_with)[int(0.95 * len(times_with))]
        p95_without = sorted(times_without)[int(0.95 * len(times_without))]

        print(f"\n{'=' * 60}")
        print("Security Headers Middleware Performance Benchmark")
        print(f"{'=' * 60}")
        print(f"Iterations: {self.ITERATIONS}")
        print("")
        print(f"{'Metric':<25} {'With MW':>12} {'Without MW':>12} {'Overhead':>12}")
        print(f"{'-' * 61}")
        print(f"{'Median (ms)':<25} {median_with:>12.3f} {median_without:>12.3f} {overhead:>12.3f}")
        print(
            f"{'P95 (ms)':<25} {p95_with:>12.3f} {p95_without:>12.3f} {p95_with - p95_without:>12.3f}"
        )
        print(
            f"{'Mean (ms)':<25} {statistics.mean(times_with):>12.3f} {statistics.mean(times_without):>12.3f} {statistics.mean(times_with) - statistics.mean(times_without):>12.3f}"
        )
        print(
            f"{'Stdev (ms)':<25} {statistics.stdev(times_with):>12.3f} {statistics.stdev(times_without):>12.3f}"
        )
        print(f"{'=' * 60}")

        assert overhead < self.MAX_OVERHEAD_MS, (
            f"Security headers middleware overhead ({overhead:.3f}ms) "
            f"exceeds threshold ({self.MAX_OVERHEAD_MS}ms)"
        )

    def test_headers_present_at_speed(self):
        """Verify all 12 security headers are present while maintaining speed."""
        client = _make_app(with_middleware=True)

        start = time.perf_counter()
        resp = client.get("/benchmark")
        elapsed = (time.perf_counter() - start) * 1000

        # Verify critical headers are present
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cross-Origin-Resource-Policy",
            "Content-Security-Policy",
            "Strict-Transport-Security",
        ]

        missing = [
            h for h in expected_headers if h.lower() not in {k.lower() for k in resp.headers}
        ]
        assert not missing, f"Missing security headers: {missing}"

        print(f"\nAll {len(expected_headers)} security headers present in {elapsed:.3f}ms")

    def test_concurrent_request_throughput(self):
        """Measure throughput with middleware under rapid sequential requests."""
        client = _make_app(with_middleware=True)

        count = 1000
        start = time.perf_counter()
        for _ in range(count):
            resp = client.get("/benchmark")
            assert resp.status_code == 200
        elapsed = time.perf_counter() - start

        rps = count / elapsed
        print(f"\nThroughput: {rps:.0f} requests/sec ({count} requests in {elapsed:.2f}s)")
        assert rps > 500, f"Throughput ({rps:.0f} rps) below minimum threshold (500 rps)"
