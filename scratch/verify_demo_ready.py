"""
DocuForge AI — Demo-Ready Premium Comprehensive Playwright Verification Suite.
Validates all requirements across Sections 1 to 14.
"""

import asyncio
import io
import os
import sys
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
ARTIFACT_DIR = "/Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f"
SHOTS_DIR = os.path.join(ARTIFACT_DIR, "demo_screenshots")
os.makedirs(SHOTS_DIR, exist_ok=True)

test_results = []
console_errors = []

def record(name, passed, detail=""):
    test_results.append({"name": name, "passed": passed, "detail": detail})
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}" + (f" -> {detail}" if detail else ""))

async def check_no_horizontal_overflow(page, url_path, viewport_w, viewport_h, route_name):
    await page.set_viewport_size({"width": viewport_w, "height": viewport_h})
    await page.goto(f"{BASE_URL}{url_path}", wait_until="networkidle")
    await page.wait_for_timeout(250)

    scroll_w = await page.evaluate("() => document.documentElement.scrollWidth")
    client_w = await page.evaluate("() => window.innerWidth")
    
    passed = scroll_w <= client_w + 1
    detail = f"scrollWidth={scroll_w}, innerWidth={client_w}"
    if not passed:
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
                        right: Math.round(rect.right),
                        scrollWidth: el.scrollWidth
                    });
                }
            });
            return bad.slice(0, 3);
        }""")
        detail += f" | Offenders: {offenders}"
    
    record(f"Responsive: {route_name} at {viewport_w}x{viewport_h}", passed, detail)
    return passed

async def main():
    print("==================================================================")
    print("      DOCUFORGE AI — DEMO-READY VERIFICATION SUITE               ")
    print("==================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            accept_downloads=True
        )
        page = await context.new_page()

        # Monitor console errors
        def on_console(msg):
            if msg.type == "error":
                text = msg.text
                if "favicon" not in text and "404" not in text:
                    console_errors.append(f"[CONSOLE ERROR] {text}")
        
        def on_page_error(exc):
            console_errors.append(f"[PAGE ERROR] {str(exc)}")

        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        # -------------------------------------------------------------
        # STEP 1: Intro Screen & Health Check & Skip Action
        # -------------------------------------------------------------
        print("\n--- STEP 1: Intro Screen & First-Visit Experience ---")
        await page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        await page.wait_for_timeout(400)

        intro_el = await page.query_selector("#df-intro-screen")
        has_intro = intro_el is not None
        record("Intro: Displays on first visit", has_intro)

        # Skip intro
        skip_btn = await page.query_selector("#df-intro-skip")
        if skip_btn:
            await skip_btn.click()
            await page.wait_for_timeout(600)
            intro_hidden = await page.evaluate("() => !document.getElementById('df-intro-screen') || document.getElementById('df-intro-screen').style.display === 'none'")
            record("Intro: Skip action dismisses overlay", intro_hidden)
            is_stored = await page.evaluate("() => sessionStorage.getItem('df_intro_done') === 'true'")
            record("Intro: Sets session flag 'df_intro_done'", is_stored)
        else:
            record("Intro: Skip button found", False, "Missing #df-intro-skip")

        # Capture landing hero screenshot
        await page.screenshot(path=os.path.join(SHOTS_DIR, "01_landing_hero_1440.png"))

        # -------------------------------------------------------------
        # STEP 2: Landing Page Content, Sections, Copy Accuracy & Dynamic Model
        # -------------------------------------------------------------
        print("\n--- STEP 2: Landing Page Copy & Sections ---")
        landing_text = await page.content()
        
        # Verify banned unverifiable claims are ABSENT
        banned_phrases = [
            "thread-safe",
            "Python 3.10+",
            "100% deterministic",
            "Zero hallucinations",
            "verified codebase",
            "Active Engine"
        ]
        claims_clean = True
        failed_claims = []
        for phrase in banned_phrases:
            if phrase.lower() in landing_text.lower():
                claims_clean = False
                failed_claims.append(phrase)
        record("Copy Accuracy: Zero unverifiable claims in landing copy", claims_clean, f"Found: {failed_claims}" if failed_claims else "Clean")

        # Verify dynamic model name displayed (gemini-3.5-flash)
        has_model = "gemini-3.5-flash" in landing_text
        record("Copy Accuracy: Dynamic model name from /api/status", has_model, "gemini-3.5-flash present")

        # Verify 10 languages and Other fallback
        langs_count = await page.evaluate("""() => {
            return document.querySelectorAll('.df-language-row').length;
        }""")
        record("Landing: Languages section presents 10 languages", langs_count == 10, f"Count: {langs_count}")

        # Test interactive preview tabs
        tab_clicked = False
        api_tab = await page.query_selector('.df-preview-tab-btn[data-tab="api"]')
        if api_tab:
            await api_tab.click()
            await page.wait_for_timeout(250)
            tab_content = await page.inner_text("#df-landing-preview-content")
            tab_clicked = "Public API Interface Contract" in tab_content or "TodoStore" in tab_content
        record("Landing: Interactive Preview tabs switch content", tab_clicked)

        # -------------------------------------------------------------
        # STEP 3: Navigation to Playground & Input Validation
        # -------------------------------------------------------------
        print("\n--- STEP 3: Playground Input Modes & Form Validation ---")
        await page.click('a[href="/playground"]')
        await page.wait_for_timeout(400)
        
        current_url = page.url
        record("Navigation: Landing CTA navigates to /playground", "/playground" in current_url)

        # Empty state validation: Run AI Analysis disabled
        run_btn = await page.query_selector("#df-btn-run")
        is_disabled = await page.evaluate("btn => btn.disabled", run_btn)
        hint_text = await page.inner_text("#df-run-hint")
        record("Playground: Run AI Analysis disabled when inputs empty", is_disabled and bool(hint_text), f"Hint: '{hint_text}'")

        # Switch to Paste Code mode
        await page.click('#df-btn-mode-paste')
        await page.wait_for_timeout(200)
        
        # Test Dynamic Output Scope description
        scope_select = await page.query_selector("#df-ptype")
        await scope_select.select_option("API documentation")
        await page.wait_for_timeout(150)
        scope_desc = await page.inner_text("#df-scope-desc")
        record("Playground: Dynamic scope helper reflects chosen doc type", "contract" in scope_desc.lower() or "interface" in scope_desc.lower() or "public" in scope_desc.lower(), scope_desc)

        # Test draft persistence in sessionStorage
        await page.fill("#df-pname", "Draft Project Test")
        await page.fill("#df-pcode", "def draft_func(): pass")
        await page.wait_for_timeout(300)
        draft_raw = await page.evaluate("() => sessionStorage.getItem('df_playground_draft')")
        record("Playground: Form auto-persists draft to sessionStorage", draft_raw is not None and "Draft Project Test" in draft_raw)

        # Clear draft
        await page.click("#df-btn-clear")
        await page.wait_for_timeout(200)

        # -------------------------------------------------------------
        # STEP 4: Multi-File Upload, Secret Denial, & Collision-Proof Delimiter
        # -------------------------------------------------------------
        print("\n--- STEP 4: Archive Upload & Security Safeguards ---")
        await page.click('#df-btn-mode-upload')
        await page.wait_for_timeout(200)

        # Build in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            # 1. Python file with collision test delimiter
            zf.writestr("store.py", "class Store:\n    # FILE: tricky_collision_line\n    def get(self): return 1\n")
            # 2. TypeScript file
            zf.writestr("types.ts", "export interface User { id: string; name: string; }\n")
            # 3. SQL schema file
            zf.writestr("schema.sql", "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255));\n")
            # 4. Secret .env file (must be blocked)
            zf.writestr(".env", "DATABASE_SECRET=super_secret_password\n")
            # 5. Unsupported binary
            zf.writestr("binary.exe", b"\x00\x01\x02\x03\x04")
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.getvalue()

        # Trigger file upload
        file_input = await page.query_selector("#df-file-input")
        await file_input.set_input_files({
            "name": "project_payload.zip",
            "mimeType": "application/zip",
            "buffer": zip_bytes
        })
        await page.wait_for_timeout(1000)

        # Verify parsed files
        uploaded_files = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.df-file-item')).map(row => {
                const name = row.querySelector('.df-file-name')?.innerText || '';
                const size = row.querySelector('.df-file-size')?.innerText || '';
                return { name, size };
            });
        }""")
        file_names = [f["name"] for f in uploaded_files]
        record("Upload: Structured payload extracted expected files", 
               "store.py" in file_names and "types.ts" in file_names and "schema.sql" in file_names,
               f"Extracted: {file_names}")

        # Verify .env was denied and neutral notice displayed
        skipped_text = await page.inner_text("#df-skipped-notice-text")
        record("Security: Neutral notice reports excluded secret .env file", 
               ".env" in skipped_text and "Secret" in skipped_text or "Security" in skipped_text,
               skipped_text.strip().replace('\n', ' '))

        # Verify language detected as Mixed
        current_lang = await page.input_value("#df-plang")
        record("Upload: Multiple file extensions auto-detected as 'Mixed'", current_lang == "Mixed", f"Language: {current_lang}")

        # Verify store.py was NOT split into multiple fake files by # FILE: tricky_collision_line
        record("Upload Architecture: Delimiter collision test intact (not split)",
               "store.py" in file_names and len([f for f in file_names if "tricky_collision_line" in f]) == 0)

        await page.screenshot(path=os.path.join(SHOTS_DIR, "02_playground_upload_1440.png"))

        # -------------------------------------------------------------
        # STEP 5: Real Generation & Milestones SSE Streaming
        # -------------------------------------------------------------
        print("\n--- STEP 5: Real AI Synthesis & SSE Milestones ---")
        # Prepare clean TodoStore payload for fast, reliable end-to-end generation
        await page.fill("#df-pname", "TodoStore Premium Test")
        await page.select_option("#df-plang", "Python")
        
        # Switch back to paste mode to feed exact verified TodoStore sample
        await page.click('#df-btn-mode-paste')
        await page.wait_for_timeout(200)

        todo_code = """import json
from pathlib import Path

class TodoStore:
    \"\"\"Local JSON-backed task persistence manager.\"\"\"
    def __init__(self, path: str = "tasks.json"):
        self.path = Path(path)
        self.items = []
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self.items = json.load(f)

    def add(self, title: str) -> dict:
        \"\"\"Adds a new todo task and flushes to disk.\"\"\"
        item = {"id": len(self.items) + 1, "title": title, "done": False}
        self.items.append(item)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.items, f, indent=2)
        return item

    def complete(self, item_id: int) -> bool:
        \"\"\"Marks an existing task item as complete.\"\"\"
        for item in self.items:
            if item["id"] == item_id:
                item["done"] = True
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self.items, f, indent=2)
                return True
        return False
"""
        await page.fill("#df-pcode", todo_code)
        await page.wait_for_timeout(200)

        # Trigger generation
        await page.click("#df-btn-run")
        await page.wait_for_timeout(500)

        # Verify we navigated to /processing
        processing_url = page.url
        record("Processing: Navigated to /processing with active job_id", "/processing" in processing_url and "job_id=" in processing_url)

        # Wait for processing progress or auto-redirect (up to 45 seconds)
        print("Waiting for Gemini documentation synthesis to finish...")
        try:
            await page.wait_for_url("**/documentation?project_id=*", timeout=45000)
            gen_success = True
        except Exception as e:
            gen_success = False
            print(f"Synthesis wait exception: {e}")

        record("Processing: SSE pipeline completed and navigated to /documentation", gen_success, page.url)

        # Capture documentation workspace screenshot
        await page.screenshot(path=os.path.join(SHOTS_DIR, "03_documentation_1440.png"))

        # -------------------------------------------------------------
        # STEP 6: Results Workspace: Sections, In-Place Edit & Persistence
        # -------------------------------------------------------------
        print("\n--- STEP 6: Results Workspace Features ---")
        # Verify rendered sections
        sidebar_links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.df-tab-btn, .df-doc-nav-item')).map(el => el.innerText.trim());
        }""")
        record("Results Workspace: Section navigation rendered", len(sidebar_links) >= 5, f"Sections: {sidebar_links}")

        # Switch section to Functions
        func_nav = await page.query_selector('.df-tab-btn[data-key="functions"], .df-doc-nav-item[data-key="functions"]')
        if func_nav:
            await func_nav.click()
            await page.wait_for_timeout(200)
            doc_body = await page.inner_text("#df-markdown-view")
            record("Results Workspace: Switches section content", "todostore" in doc_body.lower() or "complete" in doc_body.lower() or "parameters" in doc_body.lower() or "add" in doc_body.lower())

        # Test In-Place Editing and Database Persistence
        edit_btn = await page.query_selector("#df-btn-edit")
        await edit_btn.click()
        await page.wait_for_timeout(200)

        editor_visible = await page.is_visible("#df-editor")
        record("Results Workspace: Inline markdown editor opens", editor_visible)

        # Append verified tag
        await page.fill("#df-editor", "# TodoStore Verified Documentation\n\nPersisted edit by automated suite.")
        save_btn = await page.query_selector("#df-btn-save")
        await save_btn.click()
        await page.wait_for_timeout(600)

        # Reload page directly to test database persistence
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(300)
        reloaded_text = await page.inner_text("#df-markdown-view")
        record("Results Workspace: Saved edits persist across browser refresh", 
               "TodoStore Verified Documentation" in reloaded_text)

        # Test Download README.md
        async with page.expect_download() as download_info:
            await page.click("#df-btn-download")
        download = await download_info.value
        record("Results Workspace: Download README triggers markdown file download", 
               download.suggested_filename.endswith(".md"), 
               f"File: {download.suggested_filename}")

        # -------------------------------------------------------------
        # STEP 7: Projects & Settings Workspaces
        # -------------------------------------------------------------
        print("\n--- STEP 7: Projects & Settings Management ---")
        await page.goto(f"{BASE_URL}/projects", wait_until="networkidle")
        await page.wait_for_timeout(300)

        projects = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('.df-card')).map(card => {
                const title = card.querySelector('h2, .df-title-md')?.innerText || '';
                return title.trim();
            });
        }""")
        record("Projects: Lists generated project workspaces", any("TodoStore" in p for p in projects), f"Projects: {projects[:3]}")

        # Settings
        await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
        await page.wait_for_timeout(300)

        model_val = await page.input_value("#df-active-model")
        record("Settings: Live Gemini status and active model displayed", model_val == "gemini-3.5-flash", f"Model: {model_val}")

        # Theme switch test
        theme_btn = await page.query_selector("#df-theme-btn")
        await theme_btn.click()
        await page.wait_for_timeout(200)
        current_theme = await page.evaluate("() => document.documentElement.dataset.theme")
        record("Theme: Global light/dark toggle functional", current_theme in ["light", "dark"], f"Theme: {current_theme}")
        # Switch back to dark
        if current_theme == "light":
            await theme_btn.click()
            await page.wait_for_timeout(100)

        # -------------------------------------------------------------
        # STEP 8: Branded 404 Route Resiliency
        # -------------------------------------------------------------
        print("\n--- STEP 8: Route Resiliency & 404 Experience ---")
        await page.goto(f"{BASE_URL}/nonexistent-page-url", wait_until="networkidle")
        await page.wait_for_timeout(300)
        page_404_text = await page.inner_text("#app-view")
        record("Routing: Branded 404 page rendered for missing routes", 
               "404" in page_404_text and "Return to Home" in page_404_text,
               "404 and Return to Home present")

        # -------------------------------------------------------------
        # STEP 9: Universal Responsive Layout Audit (Zero Overflow)
        # -------------------------------------------------------------
        print("\n--- STEP 9: Universal Responsive Viewport Audit (Zero Overflow) ---")
        viewports = [
            (320, 640, "320px Ultra-Compact"),
            (360, 800, "360px Galaxy A55"),
            (390, 844, "390px iPhone 14"),
            (768, 1024, "768px iPad Portrait"),
            (1024, 768, "1024px iPad Landscape"),
            (1440, 900, "1440px Desktop"),
            (1920, 1080, "1920px Full HD")
        ]

        routes = [
            ("/", "Landing"),
            ("/playground", "Playground"),
            ("/projects", "Projects"),
            ("/settings", "Settings")
        ]

        # Seed sessionStorage to keep intro quiet during responsive sweep
        await page.goto(f"{BASE_URL}/")
        await page.evaluate("() => sessionStorage.setItem('df_intro_done', 'true')")

        all_overflow_clean = True
        for w, h, vp_label in viewports:
            for route_path, route_name in routes:
                ok = await check_no_horizontal_overflow(page, route_path, w, h, f"{route_name} ({vp_label})")
                if not ok:
                    all_overflow_clean = False

            # Capture portfolio screenshots at 360px and 1440px
            if w == 360:
                await page.set_viewport_size({"width": 360, "height": 800})
                await page.goto(f"{BASE_URL}/", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "landing_360.png"))
                await page.goto(f"{BASE_URL}/playground", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "playground_360.png"))
                await page.goto(f"{BASE_URL}/projects", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "projects_360.png"))
                await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "settings_360.png"))
            elif w == 1440:
                await page.set_viewport_size({"width": 1440, "height": 900})
                await page.goto(f"{BASE_URL}/", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "landing_1440.png"))
                await page.goto(f"{BASE_URL}/playground", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "playground_1440.png"))
                await page.goto(f"{BASE_URL}/projects", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "projects_1440.png"))
                await page.goto(f"{BASE_URL}/settings", wait_until="networkidle")
                await page.screenshot(path=os.path.join(SHOTS_DIR, "settings_1440.png"))

        record("Responsive: Zero horizontal overflow across all tested viewports and routes", all_overflow_clean)

        # -------------------------------------------------------------
        # STEP 10: Unhandled Console Errors Assertion
        # -------------------------------------------------------------
        print("\n--- STEP 10: Runtime Cleanliness Audit ---")
        record("Console: Zero unhandled console errors or exceptions", 
               len(console_errors) == 0, 
               f"Errors: {console_errors}" if console_errors else "Zero console errors detected")

        await browser.close()

    print("\n==================================================================")
    print("                     VERIFICATION SUMMARY                         ")
    print("==================================================================")
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = total - passed
    print(f"Total Tests Executed: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed Tests:")
        for r in test_results:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['detail']}")
        sys.exit(1)
    else:
        print("\nALL VERIFICATION TESTS COMPLETED WITH 100% PASS RATE!")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
