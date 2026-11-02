# DocuForge AI — Complete Prompt History

This document records all user prompts provided during the development, redesign, polish, debugging, and rate-limiting phases of DocuForge AI.

---

## Prompt 1

**Timestamp:** `2026-10-31T06:31:10Z`

```text
run the code
```

---

## Prompt 2

**Timestamp:** `2026-10-31T06:38:06Z`

```text
added the key run again
```

---

## Prompt 3

**Timestamp:** `2026-10-31T06:40:39Z`
**Attachments:** `image/png` (media_1793428771363_a8ccd150.png)

```text
[User uploaded image / media attachment]
```

---

## Prompt 4

**Timestamp:** `2026-10-31T07:58:52Z`
**Attachments:** `image/png` (media_1793433448635_cedd8e8a.png), `image/png` (media_1793433457797_003feb38.jpg), `image/png` (media_1793433465351_88e2da77.jpg)

```text
Read docs/REDESIGN_SPEC.md and the attached screenshot. Inspect the existing repository: stack, folder structure, API routes, DB schema, how the frontend is served, and which parts are reusable.
Do NOT edit any files yet. Produce an implementation plan covering: route map with server fallback, design tokens, backend changes needed for real processing progress (job + SSE or polling), and a phased task list for: (2) design system + routing + progress backend, (3) intro + landing, (4) playground + processing + results + projects/settings, (5) verification. Flag any spec conflicts or risks.
```

---

## Prompt 5

**Timestamp:** `2026-10-31T08:00:55Z`

```text
Approved artifact plan: file:///Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f/redesign_implementation_plan.md
```

---

## Prompt 6

**Timestamp:** `2026-10-31T08:03:07Z`

```text
Approved plan. Implement Phase 2 only: design tokens and typography, shared UI components, history-based routing with server fallback for all routes, and the backend generation job with truthful stage/status reporting (keep existing endpoints working). Verify existing projects and generation still work, then summarize.
```

---

## Prompt 7

**Timestamp:** `2026-10-31T08:09:50Z`

```text
Implement Phase 3 per the spec: first-visit-per-session intro tied to a real backend health check, with Skip and an error/retry state, then the full landing page (all 8 sections). Use real product UI components in the hero visual and label any example content as an example. Verify at 1440, 1024, 768 and 390 px.
```

---

## Prompt 8

**Timestamp:** `2026-10-31T08:18:17Z`

```text
Implement Phase 4 per the spec: /playground (upload + paste, validation, no AI call until "Run AI Analysis →"), /processing with real stage status and retry, /documentation results workspace (sidebar nav, edit/preview, copy, regenerate section, download README.md, export PDF), and restyled /projects and /settings with all current functionality kept.
```

---

## Prompt 9

**Timestamp:** `2026-10-31T08:36:31Z`

```text
Use the browser subagent to run the full journey: intro, landing scroll, Start Documenting, paste code, select language, fill details, Run AI Analysis, processing, results, edit, download. Also test ZIP upload, invalid file, empty input, missing API key, a forced API failure, refresh on every route, and that existing projects still load. Check the console for errors and capture screenshots at 1440, 1024, 768 and 390 px. Fix every defect, rerun the failed tests, and report exactly what passed and failed.
```

---

## Prompt 10

**Timestamp:** `2026-10-31T08:47:26Z`

```text
run the code
```

---

## Prompt 11

**Timestamp:** `2026-10-31T09:05:35Z`

