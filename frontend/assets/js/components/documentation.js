/**
 * DocuForge AI — Documentation Results Workspace (/documentation)
 * Left Sidebar Outline, In-document Anchors, Markdown Renderer, Edit/Preview,
 * Copy, Regenerate Section, Download Markdown, and PDF Export.
 * Source Scope with File Count and Collapsible File List,
 * Responsive Mobile Tabs Bar for <= 768px.
 */

import { state, setCurrentProject, SECTIONS_META } from '../state.js';
import { api, showToast } from '../api.js';
import { navigate, renderNavbar } from '../router.js';
import { icons } from '../icons.js';

export async function renderDocumentation(container, params) {
  const urlParams = params || new URLSearchParams(window.location.search);
  const pid = urlParams.get('project_id') || sessionStorage.getItem('df_active_project_id');

  // Guard: Redirect to projects if no project selected
  if (!pid) {
    navigate('/projects', true);
    return;
  }

  let project = state.projects.find(p => String(p.id) === String(pid));
  if (!project) {
    try {
      project = await api.getProject(pid);
      setCurrentProject(project);
    } catch (e) {
      showToast('Project not found in database', true);
      navigate('/projects', true);
      return;
    }
  }

  const tabParam = urlParams.get('tab');
  const initialHash = (window.location.hash || '').replace('#', '').toLowerCase();
  let currentTab = (tabParam && SECTIONS_META[tabParam]) ? tabParam : ((initialHash && SECTIONS_META[initialHash]) ? initialHash : 'readme');
  let isEditing = false;

  function extractFiles(code, projectName, projectLang) {
    if (!code) return [];
    const files = [];
    const delimRegex = /<<<DOCUFORGE:FILE_NAME="([^"]+)">>>\n([\s\S]*?)<<<DOCUFORGE:END_FILE>>>/g;
    let match;
    while ((match = delimRegex.exec(code)) !== null) {
      files.push({
        name: match[1],
        size: new Blob([match[2]]).size
      });
    }
    if (files.length === 0 && code.includes('# FILE: ')) {
      const parts = code.split('# FILE: ').filter(Boolean);
      parts.forEach(part => {
        const firstLineEnd = part.indexOf('\n');
        const name = part.substring(0, firstLineEnd).trim();
        const content = part.substring(firstLineEnd + 1);
        files.push({ name, size: new Blob([content]).size });
      });
    }
    if (files.length === 0 && code.trim()) {
      const extMap = {
        Python: '.py', JavaScript: '.js', TypeScript: '.ts', Java: '.java',
        Go: '.go', Rust: '.rs', C: '.c', 'C++': '.cpp', PHP: '.php', Ruby: '.rb'
      };
      const ext = extMap[projectLang] || '.txt';
      const fallbackName = (projectName || 'source').replace(/\s+/g, '-').toLowerCase() + ext;
      files.push({
        name: fallbackName,
        size: new Blob([code]).size
      });
    }
    return files;
  }

  function renderWorkspace() {
    const docs = project.docs || {};
    const content = docs[currentTab] || '_Not generated yet. Click "Regenerate Tab" to create this section._';
    const sourceFiles = extractFiles(project.code, project.name, project.language);
    const totalSourceBytes = new Blob([project.code || '']).size;

    // Parse in-document headings for anchor navigation
    const headingMatches = [];
    const lines = content.split('\n');
    lines.forEach((line) => {
      const match = line.match(/^(#{1,3})\s+(.+)$/);
      if (match) {
        const level = match[1].length;
        const text = match[2].trim();
        const slug = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
        headingMatches.push({ level, text, slug });
      }
    });

    container.innerHTML = `
      ${renderNavbar('/documentation')}
      <main class="df-page" id="main-content" style="max-width: 1380px;">
        <!-- Top Workspace Toolbar -->
        <div class="df-workspace-toolbar" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 14px; padding-bottom: 16px; border-bottom: 1px solid var(--border-subtle);">
          <div style="min-width: 0;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
              <h1 class="df-title-lg" style="margin: 0; overflow-wrap: anywhere;">${escapeHtml(project.name)}</h1>
              <span class="df-badge ${project.status === 'Documented' ? 'df-badge-documented' : 'df-badge-draft'}">
                ${project.status === 'Documented' ? `${icons.check(12)} Documented` : 'Draft'}
              </span>
              <span class="df-badge" style="background: var(--bg-surface-elevated);">${escapeHtml(project.language)}</span>
              <span class="df-sub" style="font-size: var(--fs-xs);">${escapeHtml(project.doc_type || 'Complete technical documentation')}</span>
            </div>
            <div class="df-sub" style="margin-top: 4px; font-size: var(--fs-xs);">
              Last modified ${new Date(project.updated || Date.now()).toLocaleString()}
            </div>
          </div>

          <!-- Actions Toolbar -->
          <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            <button type="button" class="df-btn df-btn-sm" id="df-btn-copy" title="Copy active section markdown">
              ${icons.copy(14)} Copy
            </button>
            <button type="button" class="df-btn df-btn-sm" id="df-btn-edit">
              ${isEditing ? `${icons.fileText(14)} Preview` : `${icons.edit(14)} Edit Markdown`}
            </button>
            ${isEditing ? `
              <button type="button" class="df-btn df-btn-sm df-btn-primary" id="df-btn-save">
                ${icons.check(14)} Save Changes
              </button>
              <button type="button" class="df-btn df-btn-sm df-btn-ghost" id="df-btn-cancel-edit">
                Cancel
              </button>
            ` : ''}
            <button type="button" class="df-btn df-btn-sm" id="df-btn-regen" title="Re-run AI generation for this section only">
              ${icons.refresh(14)} Regenerate Tab
            </button>
            <button type="button" class="df-btn df-btn-sm" id="df-btn-download" title="Download as .md file">
              ${icons.download(14)} ${currentTab === 'readme' ? 'README.md' : 'Markdown'}
            </button>
            <button type="button" class="df-btn df-btn-sm" id="df-btn-print" title="Export clean printable PDF">
              Export PDF
            </button>
          </div>
        </div>

        <!-- Mobile Horizontal Tab Bar for screens <= 768px -->
        <div class="df-doc-mobile-tabs" id="df-doc-mobile-tabs">
          ${Object.entries(SECTIONS_META).map(([key, label]) => {
            const isActive = currentTab === key;
            const hasContent = Boolean(docs[key] && !docs[key].includes('_Not generated'));
            return `
              <button type="button" class="df-doc-mobile-tab-btn ${isActive ? 'active' : ''}" data-key="${key}">
                <span>${label}</span>
                ${hasContent ? `<span style="font-size: 10px;">${icons.check(10)}</span>` : ''}
              </button>
            `;
          }).join('')}
        </div>

        <div class="df-workspace-grid" style="display: grid; grid-template-columns: 280px 1fr; gap: 24px; align-items: start;">
          <!-- Left Sidebar: Outline Navigation & In-Document Anchors -->
          <div class="df-doc-sidebar" style="position: sticky; top: 80px; display: flex; flex-direction: column; gap: 14px;">
            <div class="df-card" style="padding: 14px;">
              <div class="df-sub" style="font-weight: 650; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px; margin-bottom: 12px; color: var(--text-tertiary);">
                Sections
              </div>
              <div style="display: flex; flex-direction: column; gap: 3px;">
                ${Object.entries(SECTIONS_META).map(([key, label]) => {
                  const isActive = currentTab === key;
                  const hasContent = Boolean(docs[key] && !docs[key].includes('_Not generated'));
                  return `
                    <button type="button" class="df-btn df-btn-ghost df-btn-sm df-tab-btn df-doc-nav-item" data-key="${key}" style="justify-content: space-between; text-align: left; padding: 8px 12px; ${isActive ? 'background: var(--bg-surface-active); color: var(--text-primary); font-weight: 600; border-left: 2px solid var(--accent);' : ''}">
                      <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: ${isActive ? 'var(--accent)' : 'var(--text-tertiary)'};">${icons.fileText(14)}</span>
                        <span>${label}</span>
                      </div>
                      ${hasContent ? `<span style="color: var(--status-ok); font-size: 11px;">${icons.check(12)}</span>` : ''}
                    </button>
                  `;
                }).join('')}
              </div>
            </div>

            <!-- In-document Outline (if headings exist) -->
            ${headingMatches.length > 0 && !isEditing ? `
              <div class="df-card" id="df-doc-outline-card" style="padding: 16px;">
                <div class="df-outline-title" style="font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; font-size: 11px; margin-bottom: 10px; color: var(--text-tertiary); line-height: 1.4;">
                  In-Section Outline
                </div>
                <div class="df-doc-outline-list">
                  ${headingMatches.map(h => `
                    <a href="#df-h-${h.slug}" class="df-doc-anchor" style="margin-left: ${(h.level - 1) * 12}px;" title="${escapeHtml(h.text)}">
                      <span class="df-doc-anchor-bullet" style="color: ${h.level === 1 ? 'var(--accent)' : 'var(--text-tertiary)'}; font-size: ${h.level === 1 ? '8px' : '6px'}; line-height: 1; flex-shrink: 0; opacity: 0.85;">●</span>
                      <span class="df-doc-anchor-text">${escapeHtml(h.text)}</span>
                    </a>
                  `).join('')}
                </div>
              </div>
            ` : ''}

            <!-- Source Code Reference Card with File Count and Collapsible List -->
            <div class="df-card" style="padding: 14px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span class="df-sub" style="font-weight: 650; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px; color: var(--text-tertiary);">
                  Source Scope (${sourceFiles.length} file${sourceFiles.length === 1 ? '' : 's'})
                </span>
                <a href="/playground" class="df-sub" data-link style="font-size: 11px; color: var(--accent);">Edit Code</a>
              </div>
              <div class="df-sub" style="font-size: 12px; margin-bottom: 8px;">
                ${escapeHtml(project.language)} &middot; ${formatBytes(totalSourceBytes)}
              </div>
              <details class="df-source-scope-details" style="font-size: 12px; color: var(--text-secondary);">
                <summary style="cursor: pointer; color: var(--accent); font-weight: 550; outline: none; margin-bottom: 6px;">
                  View file list (${sourceFiles.length})
                </summary>
                <div style="display: flex; flex-direction: column; gap: 4px; max-height: 160px; overflow-y: auto;">
                  ${sourceFiles.map(f => `
                    <div style="display: flex; justify-content: space-between; gap: 6px; padding: 4px 6px; background: var(--bg-surface-elevated); border-radius: var(--r-xs); font-family: var(--font-mono); font-size: 11px;">
                      <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</span>
                      <span style="color: var(--text-tertiary); flex-shrink: 0;">${formatBytes(f.size)}</span>
                    </div>
                  `).join('')}
                </div>
              </details>
            </div>
          </div>

          <!-- Main Document Workspace Pane -->
          <div class="df-card" style="min-height: 600px; padding: 28px; min-width: 0; overflow-x: auto;">
            ${isEditing ? `
              <div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                  <b style="font-size: var(--fs-sm);">Markdown Editor — ${SECTIONS_META[currentTab]}</b>
                  <span class="df-sub" style="font-size: 12px;">Changes will be saved to your local database</span>
                </div>
                <textarea class="df-textarea df-textarea-code" id="df-editor" style="min-height: 580px; width: 100%; font-size: 13.5px; line-height: 1.65; padding: 16px;">${escapeHtml(content)}</textarea>
              </div>
            ` : `
              <div id="df-markdown-view" style="overflow-wrap: anywhere;">
                ${renderMarkdownWithAnchors(content)}
              </div>
            `}
          </div>
        </div>
      </main>
    `;

    function checkUnsavedChanges() {
      if (!isEditing) return true;
      const editor = document.getElementById('df-editor');
      if (editor && editor.value !== (project.docs?.[currentTab] || '')) {
        return confirm('You have unsaved changes in this documentation section. Discard changes?');
      }
      return true;
    }

    // Tab button handlers (Sidebar & Mobile Tabs)
    container.querySelectorAll('.df-tab-btn, .df-doc-mobile-tab-btn').forEach(b => {
      b.onclick = () => {
        if (!checkUnsavedChanges()) return;
        currentTab = b.dataset.key;
        try {
          window.history.replaceState(null, '', `${window.location.pathname}?project_id=${project.id}&tab=${currentTab}`);
        } catch (e) {}
        isEditing = false;
        renderWorkspace();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      };
    });

    // Edit button handler
    const editBtn = document.getElementById('df-btn-edit');
    if (editBtn) {
      editBtn.onclick = () => {
        if (isEditing && !checkUnsavedChanges()) return;
        isEditing = !isEditing;
        renderWorkspace();
      };
    }

    // Cancel edit button handler
    const cancelEditBtn = document.getElementById('df-btn-cancel-edit');
    if (cancelEditBtn) {
      cancelEditBtn.onclick = () => {
        if (!checkUnsavedChanges()) return;
        isEditing = false;
        renderWorkspace();
      };
    }

    // Save changes handler (persists edits)
    const saveBtn = document.getElementById('df-btn-save');
    if (saveBtn) {
      saveBtn.onclick = async () => {
        const text = document.getElementById('df-editor').value;
        project.docs = project.docs || {};
        project.docs[currentTab] = text;
        try {
          saveBtn.disabled = true;
          saveBtn.innerHTML = `${icons.spinner(14)} Saving...`;
          const updated = await api.updateProject(project.id, {
            name: project.name,
            language: project.language,
            description: project.description,
            doc_type: project.doc_type,
            code: project.code,
            docs: project.docs
          });
          project = updated;
          setCurrentProject(updated);
          isEditing = false;
          window.onbeforeunload = null;
          showToast('Changes saved successfully');
          renderWorkspace();
        } catch (e) {
          showToast(e.message, true);
          saveBtn.disabled = false;
          saveBtn.innerHTML = `${icons.check(14)} Save Changes`;
        }
      };
    }

    // Copy section handler with fallback
    const copyBtn = document.getElementById('df-btn-copy');
    if (copyBtn) {
      copyBtn.onclick = async () => {
        try {
          if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(content);
          } else {
            const ta = document.createElement('textarea');
            ta.value = content;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
          }
          showToast(`Copied ${SECTIONS_META[currentTab]} markdown to clipboard`);
        } catch (e) {
          try {
            const ta = document.createElement('textarea');
            ta.value = content;
            ta.style.position = 'fixed';
            ta.style.left = '-9999px';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
            showToast(`Copied ${SECTIONS_META[currentTab]} markdown to clipboard`);
          } catch (err2) {
            showToast('Failed to copy to clipboard', true);
          }
        }
      };
    }

    // Regenerate tab handler
    const regenBtn = document.getElementById('df-btn-regen');
    if (regenBtn) {
      regenBtn.onclick = async () => {
        try {
          regenBtn.disabled = true;
          regenBtn.innerHTML = `${icons.spinner(14)} Regenerating...`;
          const updated = await api.regenerateSection(project.id, currentTab);
          project = updated;
          setCurrentProject(updated);
          showToast(`Regenerated ${SECTIONS_META[currentTab]} section`);
        } catch (e) {
          showToast(e.message || 'Regeneration failed', true);
        } finally {
          renderWorkspace();
        }
      };
    }

    // Download Markdown handler
    const downloadBtn = document.getElementById('df-btn-download');
    if (downloadBtn) {
      downloadBtn.onclick = () => {
        const filename = currentTab === 'readme' ? 'README.md' : `${project.name}-${currentTab}.md`;
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          a.remove();
          URL.revokeObjectURL(url);
        }, 1500);
        showToast(`Downloaded ${filename}`);
      };
    }

    // Export PDF handler
    const printBtn = document.getElementById('df-btn-print');
    if (printBtn) {
      printBtn.onclick = () => {
        window.print();
      };
    }

    // Anchor smooth scroll handlers
    container.querySelectorAll('.df-doc-anchor').forEach(a => {
      a.onclick = (e) => {
        e.preventDefault();
        const targetId = a.getAttribute('href').replace('#', '');
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      };
    });
  }

  renderWorkspace();
}

/**
 * Parses markdown and adds anchor IDs to headings for in-document outline
 */
function renderMarkdownWithAnchors(content) {
  if (!window.marked || !window.DOMPurify) {
    return `<pre class="df-mono">${escapeHtml(content)}</pre>`;
  }

  const renderer = new window.marked.Renderer();
  renderer.heading = function(text, level) {
    const plainText = text.replace(/<[^>]*>/g, '');
    const slug = plainText.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
    return `<h${level} id="df-h-${slug}">${text}</h${level}>`;
  };

  const rawHtml = window.marked.parse(content, { renderer });
  return window.DOMPurify.sanitize(rawHtml);
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
