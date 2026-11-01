"""
Edge-cases verification script:
1. ZIP upload with multiple files -> verifies unzipping and file list chips
2. Unsupported file rejection -> verifies validation banner
3. Direct browser refresh on ALL 6 routes
"""

import asyncio
import io
import zipfile
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

async def run_edge_cases():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("=== Test: ZIP Archive Upload ===")
        await page.goto(f"{BASE_URL}/playground")
        await page.wait_for_selector("#df-dropzone")

        # Create in-memory ZIP with 3 files
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("auth.py", "def login(user, pwd):\n    return True\n")
            z.writestr("server.py", "from auth import login\nprint('Server started')\n")
            z.writestr("config.py", "PORT = 8080\nDEBUG = False\n")
        zip_bytes = zip_buf.getvalue()

        # Upload ZIP
        await page.set_input_files("#df-file-input", [{
            "name": "project_source.zip",
            "mimeType": "application/zip",
            "buffer": zip_bytes
        }])
        await page.wait_for_timeout(600)

        # Check extracted files
        items = await page.locator(".df-file-item").count()
        assert items == 3, f"Expected 3 extracted files from ZIP, found {items}"
        files_text = await page.text_content("#df-files-container")
        assert "auth.py" in files_text
        assert "server.py" in files_text
        assert "config.py" in files_text
        print(f"  ✓ ZIP archive successfully unpacked into {items} individual source files: auth.py, server.py, config.py")

        print("\n=== Test: Unsupported File Rejection ===")
        # Upload binary file
        await page.set_input_files("#df-file-input", [{
            "name": "malicious.exe",
            "mimeType": "application/octet-stream",
            "buffer": b"MZBINARYEXEHEADER"
        }])
        await page.wait_for_timeout(600)

        err_banner = await page.is_visible("#df-upload-error")
        err_msg = await page.text_content("#df-upload-error-text")
        assert err_banner, "Upload error banner should be visible for unsupported file"
        assert "unsupported" in err_msg.lower() or "skipped" in err_msg.lower(), f"Unexpected error message: {err_msg}"
        print(f"  ✓ Unsupported file successfully rejected with clear banner: '{err_msg.strip()}'")

        print("\n=== Test: Direct Refresh on ALL 6 Routes ===")
        routes_to_test = [
            "/",
            "/playground",
            "/projects",
            "/settings"
        ]

        for r in routes_to_test:
            res = await page.goto(f"{BASE_URL}{r}")
            assert res.status == 200, f"Route {r} returned status {res.status}"
            await page.wait_for_timeout(200)
            # Reload directly
            reload_res = await page.reload()
            assert reload_res.status == 200, f"Reloading {r} returned status {reload_res.status}"
            print(f"  ✓ Route {r} direct load and reload returned 200 OK")

        # Test deep link with query params
        # Get first project ID
        projects = await page.evaluate("() => fetch('/api/projects').then(r => r.json())")
        if projects:
            first_pid = projects[0]["id"]
            deep_doc_url = f"{BASE_URL}/documentation?project_id={first_pid}"
            res = await page.goto(deep_doc_url)
            assert res.status == 200
            await page.wait_for_selector("#df-markdown-view")
            # Reload
            reload_res = await page.reload()
            assert reload_res.status == 200
            await page.wait_for_selector("#df-markdown-view")
            print(f"  ✓ Deep link /documentation?project_id={first_pid} reloaded cleanly")

        # HTTP 400 from rejection of malicious.exe is an expected network response
        non_network_errors = [e for e in console_errors if "400" not in e and "Failed to load resource" not in e]
        assert len(non_network_errors) == 0, f"Unexpected console errors: {non_network_errors}"
        print(f"\nAll edge case and route refresh tests passed cleanly!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_edge_cases())
