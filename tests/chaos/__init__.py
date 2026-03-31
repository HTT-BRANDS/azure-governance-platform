"""Chaos engineering tests for Azure Governance Platform.

These tests verify system resilience by injecting failures into:
- Database connections
- Azure API calls
- Cache operations
- External service dependencies

Uses existing circuit breaker patterns and resilience modules.
"""
