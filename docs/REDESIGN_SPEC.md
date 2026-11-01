ROLE
You are a senior product designer and full-stack engineer. You are redesigning an EXISTING, working application called DocuForge AI (AI-powered code documentation generator). Your goal is a premium developer-SaaS experience in the class of Linear, Vercel, Raycast and Framer, not a restyled admin dashboard.

CONTEXT
- A screenshot of the current UI is attached. Treat it as the "before" state, not a layout to refine.
- The backend already works: Gemini integration, SQLite database, saved projects, file/ZIP upload, section regeneration, Markdown rendering, downloads. All of it must keep working.

STEP 0 — INSPECT BEFORE CHANGING (mandatory)
1. Read the repository: stack, folder structure, API routes, DB schema, how the frontend is served.
2. Reply with a short summary (current routes, API endpoints, what is reusable) and a phased plan.
3. Keep the existing stack unless there is a concrete reason to change it. Database changes must be additive migrations only; never drop or reset existing data.

HARD CONSTRAINTS
- The Gemini API key stays server-side only. Never expose it to the frontend, storage or logs.
- No fake data presented as real: no hardcoded stats, no pre-written "generated" docs, no fake loading percentages, no simulated AI success.
- Marketing example content (hero visual, "documentation output" preview) is allowed ONLY if clearly an illustrative example and visually distinct from real results.
- Every visible control must work. Remove anything that cannot.
- Supported languages shown anywhere must match what the app really supports (read the existing language list).
- No emoji icons, no purple AI gradients, no generic metric-card grids, no repeated rounded-card layouts.

DESIGN SYSTEM
- Palette: deep charcoal, warm off-white, muted grey, ONE distinctive accent. Support dark and light surfaces.
- Editorial typography with strong hierarchy (a display face for headlines, a clean sans for UI, a mono for code). Generous whitespace, thin borders, consistent spacing scale, one icon set.
- Motion: subtle, fast, purposeful. Respect prefers-reduced-motion. Smooth scrolling.
- Fully responsive (desktop, laptop, tablet, mobile); the editor and results workspace must adapt, not merely shrink.
- Accessibility: contrast AA, visible focus states, keyboard navigation, semantic HTML.

ROUTES (history-based, refresh-safe; the server must serve the app for every route)
/ (intro + landing) · /playground · /processing · /documentation · /projects · /settings
Deep links and browser refresh must not break. If /processing or /documentation is opened without an active job or project, redirect gracefully to /playground or /projects.

1. CINEMATIC INTRO (first visit per session only)
- Full-screen dark scene: animated brand mark, tagline "Your Code. Clearly Documented.", line "Every great codebase deserves great documentation.", supporting line "Transform source code into meaningful technical documentation with intelligent AI."
- Subtle code-themed motion (moving lines, documentation glyphs).
- Progress reflects REAL initialization (fonts/assets loaded and backend health check succeeded). No percentages. Never block longer than needed: reveal the landing page as soon as ready, with a minimum of ~1.5 s so the animation does not flash. Include a Skip control. Do not replay on internal navigation (use sessionStorage). If the backend is unreachable, show a clear error with retry instead of hanging.

2. LANDING PAGE (commercial, scroll-driven)
- Navbar: logo; Home, Features, How It Works, Supported Languages, About; "Get Started". Show "Sign In" only if authentication exists.
- Hero: editorial headline "Documentation, without the busywork." + description "Turn your source code into clear, structured, developer-friendly documentation in seconds. Let AI handle the writing while you focus on building." CTAs: "Start Documenting →" (to /playground) and "Explore Features" (scroll). Product visual: animated SOURCE CODE → AI ANALYSIS → DOCUMENTATION built from real product UI components, labelled as an example.
- Sections in order: Hero; The Problem ("Great code shouldn't be difficult to understand." Manual docs take time, unfamiliar code is hard to read, docs go stale, consistency is hard); The Solution ("Meet your intelligent documentation workspace."); How It Works (01 Upload Your Code, 02 Let AI Understand, 03 Generate Documentation); Supported Languages; Documentation Output preview (README, functions, classes, usage examples, API reference); Final CTA ("Make your next codebase easier to understand." / "Start Documenting Now →"); Footer (brand, product links, support links, copyright).
- Vary section layouts for rhythm; use real product previews, not stock illustrations.

3. PLAYGROUND (/playground) — no AI call until the user clicks the button
- Heading "Let's document your code." Subtitle "Provide your source code and let DocuForge AI turn it into structured documentation."
- Option A, Upload: drag-and-drop zone + browse; single files and ZIP; list filenames and sizes; remove individual files; clear validation errors (type, size, empty, corrupt ZIP) reusing the existing backend limits.
- Option B, Paste: syntax-highlighted editor (Monaco or equivalent), language selector, sample code, clear.
- Configuration: project name, short description, language, documentation type (Complete README / Function documentation / Class documentation / API documentation / Complete technical documentation). Map these to the existing documentation-type and section logic; extend the backend only if needed.
- Primary action "Run AI Analysis →", disabled with an explanation until valid input exists.

4. PROCESSING (/processing)
- Headline "Understanding your codebase..." with six stages: Reading source files; Identifying functions and classes; Analyzing dependencies; Understanding code structure; Generating documentation; Preparing final output.
- Progress must be truthful. Preferred: run generation as a backend job and stream or poll real stage events (SSE or polling). If a stage cannot be measured, do not fake it: show only stages whose state is actually known (e.g. upload read, request sent, awaiting Gemini, parsing, saved) and group the rest honestly.
- Errors (missing API key, rate limit, malformed AI output, network) show a specific message with Retry and "Edit input". Navigation away or refresh must not lose the job or the user's input.

5. RESULTS WORKSPACE (/documentation)
- Left sidebar: Project overview, README, Functions, Classes, Usage examples, API reference, Dependencies, Architecture, with in-document navigation (outline/anchors).
- Main panel: real generated Markdown rendered beautifully (sanitized), with code highlighting. Actions: Edit/Preview, Copy, Regenerate this section, Download README.md, Export PDF. Edits persist.
- Existing /projects and /settings pages are restyled to the new system and keep all current functionality (rename, delete, reopen, regenerate, download, preferences, API configuration status).

VERIFICATION (required before declaring completion)
Run the app and drive it with a real browser (Playwright or equivalent). Test: intro → landing → scroll all sections → Start Documenting → paste code → pick language → fill details → Run AI Analysis → live processing → results → edit → download. Also test: ZIP upload, invalid file, empty input, missing API key, forced API failure, refresh on every route, existing projects still loading, console clean, no TypeScript/backend errors. Capture screenshots at 1440, 1024, 768 and 390 px widths and fix every layout defect. Report exactly what you tested and what failed; never claim a feature works without having run it.

DELIVERABLES
Updated project, any migration notes, updated README with run/test steps, and a concise change summary listing reused vs. rebuilt parts.