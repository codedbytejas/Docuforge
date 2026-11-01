# DocuForge AI — 3-Minute Executive Demo Script

A structured, timed walkthrough script for presenting DocuForge AI to engineering leads, stakeholders, and product evaluators.

---

## Demo Overview
- **Product:** DocuForge AI
- **Positioning:** Developer-first, AI-powered codebase documentation generator that turns source code into structured technical documentation with Google Gemini.
- **Duration:** Exactly 3 minutes (180 seconds).

---

## 1. Opening & Landing Page (0:00 – 0:35)

1. **First-Visit Experience (`/`):**
   - Open browser to `http://127.0.0.1:8000/`.
   - *Presenter Note:* Highlight the cinematic intro wordmark checking backend system health and active model readiness (`gemini-3.5-flash`).
   - Click **"Skip Intro →"** to land immediately on the commercial overview.
2. **Landing Page Value Proposition:**
   - Scroll through the landing page:
     - **Headline:** *"Documentation, without the busywork."*
     - **Editorial Problem Section:** Explains why engineering docs decay (undocumented APIs, stale setups, tedious maintenance).
     - **Hero Interactive Preview:** Click between *README*, *Functions*, and *API Reference* tabs to show real component mockups backed by the `TodoStore` sample codebase.
     - **Languages Section:** Point out the 10 core languages (Python, TypeScript, Go, Rust, etc.) with the `Other` fallback for arbitrary structured code.
     - **Navigation Bar:** Toggle between Dark and Light mode to showcase consistent contrast and single-accent amber palette (`#f59e0b`).
3. **Transition:**
   - Click the primary CTA **"Start Documenting →"**.

---

## 2. Code Intake & Security Safeguards (0:35 – 1:15)

1. **Playground Overview (`/playground`):**
   - Note the clean, distraction-free two-column workspace.
   - Show the **"Load Sample"** button, which loads the clean `TodoStore` Python codebase.
2. **Security & Archive Intake:**
   - Switch to the **"Upload files"** segmented control tab.
   - Drag or select a multi-file ZIP archive containing `.py`, `.ts`, and a `.env` file.
   - Point out the **Security File Notice**:
     - Secret environment files (`.env`) and binaries are stripped upfront with a neutral notice and never transmitted to the AI engine.
     - Multiple file extensions automatically detect as **"Mixed"** language.
     - Collision-proof file delimiters prevent user source code from breaking file boundaries.
3. **Output Scope Specification:**
   - Change the **Documentation Type** dropdown from *Complete technical documentation* to *API documentation*.
   - Point out the live **Output Scope** card on the right, updating in real time with the exact deliverables Gemini will generate.
4. **Trigger Generation:**
   - Click **"Run AI Analysis & Generate →"**.

---

## 3. Truthful Live Runner & SSE Milestones (1:15 – 1:45)

1. **Processing Pipeline (`/processing`):**
   - Point out the live status badge (`Running`) and the real-time elapsed timer (`00:04s`).
   - Highlight the 5 truthful milestones:
     1. `intake` (validation)
     2. `dispatch` (schema formulation)
     3. `inference` (live in-flight Gemini call)
     4. `parsing` (JSON validation)
     5. `persisting` (SQLite storage)
   - *Presenter Note:* Mention that this is streamed live over Server-Sent Events (SSE). If needed, a user can cancel the run with the ghost "Cancel Analysis" button.
2. **Auto-Navigation:**
   - As soon as SQLite persistence finishes, the page automatically redirects into the workspace for project results.

---

## 4. Documentation Workspace & In-Place Editing (1:45 – 2:30)

1. **Workspace Layout (`/documentation`):**
   - Point out the left-hand navigation sidebar (or top tab bar on mobile/tablet) showing all 7 documentation sections: *README*, *Functions*, *Classes*, *Usage Examples*, *API Reference*, *Dependencies*, and *Architecture*.
   - In-document anchor links allow jumping straight to headers.
   - The collapsible **Source Scope** card shows total file count, language, and byte sizes.
2. **In-Place Markdown Editing:**
   - Click the **"Edit"** button. The live renderer toggles into a clean Markdown editor.
   - Type an amendment (e.g. adding a custom installation flag or operational note).
   - Click **"Save Changes"**.
   - *Presenter Note:* Demonstrate route refresh (`Cmd+R` / `F5`). The edit remains permanently persisted in the SQLite database and stays on the active section tab.
   - Show the **"Copy Section"** button, copying clean Markdown directly to clipboard.

---

## 5. Export, Management & Closing (2:30 – 3:00)

1. **Export Capabilities:**
   - Click **"Download README.md"** — downloads the file immediately to the local filesystem.
   - Click **"Export PDF"** — invokes the browser print dialog with dedicated print styles that strip nav bars and format typography cleanly for PDF generation.
2. **Saved Projects & Settings (`/projects` & `/settings`):**
   - Click **Projects** in the navigation bar: show the newly created project in the list with rename, view, and delete capabilities.
   - Click **Settings**: show the server-side Gemini credential status check and active model display.
3. **Closing Summary:**
   - *"DocuForge AI eliminates the documentation tax for engineering teams — providing automated, accurate, and completely verifiable technical docs with zero hallucinations and complete security."*

---

## Known System Limits

For transparency during technical Q&A:
- **Rate Limits:** In-flight generation speed depends on Google Gemini API latency and quota limits.
- **Maximum File Payload:** 200 KB per individual file; 5 MB total per ZIP archive; 150 KB aggregate source code per analysis job.
- **Exclusions:** `.env*`, `.pem`, `.key`, `.cert`, `.crt`, and binary files (`.exe`, `.dll`, `.so`, `.png`, etc.) are intentionally denied for security.
- **Supported Languages:** 10 core languages (Python, JavaScript, TypeScript, Java, C, C++, Go, PHP, Ruby, Rust) plus a generalized `Other` plain-text parser.