```text
TASK: Fix pass on the DocuForge AI redesign. Do not change the Gemini integration, the database, or saved projects. Work through the sections in order, keep a checklist, and verify at the end.

RULES
- No fake claims: every statement in marketing copy must be verifiable against the product or the sample code.
- Keep the palette (charcoal, warm off-white, one amber accent). No emoji icons, no purple gradients.
- Respect prefers-reduced-motion. Keep AA contrast.

1. MOBILE / RESPONSIVE (critical, new)
Bug: at 360x800 (Galaxy A55 emulation) the page overflows horizontally. The hero headline, paragraph, CTA buttons, "ILLUSTRATIVE EXAMPLE" label, hero demo card, and the "Get Started" nav button are clipped at the right edge.
- Find every element wider than the viewport (document.documentElement.scrollWidth > window.innerWidth, then inspect offenders). Likely causes: fixed or min widths, white-space: nowrap, 100vw, grid/flex children missing min-width: 0, code blocks, the hero demo card.
- Fix at the root: add min-width: 0 to flex/grid children, overflow-wrap: anywhere on text, max-width: 100% on media, internal overflow-x: auto on code blocks and tables only. Do not hide the problem with overflow-x: hidden on body.
- Add a mobile navigation: hamburger menu with all links and the Get Started CTA; the header must fit at 320 px.
- Use fluid type (clamp) so the hero headline fits at 320-390 px; stack the hero demo (source above documentation) on small screens; make CTA buttons full-width and fully visible.
- Check every page (/, /playground, /processing, /documentation, /projects, /settings) at 320, 360, 390, 768, 1024 and 1440 px. No horizontal scrolling anywhere. On /documentation the section sidebar becomes a horizontal tab bar or a drawer.

2. UPLOAD BUG (critical)
The playground file list shows a fake file named "{name}\n{raw.decode('utf-8')}")" and main.py split in two, because the backend joins files with "# FILE: <name>" lines and the frontend re-splits on that text, so a source file containing that text breaks it.
- Make /api/upload return {files:[{name,size,content}], skipped:[{name,reason}]}. The frontend keeps per-file state and must never parse headers out of concatenated text.
- Join files only when sending to generation, using a delimiter that cannot appear in user code, or send a list. Add a test with a file containing the text "# FILE: x".
- Keep backward compatibility for existing saved projects.

3. FILE HANDLING
- Skipped files show as a neutral notice, not a red error, with a short reason each.
- Add support for .html .css .sql .yml .yaml .sh. Explicitly deny .env* and other secret files (never send them to Gemini) and say so in the notice.
- Detect the language from uploaded files; show "Mixed" for several. Show file count in "Source scope" on the results page with a collapsible file list.

4. COPY ACCURACY (landing page)
- Rewrite the hero and "Documentation output preview" example so every claim matches the sample TodoStore code. Remove: "thread-safe", "Python 3.10+", "100% deterministic", "Zero hallucinations", "verified Python codebase", "Active Engine".
- The hero card shows a hardcoded model name ("gemini-3.5-flash"). Remove it or read the real model from /api/status.
- Say "10 languages" (Python, JavaScript, TypeScript, Java, C, C++, Go, PHP, Ruby, Rust) and present "Other" as a plain-text fallback, not a language.
- Keep every example clearly labelled illustrative.

5. LANDING PAGE VISUAL RHYTHM
- Replace repeated card grids: The Problem becomes an editorial list or two-column layout; How It Works becomes a vertical stepper; Languages becomes a simple list of names and extensions without "Supported" pills.
- Headline typography: letter-spacing about -0.02em, check word-spacing so words do not collide.
- Hero demo: raise the contrast of the README side, make the source-to-documentation animation visibly play (respect prefers-reduced-motion).

6. NAVIGATION
- Use :focus-visible for outlines; remove the heavy blue ring on mouse click.
- Add a clear active-section indicator while scrolling; add the "About" item.
- Remove the redundant "Document Code" header button on /playground and /processing.

7. PLAYGROUND
- Segmented control for "Upload files" vs "Paste code" instead of one stacked form.
- Syntax-highlighted editor with line numbers and a language selector.
- Output Scope panel reflects the selected documentation type instead of seven identical "Will Generate" rows.
- File list shows names, sizes, and a remove button; "Run AI Analysis" is the clear primary action, disabled with a reason until input is valid.

8. PROCESSING
- Keep the real measured stages. Add a Cancel button, file count and size analyzed, total elapsed time, and a clear retry/edit-input state on failure.
- Verify that refreshing /processing?job_id=... resumes the job.

9. INTRO
- Show a large DOCUFORGE AI wordmark with the animated mark; enlarge the tagline "Your Code. Clearly Documented."; raise the contrast of the supporting text.
- Keep Skip, the session-only behavior, and the real initialization check.

10. RESULTS PAGE
- "Source scope" shows file count and the file list instead of "Python codebase · 10.6 KB".
- Keep section sidebar, outline, edit, copy, regenerate, download README.md, export PDF; make all of them usable at 360 px.

VERIFY (browser subagent, required)
- Full journey: intro, landing scroll, Start Documenting, upload the docuforge folder as a ZIP, confirm the file list shows only the real files with correct sizes, run generation, results, edit, download.
- Also test: paste code, empty input, invalid file, missing API key, forced API failure, refresh on every route.
- Capture screenshots at 360, 390, 768, 1024 and 1440 px in light and dark mode. Confirm scrollWidth equals innerWidth on every page. Console must be clean.
- Report exactly what passed and what failed. Do not claim success for anything not run.
```

