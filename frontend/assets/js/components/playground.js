/**
 * DocuForge AI — Playground Component (/playground)
 * Upload + Paste (Segmented Control), Syntax Editor with Line Numbers,
 * Auto-language Detection, File Tracking without delimiter corruption,
 * Dynamic Output Scope Deliverables.
 */

import { state, setCurrentProject, setActiveJob, LANGS, DOC_TYPES, SECTIONS_META } from '../state.js';
import { api, showToast } from '../api.js';
import { navigate, renderNavbar } from '../router.js';
import { icons } from '../icons.js';

const SAMPLE_CODE = `import json
from pathlib import Path
from typing import List, Dict, Optional

class TodoStore:
    """A persistent todo item manager backed by JSON storage.
    
    Attributes:
        path (Path): File system location of the backing store.
        items (List[Dict]): In-memory cache of stored todo items.
    """

    def __init__(self, path: str = "todos.json"):
        """Initialize the store and load existing items if present.
        
        Args:
            path: Relative or absolute path to the JSON storage file.
        """
        self.path = Path(path)
        self.items: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        """Read and deserialize todos from disk."""
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def add(self, title: str, priority: int = 1) -> Dict:
        """Add a new task to the collection and save to disk.
        
        Args:
            title: Short description of the task.
            priority: Priority rank (1 = low, 3 = high).
            
        Returns:
            The newly created todo dictionary record.
        """
        item = {
            "id": len(self.items) + 1,
            "title": title.strip(),
            "priority": priority,
            "done": False
        }
        self.items.append(item)
        self.save()
        return item

    def complete(self, item_id: int) -> bool:
        """Mark an existing task as completed.
        
        Args:
            item_id: Unique integer identifier.
            
        Returns:
            True if found and updated, False otherwise.
        """
        for item in self.items:
            if item["id"] == item_id:
                item["done"] = True
                self.save()
                return True
        return False

    def save(self) -> None:
        """Serialize in-memory items to disk in formatted JSON."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.items, indent=2), encoding="utf-8")
`;

const EXT_TO_LANG = {
  py: 'Python',
  js: 'JavaScript', jsx: 'JavaScript', mjs: 'JavaScript', cjs: 'JavaScript',
  ts: 'TypeScript', tsx: 'TypeScript',
  java: 'Java',
  c: 'C', h: 'C',
  cpp: 'C++', hpp: 'C++', cc: 'C++', cxx: 'C++',
  go: 'Go',
  php: 'PHP',
  rb: 'Ruby',
  rs: 'Rust',
  html: 'Other', css: 'Other', sql: 'Other', yml: 'Other', yaml: 'Other', sh: 'Other', json: 'Other', md: 'Other', txt: 'Other'
};

