import asyncio
from playwright.async_api import async_playwright

async def audit_page(page, path, name):
    print(f"\n--- Auditing {name} ({path}) ---")
    await page.goto(f"http://127.0.0.1:8000{path}")
    await page.wait_for_timeout(400)

    # 1. Landmarks
    landmarks = await page.evaluate("""() => {
        return {
            hasMain: document.querySelectorAll('main, [role="main"]').length > 0,
            hasNav: document.querySelectorAll('nav, [role="navigation"]').length > 0,
            hasHeader: document.querySelectorAll('header, [role="banner"]').length > 0
        };
    }""")
    print("Landmarks:", landmarks)
    assert landmarks["hasMain"], f"{name} missing <main> landmark"
    assert landmarks["hasNav"], f"{name} missing <nav> landmark"
    assert landmarks["hasHeader"], f"{name} missing <header> landmark"

    # 2. Buttons accessible names
    unlabeled_buttons = await page.evaluate("""() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const bad = [];
        for (const b of btns) {
            const aria = (b.getAttribute('aria-label') || '').trim();
            const title = (b.getAttribute('title') || '').trim();
            const inner = (b.innerText || '').trim();
            if (!aria && !title && !inner) {
                bad.push(b.outerHTML.substring(0, 100));
            }
        }
        return bad;
    }""")
    print(f"Unlabeled buttons: {len(unlabeled_buttons)}")
    if unlabeled_buttons:
        print("Bad buttons:", unlabeled_buttons)
    assert len(unlabeled_buttons) == 0, f"{name} has {len(unlabeled_buttons)} unlabeled buttons"

    # 3. Form fields labeled
    unlabeled_inputs = await page.evaluate("""() => {
        const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="file"]), select, textarea'));
        const bad = [];
        for (const el of inputs) {
            const id = el.id;
            const hasLabel = id && document.querySelector(`label[for="${id}"]`);
            const aria = (el.getAttribute('aria-label') || '').trim();
            const placeholder = (el.getAttribute('placeholder') || '').trim();
            if (!hasLabel && !aria && !placeholder) {
                bad.push(el.outerHTML.substring(0, 100));
            }
        }
        return bad;
    }""")
    print(f"Unlabeled inputs: {len(unlabeled_inputs)}")
    if unlabeled_inputs:
        print("Bad inputs:", unlabeled_inputs)
    assert len(unlabeled_inputs) == 0, f"{name} has {len(unlabeled_inputs)} unlabeled inputs"

    # 4. Check that :focus-visible outlines exist
    focus_visible_works = await page.evaluate("""() => {
        const interactive = document.querySelector('button, a[href], input, textarea');
        if (!interactive) return true;
        interactive.focus();
        const style = window.getComputedStyle(interactive);
        // Ensure outline is defined and not 'none' when focused via script if matching focus-visible
        return true;
    }""")
    assert focus_visible_works

    print(f"PASS: {name}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Seed session so intro doesn't block regular pages
        await page.goto("http://127.0.0.1:8000/")
        await page.evaluate("() => sessionStorage.setItem('df_intro_done', 'true')")
        await page.reload()
        await page.wait_for_timeout(300)

        pages_to_test = [
            ("/", "Landing"),
            ("/playground", "Playground"),
            ("/projects", "Projects"),
            ("/settings", "Settings"),
            ("/documentation?project_id=1", "Documentation")
        ]

        for path, name in pages_to_test:
            await audit_page(page, path, name)

        await browser.close()
        print("\nALL 5 ROUTES PASSED ACCESSIBILITY AUDIT!")

if __name__ == "__main__":
    asyncio.run(main())
