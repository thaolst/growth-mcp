# Changelog

## [1.2.0] - 2026-06-27

### Added
- **Streamlit Web UI** — `streamlit_app/` with browser-based tools for marketers
- **Retention Analyzer page** — upload cohort CSV, analyze retention drops, get intervention recommendations
- **Home page** — tool overview with sidebar navigation

### Changed
- **README** — added Web UI section with setup instructions

## [1.0.0] - 2026-06-13

First stable release. The API of all 25 tools, 3 prompts, and 2 resources is now considered stable: breaking changes will bump the major version.

### Added
- `examples/` folder: 4 synthetic datasets (fixed seed, regenerable) with a walkthrough showing real output from every layer
- Integration tests through the MCP server layer (tools called via the protocol surface, not just the pure functions)

## [0.9.0] - 2026-06-12

### Added
- Loyalty economics layer: `forecast_points_expiry`, `analyze_redemption_elasticity`, `analyze_redemption_elasticity_from_csv` (per-segment in one pass), `analyze_balance_health`

## [0.8.0] - 2026-06-12

### Added
- Knowledge layer: 2 MCP resources (`growth://frameworks`, `growth://glossary`) with versioned, source-traced entries; 3 MCP prompts chaining the server's tools (`ab_test_readout`, `meu_campaign_plan`, `voucher_design_review`)

## [0.7.0] - 2026-06-12

### Added
- Mixpanel data source via the raw Export API (stdlib only, no new dependency): `analyze_experiment_from_mixpanel`, `summarize_segments_from_mixpanel`

## [0.6.0] - 2026-06-12

### Added
- BigQuery data source (optional extra `growth-mcp[bigquery]`): `analyze_experiment_from_bigquery`, `analyze_retention_from_bigquery`, `summarize_segments_from_bigquery`; read-only SQL guardrail, 200K row cap

### Changed
- Refactored row-level analyzers to be shared across all data sources

## [0.5.0] - 2026-06-10

### Added
- CSV data layer: `inspect_csv`, `analyze_experiment_from_csv`, `analyze_retention_from_csv`, `summarize_segments_from_csv`
- `optimize_voucher`: tiered voucher ladder with abuse risk assessment

## [0.3.0] and earlier

Core framework tools: campaign design, retention analysis, churn prediction, experiment analysis, sample size, monitoring, segmentation, channel mix, cohort forecasting.