---

## Prompt 12

**Timestamp:** `2026-10-31T09:46:35Z`

```text
run the code
```

---

## Prompt 13

**Timestamp:** `2026-11-01T19:29:37Z`

```text
TASK: Critical fixes on DocuForge AI. Do not change the Gemini integration, the database, or saved projects. Make a git commit before starting.

1. MOBILE OVERFLOW: at 360x800 the page overflows horizontally (hero headline, paragraph, buttons, demo card and the "Get Started" nav button are clipped on the right). Find every element wider than the viewport, fix the root cause (min-width: 0 on flex/grid children, overflow-wrap: anywhere, max-width: 100%, internal overflow-x: auto on code blocks only). Do not hide it with overflow-x: hidden on body. Add a hamburger mobile menu. Use clamp() for the hero headline. Stack the hero demo on small screens.
2. UPLOAD BUG: the file list shows a fake file named "{name}\n{raw.decode('utf-8')}")" because the frontend re-splits concatenated text on "# FILE:" headers. Make /api/upload return {files:[{name,size,content}], skipped:[{name,reason}]} and never parse headers from text. Join files only when generating, using a delimiter that cannot appear in user code. Add a test with a file containing "# FILE: x".
3. FILES: show skipped files as a neutral notice (not red). Support .html .css .sql .yml .yaml .sh. Never send .env* or other secret files to Gemini, and say so in the notice.
4. COPY: remove unverifiable claims ("thread-safe", "Python 3.10+", "100% deterministic", "Zero hallucinations", "verified codebase", "Active Engine") and the hardcoded model name in the hero card.

VERIFY with the browser subagent: upload the project as a ZIP, confirm the file list is exactly the real files, generate docs, check /, /playground, /processing and /documentation at 360 and 1440 px with no horizontal scroll and a clean console. Report what passed and failed.
```

---

## Prompt 14

**Timestamp:** `2026-11-01T19:32:57Z`

```text
TASK: Fix pass on the DocuForge AI redesign. Do not change the Gemini integration, the database, or saved projects. Commit after each numbered section.

RULES: no unverifiable claims; keep the palette (charcoal, warm off-white, one amber accent); no emoji icons; respect prefers-reduced-motion; AA contrast.

1. RESPONSIVE: fix horizontal overflow at 320-390 px on every route at the root cause; add a hamburger menu; fluid type with clamp(); hero demo stacks on mobile; CTAs full width; /documentation sidebar becomes a tab bar or drawer.
2. UPLOAD BUG: /api/upload returns structured files and skipped lists; frontend never parses "# FILE:" from text; collision-proof delimiter when generating; add a regression test; keep saved projects working.
3. FILE HANDLING: neutral skipped-files notice; support .html .css .sql .yml .yaml .sh; deny .env* and secrets; detect language (show "Mixed" for several); results page shows file count and a collapsible file list.
4. COPY ACCURACY: rewrite the hero and output-preview examples to match the sample TodoStore code exactly; remove the overclaims and the hardcoded model name; say "10 languages" and show "Other" as a plain-text fallback; keep examples labelled illustrative.
5. LANDING RHYTHM: The Problem becomes an editorial list; How It Works becomes a vertical stepper; Languages becomes a simple list without "Supported" pills; headline letter-spacing about -0.02em; raise hero README contrast and make the animation visibly play.
6. NAVIGATION: :focus-visible only, active-section indicator, add About, remove the redundant "Document Code" button on /playground and /processing.
7. PLAYGROUND: segmented "Upload files" / "Paste code"; syntax-highlighted editor with line numbers; Output Scope reflects the selected documentation type; file list with sizes and remove buttons; Run AI Analysis disabled with a reason until input is valid.
8. PROCESSING: keep the real stages; add Cancel, file count and size, total elapsed time, and a clear failure state with Retry and Edit input; verify refresh on /processing?job_id=... resumes.
9. INTRO: large DOCUFORGE AI wordmark, bigger tagline, higher-contrast supporting text, keep Skip and the session-only behavior.

VERIFY with the browser subagent: full journey with a ZIP upload, paste flow, empty input, invalid file, missing API key, forced API failure, refresh on every route. Screenshots at 360, 390, 768, 1024, 1440 px in light and dark. scrollWidth equals innerWidth on every page. Clean console. Report exactly what passed and failed.
```

