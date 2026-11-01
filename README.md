# DocuForge AI

A developer-first, AI-powered codebase documentation generator built with FastAPI, SQLite, and vanilla ES modules. Turns source code and repositories into structured technical documentation with Gemini.

---

## Architecture & Features

- **History-Based Routing**: Clean URLs (`/`, `/playground`, `/processing`, `/documentation`, `/projects`, `/settings`) with FastAPI SPA fallback serving direct links and browser refreshes reliably.
- **Dark-First Design System**: Editorial typography (Plus Jakarta Sans, Inter, JetBrains Mono), charcoal obsidian surfaces, and a warm amber accent (`#f59e0b`). Fully responsive across desktop (1440px), laptop (1024px), tablet (768px), and mobile (390px).
- **Cinematic Intro & Landing**: First-visit-per-session intro tied to real backend health checks with Skip and retry states, leading to an 8-section commercial landing page with real UI component previews.
- **Playground (`/playground`)**:
  - Drag-and-drop file upload & ZIP extraction into individual file chips with individual removal.
  - Multi-line code editor with sample Python codebase loader (`TodoStore`), character/line stats, and Tab indentation support.
  - Configuration: Project name, Language selector (11 supported languages), Documentation scope selector (5 target modes), and optional Description.
  - Strict validation: 200 KB per file limit, 5 MB ZIP limit, 40 files maximum, 150 KB code limit.
  - Zero AI calls until the user explicitly clicks **"Run AI Analysis & Generate →"**.
- **Truthful Progress Runner (`/processing`)**:
  - Backend job worker reporting 5 measured milestones:
    1. `intake`: Reading & validating source files & configuration
    2. `dispatch`: Formulating prompt schema & model dispatch
    3. `inference`: Real-time Gemini inference with live in-flight timer
    4. `parsing`: Validating JSON schema & Markdown output
    5. `persisting`: Writing structured documentation to SQLite
  - Streamed via Server-Sent Events (`GET /api/jobs/{jid}/stream`) with polling fallback.
  - Specific error states with working "Retry Generation" and "Edit Source Input" actions.
  - Auto-redirects to results workspace upon completion.
- **Results Workspace (`/documentation`)**:
  - Left sidebar outline containing all 7 sections (README, Functions, Classes, Usage Examples, API Reference, Dependencies, Architecture).
  - In-document anchor outline generated from Markdown headings with smooth scrolling.
  - Sanitized Markdown preview with code highlighting and code block copy.
  - In-place Markdown editing with persistent saving back to SQLite database.
  - Actions: Copy section, Regenerate active section, Download Markdown (`README.md` or `${name}-${section}.md`), and Export clean printable PDF via browser print dialog.
- **Projects Manager (`/projects`)**: Real-time project search, status badges (`Documented` / `Draft`), language badges, inline project renaming, deletion, and workspace deep linking.
- **Settings (`/settings`)**: Live server-side Gemini credential status check, active model indicator, default language and doc type preferences, and instant dark/light theme switching.

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

The test suite runs with Playwright across Chrome, validating the complete end-to-end user journey:

```bash
# Run full Phase 4 Playwright verification (E2E generation, edits, persistence, search, responsive viewports)
.venv/bin/python scratch/verify_phase4.py

# Run upload edge cases & route refresh test
.venv/bin/python scratch/verify_upload_edge_cases.py
```
