# Email Delivery for Portfolio Manager Summaries

## Goal

After the scheduled TradingAgents watchlist workflow finishes, scan the
configured report directory and email the authenticated Gmail account a concise
Chinese summary of Portfolio Manager decisions created that calendar day.

## Scope

- Keep the existing schedule, live watchlist refresh, sequential execution, and
  report verification unchanged.
- Resolve `report_dir` from project configuration; on this workstation it is set
  through `TRADINGAGENTS_REPORT_DIR`.
- Scan non-empty `complete_report.md` files under the ticker/date directory tree.
- Use the `America/Los_Angeles` calendar date.
- Identify scheduled symbols whose analysis or report extraction failed.
- Send one HTML email after all symbols have been processed.
- Do not store Gmail credentials, addresses, or tokens in the repository.

## Delivery

Send through the connected Gmail account to `me` with subject:

`TradingAgents 每日决策 | YYYY-MM-DD | SYMBOLS`

The compact Chinese body contains the run date, scheduled symbols, report count,
decision, confidence when present, rationale, execution guidance, target or time
horizon when present, key risk, and a failure section. Missing fields are shown
as `未提供`. Absolute report paths stay in diagnostic output rather than the
main email table.

## Data Flow

1. Fetch the current Robinhood `Agent watch list`.
2. Run and verify each symbol sequentially.
3. Resolve `report_dir` and scan today's ticker/date directories.
4. Require a non-empty `complete_report.md` modified today.
5. Extract each Portfolio Manager decision without inventing fields.
6. Build one restrained HTML summary with a plain-text fallback.
7. Send through Gmail and record success or failure in the Codex task result.

## Failure Handling

- A symbol or malformed report does not prevent later symbols from running.
- Gmail failure does not alter local reports.
- If no qualifying report exists, send a status email stating that none were
  found and include any scheduled-run failures.
