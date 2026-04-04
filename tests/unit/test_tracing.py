"""Tests for app/core/tracing.py — OpenTelemetry tracing configuration.

Covers:
- setup_tracing: disabled, OTLP endpoint, console fallback
- get_tracer: success and exception paths
- TracedContext: enter/exit, error propagation, no-tracer noop

Phase B.4 of the test coverage sprint.
"""

from unittest.mock import MagicMock, patch

from app.core.tracing import TracedContext, get_tracer, setup_tracing

# ---------------------------------------------------------------------------
# setup_tracing
# ---------------------------------------------------------------------------


class TestSetupTracing:
    @patch("app.core.tracing.get_settings")
    def test_disabled_returns_none(self, mock_settings):
        settings = MagicMock()
        settings.enable_tracing = False
        mock_settings.return_value = settings
        assert setup_tracing(MagicMock()) is None

    @patch("app.core.tracing.FastAPIInstrumentor")
    @patch("app.core.tracing.BatchSpanProcessor")
    @patch("app.core.tracing.ConsoleSpanExporter")
    @patch("app.core.tracing.trace")
    @patch("app.core.tracing.TracerProvider")
    @patch("app.core.tracing.Resource")
    @patch("app.core.tracing.get_settings")
    def test_console_exporter_when_no_endpoint(
        self,
        mock_settings,
        mock_resource,
        mock_provider_cls,
        mock_trace,
        mock_console,
        mock_processor,
        mock_instrument,
    ):
        settings = MagicMock()
        settings.enable_tracing = True
        settings.otel_exporter_endpoint = None
        settings.app_version = "1.0.0"
        settings.environment = "dev"
        mock_settings.return_value = settings

        result = setup_tracing(MagicMock())

        mock_console.assert_called_once()
        assert result is not None

    @patch("app.core.tracing.FastAPIInstrumentor")
    @patch("app.core.tracing.BatchSpanProcessor")
    @patch("app.core.tracing.OTLPSpanExporter")
    @patch("app.core.tracing.trace")
    @patch("app.core.tracing.TracerProvider")
    @patch("app.core.tracing.Resource")
    @patch("app.core.tracing.get_settings")
    def test_otlp_exporter_when_endpoint_set(
        self,
        mock_settings,
        mock_resource,
        mock_provider_cls,
        mock_trace,
        mock_otlp,
        mock_processor,
        mock_instrument,
    ):
        settings = MagicMock()
        settings.enable_tracing = True
        settings.otel_exporter_endpoint = "https://otel.example.com"
        settings.otel_exporter_headers = {"Authorization": "Bearer x"}
        settings.app_version = "2.0.0"
        settings.environment = "production"
        mock_settings.return_value = settings

        result = setup_tracing(MagicMock())

        mock_otlp.assert_called_once_with(
            endpoint="https://otel.example.com",
            headers={"Authorization": "Bearer x"},
        )
        assert result is not None

    @patch("app.core.tracing.FastAPIInstrumentor")
    @patch("app.core.tracing.BatchSpanProcessor")
    @patch("app.core.tracing.ConsoleSpanExporter")
    @patch("app.core.tracing.trace")
    @patch("app.core.tracing.TracerProvider")
    @patch("app.core.tracing.Resource")
    @patch("app.core.tracing.get_settings")
    def test_instruments_fastapi_app(
        self,
        mock_settings,
        mock_resource,
        mock_provider_cls,
        mock_trace,
        mock_console,
        mock_processor,
        mock_instrument,
    ):
        settings = MagicMock()
        settings.enable_tracing = True
        settings.otel_exporter_endpoint = None
        settings.app_version = "1.0.0"
        settings.environment = "dev"
        mock_settings.return_value = settings

        app = MagicMock()
        setup_tracing(app)

        mock_instrument.instrument_app.assert_called_once_with(app)


# ---------------------------------------------------------------------------
# get_tracer
# ---------------------------------------------------------------------------


class TestGetTracer:
    @patch("app.core.tracing.trace")
    def test_returns_tracer(self, mock_trace):
        mock_tracer = MagicMock()
        mock_trace.get_tracer.return_value = mock_tracer
        assert get_tracer("my.module") is mock_tracer
        mock_trace.get_tracer.assert_called_once_with("my.module")

    @patch("app.core.tracing.trace")
    def test_returns_none_on_exception(self, mock_trace):
        mock_trace.get_tracer.side_effect = Exception("no provider")
        assert get_tracer("broken") is None


# ---------------------------------------------------------------------------
# TracedContext
# ---------------------------------------------------------------------------


class TestTracedContext:
    def test_noop_when_tracer_is_none(self):
        """When tracer is None, enter/exit are harmless noops."""
        ctx = TracedContext(None, "test-span")
        with ctx:
            pass  # Should not raise

    def test_starts_span_with_attributes(self):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)

        attrs = {"tenant_id": "t-1", "operation": "sync"}
        ctx = TracedContext(mock_tracer, "my-span", attributes=attrs)

        with ctx:
            pass

        mock_tracer.start_as_current_span.assert_called_once_with("my-span")
        # Attributes set on the span
        assert mock_span.set_attribute.call_count == 2

    def test_records_error_on_exception(self):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)

        ctx = TracedContext(mock_tracer, "error-span")

        try:
            with ctx:
                raise ValueError("kaboom")
        except ValueError:
            pass

        # Error attributes should be set
        mock_span.set_attribute.assert_any_call("error", True)
        mock_span.set_attribute.assert_any_call("error.message", "kaboom")

    def test_default_attributes_empty_dict(self):
        ctx = TracedContext(MagicMock(), "span")
        assert ctx.attributes == {}