const OUTPUT_SCOPE_CONFIG = {
  'Complete technical documentation': {
    badge: 'All 7 Sections',
    summary: 'Comprehensive developer documentation spanning all technical modules.',
    items: [
      { title: 'Project Overview & README', desc: 'Summary, key features, prerequisites, setup and usage instructions.' },
      { title: 'Functions & Methods', desc: 'Signatures, arguments with types, return definitions, and calling examples.' },
      { title: 'Class Reference', desc: 'Object hierarchies, attributes, constructors, and method contracts.' },
      { title: 'Usage Examples', desc: 'Executable examples grounded strictly in the implemented APIs.' },
      { title: 'API Reference', desc: 'Public entrypoints, interface schemas, and return formats.' },
      { title: 'Dependencies & Imports', desc: 'Standard library vs external packages extracted directly from imports.' },
      { title: 'Architecture Overview', desc: 'System structure, data flows, and module interactions.' }
    ]
  },
  'Complete README': {
    badge: 'README Only',
    summary: 'A standalone production README.md ready to commit to your repository.',
    items: [
      { title: 'Title & High-Level Summary', desc: 'Clear statement of project purpose and capabilities.' },
      { title: 'Technology Stack', desc: 'Programming languages, standard modules, and core dependencies.' },
      { title: 'Prerequisites & Installation', desc: 'Setup steps, environment requirements, and start commands.' },
      { title: 'Configuration & Environment', desc: 'Configuration parameters, file storage paths, or runtime flags.' },
      { title: 'Quickstart & Code Examples', desc: 'Practical walkthroughs demonstrating real entrypoints.' }
    ]
  },
  'Function documentation': {
    badge: 'Functions',
    summary: 'Focused technical reference for every standalone function and method in your source.',
    items: [
      { title: 'Signature & Parameters', desc: 'Exact parameter names, types (if detectable), and default values.' },
      { title: 'Return Contracts', desc: 'Return types and structures strictly matched to the code implementation.' },
      { title: 'Exceptions & Error Paths', desc: 'Documented exceptions that the function may raise.' },
      { title: 'Invocation Examples', desc: 'Targeted code snippets demonstrating how each function is called.' }
    ]
  },
  'Class documentation': {
    badge: 'Classes',
    summary: 'Object-oriented breakdown of data structures, properties, and methods.',
    items: [
      { title: 'Class Purpose & Hierarchy', desc: 'Inheritance, interfaces, and primary responsibility of each class.' },
      { title: 'Instance Attributes', desc: 'Object state initialized in constructors or attributes.' },
      { title: 'Method Dictionary', desc: 'Public and helper methods with parameter breakdown.' }
    ]
  },
  'API documentation': {
    badge: 'API Contract',
    summary: 'Public API interface documentation and payload specification.',
    items: [
      { title: 'Public Endpoints & Interfaces', desc: 'Exposed callable routes and interface methods.' },
      { title: 'Request & Input Schemas', desc: 'Accepted parameters, required types, and body structures.' },
      { title: 'Response & Status Formats', desc: 'Returned entities, dictionaries, and result structures.' }
    ]
  }
};

