/**
 * DocuForge AI — Projects Manager Component (/projects)
 * Search, Status Badges, Open in Workspace, Rename, and Delete
 */

import { state, setCurrentProject } from '../state.js';
import { api, showToast } from '../api.js';
import { navigate, renderNavbar } from '../router.js';
import { icons } from '../icons.js';

export async function renderProjects(container) {
  try {
    state.projects = await api.getProjects();
  } catch (e) {
    showToast('Failed to load projects: ' + e.message, true);
  }

  let searchQuery = '';

  function renderList() {
    const filtered = state.projects.filter(p => {
      const q = searchQuery.toLowerCase().trim();
      if (!q) return true;
      return (p.name || '').toLowerCase().includes(q) ||
             (p.language || '').toLowerCase().includes(q) ||
             (p.doc_type || '').toLowerCase().includes(q);
    });

    container.innerHTML = `
      ${renderNavbar('/projects')}
      <main class="df-page">
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; flex-wrap: wrap; gap: 16px;">
          <div>
            <h1 class="df-title-xl">My Projects</h1>
            <p class="df-lead">Open, rename, regenerate, or export documentation workspaces.</p>
          </div>
          <a href="/playground" class="df-btn df-btn-primary" data-link>
            ${icons.sparkles(16)} New Documentation
          </a>
        </div>

        <!-- Search & Filter Bar -->
        <div class="df-card" style="padding: 14px 20px; margin-bottom: 20px;">
          <div style="position: relative; max-width: 420px;">
            <div style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-tertiary); display: flex; align-items: center;">
              ${icons.search(16)}
            </div>
            <input 
              class="df-input" 
              id="df-project-search" 
              placeholder="Search projects by name, language, or doc type..." 
              value="${escapeHtml(searchQuery)}"
              style="padding-left: 38px; width: 100%;"
            >
          </div>
        </div>

        <!-- Projects List or Empty State -->
        <div class="df-card" style="padding: 20px;">
          ${filtered.length > 0 ? `
            <div style="display: flex; flex-direction: column; gap: 12px;">
              ${filtered.map(p => {
                const isDoc = p.status === 'Documented';
                return `
                  <div style="display: flex; align-items: center; justify-content: space-between; padding: 16px 18px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md); flex-wrap: wrap; gap: 14px; transition: border-color var(--trans-fast);">
                    <div style="min-width: 0; flex: 1 1 180px;">
                      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                        <a href="/documentation?project_id=${p.id}" class="df-title-md" data-link style="color: var(--text-primary); text-decoration: none;">
                          ${escapeHtml(p.name)}
                        </a>
                        <span class="df-badge ${isDoc ? 'df-badge-documented' : 'df-badge-draft'}">
                          ${isDoc ? `${icons.check(12)} Documented` : 'Draft'}
                        </span>
                      </div>
                      <div class="df-sub" style="font-size: var(--fs-xs);">
                        <span class="df-badge" style="padding: 2px 7px; font-size: 11px;">${escapeHtml(p.language)}</span>
                        &middot;
                        <span>${escapeHtml(p.doc_type || 'Complete technical documentation')}</span>
                        &middot;
                        <span>Updated ${new Date(p.updated || Date.now()).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                      <a href="/documentation?project_id=${p.id}" class="df-btn df-btn-sm df-btn-primary" data-link>
                        Open Workspace ${icons.arrowRight(13)}
                      </a>
                      <button class="df-btn df-btn-sm df-btn-rename" data-id="${p.id}" data-name="${escapeHtml(p.name)}">
                        ${icons.edit(13)} Rename
                      </button>
                      <button class="df-btn df-btn-sm df-btn-danger df-btn-delete" data-id="${p.id}" data-name="${escapeHtml(p.name)}">
                        ${icons.trash(13)} Delete
                      </button>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          ` : `
            <div style="text-align: center; padding: 56px 20px;">
              <div style="color: var(--text-tertiary); margin-bottom: 12px;">${icons.fileText(36)}</div>
              <h3 class="df-title-md" style="margin-bottom: 6px;">${searchQuery ? 'No matching projects' : 'No documentation projects yet'}</h3>
              <p class="df-sub" style="max-width: 420px; margin: 0 auto 20px;">
                ${searchQuery ? `No projects match "${escapeHtml(searchQuery)}". Try clearing your search query.` : 'Start your first documentation workspace by analyzing source code or uploading a repository.'}
              </p>
              <a href="/playground" class="df-btn df-btn-primary" data-link>
                ${icons.sparkles(16)} Document Your First Codebase
              </a>
            </div>
          `}
        </div>
      </main>
    `;

    // Search input handler
    const searchInput = document.getElementById('df-project-search');
    if (searchInput) {
      searchInput.oninput = (e) => {
        searchQuery = e.target.value;
        renderList();
        const inputAfterRender = document.getElementById('df-project-search');
        if (inputAfterRender) {
          inputAfterRender.focus();
          inputAfterRender.setSelectionRange(searchQuery.length, searchQuery.length);
        }
      };
    }

    // Rename handlers
    container.querySelectorAll('.df-btn-rename').forEach(b => {
      b.onclick = async () => {
        const id = b.dataset.id;
        const curName = b.dataset.name;
        const newName = prompt('Enter new project name:', curName);
        if (newName && newName.trim() && newName.trim() !== curName) {
          try {
            const p = state.projects.find(x => String(x.id) === String(id));
            const updated = await api.updateProject(id, { ...p, name: newName.trim() });
            showToast(`Renamed project to "${newName.trim()}"`);
            state.projects = state.projects.map(x => String(x.id) === String(id) ? updated : x);
            renderList();
          } catch (e) {
            showToast(e.message || 'Failed to rename project', true);
          }
        }
      };
    });

    // Delete handlers
    container.querySelectorAll('.df-btn-delete').forEach(b => {
      b.onclick = async () => {
        const id = b.dataset.id;
        const name = b.dataset.name;
        if (confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) {
          try {
            await api.deleteProject(id);
            showToast(`Deleted project "${name}"`);
            state.projects = state.projects.filter(x => String(x.id) !== String(id));
            renderList();
          } catch (e) {
            showToast(e.message || 'Failed to delete project', true);
          }
        }
      };
    });
  }

  renderList();
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

