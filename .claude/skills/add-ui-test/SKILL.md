---
description: Add exactly one focused Playwright pytest UI test in this repo. Use when asked to create a new UI test, add coverage for a user flow, add a negative/edge-case test, or turn Playwright CLI/codegen findings into maintainable pytest code.
argument-hint: "[test idea or business rule]"
---

# Add UI Test

Add one focused UI test for `$ARGUMENTS`.

## Goal

Create a maintainable Python pytest + Playwright test that validates user-observable behavior.

Do not add broad refactors, raw codegen, screenshots, traces, or unrelated changes.

## Workflow

1. Inspect existing tests and helpers first.
2. Identify the smallest useful business rule to test.
3. Import page objects from `src.pages`, then create them in the class `setup()` from the raw `page` fixture:
   ```python
   from playwright.sync_api import Page

   from src.pages.alerts_list import AlertsListPage
   from src.pages.alert_detail_drawer import AlertDetailDrawer
   from src.pages.login_page import LoginPage

   class TestFeature:
       @pytest.fixture(autouse=True)
       def setup(self, page: Page) -> None:
           self.login_page = LoginPage(page)
           self.alerts_list = AlertsListPage(page)
           self.alert_detail_drawer = AlertDetailDrawer(page)
   ```
   - Add `@pytest.mark.requires_scan` to UI tests/classes that need alert data from a scan.
   - Never call `api_client.start_scan()` manually from UI tests.
   - Do NOT use `authenticated_page`; UI tests get valid session login automatically from `tests/ui/conftest.py`.
4. Always call `api_client.find_alert(...)` in the test body — the alert type is a business decision visible in the test.
5. Do not call session login manually in normal UI tests. Use this only for tests that validate the login screen itself:
   ```python
   @pytest.mark.login_via_ui
   def test_valid_login(self):
       self.login_page.login_via_ui()
   ```
6. Use `self.alerts_list.open_alert(alert)` to navigate, then page object methods for each UI section.
7. Each UI section gets its own file in `src/pages/`. Locators are defined in `__init__` — never in `src/utils/ui_helpers.py` or test files.
8. Exercise behavior through the UI after setup.
9. Exercise the behavior under test through the UI.
10. Reuse `src/utils/ui_helpers.py` helpers where possible.
11. Add exactly one test unless the user explicitly asks for more.
12. Run the UI suite.

## Playwright CLI Use

Use Playwright CLI only for exploration, selector discovery, or codegen reference.

Codegen command:

```bash
python -m playwright codegen --target=python-pytest -o /tmp/new_flow_codegen.py http://localhost:3000
```

Agent-friendly inspection:

```bash
npx -y @playwright/cli@latest open http://localhost:3000 --headed
npx -y @playwright/cli@latest snapshot
```

Rules:

- Do not commit `/tmp/*_codegen.py`.
- Do not paste raw generated code into tests.
- Convert useful locators and flow into clean pytest code.
- Keep snapshots targeted.

## Locator Policy

Prefer accessibility-first locators:

1. role/name
2. label
3. visible text
4. placeholder
5. test id
6. CSS only as last resort

Python examples:

```python
page.get_by_role("button", name=re.compile("sign in", re.I))
page.get_by_label(re.compile("email", re.I))
page.get_by_text(re.compile("resolved", re.I))
page.get_by_placeholder(re.compile("search", re.I))
```

## Assertion Policy

Use Playwright web-first assertions:

```python
expect(locator).to_be_visible()
expect(locator).to_have_text("Resolved")
expect(locator).not_to_be_visible()
```

Do not use fixed sleeps such as `page.wait_for_timeout()`.
Do not weaken assertions to make flaky tests pass.
Use self-healing only for interaction locators, not business assertions.

## Scope Policy

For this assignment, prefer lightweight helpers over Page Object Model classes.

Introduce Page Objects only when repeated behavior across multiple pages/tests makes the abstraction worthwhile.

## Validation

Default headed validation:

```bash
HEADLESS=false SLOW_MO_MS=500 pytest tests/ui -m ui -q
```

Use headless when speed matters:

```bash
HEADLESS=true SLOW_MO_MS=0 pytest tests/ui -m ui -q
```

If the user asks for a report, run tests normally first, then use `/qa-report`.

## Summary Format

Return:

1. Test added
2. Business rule covered
3. Playwright CLI/codegen used or not used
4. Validation command
5. Result
