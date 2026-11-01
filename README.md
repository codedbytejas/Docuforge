# DocuForge AI

A developer-first, AI-powered codebase documentation generator built with FastAPI, SQLite, and vanilla ES modules. Transforms source code and repositories into structured technical documentation with Google Gemini.

---

## Architecture & Features

- **History-Based Routing**: Clean URLs (`/`, `/playground`, `/processing`, `/documentation`, `/projects`, `/settings`) with FastAPI SPA fallback serving direct links and browser refreshes reliably.
- **Universal Responsive Design System**: Root-cause overflow prevention (`min-width: 0`, `overflow-wrap: anywhere`, `max-width: 100%`) verified across ultra-compact mobile (320px, 360px, 390px), tablet (768px, 1024px), standard desktop (1440px), and wide monitors (1920px). Features a mobile hamburger navigation drawer and responsive code tables.
- **Dark-First Editorial Typography**: Plus Jakarta Sans, Inter, JetBrains Mono, charcoal obsidian surfaces, and a warm amber accent (`#f59e0b`). Light mode is equally polished with WCAG AA compliant contrast.
- **Accessibility & Standards**: Strict HTML semantic landmarks (`<main id="main-content">`, `<nav>`, `<header>`, `<footer>`), keyboard skip link, visible `:focus-visible` outlines, explicit ARIA labels on all interactive controls, and full respect for `prefers-reduced-motion`.
- **Cinematic Intro & Landing**: First-visit-per-session intro tied to real backend health checks with Skip and retry states, leading to an 8-section commercial landing page with real UI component previews and zero unverifiable marketing claims.
- **Playground (`/playground`)**:
  - Segmented control for Drag-and-drop file upload & ZIP extraction vs. Syntax-highlighted paste editor with line numbers.
  - Multi-file ZIP ingestion with individual file chips and removal buttons.
  - Neutral skipped-file notice explaining excluded files (denies `.env*`, `.pem`, `.key`, and unsupported binaries without sending secrets to AI).
  - Multi-file language auto-detection (switches to `"Mixed"` when multi-extension archives are loaded).
  - Collision-proof file serialization (`<<<DOCUFORGE:FILE_NAME="..." >>> ... <<<DOCUFORGE:END_FILE>>>`) ensuring user code containing `# FILE:` headers never splits or corrupts.
  - Dynamic Output Scope preview reflecting the chosen documentation scope.
  - Draft persistence via `sessionStorage` preventing accidental work loss.
  - Strict validation: 200 KB per file limit, 5 MB ZIP limit, 40 files maximum, 150 KB code limit.
  - Zero AI calls until the user explicitly clicks **"Run AI Analysis & Generate →"**.
- **Truthful Progress Runner (`/processing`)**:
  - Backend job worker reporting 5 measured milestones:
    1. `intake`: Reading & validating source files & configuration
    2. `dispatch`: Formulating prompt schema & model dispatch
    3. `inference`: Real-time Gemini inference with live elapsed timer
    4. `parsing`: Validating JSON schema & Markdown output
    5. `persisting`: Writing structured documentation to SQLite
  - Streamed via Server-Sent Events (`GET /api/jobs/{jid}/stream`) with polling fallback and job cancellation support.
  - Specific error states with working "Retry Generation" and "Edit Source Input" actions.
  - Auto-redirects to results workspace upon completion.
- **Results Workspace (`/documentation`)**:
  - Left sidebar outline containing all 7 sections (README, Functions, Classes, Usage Examples, API Reference, Dependencies, Architecture), responsive horizontal tab bar on tablet/mobile.
  - Collapsible Source Scope card displaying loaded file count, language, and byte sizes.
  - In-document anchor outline generated from Markdown headings with smooth scrolling.
  - Sanitized Markdown preview with code highlighting and code block copy.
  - In-place Markdown editing with persistent saving back to SQLite database and tab state URL synchronization (`&tab=...`).
  - Unsaved changes dirty state guard preventing accidental navigation.
  - Actions: Copy section markdown, Regenerate active section, Download Markdown (`README.md` or `${name}-${section}.md`), and Export clean printable PDF via browser print dialog.
- **Projects Manager (`/projects`)**: Real-time project search, status badges (`Documented` / `Draft`), language badges, inline project renaming, deletion confirmation dialogs, and workspace deep linking.
- **Settings (`/settings`)**: Live server-side Gemini credential status check, active model indicator, default language and doc type preferences, and instant dark/light theme switching.

---

## System Constraints & Guardrails

| Constraint | Limit | Description |
| :--- | :--- | :--- |
| **Max File Size** | 200 KB | Maximum single file payload |
| **Max Archive Size** | 5 MB | Maximum uploaded ZIP archive size |
| **Max Files per Job** | 40 files | Maximum extracted source files |
| **Max Total Code** | 150 KB | Aggregate source code submitted to Gemini |
| **Secret Denial** | Strict | `.env*`, `.pem`, `.key`, `.cert` rejected upfront |
| **Supported Languages** | 10 Core + Other | Python, JS, TS, Java, C, C++, Go, PHP, Ruby, Rust, Other |

---

## Quickstart

### 1. Setup Environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Configure Gemini API Key
Copy the example environment file and add your Google AI Studio API key:
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```
> **Security Note**: The Gemini API key remains server-side only in `.env`. It is never sent to the browser or stored in client storage.

### 3. Run Development Server
```bash
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Open **http://127.0.0.1:8000** in your browser.

---

## Automated Verification Tests

The test suite runs with Playwright across headless Chromium, validating the complete end-to-end user journey:

```bash
# Run comprehensive demo-ready E2E suite (56 tests covering intro, copy, upload, generation, persistence, responsive sweep)
.venv/bin/python scratch/verify_demo_ready.py

# Run accessibility & landmarks audit across all 5 routes
.venv/bin/python scratch/audit_accessibility.py
```
