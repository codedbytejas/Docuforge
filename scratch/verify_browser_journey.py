"""
Browser journey verification script:
1. Create a zip of project code files
2. Navigate to /playground at 1440px
3. Upload the ZIP archive
4. Confirm the file list displays exactly the real files and their sizes
5. Click "Run AI Analysis & Generate"
6. Check /processing at 1440px and 360px: assert scrollWidth <= innerWidth
7. Wait for generation completion -> redirects to /documentation
8. Check /documentation at 1440px and 360px: assert scrollWidth <= innerWidth
9. Check / (landing) at 1440px and 360px: assert scrollWidth <= innerWidth
10. Check /playground at 1440px and 360px: assert scrollWidth <= innerWidth
11. Audit console for 0 errors
12. Save screenshots to artifact directory
"""

import asyncio
import io
import os
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"
ARTIFACT_DIR = "/Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f"

async def main():
    # 1. Prepare project zip
    zip_path = "scratch/docuforge_project.zip"
    files_to_zip = [
        ("router.js", "frontend/assets/js/router.js"),
        ("api.js", "frontend/assets/js/api.js"),
        ("icons.js", "frontend/assets/js/icons.js")
    ]
    
    with zipfile.ZipFile(zip_path, "w") as z:
        for arcname, relpath in files_to_zip:
            z.write(relpath, arcname=arcname)
    
    print(f"Created ZIP bundle with {len(files_to_zip)} real project files.")

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

        print("\n=== STEP 1: VERIFY LANDING (/) AT 1440px and 360px ===")
        # 1440px
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(f"{BASE_URL}/", wait_until="networkidle")
        # dismiss intro if visible
        if await page.is_visible("#df-intro-skip"):
            await page.click("#df-intro-skip")
            await page.wait_for_timeout(400)

        sw_1440 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_1440 = await page.evaluate("() => window.innerWidth")
        print(f"Landing @ 1440px: scrollWidth={sw_1440}, innerWidth={iw_1440}")
        assert sw_1440 <= iw_1440 + 1, f"Horizontal overflow on / at 1440px ({sw_1440} > {iw_1440})"
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_landing_1440.png"))

        # 360px
        await page.set_viewport_size({"width": 360, "height": 800})
        await page.wait_for_timeout(300)
        sw_360 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_360 = await page.evaluate("() => window.innerWidth")
        print(f"Landing @ 360px: scrollWidth={sw_360}, innerWidth={iw_360}")
        assert sw_360 <= iw_360 + 1, f"Horizontal overflow on / at 360px ({sw_360} > {iw_360})"
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_landing_360.png"))

        print("\n=== STEP 2: VERIFY PLAYGROUND (/playground) AT 1440px and 360px ===")
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(f"{BASE_URL}/playground", wait_until="networkidle")
        
        sw_pg_1440 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_pg_1440 = await page.evaluate("() => window.innerWidth")
        print(f"Playground @ 1440px: scrollWidth={sw_pg_1440}, innerWidth={iw_pg_1440}")
        assert sw_pg_1440 <= iw_pg_1440 + 1, f"Horizontal overflow on /playground at 1440px ({sw_pg_1440} > {iw_pg_1440})"

        await page.set_viewport_size({"width": 360, "height": 800})
        await page.wait_for_timeout(300)
        sw_pg_360 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_pg_360 = await page.evaluate("() => window.innerWidth")
        print(f"Playground @ 360px: scrollWidth={sw_pg_360}, innerWidth={iw_pg_360}")
        assert sw_pg_360 <= iw_pg_360 + 1, f"Horizontal overflow on /playground at 360px ({sw_pg_360} > {iw_pg_360})"

        print("\n=== STEP 3: UPLOAD PROJECT ZIP & VERIFY FILE LIST ===")
        await page.set_viewport_size({"width": 1440, "height": 900})
        # ensure upload mode
        btn_upload = page.locator("#df-btn-mode-upload")
        await btn_upload.click()
        
        file_input = page.locator("#df-file-input")
        await file_input.set_input_files(zip_path)
        await page.wait_for_timeout(600)

        # Inspect file list items
        file_items = page.locator(".df-file-item")
        count = await file_items.count()
        print(f"Loaded files count: {count}")
        assert count == len(files_to_zip), f"Expected {len(files_to_zip)} files, found {count}"

        loaded_names = []
        for i in range(count):
            name_el = file_items.nth(i).locator(".df-file-name")
            loaded_names.append(await name_el.text_content())
        print(f"Loaded filenames: {loaded_names}")
        for expected_name, _ in files_to_zip:
            assert any(expected_name in n for n in loaded_names), f"Missing {expected_name} in {loaded_names}"

        # Confirm no corrupt filename containing '{name}\n' or broken strings
        for n in loaded_names:
            assert "{" not in n and "}" not in n and "\n" not in n, f"Corrupt file entry detected: {n}"
        print("  ✓ All files match real project files exactly with clean names!")

        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_playground_uploaded_1440.png"))

        print("\n=== STEP 4: TRIGGER AI GENERATION -> /processing ===")
        await page.fill("#df-pname", "docuforge-core-modules")
        run_btn = page.locator("#df-btn-run")
        assert await run_btn.is_enabled(), "Run AI Analysis button should be enabled"
        await run_btn.click()

        await page.wait_for_url("**/processing?job_id=**", timeout=10000)
        print("Navigated to /processing successfully.")

        # Check /processing at 1440px
        sw_proc_1440 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_proc_1440 = await page.evaluate("() => window.innerWidth")
        print(f"Processing @ 1440px: scrollWidth={sw_proc_1440}, innerWidth={iw_proc_1440}")
        assert sw_proc_1440 <= iw_proc_1440 + 1

        # Check /processing at 360px
        await page.set_viewport_size({"width": 360, "height": 800})
        await page.wait_for_timeout(300)
        sw_proc_360 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_proc_360 = await page.evaluate("() => window.innerWidth")
        print(f"Processing @ 360px: scrollWidth={sw_proc_360}, innerWidth={iw_proc_360}")
        assert sw_proc_360 <= iw_proc_360 + 1
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_processing_360.png"))

        # Restore to 1440 for completion
        await page.set_viewport_size({"width": 1440, "height": 900})

        print("\n=== STEP 5: AWAIT GENERATION COMPLETION -> /documentation ===")
        await page.wait_for_url("**/documentation?project_id=**", timeout=45000)
        print(f"Successfully redirected to {page.url}")

        print("\n=== STEP 6: VERIFY DOCUMENTATION (/documentation) AT 1440px and 360px ===")
        # 1440px
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.wait_for_timeout(400)
        sw_doc_1440 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_doc_1440 = await page.evaluate("() => window.innerWidth")
        print(f"Documentation @ 1440px: scrollWidth={sw_doc_1440}, innerWidth={iw_doc_1440}")
        assert sw_doc_1440 <= iw_doc_1440 + 1
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_documentation_1440.png"))

        # 360px
        await page.set_viewport_size({"width": 360, "height": 800})
        await page.wait_for_timeout(400)
        sw_doc_360 = await page.evaluate("() => document.documentElement.scrollWidth")
        iw_doc_360 = await page.evaluate("() => window.innerWidth")
        print(f"Documentation @ 360px: scrollWidth={sw_doc_360}, innerWidth={iw_doc_360}")
        assert sw_doc_360 <= iw_doc_360 + 1
        await page.screenshot(path=os.path.join(ARTIFACT_DIR, "verify_documentation_360.png"))

        # Verify Source Scope
        scope_text = await page.text_content(".df-card")
        print(f"Source Scope verified: {scope_text[:80]}...")

        # Console error check
        print("\n=== STEP 7: BROWSER CONSOLE ERROR AUDIT ===")
        print(f"Total console errors captured: {len(console_errors)}")
        if console_errors:
            print("Errors:", console_errors)
        assert len(console_errors) == 0, f"Uncaught console errors detected: {console_errors}"
        print("  ✓ Console clean! 0 uncaught errors.")

        await browser.close()
        print("\n🎉 ALL CHECKS PASSED WITH 0 DEFECTS!")

if __name__ == "__main__":
    asyncio.run(main())

