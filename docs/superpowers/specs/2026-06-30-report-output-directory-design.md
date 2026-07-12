# Report Output Directory Design

## Goal

Save CLI reports beneath a configurable base directory. On this workstation,
`TRADINGAGENTS_REPORT_DIR` points to:

`/Users/wanghc/SynologyDrive/AI agent/report/reports`

The repository default remains portable at `~/.tradingagents/reports`.

## Design

- Add `TRADINGAGENTS_REPORT_DIR` to the standard configuration overlay.
- Group reports by normalized ticker.
- Name the run directory `<ANALYSIS_DATE>_<TICKER>`.
- The resulting layout is `<report_dir>/<TICKER>/<ANALYSIS_DATE>_<TICKER>`.
- Keep the interactive save confirmation and custom-path prompt unchanged.
- Let the shared report writer create directories as needed.

## Error Handling

The existing save error handling reports missing permissions or unavailable
storage. It does not silently fall back to a different directory.

## Verification

- Verify the portable default.
- Verify `TRADINGAGENTS_REPORT_DIR` overrides it.
- Verify ticker normalization and the report directory layout.
