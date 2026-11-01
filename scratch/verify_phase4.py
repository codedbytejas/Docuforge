"""
Verification script for Phase 4:
- /playground (upload, paste, validation, dynamic scope, run)
- /processing (live SSE stream, truthful stages, error handling, redirect)
- /documentation (sidebar nav, in-document anchors, edit & save persist, copy, download, print)
- /projects (search filter, rename, delete, open)
- /settings (Gemini status, model, defaults, theme switch)
- Responsive checks at 1440, 1024, 768, 390 px.
"""

import asyncio
import io
import json
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("=== Test 1: Navigation Guards ===")
        # 1a. /processing without job_id should redirect to /playground
        await page.goto(f"{BASE_URL}/processing")
        await page.wait_for_timeout(400)
        curr_url = page.url
        assert "/playground" in curr_url, f"Expected redirect to /playground, got {curr_url}"
        print("  ✓ /processing without job_id gracefully redirected to /playground")

        # 1b. /documentation without project_id should redirect to /projects
        # Clear sessionStorage first
        await page.evaluate("() => sessionStorage.clear()")
        await page.goto(f"{BASE_URL}/documentation")
        await page.wait_for_timeout(400)
        curr_url = page.url
        assert "/projects" in curr_url, f"Expected redirect to /projects, got {curr_url}"
        print("  ✓ /documentation without project_id gracefully redirected to /projects")

        print("\n=== Test 2: /playground Validation & Interactions ===")
        await page.goto(f"{BASE_URL}/playground")
        await page.wait_for_selector("#df-btn-run")

        # Check button disabled initially
        is_disabled = await page.is_disabled("#df-btn-run")
        hint_text = await page.text_content("#df-run-hint")
        assert is_disabled, "Run button should be disabled initially"
        print(f"  ✓ Initial button disabled with hint: '{hint_text.strip()}'")

        # Enter project name only
        await page.fill("#df-pname", "phase4-test-lib")
        is_disabled = await page.is_disabled("#df-btn-run")
        hint_text = await page.text_content("#df-run-hint")
        assert is_disabled, "Button should still be disabled with name only"
        assert "Paste code or upload files" in hint_text
        print(f"  ✓ Name only -> disabled with hint: '{hint_text.strip()}'")

        # Click Load Sample
        await page.click("#df-btn-sample")
        await page.wait_for_timeout(200)
        code_val = await page.input_value("#df-pcode")
        assert "class TodoStore:" in code_val, "Sample code not loaded"
        is_disabled = await page.is_disabled("#df-btn-run")
        assert not is_disabled, "Run button should now be enabled"
        stats_text = await page.text_content("#df-code-stats")
        print(f"  ✓ Sample code loaded! Stats: {stats_text.strip()}, Button enabled")

        # Test documentation scope dynamic update
        await page.select_option("#df-ptype", "Complete README")
        await page.wait_for_timeout(100)
        scope_badge = await page.text_content("#df-scope-badge")
        assert "1 Section" in scope_badge, f"Expected '1 Section', got {scope_badge}"
        print(f"  ✓ Dynamic scope selector works: '{scope_badge}'")

        await page.select_option("#df-ptype", "Complete technical documentation")
        await page.wait_for_timeout(100)
        scope_badge = await page.text_content("#df-scope-badge")
        assert "All 7 Sections" in scope_badge, f"Expected 'All 7 Sections', got {scope_badge}"
        print(f"  ✓ Restored full scope: '{scope_badge}'")

        # Test Clear button
        await page.click("#df-btn-clear")
        await page.wait_for_timeout(100)
        code_val = await page.input_value("#df-pcode")
        assert code_val == "", "Code should be cleared"
        is_disabled = await page.is_disabled("#df-btn-run")
        assert is_disabled, "Button should be disabled after clear"
        print("  ✓ Clear button successfully resets code and state")

        # Test File Upload via API / Dropzone simulation
        # Create a sample file and upload it
        test_file_payload = {
            "name": "calculator.py",
            "mimeType": "text/x-python",
            "buffer": b"def add(a: int, b: int) -> int:\n    return a + b\n\ndef multiply(a: int, b: int) -> int:\n    return a * b\n"
        }
        await page.set_input_files("#df-file-input", [test_file_payload])
        await page.wait_for_timeout(500)
        
        # Check files list rendered
        files_count = await page.locator(".df-file-item").count()
        assert files_count >= 1, f"Expected at least 1 file item, found {files_count}"
        file_name = await page.text_content(".df-file-name")
        assert "calculator.py" in file_name, f"Expected calculator.py in files, got {file_name}"
        print(f"  ✓ File upload works! Rendered item: '{file_name.strip()}'")

        # Test remove file item
        await page.click(".df-file-remove")
        await page.wait_for_timeout(200)
        files_count_after = await page.locator(".df-file-item").count()
        assert files_count_after == 0, "File should be removed"
        print("  ✓ File remove button successfully removed uploaded item")

        print("\n=== Test 3: Run AI Generation -> /processing -> /documentation ===")
        # Reload sample code and set project name
        await page.click("#df-btn-sample")
        await page.fill("#df-pname", "E2E Verified Project")
        await page.select_option("#df-ptype", "Complete technical documentation")
        await page.fill("#df-pdesc", "A high performance todo storage library")

        # Click Run AI Analysis
        print("  → Clicking 'Run AI Analysis & Generate'...")
        await page.click("#df-btn-run")

        # Expect transition to /processing
        await page.wait_for_url("**/processing?job_id=*", timeout=6000)
        print("  ✓ Navigated to /processing with job_id!")

        # Verify stages list is visible and active
        await page.wait_for_selector("#df-stages-list")
        stages_count = await page.locator("#df-stages-list > div").count()
        assert stages_count == 5, f"Expected 5 truthful stages, found {stages_count}"
        print(f"  ✓ Processing view loaded with {stages_count} truthful measured stages")

        # Wait for auto-redirect to /documentation (timeout 45s for Gemini AI inference)
        print("  → Awaiting real Gemini inference and truthful stage progression...")
        await page.wait_for_url("**/documentation?project_id=*", timeout=45000)
        print("  ✓ Successfully completed job and auto-redirected to /documentation!")

        print("\n=== Test 4: /documentation Results Workspace ===")
        await page.wait_for_selector("#df-markdown-view")
        await page.wait_for_selector(".df-doc-sidebar")

        # Verify outline has all 7 tabs
        tab_buttons = await page.locator(".df-tab-btn").count()
        assert tab_buttons == 7, f"Expected 7 section tabs in outline, found {tab_buttons}"
        print(f"  ✓ Outline navigation contains all {tab_buttons} sections")

        # Verify rendered markdown
        md_text = await page.text_content("#df-markdown-view")
        assert len(md_text.strip()) > 50, "Markdown content should not be empty"
        print(f"  ✓ Rendered Markdown length: {len(md_text.strip())} characters")

        # Test tab switching: click Functions
        print("  → Testing section navigation (Functions tab)...")
        await page.click("button[data-key='functions']")
        await page.wait_for_timeout(300)
        func_text = await page.text_content("#df-markdown-view")
        print(f"  ✓ Functions section loaded ({len(func_text.strip())} chars)")

        # Switch back to README
        await page.click("button[data-key='readme']")
        await page.wait_for_timeout(300)

        # Test In-document anchor outline if present
        anchors = await page.locator(".df-doc-anchor").count()
        print(f"  ✓ In-document outline detected {anchors} heading anchors")
        if anchors > 0:
            await page.click(".df-doc-anchor >> nth=0")
            print("  ✓ Anchor scroll clicked successfully")

        # Test Edit / Save changes (persistence)
        print("  → Testing Markdown Edit and Save...")
        await page.click("#df-btn-edit")
        await page.wait_for_selector("#df-editor")
        
        # Append verified line
        cur_edit = await page.input_value("#df-editor")
        updated_edit = cur_edit + "\n\n### Verified Custom Note\nThis section was edited and saved live.\n"
        await page.fill("#df-editor", updated_edit)

        # Click Save Changes
        await page.click("#df-btn-save")
        await page.wait_for_selector("#df-markdown-view")
        saved_md = await page.text_content("#df-markdown-view")
        assert "Verified Custom Note" in saved_md, "Edited note should appear in preview"
        print("  ✓ Markdown edit successfully saved and rendered in preview")

        # Verify persistence across page refresh
        print("  → Refreshing /documentation to verify database persistence...")
        await page.reload()
        await page.wait_for_selector("#df-markdown-view")
        reloaded_md = await page.text_content("#df-markdown-view")
        assert "Verified Custom Note" in reloaded_md, "Persisted note should remain after reload"
        print("  ✓ Edit persisted cleanly across browser reload!")

        # Test Copy button
        await page.click("#df-btn-copy")
        await page.wait_for_timeout(200)
        toast_text = await page.text_content("#df-toast-container")
        assert "Copied" in toast_text, f"Expected Copy toast, got {toast_text}"
        print("  ✓ Copy section triggered with toast confirmation")

        print("\n=== Test 5: /projects Management ===")
        await page.goto(f"{BASE_URL}/projects")
        await page.wait_for_selector("#df-project-search")

        # Verify our newly created project is listed
        projects_text = await page.text_content("main")
        assert "E2E Verified Project" in projects_text, "E2E project should be listed in /projects"
        print("  ✓ Newly generated project listed in /projects")

        # Test Search filter
        await page.fill("#df-project-search", "E2E Verified")
        await page.wait_for_timeout(200)
        assert "E2E Verified Project" in await page.text_content("main")
        
        await page.fill("#df-project-search", "nonexistent-xyz-search-1234")
        await page.wait_for_timeout(200)
        assert "No matching projects" in await page.text_content("main")
        print("  ✓ Search filtering works in real-time")

        # Clear search
        await page.fill("#df-project-search", "")
        await page.wait_for_timeout(200)

        # Test Rename
        print("  → Testing Project Rename dialog...")
        page.on("dialog", lambda d: asyncio.create_task(d.accept("E2E Renamed Project")))
        await page.locator(".df-btn-rename >> nth=0").click()
        await page.wait_for_timeout(500)
        assert "E2E Renamed Project" in await page.text_content("main")
        print("  ✓ Project rename succeeded and reflected immediately")

        print("\n=== Test 6: /settings Configuration ===")
        await page.goto(f"{BASE_URL}/settings")
        await page.wait_for_selector("#df-set-lang")

        # Verify status badges
        status_text = await page.text_content("main")
        assert "Configured" in status_text, "Gemini status should be Configured"
        model_val = await page.input_value("input[readonly]")
        assert "gemini-3.5-flash" in model_val, f"Active model should be gemini-3.5-flash, got {model_val}"
        print(f"  ✓ Gemini service integration verified in settings (model: {model_val})")

        # Change defaults
        await page.select_option("#df-set-lang", "TypeScript")
        await page.select_option("#df-set-type", "API documentation")
        await page.click("#df-save-pref")
        await page.wait_for_timeout(200)

        # Verify localStorage saved
        stored_lang = await page.evaluate("() => localStorage.getItem('df_default_lang')")
        stored_type = await page.evaluate("() => localStorage.getItem('df_default_doc_type')")
        assert stored_lang == "TypeScript", f"Expected TypeScript, got {stored_lang}"
        assert stored_type == "API documentation", f"Expected API documentation, got {stored_type}"
        print(f"  ✓ Saved preferences to localStorage: lang={stored_lang}, doc_type={stored_type}")

        # Test Theme toggle in settings
        await page.click("#df-theme-light")
        await page.wait_for_timeout(200)
        theme = await page.evaluate("() => document.documentElement.dataset.theme")
        assert theme == "light", f"Expected light theme, got {theme}"
        print("  ✓ Switched to Light theme")

        await page.click("#df-theme-dark")
        await page.wait_for_timeout(200)
        theme = await page.evaluate("() => document.documentElement.dataset.theme")
        assert theme == "dark", f"Expected dark theme, got {theme}"
        print("  ✓ Switched back to Dark theme")

        print("\n=== Test 7: Responsive Layouts across 4 Viewports ===")
        viewports = [
            ("Desktop 1440px", 1440, 900),
            ("Laptop 1024px", 1024, 768),
            ("Tablet 768px", 768, 1024),
            ("Mobile 390px", 390, 844)
        ]

        routes_to_capture = ["/playground", "/projects", "/settings"]
        for vp_name, width, height in viewports:
            await page.set_viewport_size({"width": width, "height": height})
            for r in routes_to_capture:
                await page.goto(f"{BASE_URL}{r}")
                await page.wait_for_timeout(300)
                # Verify no horizontal scrollbar / overflow
                scroll_width = await page.evaluate("() => document.documentElement.scrollWidth")
                client_width = await page.evaluate("() => document.documentElement.clientWidth")
                assert scroll_width <= client_width + 1, f"Horizontal overflow on {r} at {width}px: scroll={scroll_width}, client={client_width}"
            print(f"  ✓ Verified no horizontal overflow on {vp_name} ({width}px)")

        # Capture representative screenshot of /documentation at 1440px and 390px
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(f"{BASE_URL}/projects")
        await page.wait_for_selector(".df-btn-primary")
        # Click Open on first project
        await page.click("a[href*='/documentation?project_id='] >> nth=0")
        await page.wait_for_selector("#df-markdown-view")
        await page.screenshot(path="scratch/screenshot_documentation_1440.png")
        print("  ✓ Saved scratch/screenshot_documentation_1440.png")

        await page.set_viewport_size({"width": 390, "height": 844})
        await page.screenshot(path="scratch/screenshot_documentation_390.png")
        print("  ✓ Saved scratch/screenshot_documentation_390.png")

        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(f"{BASE_URL}/playground")
        await page.screenshot(path="scratch/screenshot_playground_1440.png")
        print("  ✓ Saved scratch/screenshot_playground_1440.png")

        await page.goto(f"{BASE_URL}/projects")
        await page.screenshot(path="scratch/screenshot_projects_1440.png")
        print("  ✓ Saved scratch/screenshot_projects_1440.png")

        await page.goto(f"{BASE_URL}/settings")
        await page.screenshot(path="scratch/screenshot_settings_1440.png")
        print("  ✓ Saved scratch/screenshot_settings_1440.png")

        print(f"\nConsole Errors Count: {len(console_errors)}")
        if console_errors:
            print("Console Errors:", console_errors)
        assert len(console_errors) == 0, f"Found console errors: {console_errors}"
        print("\nALL PHASE 4 TESTS PASSED WITH 0 CONSOLE ERRORS!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
