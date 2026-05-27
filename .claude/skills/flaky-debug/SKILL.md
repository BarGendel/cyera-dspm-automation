---
description: Investigate failed or flaky pytest Playwright UI tests in this repo. Use when tests fail, time out, behave differently between headed/headless runs, have locator issues, login/setup instability, API reset/scan problems, or when asked to make a test more reliable without weakening business assertions.
argument-hint: "[failure or test name]"
---

# Flaky Debug Workflow

Investigate `$ARGUMENTS` as a QA automation engineer.

## First Pass

1. Read `reports/session-summary.json` if it exists.
2. Read the current `logs/automation.log`.
3. Inspect the failed test and related helpers.
4. Identify the first failure, not only the final teardown error.
5. Classify the issue as one of:
   - product bug
   - test data/setup issue
   - locator/readiness issue
   - timing/polling issue
   - environment/rate-limit issue
   - unclear, needs more evidence

## Debugging Rules

- Do not weaken business assertions.
- Do not add `page.wait_for_timeout()` or arbitrary sleeps unless there is no better state-based wait.
- Prefer waiting for visible user state, response state, or stable UI controls.
- Prefer Playwright web-first assertions such as `expect(locator).to_be_visible()` and `expect(locator).to_have_text(...)`.
- Prefer accessibility-first locators: role/name, label, visible text, placeholder, test id, CSS last.
- Debug user-observable behavior before implementation details.
- Keep fixes minimal and close to the helper/test that owns the behavior.
- If cleanup fails after the main test failure, mention it separately.
- If a failure happened in a prior run but not the current run, do not treat it as current evidence.

## Playwright CLI

Use Playwright CLI only when source, logs, and reports are insufficient.

Prefer targeted commands:

```bash
npx -y @playwright/cli@latest open http://localhost:3000 --headed
npx -y @playwright/cli@latest snapshot
```

Avoid repeated full-page snapshots. Capture only the page or dialog needed to explain the failure.

## Fix Pattern

When making a fix:

1. State the root cause in one sentence.
2. Edit only the smallest necessary file(s).
3. Preserve strict assertions.
4. Run the narrow failing test first when possible.
5. Run the UI suite after the narrow test passes.

Commands:

```bash
HEADLESS=true SLOW_MO_MS=0 pytest tests/ui -m ui -q
HEADLESS=false SLOW_MO_MS=500 pytest tests/ui -m ui -q
```

## Summary Format

Return:

1. Root cause
2. Fix made or recommended
3. Validation command
4. Result
5. Remaining risk, if any
