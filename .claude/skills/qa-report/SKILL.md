---
description: Generate or review concise QA execution reports from this repo's pytest artifacts. Use when asked to create a QA report, summarize a test run, explain pass/fail results, review report quality, or produce an interview-ready testing report from reports/session-summary.json and logs/automation.log.
argument-hint: "[latest run | run ui | review report]"
---

# QA Report Workflow

Create or review a QA execution report for `$ARGUMENTS`.

## Source Of Truth

Use pytest artifacts as the source of truth:

- `reports/session-summary.json`
- `logs/automation.log`
- executed test source files referenced by `nodeid`

Pytest owns pass/fail. The report summarizes; it must not change the meaning of the run.

## Important Mode Choice

If already running inside Claude Code, do not call `GENERATE_AI_REPORT=true` unless the user explicitly wants to test the post-test hook. Instead:

1. Run pytest normally if the user asked to run tests.
2. Read the generated artifacts.
3. Write `reports/qa-execution-report.md` directly.

If the user wants the terminal one-liner, provide:

```bash
GENERATE_AI_REPORT=true HEADLESS=false SLOW_MO_MS=500 pytest tests/ui -m ui -q
```

## Report Requirements

Write `reports/qa-execution-report.md` with these sections:

- Test Run Summary
- Coverage
- Key Business Assertions
- Failures Or Risks
- Recommended Next Tests
- Evidence

Be conservative:

- Report only what the current run executed and asserted.
- Do not include failures from old logs.
- Do not claim a business rule is required unless the test explicitly asserts it.
- Do not call explicit source-code assertions implicit just because they are not visible in the log.
- Do not label timestamps as UTC unless the data says UTC.
- Do not include secrets, tokens, full stack traces, or raw logs.

## Failure Handling

If the run failed:

- Lead with the failing test and first failure point.
- Say which assertions were not reached.
- Separate main failure from teardown/cleanup errors.
- Keep recommended next steps practical and minimal.

If the run passed:

- State pass counts and durations.
- Summarize the tested user flow.
- List the concrete assertions verified.
- Mention risks only if they appear in the current artifacts.

## Quality Bar

The report should be interview-ready:

- short enough to skim
- accurate enough to defend
- grounded in test names, assertions, and evidence
- free of raw logs and speculation

## Summary Format

After writing or reviewing the report, return:

1. Report path
2. Overall result
3. One strength
4. One risk or "No current run risks found"