export async function renderPlayground(container) {
  let draft = null;
  if (!state.currentProject) {
    try {
      const raw = sessionStorage.getItem('df_playground_draft');
      if (raw) draft = JSON.parse(raw);
    } catch (e) {}
  }

  const p = state.currentProject || {
    id: null,
    name: draft?.name || '',
    language: draft?.language || state.defaultLang || 'Python',
    description: draft?.description || '',
    doc_type: draft?.doc_type || state.defaultDocType || 'Complete technical documentation',
    code: ''
  };

  // Parse in-memory files from project code if present
  let uploadedFiles = draft?.uploadedFiles || [];
  let initialPastedCode = draft?.pastedCode || '';
  let inputMode = draft?.inputMode || (uploadedFiles.length ? 'upload' : (initialPastedCode ? 'paste' : 'upload'));

  if (p.code) {
    const delimRegex = /<<<DOCUFORGE:FILE_NAME="([^"]+)">>>\n([\s\S]*?)<<<DOCUFORGE:END_FILE>>>/g;
    let match;
    while ((match = delimRegex.exec(p.code)) !== null) {
      uploadedFiles.push({
        name: match[1],
        content: match[2],
        size: new Blob([match[2]]).size
      });
    }
    // Backward compatibility with legacy format
    if (uploadedFiles.length === 0 && p.code.startsWith('# FILE: ')) {
      const parts = p.code.split('# FILE: ').filter(Boolean);
      uploadedFiles = parts.map(part => {
        const firstLineEnd = part.indexOf('\n');
        const name = part.substring(0, firstLineEnd).trim();
        const content = part.substring(firstLineEnd + 1);
        return { name, content, size: new Blob([content]).size };
      });
    }

    if (uploadedFiles.length === 0 && p.code.trim()) {
      initialPastedCode = p.code;
      inputMode = 'paste';
    }
  }

  container.innerHTML = `
    ${renderNavbar('/playground')}
    <main class="df-page" id="main-content">
      <div style="margin-bottom: 28px;">
        <h1 class="df-title-xl">Let's document your code.</h1>
        <p class="df-lead">Provide your source code and let DocuForge AI turn it into structured technical documentation.</p>
      </div>

      <div class="df-playground-grid" id="df-playground-grid">
        <!-- Left: Code Input & Configuration -->
        <div class="df-card">
          <h2 class="df-title-md" style="margin-bottom: 18px;">Source Code & Configuration</h2>

          <div class="df-grid-2col">
            <div class="df-field-group">
              <label class="df-label" for="df-pname">Project Name *</label>
              <input class="df-input" id="df-pname" value="${escapeHtml(p.name)}" placeholder="e.g. auth-service" maxlength="80">
            </div>
            <div class="df-field-group">
              <label class="df-label" for="df-plang">Language</label>
              <select class="df-select" id="df-plang">
                ${LANGS.map(l => `<option value="${l}" ${l === p.language ? 'selected' : ''}>${l}</option>`).join('')}
                <option value="Mixed" ${p.language === 'Mixed' ? 'selected' : ''}>Mixed</option>
              </select>
            </div>
          </div>

          <div class="df-field-group">
            <label class="df-label" for="df-ptype">Documentation Type</label>
            <select class="df-select" id="df-ptype">
              ${DOC_TYPES.map(t => `<option value="${t}" ${t === p.doc_type ? 'selected' : ''}>${t}</option>`).join('')}
            </select>
          </div>

          <div class="df-field-group" style="margin-bottom: 20px;">
            <label class="df-label" for="df-pdesc">Short Description (optional)</label>
            <input class="df-input" id="df-pdesc" value="${escapeHtml(p.description)}" placeholder="What does this codebase do?">
          </div>

          <!-- Segmented Control: Upload files vs Paste code -->
          <div class="df-segmented" id="df-input-mode-segmented">
            <button type="button" class="df-segmented-btn ${inputMode === 'upload' ? 'active' : ''}" data-mode="upload" id="df-btn-mode-upload">
              ${icons.upload(14)} Upload files
            </button>
            <button type="button" class="df-segmented-btn ${inputMode === 'paste' ? 'active' : ''}" data-mode="paste" id="df-btn-mode-paste">
              ${icons.code(14)} Paste code
            </button>
          </div>

          <!-- Mode 1: Upload Files Pane -->
          <div id="df-view-upload" style="${inputMode === 'upload' ? '' : 'display: none;'}">
            <!-- Drag and Drop Upload Zone -->
            <div id="df-dropzone" style="border: 2px dashed var(--border-default); border-radius: var(--r-md); padding: 22px; text-align: center; cursor: pointer; margin-bottom: 16px; transition: border-color var(--trans-fast), background-color var(--trans-fast);">
              <div id="df-dropzone-status" style="display: none; font-size: var(--fs-sm); color: var(--accent); font-family: var(--font-mono);">
                ${icons.spinner(16)} Reading and validating files...
              </div>
              <div id="df-dropzone-prompt">
                <div style="color: var(--text-tertiary); margin-bottom: 6px;">${icons.upload(24)}</div>
                <div style="font-size: var(--fs-sm); font-weight: 600;">Drop source files or a ZIP archive here</div>
                <div class="df-sub" style="margin-top: 2px;">Supports .py, .js, .ts, .java, .go, .c, .cpp, .php, .rb, .rs, .html, .css, .sql, .yml, .sh (ZIPs up to 5 MB)</div>
              </div>
              <input type="file" id="df-file-input" multiple hidden>
            </div>

            <!-- Skipped Files Neutral Notice Banner -->
            <div id="df-skipped-notice" class="df-banner-notice" style="display: none;">
              <span style="color: var(--accent); flex-shrink: 0; margin-top: 1px;">${icons.alert(16)}</span>
              <div id="df-skipped-notice-text"></div>
            </div>

            <!-- Uploaded Files List -->
            <div id="df-files-container" class="df-file-list" style="${uploadedFiles.length ? '' : 'display: none;'}"></div>
          </div>

          <!-- Mode 2: Paste Code Pane -->
          <div id="df-view-paste" style="${inputMode === 'paste' ? '' : 'display: none;'}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
              <label class="df-label" style="margin: 0;">Code Editor *</label>
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button type="button" class="df-btn df-btn-sm" id="df-btn-sample">${icons.fileText(13)} Load Sample</button>
                <button type="button" class="df-btn df-btn-sm" id="df-btn-clear">${icons.trash(13)} Clear</button>
              </div>
            </div>

            <div class="df-editor-wrapper">
              <div class="df-line-numbers" id="df-line-numbers">1</div>
              <textarea class="df-editor-textarea" id="df-pcode" placeholder="Paste source code here..." spellcheck="false">${escapeHtml(initialPastedCode)}</textarea>
            </div>
          </div>

          <!-- Code Stats -->
          <div id="df-code-stats" class="df-sub df-mono" style="font-size: 11px; margin-top: 8px; text-align: right; color: var(--text-tertiary);">
            0 lines &middot; 0 B
          </div>

          <!-- Action Button & Quota Indicator -->
          <div style="margin-top: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
              <span class="df-sub df-mono" id="df-quota-badge" style="font-size: var(--fs-xs); display: inline-flex; align-items: center; gap: 4px;">
                Checking usage quota...
              </span>
              <span class="df-sub df-mono" id="df-quota-reset" style="font-size: var(--fs-xs); color: var(--text-tertiary); display: none;"></span>
            </div>
            <button class="df-btn df-btn-primary df-btn-lg" id="df-btn-run" style="width: 100%;" disabled>
              Run AI Analysis & Generate ${icons.arrowRight(16)}
            </button>
            <div id="df-run-hint" class="df-sub" style="margin-top: 8px; text-align: center; font-size: var(--fs-xs);">
              Enter a project name and provide source code to begin.
            </div>
          </div>
        </div>

        <!-- Right: Scope Specification Preview -->
        <div class="df-card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <h2 class="df-title-md" style="margin: 0;">Output Scope</h2>
            <span class="df-badge df-badge-documented" id="df-scope-badge">All 7 Sections</span>
          </div>
          <p class="df-sub" id="df-scope-desc" style="margin-bottom: 20px;">
            Every generated section is strictly rooted in the source code provided without hallucinated features or fabricated APIs.
          </p>

          <div id="df-sections-preview" style="display: flex; flex-direction: column; gap: 10px;"></div>
        </div>
      </div>
    </main>
  `;

  // DOM Elements
  const segmented = document.getElementById('df-input-mode-segmented');
  const btnModeUpload = document.getElementById('df-btn-mode-upload');
  const btnModePaste = document.getElementById('df-btn-mode-paste');
  const viewUpload = document.getElementById('df-view-upload');
  const viewPaste = document.getElementById('df-view-paste');

  const dropzone = document.getElementById('df-dropzone');
  const dropzonePrompt = document.getElementById('df-dropzone-prompt');
  const dropzoneStatus = document.getElementById('df-dropzone-status');
  const fileInput = document.getElementById('df-file-input');
  const filesContainer = document.getElementById('df-files-container');
  const skippedNotice = document.getElementById('df-skipped-notice');
  const skippedNoticeText = document.getElementById('df-skipped-notice-text');

  const codeArea = document.getElementById('df-pcode');
  const lineNumbers = document.getElementById('df-line-numbers');
  const nameInput = document.getElementById('df-pname');
  const langSelect = document.getElementById('df-plang');
  const descInput = document.getElementById('df-pdesc');
  const typeSelect = document.getElementById('df-ptype');
  const runBtn = document.getElementById('df-btn-run');
  const runHint = document.getElementById('df-run-hint');
  const statsEl = document.getElementById('df-code-stats');
  const quotaBadge = document.getElementById('df-quota-badge');
  const quotaReset = document.getElementById('df-quota-reset');

  let quotaState = null;
  let rateLimitTimer = null;
  let rateLimitSecondsLeft = 0;
  let rateLimitMessage = '';

  function formatCountdown(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  function startRateLimitCountdown(seconds, msg = '') {
    if (rateLimitTimer) clearInterval(rateLimitTimer);
    rateLimitSecondsLeft = Math.max(1, Math.ceil(seconds));
    rateLimitMessage = msg;
    updateRateLimitUI();

    rateLimitTimer = setInterval(() => {
      rateLimitSecondsLeft -= 1;
      if (rateLimitSecondsLeft <= 0) {
        clearInterval(rateLimitTimer);
        rateLimitTimer = null;
        rateLimitSecondsLeft = 0;
        rateLimitMessage = '';
        loadQuotaUsage();
      } else {
        updateRateLimitUI();
      }
    }, 1000);
  }

  function updateRateLimitUI() {
    if (rateLimitSecondsLeft > 0) {
      runBtn.disabled = true;
      runBtn.innerHTML = `${icons.clock(16)} Limit reached. Resets in ${formatCountdown(rateLimitSecondsLeft)}`;
      runHint.textContent = rateLimitMessage || `Hourly generation limit reached. Resets in ${formatCountdown(rateLimitSecondsLeft)}.`;
      runHint.style.color = 'var(--accent)';
      if (quotaReset) {
        quotaReset.style.display = 'inline';
        quotaReset.textContent = `Resets in ${formatCountdown(rateLimitSecondsLeft)}`;
      }
    } else {
      runBtn.innerHTML = `Run AI Analysis & Generate ${icons.arrowRight(16)}`;
      if (quotaReset) quotaReset.style.display = 'none';
      checkValid();
    }
  }

  async function loadQuotaUsage() {
    try {
      const usage = await api.getUsage();
      quotaState = usage;
      if (!usage.rate_limiting_enabled) {
        if (quotaBadge) quotaBadge.innerHTML = `${icons.check(12)} Quota protection active`;
        return;
      }

      const hourlyRem = usage.generations?.hourly_remaining ?? 0;
      const hourlyLim = usage.generations?.hourly_limit ?? 5;
      const resetSec = usage.generations?.hourly_reset_seconds ?? 0;

      if (quotaBadge) {
        if (hourlyRem <= 0) {
          quotaBadge.innerHTML = `<span style="color: var(--status-err);">${icons.alert(12)} 0 of ${hourlyLim} generations left this hour</span>`;
        } else {
          quotaBadge.innerHTML = `${icons.sparkle(12)} ${hourlyRem} of ${hourlyLim} generations left this hour`;
        }
      }

      if (!usage.service_available) {
        startRateLimitCountdown(60, 'Service is temporarily busy under heavy traffic. Please wait.');
      } else if (hourlyRem <= 0 && resetSec > 0) {
        startRateLimitCountdown(resetSec, `Hourly generation limit reached (${hourlyLim}/${hourlyLim}). Resets in ${formatCountdown(resetSec)}.`);
      } else if (rateLimitSecondsLeft <= 0) {
        checkValid();
      }
    } catch (e) {
      console.error("loadQuotaUsage error:", e);
      if (quotaBadge) quotaBadge.textContent = 'Quota monitoring active';
    }
  }

  const sectionsPreview = document.getElementById('df-sections-preview');
  const scopeBadge = document.getElementById('df-scope-badge');
  const scopeDesc = document.getElementById('df-scope-desc');

  // Mode switching
  function setInputMode(mode) {
    inputMode = mode;
    btnModeUpload.classList.toggle('active', mode === 'upload');
    btnModePaste.classList.toggle('active', mode === 'paste');
    viewUpload.style.display = mode === 'upload' ? 'block' : 'none';
    viewPaste.style.display = mode === 'paste' ? 'block' : 'none';
    saveDraft();
    checkValid();
  }

  function saveDraft() {
    if (state.currentProject) return;
    const draftData = {
      name: nameInput.value,
      language: langSelect.value,
      description: descInput.value,
      doc_type: typeSelect.value,
      inputMode: inputMode,
      pastedCode: codeArea.value,
      uploadedFiles: uploadedFiles
    };
    try {
      sessionStorage.setItem('df_playground_draft', JSON.stringify(draftData));
    } catch (e) {}
  }

  btnModeUpload.onclick = () => setInputMode('upload');
  btnModePaste.onclick = () => setInputMode('paste');

  // Sync line numbers in paste editor
  function updateLineNumbers() {
    const text = codeArea.value || '';
    const lines = text.split('\n').length;
    let numbers = '';
    for (let i = 1; i <= lines; i++) {
      numbers += i + '\n';
    }
    lineNumbers.textContent = numbers.trimEnd();
  }

  codeArea.addEventListener('input', () => {
    updateLineNumbers();
    checkValid();
  });

  codeArea.addEventListener('scroll', () => {
    lineNumbers.scrollTop = codeArea.scrollTop;
  });

  codeArea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = codeArea.selectionStart;
      const end = codeArea.selectionEnd;
      codeArea.value = codeArea.value.substring(0, start) + '    ' + codeArea.value.substring(end);
      codeArea.selectionStart = codeArea.selectionEnd = start + 4;
      updateLineNumbers();
      checkValid();
    }
  });

  // Detect language from uploaded files
  function detectLanguageFromFiles() {
    if (!uploadedFiles.length) return;
    const detected = new Set();
    for (const f of uploadedFiles) {
      const ext = f.name.includes('.') ? f.name.split('.').pop().toLowerCase() : '';
      if (EXT_TO_LANG[ext]) {
        detected.add(EXT_TO_LANG[ext]);
      }
    }
    const detectedArray = Array.from(detected).filter(l => l !== 'Other');
    if (detectedArray.length === 1) {
      langSelect.value = detectedArray[0];
    } else if (detectedArray.length > 1) {
      langSelect.value = 'Mixed';
    } else if (detected.has('Other')) {
      langSelect.value = 'Other';
    }
  }

  function renderFileList() {
    if (!uploadedFiles.length) {
      filesContainer.style.display = 'none';
      filesContainer.innerHTML = '';
      return;
    }
    filesContainer.style.display = 'flex';
    filesContainer.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
        <span class="df-sub" style="font-weight: 600; font-size: 11px; text-transform: uppercase;">
          Loaded Source Files (${uploadedFiles.length})
        </span>
        <button type="button" class="df-btn df-btn-ghost df-btn-sm" id="df-clear-files" style="font-size: 11px; padding: 2px 6px;">
          Remove All
        </button>
      </div>
      ${uploadedFiles.map((f, idx) => `
        <div class="df-file-item">
          <div class="df-file-info">
            <span style="color: var(--accent);">${icons.fileText(14)}</span>
            <span class="df-file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
            <span class="df-file-size">(${formatBytes(f.size)})</span>
          </div>
          <button type="button" class="df-file-remove" data-idx="${idx}" title="Remove file">${icons.close(14)}</button>
        </div>
      `).join('')}
    `;

    filesContainer.querySelectorAll('.df-file-remove').forEach(b => {
      b.onclick = (e) => {
        e.stopPropagation();
        const idx = parseInt(b.dataset.idx, 10);
        uploadedFiles.splice(idx, 1);
        renderFileList();
        detectLanguageFromFiles();
        checkValid();
      };
    });

    const clearAll = document.getElementById('df-clear-files');
    if (clearAll) {
      clearAll.onclick = () => {
        uploadedFiles = [];
        renderFileList();
        checkValid();
      };
    }
  }

  function updateOutputScope() {
    const docType = typeSelect.value;
    const config = OUTPUT_SCOPE_CONFIG[docType] || OUTPUT_SCOPE_CONFIG['Complete technical documentation'];

    scopeBadge.textContent = config.badge;
    scopeDesc.textContent = config.summary;

    sectionsPreview.innerHTML = config.items.map(item => `
      <div style="padding: 12px 14px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md);">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: var(--accent);">${icons.fileText(14)}</span>
            <b style="font-size: var(--fs-xs); color: var(--text-primary);">${escapeHtml(item.title)}</b>
          </div>
          <span class="df-badge" style="font-size: 10px;">Will Generate</span>
        </div>
        <div class="df-sub" style="font-size: 12px; line-height: 1.45; margin-left: 22px;">
          ${escapeHtml(item.desc)}
        </div>
      </div>
    `).join('');
  }

  function getCombinedCode() {
    if (inputMode === 'upload') {
      if (uploadedFiles.length === 0) return '';
      return uploadedFiles.map(f => `<<<DOCUFORGE:FILE_NAME="${f.name}">>>\n${f.content}\n<<<DOCUFORGE:END_FILE>>>`).join('\n\n');
    } else {
      return codeArea.value.trim();
    }
  }

  function checkValid() {
    if (rateLimitSecondsLeft > 0) {
      runBtn.disabled = true;
      runBtn.innerHTML = `${icons.clock(16)} Limit reached. Resets in ${formatCountdown(rateLimitSecondsLeft)}`;
      runHint.textContent = rateLimitMessage || `Hourly limit reached. Resets in ${formatCountdown(rateLimitSecondsLeft)}.`;
      runHint.style.color = 'var(--accent)';
      saveDraft();
      return;
    }

    const hasName = Boolean(nameInput.value.trim());
    let totalBytes = 0;
    let totalLines = 0;

    if (inputMode === 'upload') {
      totalBytes = uploadedFiles.reduce((acc, f) => acc + f.size, 0);
      totalLines = uploadedFiles.reduce((acc, f) => acc + (f.content ? f.content.split('\n').length : 0), 0);
    } else {
      const codeVal = codeArea.value;
      totalBytes = new Blob([codeVal]).size;
      totalLines = codeVal ? codeVal.split('\n').length : 0;
    }

    const hasContent = inputMode === 'upload' ? uploadedFiles.length > 0 : Boolean(codeArea.value.trim());
    const isTooLarge = totalBytes > 150_000;

    statsEl.textContent = `${totalLines} line${totalLines === 1 ? '' : 's'} · ${formatBytes(totalBytes)}` + (inputMode === 'upload' ? ` (${uploadedFiles.length} file${uploadedFiles.length === 1 ? '' : 's'})` : '');

    if (isTooLarge) {
      runBtn.disabled = true;
      runHint.textContent = `Code size (${formatBytes(totalBytes)}) exceeds 150 KB limit. Please reduce code or split files.`;
      runHint.style.color = 'var(--status-err)';
      return;
    }

    runHint.style.color = 'var(--text-secondary)';
    if (!hasName && !hasContent) {
      runBtn.disabled = true;
      runHint.textContent = 'Enter a project name and provide source code to begin.';
    } else if (!hasName) {
      runBtn.disabled = true;
      runHint.textContent = 'Enter a project name to continue.';
    } else if (!hasContent) {
      runBtn.disabled = true;
      runHint.textContent = inputMode === 'upload' ? 'Upload at least one source file to continue.' : 'Paste source code to continue.';
    } else {
      runBtn.disabled = false;
      runHint.textContent = 'Ready to analyze. Click button to begin.';
    }

    saveDraft();
  }

  nameInput.oninput = checkValid;
  descInput.oninput = saveDraft;
  langSelect.onchange = saveDraft;
  typeSelect.onchange = () => {
    updateOutputScope();
    saveDraft();
  };

  document.getElementById('df-btn-sample').onclick = () => {
    setInputMode('paste');
    codeArea.value = SAMPLE_CODE;
    updateLineNumbers();
    langSelect.value = 'Python';
    if (!nameInput.value.trim()) nameInput.value = 'todo-store';
    checkValid();
    showToast('Loaded sample Python codebase');
  };

  document.getElementById('df-btn-clear').onclick = () => {
    codeArea.value = '';
    uploadedFiles = [];
    sessionStorage.removeItem('df_playground_draft');
    updateLineNumbers();
    renderFileList();
    checkValid();
  };

  // Upload handling
  dropzone.onclick = () => fileInput.click();
  dropzone.ondragover = (e) => {
    e.preventDefault();
    dropzone.style.borderColor = 'var(--accent)';
    dropzone.style.backgroundColor = 'var(--accent-dim)';
  };
  dropzone.ondragleave = () => {
    dropzone.style.borderColor = 'var(--border-default)';
    dropzone.style.backgroundColor = 'transparent';
  };
  dropzone.ondrop = async (e) => {
    e.preventDefault();
    dropzone.style.borderColor = 'var(--border-default)';
    dropzone.style.backgroundColor = 'transparent';
    if (e.dataTransfer.files.length) {
      await handleUpload(e.dataTransfer.files);
    }
  };

  fileInput.onchange = async () => {
    if (fileInput.files.length) {
      await handleUpload(fileInput.files);
    }
  };

  async function handleUpload(files) {
    skippedNotice.style.display = 'none';
    skippedNoticeText.innerHTML = '';

    try {
      if (dropzonePrompt) dropPromptVisible(false);

      const res = await api.uploadFiles(files);
      
      // Keep per-file state from backend response without parsing headers
      if (res.files && Array.isArray(res.files)) {
        uploadedFiles = res.files;
      }

      if (!nameInput.value.trim() && files.length > 0) {
        const first = files[0].name.replace(/\.[^.]+$/, '');
        nameInput.value = first.replace(/[_\s]+/g, '-').toLowerCase();
      }

      renderFileList();
      detectLanguageFromFiles();
      checkValid();

      // Neutral notice for skipped files
      if (res.skipped && res.skipped.length > 0) {
        skippedNotice.style.display = 'flex';
        const skippedListHtml = res.skipped.map(s => `
          <div>&bull; <b>${escapeHtml(s.name)}</b>: ${escapeHtml(s.reason)}</div>
        `).join('');
        skippedNoticeText.innerHTML = `
          <div style="font-weight: 600; margin-bottom: 4px; color: var(--text-primary);">
            File Notice (${res.skipped.length} skipped)
          </div>
          <div style="font-size: 12px; line-height: 1.5; color: var(--text-secondary);">
            ${skippedListHtml}
          </div>
          <div style="font-size: 11px; margin-top: 4px; color: var(--text-tertiary);">
            Secret credential files (.env*, keys, certs) and binaries are denied for security and never sent to Gemini.
          </div>
        `;
      }

      showToast(`Loaded ${uploadedFiles.length} source file(s)`);
    } catch (err) {
      skippedNotice.style.display = 'flex';
      skippedNoticeText.innerHTML = `
        <div style="font-weight: 600; color: var(--status-err); margin-bottom: 2px;">Upload Notice</div>
        <div style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(err.message || 'File upload failed.')}</div>
      `;
      showToast(err.message, true);
    } finally {
      if (dropzonePrompt) dropPromptVisible(true);
      fileInput.value = '';
    }
  }

  function dropPromptVisible(show) {
    if (dropzonePrompt) dropzonePrompt.style.display = show ? 'block' : 'none';
    if (dropzoneStatus) dropzoneStatus.style.display = show ? 'none' : 'block';
  }

  runBtn.onclick = async () => {
    try {
      runBtn.disabled = true;
      runBtn.innerHTML = `${icons.spinner(16)} Preparing analysis...`;

      const finalCode = getCombinedCode();

      // 1. Save or update project in SQLite backend
      const projectData = {
        name: nameInput.value.trim(),
        language: langSelect.value,
        description: descInput.value.trim(),
        doc_type: typeSelect.value,
        code: finalCode
      };

      let project;
      if (p.id) {
        project = await api.updateProject(p.id, projectData);
      } else {
        project = await api.createProject(projectData);
      }
      setCurrentProject(project);

      // 2. Spawn backend generation job
      const job = await api.createJob(project.id);
      setActiveJob(job);

      // 3. Navigate to processing view
      sessionStorage.removeItem('df_playground_draft');
      navigate(`/processing?job_id=${job.id}`);
    } catch (err) {
      if (err.status === 429) {
        const retrySec = err.retryAfter || (err.data && err.data.retry_after_seconds) || 60;
        const scope = (err.data && err.data.scope) || 'user';
        const msg = err.message || (scope === 'global' ? 'Service is busy under heavy load. Please retry shortly.' : 'You have reached your request limit.');
        showToast(msg, true);
        startRateLimitCountdown(retrySec, msg);
      } else {
        showToast(err.message, true);
        runBtn.disabled = false;
        runBtn.innerHTML = `Run AI Analysis & Generate ${icons.arrowRight(16)}`;
        checkValid();
      }
    }
  };

  // Initial render
  updateLineNumbers();
  renderFileList();
  updateOutputScope();
  checkValid();
  loadQuotaUsage();
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
