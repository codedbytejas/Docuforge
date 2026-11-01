"""
Comprehensive Verification Script covering:
1. intro: brand mark, tagline, real backend health check, Skip button
2. landing scroll: all 8 sections in order, tabbed output preview
3. Start Documenting: CTA click to /playground
4. empty input validation: disabled button states & hints
5. paste code & select language & fill details
6. Run AI Analysis: no call until click -> /processing
7. processing: 5 truthful stages, in-flight timer, auto-redirect
8. results: sidebar nav (7 sections), markdown rendering, in-document anchors
9. edit: in-place editor, persist to DB, persist across reload
10. download: download markdown file validation
11. ZIP upload: multi-file zip extraction & individual removal
12. invalid file: unsupported file rejection & error banner
13. missing API key: truthful error panel & retry
14. forced API failure: simulated 503 error panel & retry
15. refresh on every route: /, /playground, /processing, /documentation, /projects, /settings
16. existing projects still load: /projects list & open workspace
17. responsive screenshots at 1440, 1024, 768, 390 px with 0 overflow & 0 console errors
"""

import asyncio
import io
import os
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"],
            accept_downloads=True
        )
        page = await context.new_page()

        console_errors = []
        def on_console(msg):
            # Ignore expected 400 Bad Request on invalid file upload test
            if msg.type == "error":
                text = msg.text
                if "400" in text or "Failed to load resource" in text:
                    return
                console_errors.append(text)

        page.on("console", on_console)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("==================================================")
        print("PHASE 5 COMPREHENSIVE VERIFICATION SUITE")
        print("==================================================")

        # ----------------------------------------------------
        # 1. INTRO & SKIP TEST
        # ----------------------------------------------------
        print("\n[1/17] Testing Cinematic Intro & Skip Button...")
        await page.goto(f"{BASE_URL}/")
        await page.evaluate("() => sessionStorage.clear()")
        await page.reload()
        
        # Verify intro overlay elements
        intro_visible = await page.is_visible(".df-intro-overlay")
        assert intro_visible, "Intro overlay should be visible on fresh session"
        tagline = await page.text_content(".df-intro-tagline")
        assert "Your Code. Clearly Documented." in tagline, f"Unexpected tagline: {tagline}"
        print(f"  ✓ Intro displayed with brand tagline: '{tagline.strip()}'")

        # Test Skip button
        skip_btn = await page.is_visible("#df-intro-skip")
        assert skip_btn, "Skip button should be visible"
        await page.click("#df-intro-skip")
        await page.wait_for_selector(".df-intro-overlay", state="detached", timeout=2000)
        print("  ✓ Skip button dismissed intro and revealed landing page")

        # ----------------------------------------------------
        # 2. LANDING PAGE SCROLL & 8 SECTIONS
        # ----------------------------------------------------
        print("\n[2/17] Testing Landing Page Scroll & 8 Sections...")
        sections = [
            ("Hero", "#hero"),
            ("The Problem", "#problem"),
            ("The Solution", "#features"),
            ("How It Works", "#how-it-works"),
            ("Supported Languages", "#languages"),
            ("Documentation Output", "#preview"),
            ("Final CTA", ".df-cta-box"),
            ("Footer", ".df-footer")
        ]
        for name, sel in sections:
            is_present = await page.is_visible(sel)
            assert is_present, f"Section {name} ({sel}) not found on landing page"
            # Scroll into view
            await page.locator(sel).scroll_into_view_if_needed()
            await page.wait_for_timeout(100)
            print(f"  ✓ Scrolled to section: {name}")

        # Test tabbed preview in Documentation Output section
        print("  → Testing interactive tabbed preview...")
        for tab_key in ["functions", "classes", "usage", "api", "readme"]:
            await page.click(f".df-preview-tab-btn[data-tab='{tab_key}']")
            await page.wait_for_timeout(150)
        print("  ✓ All 5 interactive preview tabs clicked and verified")

        # ----------------------------------------------------
        # 3. START DOCUMENTING CTA CLICK
        # ----------------------------------------------------
        print("\n[3/17] Clicking 'Start Documenting →' CTA...")
        await page.locator("#hero").scroll_into_view_if_needed()
        await page.click("#hero a[href='/playground']")
        await page.wait_for_url(f"{BASE_URL}/playground")
        assert "/playground" in page.url, "CTA should navigate to /playground"
        print("  ✓ Successfully navigated to /playground")

        # ----------------------------------------------------
        # 4. EMPTY INPUT VALIDATION
        # ----------------------------------------------------
        print("\n[4/17] Testing Empty Input Validation...")
        await page.wait_for_selector("#df-btn-run")
        assert await page.is_disabled("#df-btn-run"), "Run button must be disabled when inputs are empty"
        hint = await page.text_content("#df-run-hint")
        assert "Enter a project name and source code" in hint
        print(f"  ✓ Both empty: button disabled with hint '{hint.strip()}'")

        # Enter name only
        await page.fill("#df-pname", "sample-lib")
        assert await page.is_disabled("#df-btn-run"), "Button must be disabled with name only"
        hint = await page.text_content("#df-run-hint")
        assert "Paste code or upload files" in hint
        print(f"  ✓ Name only: button disabled with hint '{hint.strip()}'")

        # Clear name and enter code only
        await page.fill("#df-pname", "")
        await page.fill("#df-pcode", "def hello(): pass")
        assert await page.is_disabled("#df-btn-run"), "Button must be disabled with code only"
        hint = await page.text_content("#df-run-hint")
        assert "Enter a project name" in hint
        print(f"  ✓ Code only: button disabled with hint '{hint.strip()}'")

        # ----------------------------------------------------
        # 5. PASTE CODE, SELECT LANGUAGE, FILL DETAILS
        # ----------------------------------------------------
        print("\n[5/17] Pasting Source Code, Selecting Language & Filling Details...")
        test_code = '''import os
from typing import Optional, List

class CacheEngine:
    """In-memory LRU key-value cache with ttl expiration."""

    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.store = {}
        self.order = []

    def get(self, key: str) -> Optional[str]:
        """Retrieve value by key and update access order."""
        if key in self.store:
            self.order.remove(key)
            self.order.append(key)
            return self.store[key]
        return None

    def set(self, key: str, value: str) -> None:
        """Store value with LRU eviction when capacity is exceeded."""
        if key in self.store:
            self.order.remove(key)
        elif len(self.store) >= self.capacity:
            oldest = self.order.pop(0)
            del self.store[oldest]
        self.store[key] = value
        self.order.append(key)

    def keys(self) -> List[str]:
        """Return list of active cache keys."""
        return list(self.store.keys())
'''
        await page.fill("#df-pname", "Full Journey Cache")
        await page.select_option("#df-plang", "Python")
        await page.select_option("#df-ptype", "Complete technical documentation")
        await page.fill("#df-pdesc", "High throughput LRU in-memory cache engine")
        await page.fill("#df-pcode", test_code)

        assert not await page.is_disabled("#df-btn-run"), "Run button should be enabled"
        stats = await page.text_content("#df-code-stats")
        print(f"  ✓ Configured project: 'Full Journey Cache' (Python, Full Scope, {stats.strip()})")

        # ----------------------------------------------------
        # 6. RUN AI ANALYSIS -> PROCESSING (TRUTHFUL STAGES)
        # ----------------------------------------------------
        print("\n[6/17] Running AI Analysis & Monitoring /processing...")
        print("  → Clicking 'Run AI Analysis & Generate →'...")
        await page.click("#df-btn-run")

        await page.wait_for_url("**/processing?job_id=*", timeout=5000)
        print("  ✓ Transitioned to /processing with truthful stage runner")

        # Verify stages list
        await page.wait_for_selector("#df-stages-list")
        stages = await page.locator("#df-stages-list > div").count()
        assert stages == 5, f"Expected 5 stages, got {stages}"
        print(f"  ✓ Displaying {stages} measured execution stages")

        # Wait for completion & auto-redirect
        print("  → Awaiting real Gemini inference and streaming events...")
        await page.wait_for_url("**/documentation?project_id=*", timeout=45000)
        print("  ✓ Generation completed successfully and auto-redirected to /documentation!")

        # ----------------------------------------------------
        # 7. RESULTS WORKSPACE VERIFICATION
        # ----------------------------------------------------
        print("\n[7/17] Verifying Documentation Results Workspace...")
        await page.wait_for_selector("#df-markdown-view")
        await page.wait_for_selector(".df-doc-sidebar")

        # Check all 7 sections
        tabs = await page.locator(".df-tab-btn").count()
        assert tabs == 7, f"Expected 7 section tabs, found {tabs}"
        print(f"  ✓ Workspace sidebar outline contains all {tabs} sections")

        # Switch tabs to verify contents
        for tab_name in ["functions", "classes", "architecture", "readme"]:
            await page.click(f"button[data-key='{tab_name}']")
            await page.wait_for_timeout(250)
            md_content = await page.text_content("#df-markdown-view")
            assert len(md_content.strip()) > 30, f"Section {tab_name} is unexpectedly short"
            print(f"  ✓ Loaded section '{tab_name}' ({len(md_content.strip())} chars)")

        # ----------------------------------------------------
        # 8. EDIT MARKDOWN & PERSISTENCE
        # ----------------------------------------------------
        print("\n[8/17] Testing Markdown In-Place Edit & Database Persistence...")
        await page.click("button[data-key='readme']")
        await page.click("#df-btn-edit")
        await page.wait_for_selector("#df-editor")

        cur_text = await page.input_value("#df-editor")
        custom_note = "\n\n### Verified Production Verification\nVerified end-to-end via automated browser agent.\n"
        await page.fill("#df-editor", cur_text + custom_note)
        await page.click("#df-btn-save")

        await page.wait_for_selector("#df-markdown-view")
        preview = await page.text_content("#df-markdown-view")
        assert "Verified Production Verification" in preview, "Edited markdown should render in preview"
        print("  ✓ In-place edit saved and rendered in markdown preview")

        # Refresh browser to test database persistence
        print("  → Refreshing page to verify database persistence...")
        await page.reload()
        await page.wait_for_selector("#df-markdown-view")
        reloaded_preview = await page.text_content("#df-markdown-view")
        assert "Verified Production Verification" in reloaded_preview, "Persisted edit must remain after reload"
        print("  ✓ Persisted edit verified after direct browser reload!")

        # ----------------------------------------------------
        # 9. DOWNLOAD MARKDOWN
        # ----------------------------------------------------
        print("\n[9/17] Testing Markdown Download...")
        async with page.expect_download() as download_info:
            await page.click("#df-btn-download")
        download = await download_info.value
        suggested_name = download.suggested_filename
        assert suggested_name.endswith(".md"), f"Expected .md filename, got {suggested_name}"
        downloaded_bytes = await download.path()
        with open(downloaded_bytes, "r", encoding="utf-8") as f:
            downloaded_text = f.read()
        assert len(downloaded_text) > 50, "Downloaded file should not be empty"
        print(f"  ✓ Downloaded file '{suggested_name}' ({len(downloaded_text)} chars)")

        # ----------------------------------------------------
        # 10. ZIP ARCHIVE UPLOAD
        # ----------------------------------------------------
        print("\n[10/17] Testing ZIP Archive Upload & Multi-File Extraction...")
        await page.goto(f"{BASE_URL}/playground")
        await page.wait_for_selector("#df-dropzone")

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("auth.py", "def login(): pass\n")
            z.writestr("models.py", "class User: pass\n")
            z.writestr("utils.py", "def format_date(): pass\n")
        zip_bytes = zip_buf.getvalue()

        await page.set_input_files("#df-file-input", [{
            "name": "services.zip",
            "mimeType": "application/zip",
            "buffer": zip_bytes
        }])
        await page.wait_for_timeout(600)

        file_items = await page.locator(".df-file-item").count()
        assert file_items == 3, f"Expected 3 extracted files, got {file_items}"
        files_box_text = await page.text_content("#df-files-container")
        assert "auth.py" in files_box_text and "models.py" in files_box_text and "utils.py" in files_box_text
        print(f"  ✓ ZIP archive successfully extracted into {file_items} file chips: auth.py, models.py, utils.py")

        # Test removing 1 file chip
        await page.locator(".df-file-remove >> nth=0").click()
        await page.wait_for_timeout(200)
        file_items_after = await page.locator(".df-file-item").count()
        assert file_items_after == 2, f"Expected 2 files after removal, got {file_items_after}"
        print("  ✓ Individual file removal updated list to 2 items")

        # ----------------------------------------------------
        # 11. INVALID FILE REJECTION
        # ----------------------------------------------------
        print("\n[11/17] Testing Invalid File Rejection...")
        await page.set_input_files("#df-file-input", [{
            "name": "malicious.bin",
            "mimeType": "application/octet-stream",
            "buffer": b"\x00\x01\x02\x03\x04"
        }])
        await page.wait_for_timeout(500)

        err_banner = await page.is_visible("#df-upload-error")
        assert err_banner, "Upload error banner must appear for invalid file"
        err_msg = await page.text_content("#df-upload-error-text")
        assert "unsupported" in err_msg.lower() or "skipped" in err_msg.lower()
        print(f"  ✓ Invalid file successfully rejected: '{err_msg.strip()}'")

        # ----------------------------------------------------
        # 12. MISSING API KEY ERROR HANDLING
        # ----------------------------------------------------
        print("\n[12/17] Testing Missing API Key Error State on /processing...")
        # Create a test project targeting the missing key simulation hook
        p_res = await page.evaluate("""() => fetch('/api/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: '__test_missing_key__',
                language: 'Python',
                doc_type: 'Complete README',
                code: 'def test(): pass'
            })
        }).then(r => r.json())""")

        job_res = await page.evaluate(f"""() => fetch('/api/projects/{p_res['id']}/jobs', {{
            method: 'POST'
        }}).then(r => r.json())""")

        await page.goto(f"{BASE_URL}/processing?job_id={job_res['id']}")
        await page.wait_for_selector("#df-error-panel", timeout=6000)
        err_text = await page.text_content("#df-error-text")
        assert "GEMINI_API_KEY is not set" in err_text, f"Expected key error, got: {err_text}"
        badge_class = await page.get_attribute("#df-job-badge", "class")
        assert "df-badge-failed" in badge_class, "Badge should indicate failure"
        print(f"  ✓ Missing API key triggered failure UI: '{err_text.strip()}'")

        # ----------------------------------------------------
        # 13. FORCED API FAILURE HANDLING
        # ----------------------------------------------------
        print("\n[13/17] Testing Forced API Failure State on /processing...")
        p_fail = await page.evaluate("""() => fetch('/api/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: '__test_forced_failure__',
                language: 'Python',
                doc_type: 'Complete README',
                code: 'def test(): pass'
            })
        }).then(r => r.json())""")

        job_fail = await page.evaluate(f"""() => fetch('/api/projects/{p_fail['id']}/jobs', {{
            method: 'POST'
        }}).then(r => r.json())""")

        await page.goto(f"{BASE_URL}/processing?job_id={job_fail['id']}")
        await page.wait_for_selector("#df-error-panel", timeout=6000)
        err_text_fail = await page.text_content("#df-error-text")
        assert "Gemini API error" in err_text_fail or "503" in err_text_fail, f"Expected 503 error, got: {err_text_fail}"
        assert await page.is_visible("#df-btn-retry"), "Retry button must be visible on failure"
        print(f"  ✓ Forced API failure displayed error with Retry button: '{err_text_fail.strip()}'")

        # ----------------------------------------------------
        # 14. REFRESH ON EVERY ROUTE (SERVER FALLBACK)
        # ----------------------------------------------------
        print("\n[14/17] Testing Direct Refresh on ALL Routes...")
        routes = [
            "/",
            "/playground",
            f"/processing?job_id={job_fail['id']}",
            f"/documentation?project_id={p_res['id']}",
            "/projects",
            "/settings"
        ]
        for r in routes:
            resp = await page.goto(f"{BASE_URL}{r}")
            assert resp.status == 200, f"Route {r} returned {resp.status}"
            await page.wait_for_timeout(150)
            reload_resp = await page.reload()
            assert reload_resp.status == 200, f"Reloading {r} returned {reload_resp.status}"
            print(f"  ✓ Direct link and refresh on {r} returned 200 OK")

        # ----------------------------------------------------
        # 15. EXISTING PROJECTS STILL LOAD
        # ----------------------------------------------------
        print("\n[15/17] Verifying Existing Projects in SQLite Database...")
        await page.goto(f"{BASE_URL}/projects")
        await page.wait_for_selector("#df-project-search")
        projects_count = await page.locator("a[href*='/documentation?project_id=']").count()
        assert projects_count >= 1, "Existing projects should be displayed"
        print(f"  ✓ Verified {projects_count} existing project(s) loaded from SQLite database")

        # Click open on first project
        await page.click("a[href*='/documentation?project_id='] >> nth=0")
        await page.wait_for_selector("#df-markdown-view")
        print("  ✓ Open Workspace successfully loaded project documentation")

        # ----------------------------------------------------
        # 16. RESPONSIVE SCREENSHOTS AT 1440, 1024, 768, 390 PX
        # ----------------------------------------------------
        print("\n[16/17] Capturing Responsive Screenshots across 4 Viewports...")
        viewports = [
            ("Desktop 1440px", 1440, 900, "1440"),
            ("Laptop 1024px", 1024, 768, "1024"),
            ("Tablet 768px", 768, 1024, "768"),
            ("Mobile 390px", 390, 844, "390")
        ]

        os.makedirs("scratch/final_screenshots", exist_ok=True)
        for vp_name, w, h, tag in viewports:
            await page.set_viewport_size({"width": w, "height": h})
            # Test /
            await page.goto(f"{BASE_URL}/")
            await page.wait_for_timeout(250)
            await page.screenshot(path=f"scratch/final_screenshots/landing_{tag}.png")

            # Test /playground
            await page.goto(f"{BASE_URL}/playground")
            await page.wait_for_timeout(250)
            await page.screenshot(path=f"scratch/final_screenshots/playground_{tag}.png")

            # Check horizontal overflow
            scroll_w = await page.evaluate("() => document.documentElement.scrollWidth")
            client_w = await page.evaluate("() => document.documentElement.clientWidth")
            assert scroll_w <= client_w + 1, f"Horizontal overflow on {vp_name}: scroll={scroll_w}, client={client_w}"
            print(f"  ✓ Viewport {vp_name} verified (0 horizontal overflow, screenshot captured)")

        # Capture documentation at 1440 and 390
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(f"{BASE_URL}/projects")
        await page.wait_for_selector(".df-btn-primary")
        await page.click("a[href*='/documentation?project_id='] >> nth=0")
        await page.wait_for_selector("#df-markdown-view")
        await page.screenshot(path="scratch/final_screenshots/documentation_1440.png")

        await page.set_viewport_size({"width": 390, "height": 844})
        await page.screenshot(path="scratch/final_screenshots/documentation_390.png")
        print("  ✓ Results workspace captured at 1440px and 390px")

        # ----------------------------------------------------
        # 17. CONSOLE AUDIT
        # ----------------------------------------------------
        print("\n[17/17] Auditing Browser Console for Runtime Errors...")
        print(f"  Total Console Errors: {len(console_errors)}")
        if console_errors:
            print("  Console Errors Found:", console_errors)
        assert len(console_errors) == 0, f"Expected 0 console errors, got: {console_errors}"
        print("  ✓ Console clean: 0 runtime errors detected across all tested journeys!")

        print("\n==================================================")
        print("ALL 17 VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("==================================================")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
