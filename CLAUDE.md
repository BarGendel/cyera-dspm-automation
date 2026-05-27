# Claude Code Policy

Use this policy when working in this repo.

## Main Workflow

This project uses Python pytest with the Python Playwright library as the source of truth for automated test execution.

- Use Playwright CLI for exploration, codegen, selector discovery, and debugging.
- Convert any generated code into clean pytest code before keeping it.
- Run the real suite through pytest, not through Playwright CLI.
- Use Claude only as an assistant for exploration, implementation, and report generation. Pytest owns pass/fail.

## Playwright CLI Usage

Good commands:

```bash
python -m playwright codegen --target=python-pytest -o /tmp/new_flow_codegen.py http://localhost:3000
npx -y @playwright/cli@latest open http://localhost:3000 --headed
npx -y @playwright/cli@latest snapshot
npx @playwright/mcp@latest --output-dir .artifacts/playwright-mcp
```

Rules:

- Do not commit raw codegen output.
- Do not commit `.artifacts/`, `.playwright-cli/`, `.playwright-mcp/`, screenshots, traces, videos, or temporary snapshots.
- Keep CLI snapshots small and targeted. Do not dump the full page repeatedly unless a failure requires it.
- Prefer headed mode when the user wants to watch the demo.

## Test Authoring

When adding UI tests:

- Test user behavior, not implementation details.
- Use API helpers only to create reliable preconditions, such as reset, scan, and finding a known alert.
- Keep `api_client.find_alert(...)` inside the test so the selected business precondition is visible.
- Add `@pytest.mark.requires_scan` to UI tests/classes that need alert data from a scan.
- Follow the class setup pattern: create page objects from the raw `page` fixture in `setup()`.
- Include `self.login_page = LoginPage(page)` in UI test classes that need authenticated navigation.
- UI tests get valid session login automatically from `tests/ui/conftest.py`.
- Do not call `self.login_page.login_via_session("valid")` manually in normal UI tests.
- Use `@pytest.mark.login_via_ui` plus `self.login_page.login_via_ui()` only when the login page itself is the behavior under test.
- For UI alert tests, select the alert in the test and then call `self.alerts_list.open_alert(alert)`.
- Exercise the behavior under test through the UI.
- Reuse page objects and helpers where possible.
- Prefer existing pytest fixtures (`page`, `api_client`, `settings`) over repeated setup.
- Keep each test focused on one business rule.
- Keep assertions strict. Do not soften assertions to make flaky tests pass.
- Use Playwright web-first assertions such as `expect(locator).to_be_visible()`.
- Do not use fixed sleeps such as `page.wait_for_timeout()`; wait for real UI or backend state.
- Use self-healing only for interaction locators, not for business assertions.
- Prefer semantic Playwright locators in this order: role/name, label, visible text, placeholder, data-testid, CSS as last resort.
- Do not introduce Page Object Model classes until repeated page behavior across multiple tests justifies it.

Example target test:

```text
test_open_alert_cannot_jump_to_resolved
```

Purpose:

```text
An Open manual-remediation alert should show In Progress as an available transition and should not offer Resolved directly.
```

## Running Tests

Watch the browser:

```bash
HEADLESS=false SLOW_MO_MS=500 pytest tests/ui -m ui -q
```

Run headless:

```bash
HEADLESS=true SLOW_MO_MS=0 pytest tests/ui -m ui -q
```

Run tests and generate the AI report:

```bash
GENERATE_AI_REPORT=true HEADLESS=false SLOW_MO_MS=500 pytest tests/ui -m ui -q
```

## Claude Code Skills

Use project skills for repeatable workflows:

```text
/add-ui-test add a test that Open alert cannot jump directly to Resolved
/flaky-debug analyze the latest UI failure
/qa-report summarize the latest UI run
```

Use `/add-ui-test` when creating one focused UI test.
Use `/flaky-debug` when a test fails or flakes.
Use `/qa-report` when generating or reviewing the execution report.

## AI Report Policy

The AI report is a post-test summary only.

- Pytest generates `.artifacts/reports/session-summary.json`.
- Pytest writes `.artifacts/logs/automation.log`.
- Claude summarizes those artifacts into `.artifacts/reports/qa-execution-report.md` only when `GENERATE_AI_REPORT=true`.
- Claude must not change source files during report generation.
- Reports must describe only what the tests executed and asserted.
- Do not report failures from prior runs.
- Do not include secrets, tokens, full stack traces, or raw logs.

## Interview Explanation

Use this wording:

```text
I use Playwright CLI to inspect and capture the real browser flow, then convert that into maintainable pytest code. The actual suite runs through pytest with fixtures, setup/teardown, strict assertions, logs, JSON reporting, and optional Claude-generated QA reporting. Claude helps summarize the results, but pytest is the source of truth.
```
