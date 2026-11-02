/**
 * DocuForge AI — Settings Component (/settings)
 * Gemini Service Status, Active Model, Default Language & Doc Type Preferences, Theme Switcher
 */

import { state, setTheme, LANGS, DOC_TYPES } from '../state.js';
import { api, showToast } from '../api.js';
import { renderNavbar } from '../router.js';
import { icons } from '../icons.js';

export async function renderSettings(container) {
  try {
    state.status = await api.getStatus();
  } catch (e) {
    showToast('Failed to load status: ' + e.message, true);
  }

  const isConfigured = Boolean(state.status?.gemini_configured);
  const activeModel = state.status?.model || 'gemini-3.5-flash';
  const rateLimits = state.status?.rate_limits;

  container.innerHTML = `
    ${renderNavbar('/settings')}
    <main class="df-page" id="main-content" style="max-width: 720px;">
      <div style="margin-bottom: 28px;">
        <h1 class="df-title-xl">Settings</h1>
        <p class="df-lead">Configure Gemini AI integration, default generation options, and workspace preferences.</p>
      </div>

      <!-- Gemini AI Service Card -->
      <div class="df-card" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <h2 class="df-title-md" style="margin: 0;">Gemini AI Integration</h2>
          <span class="df-badge ${isConfigured ? 'df-badge-documented' : 'df-badge-failed'}">
            ${isConfigured ? `${icons.check(12)} Configured` : `${icons.alert(12)} Missing Key`}
          </span>
        </div>

        <div style="padding: 14px 16px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md); margin-bottom: 18px;">
          <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
            <div>
              <b style="font-size: var(--fs-sm);">API Credential Status</b>
              <div class="df-sub" style="font-size: var(--fs-xs); margin-top: 2px;">
                ${isConfigured ? 'API key is securely managed server-side in <code>.env</code>. Never exposed to browser.' : 'No API key detected in server environment.'}
              </div>
            </div>
            <span class="df-mono df-sub" style="font-size: 11px; background: var(--bg-surface); padding: 4px 8px; border-radius: var(--r-xs); border: 1px solid var(--border-subtle);">
              ${isConfigured ? 'SERVER-SIDE LOADED' : 'UNCONFIGURED'}
            </span>
          </div>
        </div>

        <div class="df-field-group">
          <label class="df-label" for="df-active-model">
            <span>Active Model</span>
            <span class="df-sub" style="font-size: 11px;">Configured in <code>.env</code></span>
          </label>
          <input id="df-active-model" class="df-input df-mono" aria-label="Active Model" value="${escapeHtml(activeModel)}" readonly disabled style="opacity: 0.85;">
          <div class="df-sub" style="margin-top: 4px; font-size: 11px;">
            Primary model for zero-shot structured technical documentation synthesis.
          </div>
        </div>
      </div>

      <!-- Usage & Quota Limits Card -->
      <div class="df-card" style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <h2 class="df-title-md" style="margin: 0;">Usage & Quota Protection</h2>
          <span class="df-badge ${rateLimits?.enabled !== false ? 'df-badge-documented' : ''}">
            ${rateLimits?.enabled !== false ? `${icons.check(12)} Active Protection` : 'Disabled'}
          </span>
        </div>

        <p class="df-sub" style="margin-bottom: 16px;">
          Read-only system rate limits configured server-side via environment variables to protect Gemini API quotas.
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
          <div style="padding: 12px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md);">
            <div class="df-sub" style="font-size: var(--fs-xs);">User Generations</div>
            <div style="font-size: var(--fs-md); font-weight: 600; margin-top: 2px;">
              ${rateLimits?.generations_per_hour ?? 5} / hour &middot; ${rateLimits?.generations_per_day ?? 15} / day
            </div>
            <div class="df-sub" style="font-size: 11px; margin-top: 2px; color: var(--text-tertiary);">RL_GENERATIONS_PER_HOUR</div>
          </div>
          <div style="padding: 12px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md);">
            <div class="df-sub" style="font-size: var(--fs-xs);">Section Regenerations</div>
            <div style="font-size: var(--fs-md); font-weight: 600; margin-top: 2px;">
              ${rateLimits?.regenerations_per_hour ?? 15} / hour
            </div>
            <div class="df-sub" style="font-size: 11px; margin-top: 2px; color: var(--text-tertiary);">RL_REGENERATIONS_PER_HOUR</div>
          </div>
          <div style="padding: 12px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md);">
            <div class="df-sub" style="font-size: var(--fs-xs);">Concurrency & Uploads</div>
            <div style="font-size: var(--fs-md); font-weight: 600; margin-top: 2px;">
              ${rateLimits?.max_concurrent_jobs ?? 1} job &middot; ${rateLimits?.uploads_per_minute ?? 10} uploads/min
            </div>
            <div class="df-sub" style="font-size: 11px; margin-top: 2px; color: var(--text-tertiary);">RL_MAX_CONCURRENT_JOBS_PER_USER</div>
          </div>
          <div style="padding: 12px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--r-md);">
            <div class="df-sub" style="font-size: var(--fs-xs);">Global Gemini Budget</div>
            <div style="font-size: var(--fs-md); font-weight: 600; margin-top: 2px;">
              ${rateLimits?.global_requests_per_minute ?? 15} / min &middot; ${rateLimits?.global_daily_requests ?? 1500} / day
            </div>
            <div class="df-sub" style="font-size: 11px; margin-top: 2px; color: var(--text-tertiary);">RL_GLOBAL_REQUESTS_PER_MINUTE</div>
          </div>
        </div>
      </div>

      <!-- Workspace Preferences Card -->
      <div class="df-card">
        <h2 class="df-title-md" style="margin-bottom: 16px;">Workspace Defaults</h2>

        <div class="df-field-group">
          <label class="df-label" for="df-set-lang">Default Programming Language</label>
          <select class="df-select" id="df-set-lang" aria-label="Default Programming Language">
            ${LANGS.map(l => `<option value="${l}" ${l === state.defaultLang ? 'selected' : ''}>${l}</option>`).join('')}
          </select>
          <div class="df-sub" style="margin-top: 3px; font-size: 11px;">
            Pre-selected when drafting new documentation projects.
          </div>
        </div>

        <div class="df-field-group">
          <label class="df-label" for="df-set-type">Default Documentation Scope</label>
          <select class="df-select" id="df-set-type" aria-label="Default Documentation Scope">
            ${DOC_TYPES.map(t => `<option value="${t}" ${t === state.defaultDocType ? 'selected' : ''}>${t}</option>`).join('')}
          </select>
          <div class="df-sub" style="margin-top: 3px; font-size: 11px;">
            Target output type when creating a new documentation analysis.
          </div>
        </div>

        <div class="df-field-group" style="margin-bottom: 24px;">
          <label class="df-label">Visual Theme</label>
          <div class="df-grid-2col" style="margin-top: 4px;">
            <button class="df-btn ${state.theme === 'dark' ? 'df-btn-primary' : ''}" id="df-theme-dark" style="justify-content: center;">
              ${icons.moon(14)} Dark Theme
            </button>
            <button class="df-btn ${state.theme === 'light' ? 'df-btn-primary' : ''}" id="df-theme-light" style="justify-content: center;">
              ${icons.sun(14)} Light Theme
            </button>
          </div>
        </div>

        <div>
          <button class="df-btn df-btn-primary df-btn-lg" id="df-save-pref" style="width: 100%;">
            ${icons.check(14)} Save Preferences
          </button>
        </div>
      </div>
    </main>
  `;

  // Event handlers
  const darkBtn = document.getElementById('df-theme-dark');
  const lightBtn = document.getElementById('df-theme-light');
  const langSelect = document.getElementById('df-set-lang');
  const typeSelect = document.getElementById('df-set-type');
  const saveBtn = document.getElementById('df-save-pref');

  darkBtn.onclick = () => {
    setTheme('dark');
    renderSettings(container);
  };

  lightBtn.onclick = () => {
    setTheme('light');
    renderSettings(container);
  };

  saveBtn.onclick = () => {
    state.defaultLang = langSelect.value;
    state.defaultDocType = typeSelect.value;
    localStorage.setItem('df_default_lang', state.defaultLang);
    localStorage.setItem('df_default_doc_type', state.defaultDocType);
    showToast('Saved workspace preferences');
  };
}

function escapeHtml(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
