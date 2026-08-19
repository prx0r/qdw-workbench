# API Gold Standard v1

Dell is the reference product, not a directory template. The eventual QDW factory should encode requirements plus verification.

Required product surfaces:
- versioned machine-readable REST API + OpenAPI
- health/readiness contract
- MCP/agent-facing interface when useful
- source provenance/freshness/health
- explicit UNKNOWN values (never coerced to zero)
- stable versioned public schemas
- reproducible migrations
- evidence-bound release certificate
- docs and operator documentation
- production/staging deployment recipe
- website/product page
- unit + integration + adversarial tests
- mutation/anti-cheat fixture
- resource/cost measurements

The Workbench `Gold Standards` page reads such requirements from QDW FactoryDefinition/VerificationPlan in the future. This document is a human reference only and must not become the authoritative manifest.
