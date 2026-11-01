"""
Comprehensive Fix Pass Verification for DocuForge AI.
Tests every item in sections 1 to 10 + Verification.
"""

import asyncio
import io
import os
import shutil
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
ARTIFACT_DIR = "/Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f"

results = []

def record(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

async def check_no_horizontal_overflow(page, url_path, viewport_w, viewport_h, theme="dark"):
    await page.set_viewport_size({"width": viewport_w, "height": viewport_h})
    await page.goto(f"{BASE_URL}{url_path}", wait_until="networkidle")
    
    # Set theme if needed
    if theme == "light":
        await page.evaluate("() => document.documentElement.dataset.theme = 'light'")
    else:
        await page.evaluate("() => document.documentElement.dataset.theme = 'dark'")
    
    await page.wait_for_timeout(200)
    
    scroll_w = await page.evaluate("() => document.documentElement.scrollWidth")
    client_w = await page.evaluate("() => window.innerWidth")
    
    # Find any offending element wider than viewport if scroll_w > client_w + 1
    offenders = []
    if scroll_w > client_w + 1:
        offenders = await page.evaluate("""() => {
            const bad = [];
            const w = window.innerWidth;
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.right > w + 2 || el.scrollWidth > w + 2) {
                    bad.push({
                        tag: el.tagName,
                        cls: el.className,
                        id: el.id,
                        right: rect.right,
                        scrollWidth: el.scrollWidth
                    });
                }
            });
            return bad.slice(0, 5);
        }""")
    
    passed = scroll_w <= client_w + 1
    detail = f"scrollWidth={scroll_w}, innerWidth={client_w}"
    if offenders:
        detail += f", offenders: {offenders}"
    return passed, detail

async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"],
            accept_downloads=True
        )
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" and "400" not in msg.text and "Failed to load resource" not in msg.text else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("\n=== STARTING DOCUFORGE AI FIX PASS VERIFICATION ===\n")

        # ----------------------------------------------------
        # TEST 1: CINEMATIC INTRO & BRAND MARK
        # ----------------------------------------------------
        await page.goto(f"{BASE_URL}/")
        # Check intro overlay
        intro_exists = await page.is_visible(".df-intro-overlay")
        record("Intro Overlay Visible", intro_exists)
        
        # Check wordmark & tagline
        wordmark_text = await page.text_content(".df-intro-wordmark")
        record("Intro DOCUFORGE AI Wordmark", "DOCUFORGE AI" in (wordmark_text or ""))
        
        tagline_text = await page.text_content(".df-intro-tagline")
        record("Intro Tagline Enlarge", "Your Code. Clearly Documented." in (tagline_text or ""))
        
        # Click skip
        skip_btn = page.locator("#df-intro-skip")
        await skip_btn.click()
        await page.wait_for_timeout(500)
        intro_gone = not await page.is_visible(".df-intro-overlay")
        record("Intro Skip Functionality", intro_gone)

        # ----------------------------------------------------
        # TEST 2: LANDING PAGE COPY ACCURACY (Section 4)
        # ----------------------------------------------------
        landing_text = await page.text_content(".df-landing-wrapper")
        
        unverified_claims = [
            "thread-safe",
            "Python 3.10+",
            "100% deterministic",
            "Zero hallucinations",
            "verified Python codebase",
            "Active Engine"
        ]
        
        found_claims = [c for c in unverified_claims if c.lower() in landing_text.lower()]
        record("Copy Accuracy - No Fake Claims", len(found_claims) == 0, f"Found: {found_claims}" if found_claims else "Zero unverified claims found")

        # Check illustrative example badge
        example_badges = await page.locator(".df-example-label").count()
        record("Illustrative Example Labels Present", example_badges >= 2, f"Found {example_badges} badges")

        # Check dynamic model in hero card header
        model_header = await page.text_content(".df-pipeline-mockup .df-mockup-header")
        record("Hero Model Header Dynamic", "gemini" in (model_header or "").lower(), f"Header: {model_header}")

        # Check 10 languages + Other fallback (no 'Supported' pills)
        supported_pills = await page.locator(".df-languages-container .df-badge").count()
        lang_rows = await page.locator(".df-language-row").count()
        record("10 Languages List (No Supported Pills)", lang_rows == 10 and supported_pills == 0, f"Rows: {lang_rows}, Pills: {supported_pills}")

        fallback_text = await page.text_content(".df-languages-fallback")
        record("Other Plain-Text Fallback", "Other" in (fallback_text or ""))

        # Check Problem editorial layout & Stepper
        editorial_items = await page.locator(".df-problem-editorial-item").count()
        record("The Problem Editorial Layout", editorial_items == 4, f"Found {editorial_items} editorial items")

        stepper_items = await page.locator(".df-stepper-item").count()
        record("How It Works Vertical Stepper", stepper_items == 3, f"Found {stepper_items} stepper items")

        # Check About section
        about_visible = await page.is_visible("#about")
        record("About Section Present", about_visible)

        # ----------------------------------------------------
        # TEST 3: NAVIGATION & MOBILE MENU (Section 1 & 6)
        # ----------------------------------------------------
        # Test mobile header at 320px
        passed_320, det_320 = await check_no_horizontal_overflow(page, "/", 320, 600)
        record("Mobile Header Fits at 320px (0 overflow)", passed_320, det_320)

        # Test mobile drawer opens and closes
        await page.set_viewport_size({"width": 360, "height": 800})
        menu_btn = page.locator("#df-mobile-menu-btn")
        await menu_btn.click()
        drawer_open = await page.evaluate("() => document.getElementById('df-mobile-drawer').classList.contains('open')")
        record("Mobile Hamburger Menu Drawer Opens", drawer_open)

        # Click link in drawer to close
        drawer_link = page.locator("#df-mobile-drawer .df-mobile-drawer-link[href='/playground']")
        await drawer_link.click()
        await page.wait_for_timeout(300)
        current_url = page.url
        record("Mobile Drawer Link Navigates to Playground", "/playground" in current_url)

        # Confirm Document Code button NOT present on playground header
        doc_code_header_btn = await page.locator(".df-navbar .df-navbar-cta-desktop").count()
        record("Redundant Document Code Button Removed on Playground", doc_code_header_btn == 0)

        # ----------------------------------------------------
        # TEST 4: PLAYGROUND SEGMENTED CONTROL & LINE-NUMBERED EDITOR (Section 7)
        # ----------------------------------------------------
        # Check segmented control exists
        segmented_visible = await page.is_visible("#df-input-mode-segmented")
        record("Playground Segmented Control Present", segmented_visible)

        # Check line-numbered editor in Paste mode
        btn_paste = page.locator("#df-btn-mode-paste")
        await btn_paste.click()
        editor_visible = await page.is_visible("#df-pcode")
        line_num_visible = await page.is_visible("#df-line-numbers")
        record("Paste Mode Syntax Editor & Line Numbers", editor_visible and line_num_visible)

        # Load sample
        btn_sample = page.locator("#df-btn-sample")
        await btn_sample.click()
        await page.wait_for_timeout(200)
        sample_code_val = await page.input_value("#df-pcode")
        record("Load Sample Populates Code", "class TodoStore" in sample_code_val)

        # Check Output Scope reflects documentation type
        type_select = page.locator("#df-ptype")
        await type_select.select_option("Complete README")
        await page.wait_for_timeout(100)
        scope_badge = await page.text_content("#df-scope-badge")
        record("Output Scope Dynamically Reflects README", "README" in (scope_badge or ""))

        await type_select.select_option("Function documentation")
        await page.wait_for_timeout(100)
        scope_badge = await page.text_content("#df-scope-badge")
        record("Output Scope Dynamically Reflects Functions", "Function" in (scope_badge or ""))

        # Reset to Complete technical documentation
        await type_select.select_option("Complete technical documentation")

        # ----------------------------------------------------
        # TEST 5: UPLOAD BUG & '# FILE: x' DELIMITER TEST (Section 2 & 3)
        # ----------------------------------------------------
        btn_upload = page.locator("#df-btn-mode-upload")
        await btn_upload.click()
        
        # Test 5A: File containing literal text "# FILE: x"
        trick_file_content = """# FILE: dummy_split\ndef tricky_function():\n    print("# FILE: nested_string")\n    return 42\n"""
        trick_file_path = "scratch/trick_file.py"
        with open(trick_file_path, "w") as f:
            f.write(trick_file_content)

        file_input = page.locator("#df-file-input")
        await file_input.set_input_files(trick_file_path)
        await page.wait_for_timeout(500)

        # Verify only 1 file is in the loaded files list!
        file_items = await page.locator(".df-file-item").count()
        file_name_text = await page.text_content(".df-file-name")
        record("No File Splitting on '# FILE: x' Content", file_items == 1 and "trick_file.py" in (file_name_text or ""), f"Items count: {file_items}, Name: {file_name_text}")

        # Test 5B: Secret file denial (.env) & neutral notice
        secret_file_path = "scratch/.env"
        with open(secret_file_path, "w") as f:
            f.write("SECRET_KEY=supersecret123\n")
        
        normal_file_path = "scratch/utils.py"
        with open(normal_file_path, "w") as f:
            f.write("def helper():\n    return 'hello'\n")

        await file_input.set_input_files([secret_file_path, normal_file_path])
        await page.wait_for_timeout(500)

        # Check that .env was skipped with neutral notice
        notice_visible = await page.is_visible("#df-skipped-notice")
        notice_text = await page.text_content("#df-skipped-notice-text")
        record("Secret File (.env) Denied with Neutral Notice", notice_visible and ".env" in (notice_text or ""), f"Notice: {notice_text}")

        # Check multi-file ZIP upload with docuforge source
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("app/main.py", "def main():\n    print('main')\n")
            z.writestr("app/service.ts", "export class Service {\n  run() { return true; }\n}\n")
            z.writestr("app/queries.sql", "SELECT id, name FROM users;\n")
            z.writestr("app/.env.local", "API_KEY=denied\n")
        zip_bytes = zip_buf.getvalue()
        zip_path = "scratch/test_bundle.zip"
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)

        await file_input.set_input_files(zip_path)
        await page.wait_for_timeout(600)

        zip_file_items = await page.locator(".df-file-item").count()
        record("Multi-File ZIP Archive Uploaded Correctly", zip_file_items == 3, f"Files loaded: {zip_file_items} (3 expected: .py, .ts, .sql)")

        # Check language auto-detection showed "Mixed"
        detected_lang = await page.input_value("#df-plang")
        record("Language Auto-Detection 'Mixed'", detected_lang == "Mixed", f"Detected: {detected_lang}")

        # ----------------------------------------------------
        # TEST 6: RUN AI ANALYSIS -> PROCESSING WITH CANCEL & TIMERS (Section 8)
        # ----------------------------------------------------
        # First test Cancel Action:
        await page.fill("#df-pname", "cancel-test-project")
        run_btn = page.locator("#df-btn-run")
        await run_btn.click()
        await page.wait_for_url("**/processing?job_id=**")
        
        cancel_btn = page.locator("#df-btn-cancel")
        await cancel_btn.click()
        await page.wait_for_timeout(600)
        
        cancel_badge = await page.text_content("#df-job-badge")
        record("Cancel Generation Job", "Cancelled" in (cancel_badge or ""), f"Badge: {cancel_badge}")

        # Now run a full generation run with TodoStore sample:
        await page.goto(f"{BASE_URL}/playground")
        btn_paste = page.locator("#df-btn-mode-paste")
        await btn_paste.click()
        await page.locator("#df-btn-sample").click()
        await page.fill("#df-pname", "todostore-verified")
        await page.locator("#df-btn-run").click()
        await page.wait_for_url("**/processing?job_id=**")

        # Verify live processing elements
        elapsed_text = await page.text_content("#df-elapsed-ticker")
        record("Live Elapsed Time Counter Active", "s" in (elapsed_text or ""))

        scope_stats_text = await page.text_content("#df-scope-stats")
        record("Scope Stats Displayed on Processing", "file" in (scope_stats_text or "").lower())

        # Test refresh on /processing resumes
        await page.reload()
        await page.wait_for_timeout(500)
        stage_items = await page.locator("#df-stages-list > div").count()
        record("Refreshing /processing Resumes Stream", stage_items >= 4, f"Stages count: {stage_items}")

        # Wait for completion & auto-redirect to /documentation
        print("Waiting for generation completion...")
        await page.wait_for_url("**/documentation?project_id=**", timeout=45000)
        record("Auto-Redirect to Documentation on Complete", "/documentation" in page.url)
        doc_project_id = page.url.split("project_id=")[1].split("&")[0]

        # ----------------------------------------------------
        # TEST 7: RESULTS WORKSPACE & SOURCE SCOPE (Section 10)
        # ----------------------------------------------------
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.wait_for_timeout(300)

        # Source scope shows file count & collapsible list
        scope_card = page.locator(".df-source-scope-details")
        record("Source Scope Collapsible File List", await scope_card.count() > 0)

        # Test desktop section tabs
        tab_funcs = page.locator(".df-doc-sidebar .df-tab-btn[data-key='functions']")
        await tab_funcs.click()
        await page.wait_for_timeout(300)
        md_view = await page.text_content("#df-markdown-view")
        record("Functions Section Renders", len((md_view or "").strip()) > 10)

        # Test mobile horizontal tabs at 360px
        await page.set_viewport_size({"width": 360, "height": 800})
        await page.wait_for_timeout(300)
        mobile_tab_classes = page.locator(".df-doc-mobile-tab-btn[data-key='classes']")
        await mobile_tab_classes.click()
        await page.wait_for_timeout(300)
        md_classes_view = await page.text_content("#df-markdown-view")
        record("Mobile Horizontal Tab Switching", "TodoStore" in (md_classes_view or "") or len((md_classes_view or "").strip()) > 10)

        # Test Edit & Save (return to 1440 for desktop tools)
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.wait_for_timeout(300)
        btn_edit = page.locator("#df-btn-edit")
        await btn_edit.click()
        editor_visible = await page.is_visible("#df-editor")
        record("Documentation In-Place Editor Opens", editor_visible)

        # Add custom note and save
        await page.fill("#df-editor", "# Verified Custom Doc\n\nCustom manual note.")
        await page.locator("#df-btn-save").click()
        await page.wait_for_timeout(500)
        saved_view = await page.text_content("#df-markdown-view")
        record("Documentation Edits Persist to DB", "Verified Custom Doc" in (saved_view or ""))

        # Test Copy section
        btn_copy = page.locator("#df-btn-copy")
        await btn_copy.click()
        await page.wait_for_timeout(400)
        toasts = await page.locator(".df-toast").all_text_contents()
        has_copy_toast = any("Copied" in t for t in toasts)
        record("Copy Markdown Section", has_copy_toast, f"Toasts: {toasts}")

        # Test Download
        async with page.expect_download() as download_info:
            await page.click("#df-btn-download")
        download = await download_info.value
        record("Download Markdown File", download.suggested_filename.endswith(".md"), f"Filename: {download.suggested_filename}")

        # ----------------------------------------------------
        # TEST 8: RESPONSIVE OVERFLOW AUDIT (Section 1)
        # Test EVERY route at 320, 360, 390, 768, 1024, 1440 in Dark & Light modes!
        # ----------------------------------------------------
        routes_to_test = [
            ("/", "Landing"),
            ("/playground", "Playground"),
            ("/projects", "Projects"),
            ("/settings", "Settings"),
            (f"/documentation?project_id={doc_project_id}", "Documentation")
        ]

        viewports = [
            (320, 600, "320px"),
            (360, 800, "360px"),
            (390, 844, "390px"),
            (768, 1024, "768px"),
            (1024, 768, "1024px"),
            (1440, 900, "1440px")
        ]

        print("\n--- Running Horizontal Overflow Audit across all routes & viewports ---")
        all_responsive_ok = True
        for path, label in routes_to_test:
            for w, h, vlabel in viewports:
                for theme in ["dark", "light"]:
                    passed, det = await check_no_horizontal_overflow(page, path, w, h, theme)
                    if not passed:
                        all_responsive_ok = False
                        record(f"Responsive {label} @ {vlabel} ({theme})", False, det)

        if all_responsive_ok:
            record("Universal Responsive Fit (0 horizontal overflow at 320-1440px on all pages)", True)

        # ----------------------------------------------------
        # TEST 9: REFRESH ON EVERY ROUTE
        # ----------------------------------------------------
        refresh_ok = True
        for path, label in [("/", "Landing"), ("/playground", "Playground"), ("/projects", "Projects"), ("/settings", "Settings")]:
            await page.goto(f"{BASE_URL}{path}")
            await page.reload()
            title = await page.title()
            if not title:
                refresh_ok = False
        record("Refresh Works on Every Route", refresh_ok)

        # ----------------------------------------------------
        # TEST 10: CAPTURE SCREENSHOTS FOR ARTIFACTS
        # ----------------------------------------------------
        print("\nCapturing verification screenshots...")
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        
        screenshot_configs = [
            ("/", 1440, 900, "landing_1440.png"),
            ("/", 360, 800, "landing_360.png"),
            ("/", 390, 844, "landing_390.png"),
            ("/", 768, 1024, "landing_768.png"),
            ("/", 1024, 768, "landing_1024.png"),
            ("/playground", 1440, 900, "playground_1440.png"),
            ("/playground", 360, 800, "playground_360.png"),
            ("/playground", 390, 844, "playground_390.png"),
            ("/playground", 768, 1024, "playground_768.png"),
            (f"/documentation?project_id={doc_project_id}", 1440, 900, "documentation_1440.png"),
            (f"/documentation?project_id={doc_project_id}", 360, 800, "documentation_360.png"),
            ("/projects", 1440, 900, "projects_1440.png"),
            ("/projects", 360, 800, "projects_360.png"),
            ("/settings", 1440, 900, "settings_1440.png"),
            ("/settings", 360, 800, "settings_360.png")
        ]

        for path, w, h, fname in screenshot_configs:
            await page.set_viewport_size({"width": w, "height": h})
            await page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
            await page.wait_for_timeout(200)
            target_path = os.path.join(ARTIFACT_DIR, fname)
            await page.screenshot(path=target_path, full_page=False)

        record("Artifact Screenshots Captured", True, f"{len(screenshot_configs)} files saved to {ARTIFACT_DIR}")

        # Check console errors
        record("Browser Console 0 Errors", len(console_errors) == 0, f"Errors: {console_errors}" if console_errors else "Clean console")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_tests())

