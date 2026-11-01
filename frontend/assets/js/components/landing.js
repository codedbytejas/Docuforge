/**
 * DocuForge AI — Full Commercial Landing Page
 * 8 Sections in strict spec order, real product UI mockup, no emojis, single warm amber accent.
 */

import { state, LANGS, SECTIONS_META } from '../state.js';
import { icons } from '../icons.js';
import { renderNavbar } from '../router.js';

export function renderLandingPage(container) {
  const isKeyConfigured = state.status?.gemini_configured;
  const currentModel = state.status?.model || 'gemini-3.5-flash';

  const CORE_10_LANGS = [
    { name: 'Python', ext: '.py' },
    { name: 'JavaScript', ext: '.js, .jsx' },
    { name: 'TypeScript', ext: '.ts, .tsx' },
    { name: 'Java', ext: '.java' },
    { name: 'C', ext: '.c, .h' },
    { name: 'C++', ext: '.cpp, .hpp' },
    { name: 'Go', ext: '.go' },
    { name: 'PHP', ext: '.php' },
    { name: 'Ruby', ext: '.rb' },
    { name: 'Rust', ext: '.rs' },
  ];

  container.innerHTML = `
    ${renderNavbar('/')}

    <main class="df-landing-wrapper" id="main-content">
      <!-- 1. Hero Section -->
      <section class="df-hero-section" id="hero">
        <div class="df-hero-ambient"></div>
        <div class="df-container">
          <div class="df-hero-content">
            <div class="df-badge-pill">
              <span class="df-badge-pulse"></span>
              <span>Intelligent Technical Documentation</span>
            </div>

            <h1 class="df-hero-title">
              Documentation, without the busywork.
            </h1>

            <p class="df-hero-desc">
              Turn your source code into clear, structured, developer-friendly documentation in seconds. Let AI handle the writing while you focus on building.
            </p>

            <div class="df-hero-ctas">
              <a href="/playground" class="df-btn df-btn-primary df-btn-lg" data-link>
                Start Documenting &rarr;
              </a>
              <a href="#problem" class="df-btn df-btn-secondary df-btn-lg" id="df-btn-explore">
                Explore Features &darr;
              </a>
            </div>
          </div>

          <!-- Hero Product Visual: Real Product Component Mockup -->
          <div class="df-hero-visual-container">
            <div class="df-example-label">
              ${icons.mark(12)} Illustrative Example &middot; Real Product Architecture
            </div>

            <div class="df-pipeline-mockup">
              <div class="df-mockup-header">
                <div class="df-mockup-dots">
                  <div class="df-mockup-dot"></div>
                  <div class="df-mockup-dot"></div>
                  <div class="df-mockup-dot"></div>
                </div>
                <div class="df-mono df-sub" style="font-size: 11px;">docuforge-pipeline &mdash; ${escapeHtml(currentModel)}</div>
                <div class="df-badge df-badge-documented" style="font-size: 11px;">Execution Runner</div>
              </div>

              <div class="df-pipeline-grid">
                <!-- Step 1: Real Source Code -->
                <div class="df-pipeline-col">
                  <div class="df-pipeline-col-header">
                    <span>${icons.file(14)}</span>
                    <span>01 / Source Input</span>
                    <span class="df-badge" style="margin-left: auto;">todo_store.py</span>
                  </div>
                  <pre class="df-mono" style="margin: 0; font-size: 12.5px; line-height: 1.6; color: var(--text-secondary);"><code style="color: #f4f4f6;"><span style="color: var(--accent);">class</span> TodoStore:
    <span style="color: var(--text-tertiary);">"""Persist todo items in JSON."""</span>
    <span style="color: var(--accent);">def</span> __init__(self, path: str):
        self.path = Path(path)
        self.items = json.loads(...)

    <span style="color: var(--accent);">def</span> add(self, title: str) -> dict:
        item = {"id": len(self.items)+1, "title": title}
        self.items.append(item)
        return item</code></pre>
                </div>

                <!-- Divider Node: Real AI Analysis -->
                <div class="df-pipeline-divider">
                  <div class="df-pipeline-node" title="Gemini Analysis in Flight">
                    ${icons.mark(16)}
                  </div>
                </div>

                <!-- Step 3: Real Structured Documentation Output -->
                <div class="df-pipeline-col df-demo-readme-col">
                  <div class="df-pipeline-col-header">
                    <span>${icons.code(14)}</span>
                    <span>03 / Structured Output</span>
                    <span class="df-badge df-badge-documented" style="margin-left: auto;">README.md</span>
                  </div>
                  <div class="df-demo-readme-preview" style="font-size: 13px; line-height: 1.6;">
                    <h4 style="font-size: 15px; font-weight: 700; color: #ffffff; margin-bottom: 6px;"># TodoStore</h4>
                    <p style="margin: 0 0 10px; color: #d1d1db;">JSON-backed persistence module for managing and storing todo items.</p>
                    <div style="background: var(--bg-surface); padding: 8px 12px; border-radius: var(--r-sm); border: 1px solid var(--border-subtle); margin-bottom: 8px;">
                      <span class="df-mono" style="color: var(--accent); font-size: 12px;">store.add("Finish documentation")</span>
                    </div>
                    <div class="df-sub" style="font-size: 11px;">Illustrative output &middot; Derived from source code</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. The Problem Section: Two-Column Editorial Layout -->
      <section class="df-section" id="problem">
        <div class="df-container">
          <div class="df-problem-editorial">
            <div class="df-problem-editorial-left">
              <div class="df-section-tag">The Problem</div>
              <h2 class="df-section-title">Great code shouldn't be difficult to understand.</h2>
              <p class="df-section-desc">Engineering teams lose productive momentum when critical codebases lack clear, accurate documentation.</p>
            </div>

            <div class="df-problem-editorial-list">
              <div class="df-problem-editorial-item">
                <span class="df-problem-editorial-num">01</span>
                <div>
                  <h3>Manual docs divert senior engineering focus</h3>
                  <p>Writing and formatting technical manuals takes developers away from solving core business problems and shipping features.</p>
                </div>
              </div>

              <div class="df-problem-editorial-item">
                <span class="df-problem-editorial-num">02</span>
                <div>
                  <h3>Unfamiliar code is slow to parse</h3>
                  <p>Joining a new project or maintaining legacy services requires hours of manual code inspection to map out dependencies and APIs.</p>
                </div>
              </div>

              <div class="df-problem-editorial-item">
                <span class="df-problem-editorial-num">03</span>
                <div>
                  <h3>Static documentation drifts over time</h3>
                  <p>As signatures evolve and parameters change, outdated READMEs quickly diverge from what is actually implemented in the code.</p>
                </div>
              </div>

              <div class="df-problem-editorial-item">
                <span class="df-problem-editorial-num">04</span>
                <div>
                  <h3>Variable conventions across contributors</h3>
                  <p>Different engineers document in inconsistent formats, leaving gaps in prerequisite installation, configurations, and exception contracts.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. The Solution Section -->
      <section class="df-section" id="features" style="background-color: var(--bg-surface);">
        <div class="df-container">
          <div class="df-section-header">
            <div class="df-section-tag">The Solution</div>
            <h2 class="df-section-title">Meet your intelligent documentation workspace.</h2>
            <p class="df-section-desc">DocuForge AI inspects your actual code structure and generates comprehensive, accurate documentation without hallucinations.</p>
          </div>

          <div class="df-solution-grid">
            <div class="df-solution-card">
              <div>
                <span class="df-badge df-badge-running" style="margin-bottom: 16px;">Core Architecture</span>
                <h3 class="df-title-md" style="margin-bottom: 12px;">Source-Truthful Synthesis</h3>
                <p class="df-sub" style="line-height: 1.6; margin: 0 0 20px;">
                  Strict technical rules enforce that the AI writes documentation <i>only</i> for what truly exists in your code. It never invents endpoints, methods, or third-party packages.
                </p>
              </div>
              <div style="background: var(--bg-canvas); padding: 14px; border-radius: var(--r-md); border: 1px solid var(--border-subtle); font-family: var(--font-mono); font-size: 12px; color: var(--accent);">
                // Zero fabricated parameters<br>
                // Omit or state 'Not provided'
              </div>
            </div>

            <div class="df-solution-card">
              <div>
                <span class="df-badge df-badge-documented" style="margin-bottom: 16px;">Comprehensive Structure</span>
                <h3 class="df-title-md" style="margin-bottom: 12px;">7 Technical Sections</h3>
                <p class="df-sub" style="line-height: 1.6; margin: 0 0 20px;">
                  Produces complete documentation divided into modular tabs: README, Functions, Classes, Usage Examples, API Reference, Dependencies, and Architecture Overview.
                </p>
              </div>
              <div style="background: var(--bg-canvas); padding: 14px; border-radius: var(--r-md); border: 1px solid var(--border-subtle); font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary);">
                [README &middot; Functions &middot; Classes &middot; API &middot; Arch]
              </div>
            </div>

            <div class="df-solution-card">
              <div>
                <span class="df-badge" style="margin-bottom: 16px;">Universal Portability</span>
                <h3 class="df-title-md" style="margin-bottom: 12px;">Edit, Export & PDF Print</h3>
                <p class="df-sub" style="line-height: 1.6; margin: 0 0 20px;">
                  Live preview with instant toggle to edit raw Markdown. Download clean <code>.md</code> files directly to your repo or export formatted PDFs with clean browser print styles.
                </p>
              </div>
              <div style="background: var(--bg-canvas); padding: 14px; border-radius: var(--r-md); border: 1px solid var(--border-subtle); font-family: var(--font-mono); font-size: 12px; color: var(--text-primary);">
                Download .md &bull; PDF Export &bull; Auto-save SQLite
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. How It Works Section: Vertical Stepper -->
      <section class="df-section" id="how-it-works">
        <div class="df-container">
          <div class="df-section-header">
            <div class="df-section-tag">Workflow</div>
            <h2 class="df-section-title">How DocuForge AI works.</h2>
            <p class="df-section-desc">From raw source files to production-ready documentation in three transparent steps.</p>
          </div>

          <div class="df-stepper">
            <div class="df-stepper-item">
              <div class="df-stepper-badge">1</div>
              <div class="df-stepper-content">
                <h3>Provide Your Source Code</h3>
                <p>Upload a project ZIP, drop individual source files, or paste raw code directly into the editor. Files are held securely in memory without writing to disk.</p>
              </div>
            </div>

            <div class="df-stepper-item">
              <div class="df-stepper-badge">2</div>
              <div class="df-stepper-content">
                <h3>Structured AI Analysis</h3>
                <p>The runner streams real-time stage progress while Gemini inspects syntax, classes, functions, and interfaces against strict technical prompts.</p>
              </div>
            </div>

            <div class="df-stepper-item">
              <div class="df-stepper-badge">3</div>
              <div class="df-stepper-content">
                <h3>Review, Edit & Export</h3>
                <p>Inspect structured documentation tabs, edit markdown in real time, regenerate individual sections on demand, and download clean Markdown or PDF files.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 5. Supported Languages Section: Clean 10 Languages List -->
      <section class="df-section" id="languages" style="background-color: var(--bg-surface);">
        <div class="df-container">
          <div class="df-section-header">
            <div class="df-section-tag">Supported Languages</div>
            <h2 class="df-section-title">Engineered for 10 core languages.</h2>
            <p class="df-section-desc">DocuForge AI inspects and documents 10 popular programming languages across single and multi-file projects.</p>
          </div>

          <div class="df-languages-container">
            <div class="df-languages-list">
              ${CORE_10_LANGS.map(l => `
                <div class="df-language-row">
                  <span class="df-language-name">${escapeHtml(l.name)}</span>
                  <span class="df-language-ext">${escapeHtml(l.ext)}</span>
                </div>
              `).join('')}
            </div>
            <div class="df-languages-fallback">
              Working with another language? Select <b>Other</b> for general plain-text and structured code parsing.
            </div>
          </div>
        </div>
      </section>

      <!-- 6. Documentation Output Preview -->
      <section class="df-section" id="preview">
        <div class="df-container">
          <div class="df-section-header">
            <div class="df-section-tag">Interactive Preview</div>
            <h2 class="df-section-title">Documentation output preview.</h2>
            <p class="df-section-desc">Inspect sample output generated from a Python codebase. Click any tab to preview its structured layout.</p>
          </div>

          <div class="df-preview-box">
            <div class="df-example-label" style="margin: 16px 16px 8px;">
              ${icons.mark(12)} Illustrative Preview &middot; Generated Output Sample
            </div>

            <div class="df-preview-tabs" id="df-landing-preview-tabs">
              <button class="df-preview-tab-btn active" data-tab="readme">README.md</button>
              <button class="df-preview-tab-btn" data-tab="functions">Functions & Methods</button>
              <button class="df-preview-tab-btn" data-tab="classes">Class Reference</button>
              <button class="df-preview-tab-btn" data-tab="usage">Usage Examples</button>
              <button class="df-preview-tab-btn" data-tab="api">API Documentation</button>
            </div>

            <div class="df-preview-content" id="df-landing-preview-content">
              <!-- Rendered via JS -->
            </div>
          </div>
        </div>
      </section>

      <!-- 7. About Section -->
      <section class="df-section" id="about">
        <div class="df-container">
          <div class="df-section-header">
            <div class="df-section-tag">About DocuForge AI</div>
            <h2 class="df-section-title">Built for developers who value clarity.</h2>
            <p class="df-section-desc">A fast, focused documentation assistant combining local FastAPI execution with Google Gemini intelligence.</p>
          </div>

          <div class="df-about-grid">
            <div class="df-about-card">
              <h3>Local & Private First</h3>
              <p>Your code is processed in-memory and stored locally in your own SQLite database. Secrets, private keys, and environment files are blocked upfront.</p>
            </div>
            <div class="df-about-card">
              <h3>Source-Truthful Documentation</h3>
              <p>Strict system prompts instruct the model to document only what is genuinely implemented in your code, omitting unverified assumptions.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 8. Final CTA Section -->
      <section class="df-section" style="border-top: none; padding-top: 40px;">
        <div class="df-container">
          <div class="df-cta-box">
            <h2 class="df-title-xl" style="font-size: clamp(28px, 4.5vw, 42px); margin-bottom: 16px; color: #ffffff;">
              Make your next codebase easier to understand.
            </h2>
            <p class="df-lead" style="margin: 0 auto 32px; max-width: 580px; color: var(--text-secondary);">
              Join developers turning raw code into clean, structured technical documentation in seconds.
            </p>
            <a href="/playground" class="df-btn df-btn-primary df-btn-lg" data-link>
              Start Documenting Now &rarr;
            </a>
          </div>
        </div>
      </section>

      </main>

      <!-- 9. Footer Section -->
      <footer class="df-footer">
        <div class="df-container">
          <div class="df-footer-top" style="display: grid; grid-template-columns: 1.5fr repeat(3, 1fr); gap: 32px; margin-bottom: 40px;">
            <div>
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span class="df-brand-mark">${icons.mark(16)}</span>
                <b style="font-size: 16px;">DocuForge AI</b>
              </div>
              <p class="df-sub" style="max-width: 320px; line-height: 1.6; margin-bottom: 16px;">
                Developer-first technical documentation synthesizer. Inspects real source code structures to generate accurate Markdown and PDF documentation.
              </p>
              <div class="df-badge" style="font-size: 11px;">
                <span class="df-badge-dot" style="background-color: var(--status-ok);"></span>
                Engine Online &middot; ${escapeHtml(currentModel)}
              </div>
            </div>

            <div>
              <b class="df-sub" style="font-weight: 650; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px; color: var(--text-tertiary); display: block; margin-bottom: 14px;">Product</b>
              <div style="display: flex; flex-direction: column; gap: 10px;" class="df-sub">
                <a href="/playground" data-link>Playground Workspace</a>
                <a href="/projects" data-link>Saved Projects</a>
                <a href="#how-it-works">How It Works</a>
                <a href="#languages">Supported Languages</a>
              </div>
            </div>

            <div>
              <b class="df-sub" style="font-weight: 650; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px; color: var(--text-tertiary); display: block; margin-bottom: 14px;">Resources</b>
              <div style="display: flex; flex-direction: column; gap: 10px;" class="df-sub">
                <a href="#preview">Interactive Preview</a>
                <a href="#features">Architecture Overview</a>
                <a href="/settings" data-link>Environment & API Status</a>
                <a href="#about">Privacy & Data Handling</a>
              </div>
            </div>

            <div>
              <b class="df-sub" style="font-weight: 650; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px; color: var(--text-tertiary); display: block; margin-bottom: 14px;">Developer Support</b>
              <div style="display: flex; flex-direction: column; gap: 10px;" class="df-sub">
                <a href="/docs" target="_blank" rel="noopener">FastAPI Documentation</a>
                <a href="/settings" data-link>System Preferences</a>
                <a href="#about">Technical Safeguards</a>
                <span style="color: var(--text-tertiary); font-size: 11.5px;">v1.2.0 &middot; SQLite Local</span>
              </div>
            </div>
          </div>

          <div style="border-top: 1px solid var(--border-subtle); padding-top: 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
            <div class="df-sub" style="font-size: 12px;">
              &copy; ${new Date().getFullYear()} DocuForge AI. Designed for engineering teams.
            </div>
            <div class="df-sub" style="font-size: 12px; display: flex; gap: 16px; flex-wrap: wrap;">
              <span>Zero fabricated APIs</span>
              <span>&bull;</span>
              <span>Server-side secrets</span>
              <span>&bull;</span>
              <span>Dark-first design</span>
            </div>
          </div>
        </div>
      </footer>
  `;

  // Bind smooth scroll on navigation links
  container.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.onclick = (e) => {
      e.preventDefault();
      const targetId = anchor.getAttribute('href').substring(1);
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth' });
        container.querySelectorAll('.df-nav-link').forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === '#' + targetId);
        });
      }
    };
  });

  // Interactive tabbed preview logic
  const PREVIEWS = {
    readme: `
# TodoStore

## Overview
A lightweight persistence module for managing todo items stored in a local JSON document.

## Technology Stack
- **Language:** Python
- **Standard Library:** \`json\`, \`pathlib.Path\`
- **Storage:** Local JSON file format

## Prerequisites & Installation
No external third-party dependencies required. Uses the Python standard library.

\`\`\`bash
# Run with Python standard library
python -c "import json, pathlib; print('Ready')"
\`\`\`

## Configuration
Pass the desired JSON storage path directly into the \`TodoStore\` constructor. If the target file does not exist, an empty store is initialized automatically.
    `,
    functions: `
### \`TodoStore.add(title: str) -> dict\`
Creates a new todo item with an auto-incremented integer ID, appends it to memory, and immediately persists changes to disk.

- **Parameters:**
  - \`title\` (\`str\`): The name of the todo task.
- **Returns:**
  - \`dict\`: The created task entity containing \`id\` and \`title\`.

---

### \`TodoStore.complete(item_id: int) -> bool\`
Marks an existing todo task as completed.

- **Parameters:**
  - \`item_id\` (\`int\`): Identifier of the task to resolve.
- **Returns:**
  - \`bool\`: \`True\` if item was found and modified; \`False\` otherwise.
    `,
    classes: `
### Class: \`TodoStore\`

#### Purpose
Encapsulates CRUD operations over an on-disk JSON list of task records.

#### Attributes
- \`path\` (\`pathlib.Path\`): Filesystem location of the backing JSON storage.
- \`items\` (\`list[dict]\`): In-memory cache of deserialized todo records.

#### Methods
- \`__init__(path: str)\`: Connects to target file and loads initial data.
- \`add(title: str) -> dict\`: Inserts and persists a new item.
- \`complete(item_id: int) -> bool\`: Sets done status for matching ID.
    `,
    usage: `
### Initializing and Adding Items
\`\`\`python
from todo_store import TodoStore

# Initialize store on local filesystem
store = TodoStore("tasks.json")

# Add an item
task = store.add("Finish documentation")
print(f"Task created with ID: {task['id']}")
\`\`\`

### Completing Tasks
\`\`\`python
# Mark task complete by ID
success = store.complete(task["id"])
if success:
    print("Task successfully marked as completed.")
\`\`\`
    `,
    api: `
### Public API Interface Contract

| Symbol | Signature | Return Type | Description |
| :--- | :--- | :--- | :--- |
| \`TodoStore.__init__\` | \`(path: str)\` | \`None\` | Initializes store at specified file path |
| \`TodoStore.add\` | \`(title: str)\` | \`dict\` | Appends item and writes to file |
| \`TodoStore.complete\` | \`(item_id: int)\` | \`bool\` | Toggles status to done |
    `
  };

  const previewTabs = container.querySelectorAll('.df-preview-tab-btn');
  const previewContent = container.querySelector('#df-landing-preview-content');

  function showPreviewTab(tabKey) {
    previewTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tabKey));
    const rawMd = PREVIEWS[tabKey] || '';
    if (window.marked && window.DOMPurify) {
      previewContent.innerHTML = window.DOMPurify.sanitize(window.marked.parse(rawMd));
    } else {
      previewContent.innerHTML = `<pre class="df-mono">${rawMd}</pre>`;
    }
  }

  previewTabs.forEach(t => {
    t.onclick = () => showPreviewTab(t.dataset.tab);
  });

  // Default tab
  showPreviewTab('readme');

  // Subtle section reveals (respects prefers-reduced-motion)
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('df-section-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    container.querySelectorAll('.df-section').forEach(sec => {
      sec.classList.add('df-section-reveal');
      observer.observe(sec);
    });
  }
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