---

## Prompt 15

**Timestamp:** `2026-11-01T19:33:24Z`

```text
TASK: Take DocuForge AI from "works" to "demo-ready premium". Preserve the Gemini integration, database, and saved projects. Work in Planning mode: first produce a plan artifact with a checklist, then implement. Create a git branch "polish" and commit after each numbered section so any step can be reverted.

NON-NEGOTIABLES
- Nothing fake: no hardcoded stats, no pre-written "generated" docs, no fake progress, no unverifiable marketing claims. Examples are labelled illustrative.
- API keys stay server-side. Never send .env* or secret files to Gemini.
- Palette: charcoal, warm off-white, one amber accent; dark mode must be as polished as light. No emoji icons, no purple gradients, no repeated generic card grids.
- Respect prefers-reduced-motion; AA contrast; keyboard navigable; visible :focus-visible states; semantic HTML and landmarks.

A. FOUNDATION (critical)
1. RESPONSIVE: fix overflow at 320-390 px on every route at the root cause (min-width: 0, overflow-wrap, max-width: 100%, internal scroll for code/tables; never overflow-x: hidden on body). Mobile hamburger menu, clamp() typography, stacked hero demo, full-width CTAs, tab bar or drawer for the documentation sidebar. Check 320, 360, 390, 768, 1024, 1440, and 1920.
2. UPLOAD ARCHITECTURE: /api/upload returns {files:[{name,size,content}], skipped:[{name,reason}]}; the frontend keeps per-file state and never parses "# FILE:" from text; collision-proof delimiter or list payload when generating; regression test with a file containing "# FILE: x"; saved projects keep working.
3. FILE HANDLING: neutral skipped notice with reasons; support .html .css .sql .yml .yaml .sh; deny .env* and secrets with a visible explanation; language detection ("Mixed" when several); file count and collapsible file list on the results page.

B. CONTENT AND LANDING
4. COPY ACCURACY: every claim verifiable against the sample TodoStore code or the real product; remove "thread-safe", "Python 3.10+", "100% deterministic", "Zero hallucinations", "verified codebase", "Active Engine", and the hardcoded model name (read the real model from /api/status if shown). Say "10 languages"; "Other" is a plain-text fallback.
5. LANDING DESIGN: editorial problem section, vertical-stepper How It Works, simple language list (names and extensions, no pills), tighter headline tracking (about -0.02em), high-contrast hero README, a visibly animated source-to-documentation sequence built from real UI components, smooth section reveals (subtle, reduced-motion safe), a footer with product/support links.
6. NAVIGATION: active-section indicator while scrolling, About item, :focus-visible only, remove the redundant "Document Code" button on /playground and /processing, a branded 404 page, and per-route page titles, meta descriptions and favicon.

C. PRODUCT EXPERIENCE
7. PLAYGROUND: segmented "Upload files" / "Paste code"; syntax-highlighted editor with line numbers; Output Scope reflects the selected documentation type; file list with sizes and remove buttons; drag-over, error and empty states; Run AI Analysis disabled with a reason until input is valid; remember form values if the user navigates away and back.
8. PROCESSING: keep real measured stages; Cancel, file count and size, total elapsed time; error states for missing key, rate limit, malformed output and network failure, each with Retry and Edit input; refresh on /processing?job_id=... resumes the job.
9. INTRO: large DOCUFORGE AI wordmark with the animated mark, bigger tagline, readable supporting text, real initialization check, Skip, session-only, graceful backend-down state.
10. RESULTS WORKSPACE: file count and file list in "Source scope"; sticky section sidebar and outline with scroll-spy; unsaved-changes warning when editing; copy confirmation; per-section regenerate with a loading state; clean print stylesheet for Export PDF; fully usable at 360 px.
11. PROJECTS AND SETTINGS: restyle to match; search, rename, delete with confirmation, reopen, regenerate, download; Settings shows the real Gemini configuration status; first-time empty states with a clear next action.

D. QUALITY
12. PERFORMANCE AND ACCESSIBILITY: run Lighthouse on /, /playground and /documentation; target 90+ for Accessibility and Best Practices and fix the issues; lazy-load below-the-fold assets; no layout shift.
13. AUTOMATED TESTS: add Playwright tests for the whole journey (ZIP upload, paste, generate with a mocked Gemini response in test mode only, edit, download), the empty-input, invalid-file, API-failure and refresh-on-every-route cases, and the "# FILE:" regression. Document how to run them in the README.
14. DOCS: update the README (setup, env vars, run, test) and add a short DEMO.md with a 3-minute demo script and known limits (200 KB per file, 5 MB ZIP, 40 files).

VERIFY (browser subagent, required)
Run the full journey and capture screenshots and a recording: intro, landing scroll, Start Documenting, ZIP upload of this project, generation, results, edit, download. Capture 360, 390, 768, 1024, 1440 px in light and dark. Confirm scrollWidth equals innerWidth on every page, the console is clean, and the tests pass. Finish with a report listing exactly what passed, what failed, and anything not tested. Never claim success for anything not run.
```

---

## Prompt 16

**Timestamp:** `2026-11-01T19:44:19Z`

```text
Approved artifact plan: file:///Users/tejaschavan1907/.gemini/antigravity/brain/cdb0f7dc-968f-4cc8-859c-e15283e2ee5f/demo_ready_premium_plan.md
```

---

## Prompt 17

**Timestamp:** `2026-11-01T20:12:38Z`

```text
https://github.com/codedbytejas/Docuforge.git
push code to this repo
```

---

## Prompt 18

**Timestamp:** `2026-11-01T20:17:08Z`
**Attachments:** `image/png` (media_1793564226646_a8383886.png)

```text
[User uploaded image / media attachment]
```

---

## Prompt 19

**Timestamp:** `2026-11-01T20:28:43Z`

```text
run the code
```

---

## Prompt 20

**Timestamp:** `2026-11-02T03:39:31Z`

```text
TASK: Add usage rate limiting and quota protection to DocuForge AI. Do not change the Gemini integration's behavior for normal users, the database contents, or saved projects. Create a git branch "rate-limit" and commit after each numbered section.

GOALS
Prevent any single user from exhausting the Gemini API quota, and prevent the whole app from exceeding it. Fail with clear, friendly messages, never silent failures or crashes.

CONFIG (all via environment variables with documented defaults in .env.example; no hardcoded limits)
- RL_GENERATIONS_PER_HOUR (default 5), RL_GENERATIONS_PER_DAY (default 15)
- RL_REGENERATIONS_PER_HOUR (default 15) (section regeneration is cheaper but still counts)
- RL_MAX_CONCURRENT_JOBS_PER_USER (default 1)
- RL_GLOBAL_REQUESTS_PER_MINUTE (set below my Gemini tier's limit) and RL_GLOBAL_DAILY_REQUESTS
- RL_MAX_INPUT_CHARS (reuse the existing code-size limit), RL_UPLOADS_PER_MINUTE
- TRUSTED_PROXY (true/false): only when true read the client IP from X-Forwarded-For; otherwise use the socket address. Never trust the header by default.
- RL_ENABLED (default true) so tests and local development can disable it.

1. IDENTITY
Identify a user by a signed, HttpOnly anonymous client-id cookie combined with the client IP. Count against BOTH the cookie id and the IP (the stricter one wins), so clearing cookies does not reset the limit. If authentication exists or is added later, use the user id instead.

2. LIMITER
Implement a sliding-window or token-bucket limiter as FastAPI dependency/middleware applied to: generate, regenerate, upload, and job-creation endpoints. Store counters in SQLite (new additive table, no changes to existing tables) with automatic cleanup of expired rows, so limits survive restarts. Make the storage layer swappable (interface) so Redis can replace it later. Operations must be atomic to avoid races under concurrent requests.

3. CONCURRENCY AND GLOBAL BUDGET
Reject a new generation when the user already has an active job (RL_MAX_CONCURRENT_JOBS_PER_USER). Add a global limiter for total Gemini calls per minute and per day; when exhausted, return a clear "service is busy, try again at HH:MM" response instead of calling Gemini. Release the concurrency slot on job success, failure, cancel and server-side timeout.

4. GEMINI-SIDE PROTECTION
Handle Gemini 429/RESOURCE_EXHAUSTED with exponential backoff and jitter (max 2 retries, bounded total wait), then surface a friendly retryable error. Add a request timeout. Count only real Gemini calls against quotas (not cache hits, not rejected requests).

5. COST REDUCTION
Cache results by a hash of (code, language, documentation type, section, model, prompt version). An identical repeat request returns the stored result without calling Gemini and without consuming quota, and the UI labels it as "Loaded from cache". Reject empty or oversized input before any quota is consumed.

6. API RESPONSES
On limit hit return HTTP 429 with a JSON body {error:"rate_limited", message, scope:"user|global|concurrency", retry_after_seconds} and a Retry-After header. Add GET /api/usage returning the caller's remaining generations (hour/day) and reset times, plus whether the service is currently available. Never expose other users' data or the API key.

7. FRONTEND
- Playground: show remaining generations ("3 of 5 left this hour") near "Run AI Analysis", reading /api/usage.
- When limited: disable the button with a live countdown to reset and a clear message; do not wipe the user's code or form values.
- Processing page: handle a 429 with a calm explanation and "Try again at HH:MM" instead of a generic error; the Retry button respects retry_after.
- Show a non-blocking toast when the cache is used, and a distinct message for "service busy" (global) vs "you've reached your limit" (user).
- Settings page: show the configured limits read-only.

8. LOGGING AND SAFETY
Log limit events (scope, anonymized identifier, endpoint) without code content or keys. Make sure the limiter fails safe: if the counter store errors, apply a conservative global fallback instead of allowing unlimited calls, and log it.

9. TESTS (automated, mock Gemini)
- Limit enforced at N+1 requests with a correct 429, Retry-After and body.
- Window reset allows requests again (use a fake clock).
- Cookie cleared still limited via IP; two IPs with one cookie are limited via the cookie.
- Concurrency slot released on success, failure and cancel.
- Global budget exhausted returns "service busy" without calling Gemini.
- Cache hit consumes no quota.
- Gemini 429 triggers bounded backoff, then a friendly error.
- Concurrent requests do not overshoot the limit (race test).
- X-Forwarded-For ignored unless TRUSTED_PROXY=true.
- Existing flows still work with RL_ENABLED=false.

10. VERIFY (browser subagent)
Run generations until the limit is hit and confirm: the counter text updates, the button disables with a countdown, the 429 message is friendly, the user's input is preserved, and the limit lifts after the reset. Then confirm a cached repeat does not consume quota. Update README with the env vars, defaults and how to tune them. Report exactly what passed, failed and was not tested.
```

---

## Prompt 21

**Timestamp:** `2026-11-02T04:32:57Z`

```text
update on github
```

---

## Prompt 22

**Timestamp:** `2026-11-02T04:35:54Z`

```text
include all the prompts i gave in prompts.md
```

---
